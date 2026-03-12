/**
 * DT-QUEST Equation Evaluator
 * Safe math expression parsing & evaluation using mathjs.
 * No eval() or Function() — only whitelisted operations.
 */

const { create, all } = require('mathjs');

// Create a restricted mathjs instance
const math = create(all);

// Whitelist: only these functions are available in equations
const ALLOWED_FUNCTIONS = new Set([
  'log10', 'log', 'log2', 'sqrt', 'pow', 'abs', 'exp',
  'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
  'ceil', 'floor', 'round', 'min', 'max', 'sign',
]);

// Built-in constants available in equations
const BUILTIN_CONSTANTS = {
  pi: Math.PI,
  PI: Math.PI,
  c: 3e8,           // speed of light (m/s)
  e: Math.E,
  k: 1.380649e-23,  // Boltzmann constant (J/K)
};

/**
 * Parse an equation string and extract variable names.
 * Throws if syntax is invalid or uses disallowed operations.
 * @param {string} exprString - e.g. "51.41 + 30*log10(d)"
 * @returns {{ parsed: object, variables: string[] }}
 */
function parseEquation(exprString) {
  if (!exprString || typeof exprString !== 'string') {
    throw new Error('Equation must be a non-empty string');
  }

  // Security: reject obvious injection patterns
  const banned = /require|import|process|global|__proto__|constructor|eval|Function/i;
  if (banned.test(exprString)) {
    throw new Error('Equation contains disallowed keywords');
  }

  let parsed;
  try {
    parsed = math.parse(exprString);
  } catch (err) {
    throw new Error(`Syntax error: ${err.message}`);
  }

  // Walk the AST to extract variables and validate function calls
  const variables = new Set();

  parsed.traverse((node) => {
    if (node.type === 'SymbolNode') {
      const name = node.name;
      // If it's not a built-in constant or allowed function, it's a variable
      if (!BUILTIN_CONSTANTS.hasOwnProperty(name) && !ALLOWED_FUNCTIONS.has(name)) {
        variables.add(name);
      }
    }
    if (node.type === 'FunctionNode') {
      const fname = node.fn.name || node.fn;
      if (!ALLOWED_FUNCTIONS.has(fname)) {
        throw new Error(`Function '${fname}' is not allowed. Allowed: ${[...ALLOWED_FUNCTIONS].join(', ')}`);
      }
    }
  });

  return {
    parsed,
    variables: [...variables],
  };
}

/**
 * Evaluate an equation for a single set of variable values.
 * @param {string} exprString
 * @param {object} variableValues - e.g. { d: 100, f: 5.9e9 }
 * @returns {number}
 */
function evaluateEquation(exprString, variableValues) {
  const { parsed } = parseEquation(exprString);
  const scope = { ...BUILTIN_CONSTANTS, ...variableValues };
  try {
    const result = parsed.evaluate(scope);
    return typeof result === 'number' ? result : NaN;
  } catch (err) {
    return NaN;
  }
}

/**
 * Run a validation equation across a dataset.
 *
 * @param {object} equation - equation definition:
 *   { id, name, type, equation, input_vars, measured_param, tolerance_db?, variable_mapping? }
 *   - type: 'reference_model' | 'relationship' | 'constraint'
 *   - input_vars: array of variable names used in the equation
 *   - variable_mapping: { equation_var: dataset_column_name }
 *   - measured_param: dataset column to compare against (for reference_model / relationship)
 * @param {Array} data - array of row objects
 * @param {object} mapping - param_key → column_name
 * @returns {object} validation results
 */
function runValidation(equation, data, mapping) {
  const {
    id, name, type, equation: exprString,
    input_vars = [], measured_param, tolerance_db = 3,
    variable_mapping = {},
  } = equation;

  // Parse once
  let parseResult;
  try {
    parseResult = parseEquation(exprString);
  } catch (err) {
    return {
      id, name, type,
      status: 'error',
      error: err.message,
    };
  }

  const { parsed, variables } = parseResult;

  // Build column lookup: for each variable in the equation, find the dataset column
  const varToCol = {};
  for (const v of variables) {
    if (variable_mapping[v]) {
      varToCol[v] = variable_mapping[v];
    } else if (mapping[v]) {
      varToCol[v] = mapping[v];
    } else {
      // Try using the variable name directly as a column name
      varToCol[v] = v;
    }
  }

  // Find the measured column
  const measuredCol = measured_param
    ? (mapping[measured_param] || measured_param)
    : null;

  if (type === 'constraint') {
    return _runConstraintValidation(parsed, varToCol, data, id, name);
  }

  if (!measuredCol) {
    return {
      id, name, type,
      status: 'error',
      error: 'No measured parameter specified for comparison',
    };
  }

  return _runModelValidation(parsed, varToCol, measuredCol, data, id, name, type, tolerance_db);
}

/**
 * Reference model / relationship validation:
 * Compare predicted values from equation to measured column.
 */
