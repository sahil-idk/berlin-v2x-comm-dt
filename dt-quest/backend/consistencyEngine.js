/**
 * DT-QUEST Consistency Engine
 * Adaptive cross-parameter consistency checking that dynamically discovers
 * applicable checks based on mapped columns and domain rules.
 */

const ss = require('simple-statistics');

// ── Helpers ──────────────────────────────────────────────────

function toNumber(val) {
  if (val === null || val === undefined || val === '') return null;
  const num = Number(val);
  return isNaN(num) ? null : num;
}

function pearsonCorrelation(x, y) {
  if (x.length !== y.length || x.length < 3) return null;
  try {
    const meanX = ss.mean(x);
    const meanY = ss.mean(y);
    const stdX = ss.standardDeviation(x);
    const stdY = ss.standardDeviation(y);
    if (stdX === 0 || stdY === 0) return null;
    let sum = 0;
    for (let i = 0; i < x.length; i++) {
      sum += ((x[i] - meanX) / stdX) * ((y[i] - meanY) / stdY);
    }
    return sum / (x.length - 1);
  } catch (e) {
    return null;
  }
}

function histogram(values, bins = 30) {
  if (values.length === 0) return { counts: [], bins: [] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const binWidth = (max - min) / bins || 1;
  const counts = new Array(bins).fill(0);
  const binEdges = [];
  for (let i = 0; i <= bins; i++) binEdges.push(min + i * binWidth);
  values.forEach(v => {
    const idx = Math.min(Math.floor((v - min) / binWidth), bins - 1);
    if (idx >= 0 && idx < bins) counts[idx]++;
  });
  return { counts, bins: binEdges };
}

// ── Phase 1: Discovery ──────────────────────────────────────

/**
 * Scan domain consistency_rules against the current column mapping
 * to determine which checks can actually be executed.
 */
function discoverApplicableChecks(rules, mapping) {
  const applicable = [];
  const unavailable = [];

  for (const rule of rules) {
    const requiredParams = getRequiredParams(rule);
    const missingParams = requiredParams.filter(p => !mapping[p]);

    if (missingParams.length === 0) {
      applicable.push({
        id: rule.id,
        name: rule.name,
        description: rule.description || '',
        type: rule.type,
        criticality: rule.criticality || 'recommended',
        required_params: requiredParams,
        all_mapped: true,
        rule,
      });
    } else {
      unavailable.push({
        id: rule.id,
        name: rule.name,
        description: rule.description || '',
        type: rule.type,
        criticality: rule.criticality || 'recommended',
        required_params: requiredParams,
        missing_params: missingParams,
        reason: `Missing mapped column(s): ${missingParams.join(', ')}`,
      });
    }
  }

  return { applicable, unavailable };
}

/**
 * Extract the parameter keys that a rule needs.
 */
function getRequiredParams(rule) {
  if (rule.type === 'relationship' && rule.formula) {
    const params = [];
    if (rule.formula.derived_param) params.push(rule.formula.derived_param);
    if (rule.formula.component_a) params.push(rule.formula.component_a);
    if (rule.formula.component_b) params.push(rule.formula.component_b);
    return params;
  }
  if (rule.type === 'correlation' && rule.correlation) {
    return [rule.correlation.param_a, rule.correlation.param_b].filter(Boolean);
  }
  return [];
}

/**
 * Agentic discovery: scan all numeric column pairs for significant correlations.
 * Returns suggestions for pairs with |r| above the threshold.
 */
function autoDetectCorrelations(data, mapping, threshold = 0.3) {
  const numericParams = [];
  for (const [paramKey, colName] of Object.entries(mapping)) {
    // Quick check: at least some rows have numeric values
    let numericCount = 0;
    for (let i = 0; i < Math.min(data.length, 100); i++) {
      if (toNumber(data[i][colName]) !== null) numericCount++;
    }
    if (numericCount > 10) {
      numericParams.push({ paramKey, colName });
    }
  }

  const suggestions = [];
  for (let i = 0; i < numericParams.length; i++) {
    for (let j = i + 1; j < numericParams.length; j++) {
      const a = numericParams[i];
      const b = numericParams[j];

      // Build paired arrays (skip rows where either is null)
      const xVals = [];
      const yVals = [];
      for (let k = 0; k < data.length; k++) {
        const xv = toNumber(data[k][a.colName]);
        const yv = toNumber(data[k][b.colName]);
        if (xv !== null && yv !== null) {
          xVals.push(xv);
          yVals.push(yv);
        }
        // Cap at 5000 for performance
        if (xVals.length >= 5000) break;
      }

      if (xVals.length < 30) continue;

      const r = pearsonCorrelation(xVals, yVals);
      if (r !== null && Math.abs(r) >= threshold) {
        const direction = r > 0 ? 'positive' : 'negative';
        suggestions.push({
          param_a: a.paramKey,
          param_b: b.paramKey,
          col_a: a.colName,
          col_b: b.colName,
          correlation: parseFloat(r.toFixed(4)),
          direction,
          sample_size: xVals.length,
          suggestion: `${a.paramKey} and ${b.paramKey} show ${Math.abs(r) > 0.7 ? 'strong' : 'moderate'} ${direction} correlation (r = ${r.toFixed(3)})`,
        });
      }
    }
  }

  // Sort by absolute correlation descending
  suggestions.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
  return suggestions.slice(0, 20); // Cap at 20 suggestions
}

// ── Phase 2: Row Integrity ──────────────────────────────────

/**
 * Audit per-row completeness for the specified columns.
 * Returns per-column null stats and a global integrity score.
 */
function auditRowIntegrity(data, mapping, columnCriticality = {}) {
  const columns = Object.entries(mapping);
  const totalRows = data.length;

  const columnStats = {};
  let completeRows = 0;

  // Per-column null counts
  for (const [paramKey, colName] of columns) {
    let nullCount = 0;
    for (let i = 0; i < totalRows; i++) {
      const val = data[i][colName];
      if (val === null || val === undefined || val === '' ||
          (typeof val === 'number' && isNaN(val))) {
        nullCount++;
      }
    }
    columnStats[paramKey] = {
      column: colName,
      null_count: nullCount,
      null_pct: totalRows > 0 ? parseFloat(((nullCount / totalRows) * 100).toFixed(2)) : 0,
      completeness_pct: totalRows > 0 ? parseFloat((((totalRows - nullCount) / totalRows) * 100).toFixed(2)) : 0,
      criticality: columnCriticality[paramKey] || 'recommended',
    };
  }

  // Count rows where ALL mapped columns are non-null
  for (let i = 0; i < totalRows; i++) {
    let allPresent = true;
    for (const [, colName] of columns) {
      const val = data[i][colName];
      if (val === null || val === undefined || val === '' ||
          (typeof val === 'number' && isNaN(val))) {
        allPresent = false;
        break;
      }
    }
    if (allPresent) completeRows++;
  }

  return {
    total_rows: totalRows,
    complete_rows: completeRows,
    integrity_score: totalRows > 0 ? parseFloat(((completeRows / totalRows) * 100).toFixed(2)) : 0,
    column_stats: columnStats,
  };
}

/**
 * Apply null-handling strategies per column.
 * strategyMap: { paramKey: { action: 'remove'|'impute_mean'|'impute_median'|'exclude'|'keep', column: colName } }
 * Returns { data, removedRows, imputedCells, excludedColumns }
 */
function applyNullStrategy(data, strategyMap) {
  let result = [...data];
  const stats = { removed_rows: 0, imputed_cells: {}, excluded_columns: [] };
  const rowsToRemove = new Set();

  for (const [paramKey, strategy] of Object.entries(strategyMap)) {
    const colName = strategy.column;
    if (!colName) continue;

    if (strategy.action === 'remove') {
      for (let i = 0; i < result.length; i++) {
        const val = result[i][colName];
        if (val === null || val === undefined || val === '' ||
            (typeof val === 'number' && isNaN(val))) {
          rowsToRemove.add(i);
        }
      }
    } else if (strategy.action === 'impute_mean' || strategy.action === 'impute_median') {
      const numericVals = [];
      for (let i = 0; i < result.length; i++) {
        const n = toNumber(result[i][colName]);
        if (n !== null) numericVals.push(n);
      }
      if (numericVals.length > 0) {
        const fillValue = strategy.action === 'impute_mean'
          ? ss.mean(numericVals)
          : ss.median(numericVals);
        let count = 0;
        for (let i = 0; i < result.length; i++) {
          const val = result[i][colName];
          if (val === null || val === undefined || val === '' ||
              (typeof val === 'number' && isNaN(val))) {
            result[i] = { ...result[i], [colName]: fillValue };
            count++;
          }
        }
        stats.imputed_cells[paramKey] = { count, fill_value: parseFloat(fillValue.toFixed(4)), method: strategy.action };
      }
    } else if (strategy.action === 'exclude') {
      stats.excluded_columns.push(paramKey);
    }
    // 'keep' → do nothing
  }

  // Remove flagged rows
  if (rowsToRemove.size > 0) {
    result = result.filter((_, i) => !rowsToRemove.has(i));
    stats.removed_rows = rowsToRemove.size;
  }

  return { data: result, stats };
}

// ── Phase 3: Validation ─────────────────────────────────────

/**
 * Execute a relationship check: derived_param ≈ component_a <op> component_b
 */
function runRelationshipCheck(data, rule, mapping) {
  const formula = rule.formula;
  if (!formula) return { status: 'error', reason: 'No formula defined' };

  const derivedCol = mapping[formula.derived_param];
  const compACol = mapping[formula.component_a];
  const compBCol = mapping[formula.component_b];

  if (!derivedCol || !compACol || !compBCol) {
    return { status: 'error', reason: 'Required columns not mapped' };
  }

  const tolerance = rule.tolerance_db || 3;

  // Build paired data
  const validData = [];
  for (let i = 0; i < data.length; i++) {
    const derived = toNumber(data[i][derivedCol]);
    const compA = toNumber(data[i][compACol]);
    const compB = toNumber(data[i][compBCol]);
    if (derived !== null && compA !== null && compB !== null) {
      validData.push({ derived, compA, compB });
    }
  }

  if (validData.length < 10) {
    return { status: 'insufficient_data', reason: `Only ${validData.length} valid rows (need >= 10)`, valid_rows: validData.length };
  }

  // Mode A: direct subtraction (dBm assumption)
  const computedA = validData.map(d => {
    if (formula.operator === 'subtract') return d.compA - d.compB;
    if (formula.operator === 'add') return d.compA + d.compB;
    return d.compA - d.compB;
  });
  const measured = validData.map(d => d.derived);

  const residualsA = computedA.map((c, i) => Math.abs(c - measured[i]));
  const pctWithinTolA = parseFloat(((residualsA.filter(r => r <= tolerance).length / residualsA.length) * 100).toFixed(2));
  const corrA = pearsonCorrelation(computedA, measured);
  const meanResidualA = parseFloat(ss.mean(residualsA).toFixed(3));

  const modeA = {
    name: 'dBm (logarithmic)',
    correlation: corrA !== null ? parseFloat(corrA.toFixed(4)) : 0,
    pct_within_tolerance: pctWithinTolA,
    mean_residual: meanResidualA,
    tolerance_db: tolerance,
    scatter_data: {
      derived: computedA.slice(0, 500),
      measured: measured.slice(0, 500),
    },
    residual_histogram: histogram(residualsA, 30).counts,
  };

  // Mode B: linear watts assumption (10*log10 conversion)
  const linearValid = validData.filter(d => d.compA > 0 && d.compB > 0);
  let modeB;
  if (linearValid.length > 10) {
    const computedB = linearValid.map(d => {
      if (formula.operator === 'subtract') return 10 * Math.log10(d.compA) - 10 * Math.log10(d.compB);
      return 10 * Math.log10(d.compA) - 10 * Math.log10(d.compB);
    });
    const measuredB = linearValid.map(d => d.derived);
    const residualsB = computedB.map((c, i) => Math.abs(c - measuredB[i]));
    const pctWithinTolB = parseFloat(((residualsB.filter(r => r <= tolerance).length / residualsB.length) * 100).toFixed(2));
    const corrB = pearsonCorrelation(computedB, measuredB);

    modeB = {
      name: 'Linear watts (needs conversion)',
      correlation: corrB !== null ? parseFloat(corrB.toFixed(4)) : 0,
      pct_within_tolerance: pctWithinTolB,
      mean_residual: parseFloat(ss.mean(residualsB).toFixed(3)),
      tolerance_db: tolerance,
      scatter_data: {
        derived: computedB.slice(0, 500),
        measured: measuredB.slice(0, 500),
      },
      residual_histogram: histogram(residualsB, 30).counts,
    };
  } else {
    modeB = { name: 'Linear watts', status: 'not_applicable', reason: 'Values contain zeros or negatives' };
  }

  // Verdict
  const scoreA = (corrA || 0) * 0.5 + pctWithinTolA / 200;
  const scoreB = modeB.correlation ? modeB.correlation * 0.5 + (modeB.pct_within_tolerance || 0) / 200 : 0;

  let verdict;
  if (scoreA > 0.85) {
    verdict = { status: 'pass', message: 'Values are in dBm scale - relationship holds', score: scoreA };
  } else if (scoreB > scoreA && scoreB > 0.85) {
    verdict = { status: 'warning', message: 'Representation Error: values appear to be in linear watts', score: scoreB };
  } else if (scoreA > 0.5 || scoreB > 0.5) {
    verdict = { status: 'marginal', message: 'Weak cross-parameter consistency', score: Math.max(scoreA, scoreB) };
  } else {
    verdict = { status: 'fail', message: 'Cross-parameter relationship does not hold', score: Math.max(scoreA, scoreB) };
  }

  return {
    check_id: rule.id,
    check_name: rule.name,
    type: 'relationship',
    status: verdict.status,
    valid_rows: validData.length,
    mode_a: modeA,
    mode_b: modeB,
    verdict,
  };
}

/**
 * Execute a correlation check: verify two params have expected correlation direction.
 */
function runCorrelationCheck(data, rule, mapping) {
  const corr = rule.correlation;
  if (!corr) return { status: 'error', reason: 'No correlation config defined' };

  const colA = mapping[corr.param_a];
  const colB = mapping[corr.param_b];
  if (!colA || !colB) return { status: 'error', reason: 'Required columns not mapped' };

  const xVals = [];
  const yVals = [];
  for (let i = 0; i < data.length; i++) {
    const xv = toNumber(data[i][colA]);
    const yv = toNumber(data[i][colB]);
    if (xv !== null && yv !== null) {
      xVals.push(xv);
      yVals.push(yv);
    }
  }

  if (xVals.length < 10) {
    return {
      check_id: rule.id,
      check_name: rule.name,
      type: 'correlation',
      status: 'insufficient_data',
      reason: `Only ${xVals.length} paired data points (need >= 10)`,
      valid_rows: xVals.length,
    };
  }

  const r = pearsonCorrelation(xVals, yVals);
  if (r === null) {
    return {
      check_id: rule.id,
      check_name: rule.name,
      type: 'correlation',
      status: 'error',
      reason: 'Could not compute correlation (zero variance)',
    };
  }

  const expectedDir = corr.expected_direction || 'positive';
  const minAbs = corr.min_abs_correlation || 0.2;
  const actualDir = r > 0 ? 'positive' : 'negative';
  const directionMatch = expectedDir === actualDir;
  const strengthOk = Math.abs(r) >= minAbs;

  let status;
  if (directionMatch && strengthOk) status = 'pass';
  else if (directionMatch && !strengthOk) status = 'marginal';
  else status = 'fail';

  return {
    check_id: rule.id,
    check_name: rule.name,
    type: 'correlation',
    status,
    valid_rows: xVals.length,
    correlation: parseFloat(r.toFixed(4)),
    expected_direction: expectedDir,
    actual_direction: actualDir,
    direction_match: directionMatch,
    min_abs_correlation: minAbs,
    strength_ok: strengthOk,
    scatter_data: {
      x: xVals.slice(0, 500),
      y: yVals.slice(0, 500),
      x_label: corr.param_a,
      y_label: corr.param_b,
    },
    verdict: {
      status,
      message: status === 'pass'
        ? `${corr.param_a} and ${corr.param_b} show expected ${expectedDir} correlation (r = ${r.toFixed(3)})`
        : status === 'marginal'
        ? `Direction correct but weak correlation (r = ${r.toFixed(3)}, threshold = ${minAbs})`
        : `Expected ${expectedDir} but got ${actualDir} correlation (r = ${r.toFixed(3)})`,
    },
  };
}

module.exports = {
  discoverApplicableChecks,
  autoDetectCorrelations,
  runRelationshipCheck,
  runCorrelationCheck,
  auditRowIntegrity,
  applyNullStrategy,
};