function _runModelValidation(parsed, varToCol, measuredCol, data, id, name, type, tolerance_db) {
  const predicted = [];
  const measured = [];
  const residuals = [];
  let validCount = 0;

  for (const row of data) {
    // Build variable scope for this row
    const scope = { ...BUILTIN_CONSTANTS };
    let skip = false;
    for (const [varName, colName] of Object.entries(varToCol)) {
      const val = _toNumber(row[colName]);
      if (val === null || isNaN(val)) { skip = true; break; }
      scope[varName] = val;
    }
    if (skip) continue;

    const measuredVal = _toNumber(row[measuredCol]);
    if (measuredVal === null || isNaN(measuredVal)) continue;

    try {
      const predVal = parsed.evaluate(scope);
      if (typeof predVal !== 'number' || isNaN(predVal) || !isFinite(predVal)) continue;

      predicted.push(predVal);
      measured.push(measuredVal);
      residuals.push(Math.abs(predVal - measuredVal));
      validCount++;
    } catch (e) {
      continue;
    }
  }

  if (validCount < 2) {
    return {
      id, name, type,
      status: 'insufficient_data',
      error: `Only ${validCount} valid data point(s) — need at least 2`,
      valid_count: validCount,
    };
  }

  // Compute statistics
  const mae = residuals.reduce((s, v) => s + v, 0) / validCount;
  const rmse = Math.sqrt(residuals.reduce((s, v) => s + v * v, 0) / validCount);
  const withinTolerance = residuals.filter(r => r <= tolerance_db).length;
  const pctWithinTolerance = (withinTolerance / validCount) * 100;

  // R² (coefficient of determination)
  const meanMeasured = measured.reduce((s, v) => s + v, 0) / validCount;
  const ssTot = measured.reduce((s, v) => s + (v - meanMeasured) ** 2, 0);
  const ssRes = residuals.reduce((s, v) => s + v * v, 0);
  const rSquared = ssTot > 0 ? 1 - ssRes / ssTot : 0;

  // Correlation
  const meanPredicted = predicted.reduce((s, v) => s + v, 0) / validCount;
  let num = 0, denA = 0, denB = 0;
  for (let i = 0; i < validCount; i++) {
    const dp = predicted[i] - meanPredicted;
    const dm = measured[i] - meanMeasured;
    num += dp * dm;
    denA += dp * dp;
    denB += dm * dm;
  }
  const correlation = (denA > 0 && denB > 0) ? num / Math.sqrt(denA * denB) : 0;

  // Sample for scatter plot (max 500 points)
  const sampleSize = Math.min(validCount, 500);
  const step = Math.max(1, Math.floor(validCount / sampleSize));

  const scatterPredicted = [];
  const scatterMeasured = [];
  for (let i = 0; i < validCount; i += step) {
    scatterPredicted.push(+predicted[i].toFixed(2));
    scatterMeasured.push(+measured[i].toFixed(2));
  }

  // Status
  let status;
  if (mae <= tolerance_db) status = 'pass';
  else if (mae <= tolerance_db * 2) status = 'marginal';
  else status = 'fail';

  return {
    id, name, type, status,
    valid_count: validCount,
    mae: +mae.toFixed(2),
    rmse: +rmse.toFixed(2),
    r_squared: +rSquared.toFixed(4),
    correlation: +correlation.toFixed(4),
    pct_within_tolerance: +pctWithinTolerance.toFixed(1),
    tolerance_db,
    scatter_sample: {
      predicted: scatterPredicted,
      measured: scatterMeasured,
    },
  };
}

/**
 * Constraint validation:
 * Evaluate a boolean expression for each row.
 */
function _runConstraintValidation(parsed, varToCol, data, id, name) {
  let passCount = 0;
  let failCount = 0;
  let skipCount = 0;

  for (const row of data) {
    const scope = { ...BUILTIN_CONSTANTS };
    let skip = false;
    for (const [varName, colName] of Object.entries(varToCol)) {
      const val = _toNumber(row[colName]);
      if (val === null || isNaN(val)) { skip = true; break; }
      scope[varName] = val;
    }
    if (skip) { skipCount++; continue; }

    try {
      const result = parsed.evaluate(scope);
      if (result === true || result === 1) passCount++;
      else failCount++;
    } catch (e) {
      skipCount++;
    }
  }

  const total = passCount + failCount;
  const passRate = total > 0 ? (passCount / total) * 100 : 0;

  return {
    id, name, type: 'constraint',
    status: passRate >= 95 ? 'pass' : passRate >= 80 ? 'marginal' : 'fail',
    pass_count: passCount,
    fail_count: failCount,
    skip_count: skipCount,
    pass_rate: +passRate.toFixed(1),
    total_evaluated: total,
  };
}

function _toNumber(val) {
  if (val === null || val === undefined || val === '') return null;
  const n = Number(val);
  return isNaN(n) ? null : n;
}

module.exports = { parseEquation, evaluateEquation, runValidation, BUILTIN_CONSTANTS, ALLOWED_FUNCTIONS };
