/**
 * DT-QUEST Backend API
 * Digital Twin QUality Evaluation for Simulation-ready Transport
 * Node.js/Express Implementation
 */

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const Papa = require('papaparse');
const ss = require('simple-statistics');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');
const path = require('path');
const domainRegistry = require('./domains/registry');
const sessionStore = require('./sessionStore');
const equationEvaluator = require('./equationEvaluator');
const consistencyEngine = require('./consistencyEngine');

const app = express();
const PORT = 8000;

// Middleware
app.use(cors());
app.use(express.json());

// File upload configuration
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// Helper: get domain config for a session (falls back to default)
function getSessionDomain(sessionId) {
  const domainId = datasets[sessionId]?.domainId || 'its-v2x';
  return domainRegistry.getDomain(domainId) || domainRegistry.getDefaultDomain();
}

// Helper: get parameter ranges for a session's domain
function getSessionParameterRanges(sessionId) {
  const domainId = datasets[sessionId]?.domainId || 'its-v2x';
  return domainRegistry.getParameterRanges(domainId);
}

// In-memory storage for uploaded data
const datasets = {};

// Rehydrate sessions from disk on startup
try {
  const savedSessions = sessionStore.listSessions();
  savedSessions.forEach(summary => {
    const full = sessionStore.loadSession(summary.sessionId);
    if (full && full.data && full.data.length > 0) {
      datasets[summary.sessionId] = {
        data: full.data,
        columns: full.columns || (full.data.length > 0 ? Object.keys(full.data[0]) : []),
        mapping: full.mapping || {},
        filename: full.filename,
        domainId: full.domainId || 'its-v2x',
        pipelineResults: full.pipelineResults || {},
        appliedCorrections: full.appliedCorrections || null,
        cleanedData: full.cleanedDataSample || null,
        cleanedColumns: full.cleanedColumns || null,
        customEquations: full.customEquations || [],
        createdAt: full.createdAt,
      };
      console.log(`[Session] Restored: ${summary.sessionId} (${full.data.length} rows)`);
    }
  });
  if (savedSessions.length > 0) {
    console.log(`[Session] ${Object.keys(datasets).length} session(s) rehydrated from disk.`);
  }
} catch (err) {
  console.error('[Session] Failed to rehydrate sessions:', err.message);
}

// Helper: Convert value to number, return null if not possible
function toNumber(val) {
  if (val === null || val === undefined || val === '') return null;
  const num = Number(val);
  return isNaN(num) ? null : num;
}

// Helper: Get numeric column data
function getNumericColumn(data, colName) {
  return data
    .map(row => toNumber(row[colName]))
    .filter(v => v !== null);
}

// Helper: Calculate histogram
function histogram(values, bins = 50) {
  if (values.length === 0) return { counts: [], bins: [] };
  
  const min = Math.min(...values);
  const max = Math.max(...values);
  const binWidth = (max - min) / bins || 1;
  
  const counts = new Array(bins).fill(0);
  const binEdges = [];
  
  for (let i = 0; i <= bins; i++) {
    binEdges.push(min + i * binWidth);
  }
  
  values.forEach(v => {
    const binIndex = Math.min(Math.floor((v - min) / binWidth), bins - 1);
    if (binIndex >= 0 && binIndex < bins) {
      counts[binIndex]++;
    }
  });
  
  return { counts, bins: binEdges };
}

// Helper: Pearson correlation
function pearsonCorrelation(x, y) {
  if (x.length !== y.length || x.length < 2) return 0;
  try {
    const meanX = ss.mean(x);
    const meanY = ss.mean(y);
    const stdX = ss.standardDeviation(x);
    const stdY = ss.standardDeviation(y);
    
    if (stdX === 0 || stdY === 0) return 0;
    
    let sum = 0;
    for (let i = 0; i < x.length; i++) {
      sum += ((x[i] - meanX) / stdX) * ((y[i] - meanY) / stdY);
    }
    return sum / (x.length - 1);
  } catch (e) {
    return 0;
  }
}

// Routes

app.get('/', (req, res) => {
  res.json({ message: 'DT-QUEST API is running', version: '1.0.0' });
});

// Domain listing
app.get('/domains', (req, res) => {
  res.json(domainRegistry.getAllDomains());
});

// Session management endpoints
app.get('/sessions', (req, res) => {
  res.json(sessionStore.listSessions());
});

app.delete('/sessions/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  if (datasets[sessionId]) delete datasets[sessionId];
  sessionStore.deleteSession(sessionId);
  res.json({ status: 'deleted', sessionId });
});

// Set domain for a session
app.post('/session/:sessionId/domain', (req, res) => {
  const { sessionId } = req.params;
  const { domainId } = req.body;

  if (!datasets[sessionId]) {
    return res.status(404).json({ detail: 'Session not found' });
  }
  const domain = domainRegistry.getDomain(domainId);
  if (!domain) {
    return res.status(400).json({ detail: `Domain '${domainId}' not found` });
  }

  datasets[sessionId].domainId = domainId;
  // Reset pipeline results when domain changes
  datasets[sessionId].mapping = {};
  datasets[sessionId].pipelineResults = {};
  
  res.json({ status: 'success', domain: domain.domain.name });
});

app.get('/presets', (req, res) => {
  const domainId = req.query.domain || 'its-v2x';
  res.json(domainRegistry.getPresets(domainId));
});

app.get('/parameter-ranges', (req, res) => {
  const domainId = req.query.domain || 'its-v2x';
  res.json(domainRegistry.getParameterRanges(domainId));
});

// Full parameter details for a domain (used by column mapping UI)
app.get('/domain/:domainId/parameters', (req, res) => {
  const domain = domainRegistry.getDomain(req.params.domainId);
  if (!domain) {
    return res.status(404).json({ detail: `Domain '${req.params.domainId}' not found` });
  }
  // Return parameters as an object keyed by parameter key for easy lookup
  const params = {};
  for (const p of domain.parameters) {
    params[p.key] = {
      label: p.label,
      unit: p.unit,
      category: p.category || 'other',
      required: p.required || false,
      range: p.range || null,
      description: p.description || ''
    };
  }
  res.json(params);
});

// Upload endpoint
app.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ detail: 'No file uploaded' });
    }

    const filename = req.file.originalname.toLowerCase();
    let data = [];
    let columns = [];

    if (filename.endsWith('.csv')) {
      const csvString = req.file.buffer.toString('utf-8');
      const parsed = Papa.parse(csvString, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true
      });
      data = parsed.data;
      columns = parsed.meta.fields || [];
    } else if (filename.endsWith('.parquet')) {
      return res.status(400).json({ 
        detail: 'Parquet not supported in Node.js version. Please convert to CSV.' 
      });
    } else {
      return res.status(400).json({ detail: 'Unsupported file format. Use CSV.' });
    }

    // Generate session ID
    const sessionId = `session_${Date.now()}_${uuidv4().slice(0, 4)}`;

    // Store dataset
    const domainId = req.body?.domain || 'its-v2x';
    datasets[sessionId] = {
      data: data,
      domainId: domainId,
      filename: req.file.originalname,
      columns: columns,
      mapping: {},
      pipelineResults: {}
    };

    // Calculate NaN counts
    const nanCounts = {};
    columns.forEach(col => {
      nanCounts[col] = data.filter(row => 
        row[col] === null || row[col] === undefined || row[col] === '' || 
        (typeof row[col] === 'number' && isNaN(row[col]))
      ).length;
    });

    // Get preview
    const preview = data.slice(0, 10);

    res.json({
      session_id: sessionId,
      filename: req.file.originalname,
      rows: data.length,
      columns: columns.length,
      file_size: req.file.size,
      column_names: columns,
      preview: preview,
      nan_counts: nanCounts
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Set column mapping
app.post('/mapping/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  
  if (!datasets[sessionId]) {
    return res.status(404).json({ detail: 'Session not found' });
  }

  const mapping = req.body;
  
  // Filter out null/undefined values
  const cleanMapping = {};
  Object.entries(mapping).forEach(([key, value]) => {
    if (value) cleanMapping[key] = value;
  });

  datasets[sessionId].mapping = cleanMapping;

  const data = datasets[sessionId].data;
  const mappedCols = Object.values(cleanMapping);
  const unmappedCols = datasets[sessionId].columns.filter(c => !mappedCols.includes(c));

  // Calculate initial NaN count for mapped columns
  let nanCount = 0;
  mappedCols.forEach(col => {
    nanCount += data.filter(row => 
      row[col] === null || row[col] === undefined || row[col] === ''
    ).length;
  });

  res.json({
    status: 'success',
    mapped_columns: mappedCols.length,
    unmapped_columns: unmappedCols.length,
    total_records: data.length,
    initial_nan_count: nanCount
  });
});

// Step 1: Range Validation
app.post('/pipeline/step1/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping } = datasets[sessionId];
    const results = {};
    const systematicOffsets = {};

    const PARAMETER_RANGES = getSessionParameterRanges(sessionId);

    Object.entries(mapping).forEach(([param, colName]) => {
      if (!PARAMETER_RANGES[param]) return;
      
      const colData = getNumericColumn(data, colName);
      if (colData.length === 0) return;

      const range = PARAMETER_RANGES[param];
      const minVal = range.min;
      const maxVal = range.max;

      const inRange = colData.filter(v => v >= minVal && v <= maxVal).length;
      const outOfRange = colData.length - inRange;
      const complianceRate = (inRange / colData.length) * 100;

      // Determine status
      let status;
      if (complianceRate < 5) {
        status = 'systematic_error';
        const rangeMidpoint = (minVal + maxVal) / 2;
        const currentMean = ss.mean(colData);
        systematicOffsets[param] = {
          offset: rangeMidpoint - currentMean,
          current_mean: currentMean,
          target_midpoint: rangeMidpoint
        };
      } else if (complianceRate > 95) {
        status = 'pass';
      } else {
        status = 'outliers_present';
      }

      const hist = histogram(colData);

      results[param] = {
        column: colName,
        total_non_nan: colData.length,
        in_range_count: inRange,
        out_of_range_count: outOfRange,
        compliance_rate: complianceRate,
        status: status,
        valid_range: { min: minVal, max: maxVal },
        unit: range.unit,
        actual_range: { min: Math.min(...colData), max: Math.max(...colData) },
        mean: ss.mean(colData),
        std: ss.standardDeviation(colData),
        histogram: hist
      };
    });

    const summary = {
      total_params: Object.keys(results).length,
      passing: Object.values(results).filter(r => r.status === 'pass').length,
      outliers: Object.values(results).filter(r => r.status === 'outliers_present').length,
      systematic_errors: Object.values(results).filter(r => r.status === 'systematic_error').length
    };

    const response = {
      results,
      systematic_offsets: systematicOffsets,
      summary
    };

    datasets[sessionId].pipelineResults.step1 = response;
    sessionStore.saveSession(sessionId, datasets[sessionId]);
    res.json(response);
  } catch (error) {
    console.error('Step 1 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 2: Cross-Parameter Consistency — Discovery endpoint
app.post('/pipeline/step2/:sessionId/discover', (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping } = datasets[sessionId];
    const domainConfig = getSessionDomain(sessionId);
    const rules = domainConfig.consistency_rules || [];

    // Phase 1: discover which rules can run
    const { applicable, unavailable } = consistencyEngine.discoverApplicableChecks(rules, mapping);

    // Agentic: auto-detect correlations from actual data
    const autoDetected = consistencyEngine.autoDetectCorrelations(data, mapping, 0.3);

    // Phase 2: row integrity audit
    // Build criticality map from domain parameters
    const columnCriticality = {};
    for (const p of (domainConfig.parameters || [])) {
      columnCriticality[p.key] = p.required ? 'required' : 'optional';
    }
    // Override with rule-level criticality
    for (const rule of rules) {
      if (rule.criticality) {
        const params = [];
        if (rule.formula) {
          if (rule.formula.derived_param) params.push(rule.formula.derived_param);
          if (rule.formula.component_a) params.push(rule.formula.component_a);
          if (rule.formula.component_b) params.push(rule.formula.component_b);
        }
        if (rule.correlation) {
          if (rule.correlation.param_a) params.push(rule.correlation.param_a);
          if (rule.correlation.param_b) params.push(rule.correlation.param_b);
        }
        params.forEach(p => { columnCriticality[p] = rule.criticality; });
      }
    }

    const integrity = consistencyEngine.auditRowIntegrity(data, mapping, columnCriticality);

    const response = {
      applicable_checks: applicable.map(a => ({
        id: a.id,
        name: a.name,
        description: a.description,
        type: a.type,
        criticality: a.criticality,
        required_params: a.required_params,
        all_mapped: true,
      })),
      unavailable_checks: unavailable,
      auto_detected: autoDetected,
      integrity,
    };

    res.json(response);
  } catch (error) {
    console.error('Step 2 discover error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 2: Cross-Parameter Consistency — Run selected checks
app.post('/pipeline/step2/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;

    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping } = datasets[sessionId];
    const domainConfig = getSessionDomain(sessionId);
    const rules = domainConfig.consistency_rules || [];

    // Accept user config from body (optional — if absent, run all applicable)
    const userConfig = req.body || {};
    const selectedCheckIds = userConfig.selected_checks; // array of check IDs or null for all
    const nullStrategies = userConfig.null_strategies || {}; // { paramKey: { action, column } }
    const autoDetectedChecks = userConfig.auto_detected_checks || []; // promoted auto-detected pairs

    // Discover applicable checks
    const { applicable } = consistencyEngine.discoverApplicableChecks(rules, mapping);

    // Filter to user-selected checks (or all if not specified)
    let checksToRun = applicable;
    if (selectedCheckIds && Array.isArray(selectedCheckIds)) {
      checksToRun = applicable.filter(c => selectedCheckIds.includes(c.id));
    }

    // Apply null strategies if provided
    let workingData = data;
    let nullStats = null;
    if (Object.keys(nullStrategies).length > 0) {
      const result = consistencyEngine.applyNullStrategy(data, nullStrategies);
      workingData = result.data;
      nullStats = result.stats;
    }

    // Run each selected check
    const checkResults = [];
    for (const check of checksToRun) {
      let result;
      if (check.type === 'relationship') {
        result = consistencyEngine.runRelationshipCheck(workingData, check.rule, mapping);
      } else if (check.type === 'correlation') {
        result = consistencyEngine.runCorrelationCheck(workingData, check.rule, mapping);
      } else {
        result = { check_id: check.id, check_name: check.name, type: check.type, status: 'error', reason: `Unknown check type: ${check.type}` };
      }
      checkResults.push(result);
    }

    // Run promoted auto-detected correlation checks
    for (const autoCheck of autoDetectedChecks) {
      const syntheticRule = {
        id: `auto_${autoCheck.param_a}_${autoCheck.param_b}`,
        name: `${autoCheck.param_a} vs ${autoCheck.param_b}`,
        type: 'correlation',
        correlation: {
          param_a: autoCheck.param_a,
          param_b: autoCheck.param_b,
          expected_direction: autoCheck.expected_direction || (autoCheck.correlation > 0 ? 'positive' : 'negative'),
          min_abs_correlation: 0.2,
        },
      };
      const result = consistencyEngine.runCorrelationCheck(workingData, syntheticRule, mapping);
      result.source = 'auto_detected';
      checkResults.push(result);
    }

    // Build integrity audit on working data
    const integrity = consistencyEngine.auditRowIntegrity(workingData, mapping);

    // Overall verdict
    const passing = checkResults.filter(r => r.status === 'pass').length;
    const marginal = checkResults.filter(r => r.status === 'marginal').length;
    const failing = checkResults.filter(r => r.status === 'fail').length;
    const warnings = checkResults.filter(r => r.status === 'warning').length;
    const total = checkResults.length;

    let overallStatus;
    if (total === 0) overallStatus = 'no_checks';
    else if (failing > 0) overallStatus = 'issues_found';
    else if (warnings > 0) overallStatus = 'warnings';
    else if (marginal > 0) overallStatus = 'marginal';
    else overallStatus = 'all_pass';

    // Backward compatibility: if there's exactly 1 relationship check (SNR),
    // also include mode_a / mode_b / verdict at the top level
    let legacyCompat = {};
    const snrCheck = checkResults.find(r => r.check_id === 'snr_derivation' && r.type === 'relationship');
    if (snrCheck && snrCheck.mode_a) {
      legacyCompat = {
        mode_a: snrCheck.mode_a,
        mode_b: snrCheck.mode_b,
        verdict: {
          status: snrCheck.verdict.status === 'pass' ? 'dBm_confirmed'
            : snrCheck.verdict.status === 'warning' ? 'linear_detected'
            : 'inconclusive',
          message: snrCheck.verdict.message,
          mode_a_score: snrCheck.verdict.score || 0,
          mode_b_score: snrCheck.mode_b?.correlation ? snrCheck.mode_b.correlation * 0.5 + (snrCheck.mode_b.pct_within_tolerance || 0) / 200 : 0,
        },
      };
    }

    const response = {
      ...legacyCompat,
      check_results: checkResults,
      integrity,
      null_handling: nullStats,
      summary: {
        total_checks: total,
        passing,
        marginal,
        warnings,
        failing,
        overall_status: overallStatus,
      },
    };

    datasets[sessionId].pipelineResults.step2 = response;
    sessionStore.saveSession(sessionId, datasets[sessionId]);
    res.json(response);
  } catch (error) {
    console.error('Step 2 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 3: Constant-Value Screening
app.post('/pipeline/step3/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping } = datasets[sessionId];
    const results = {};

    Object.entries(mapping).forEach(([param, colName]) => {
      const colData = getNumericColumn(data, colName);
      if (colData.length === 0) return;

      // Find mode
      const valueCounts = {};
      colData.forEach(v => {
        valueCounts[v] = (valueCounts[v] || 0) + 1;
      });

      let modeValue = null;
      let modeCount = 0;
      Object.entries(valueCounts).forEach(([val, count]) => {
        if (count > modeCount) {
          modeValue = Number(val);
          modeCount = count;
        }
      });

      const modePct = (modeCount / colData.length) * 100;
      const isConstant = modePct >= 95;

      results[param] = {
        column: colName,
        mode_value: modeValue,
        mode_percentage: modePct,
        unique_values: Object.keys(valueCounts).length,
        is_constant_placeholder: isConstant,
        status: isConstant ? '🔴 Constant' : '🟢 OK'
      };
    });

    const summary = {
      total_checked: Object.keys(results).length,
      constant_placeholders: Object.values(results).filter(r => r.is_constant_placeholder).length,
      valid_params: Object.values(results).filter(r => !r.is_constant_placeholder).length
    };

    const response = { results, summary };
    datasets[sessionId].pipelineResults.step3 = response;
    sessionStore.saveSession(sessionId, datasets[sessionId]);
    res.json(response);
  } catch (error) {
    console.error('Step 3 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 4: Completeness Profiling
app.post('/pipeline/step4/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping, columns } = datasets[sessionId];
    const mappedCols = Object.values(mapping).filter(c => columns.includes(c));

    if (mappedCols.length === 0) {
      return res.json({ status: 'error', reason: 'No valid mapped columns' });
    }

    // Overall completeness per column
    const overallCompleteness = {};
    mappedCols.forEach(col => {
      const nanCount = data.filter(row => 
        row[col] === null || row[col] === undefined || row[col] === ''
      ).length;
      overallCompleteness[col] = {
        nan_count: nanCount,
        nan_percentage: (nanCount / data.length) * 100,
        completeness_percentage: ((data.length - nanCount) / data.length) * 100
      };
    });

    // Per-vehicle completeness
    const vehicleCompleteness = {};
    const vehicleCol = mapping.vehicle_id;
    let completenessGap = 0;

    if (vehicleCol && columns.includes(vehicleCol)) {
      const vehicles = [...new Set(data.map(row => row[vehicleCol]))];
      
      vehicles.forEach(vehicleId => {
        const vehicleData = data.filter(row => row[vehicleCol] === vehicleId);
        let totalNan = 0;
        let totalCells = 0;

        mappedCols.forEach(col => {
          const nanCount = vehicleData.filter(row => 
            row[col] === null || row[col] === undefined || row[col] === ''
          ).length;
          totalNan += nanCount;
          totalCells += vehicleData.length;
        });

        const nanRate = totalCells > 0 ? (totalNan / totalCells) * 100 : 0;
        vehicleCompleteness[String(vehicleId)] = {
          total_records: vehicleData.length,
          avg_nan_rate: nanRate,
          completeness_rate: 100 - nanRate
        };
      });

      if (Object.keys(vehicleCompleteness).length > 0) {
        const rates = Object.values(vehicleCompleteness).map(v => v.completeness_rate);
        completenessGap = Math.max(...rates) - Math.min(...rates);
      }
    }

    // Create heatmap data (first 20 vehicles)
    const heatmapData = [];
    if (vehicleCol && columns.includes(vehicleCol)) {
      const vehicles = [...new Set(data.map(row => row[vehicleCol]))].slice(0, 20);
      vehicles.forEach(vehicleId => {
        const vehicleData = data.filter(row => row[vehicleCol] === vehicleId);
        const row = { vehicle_id: String(vehicleId) };
        mappedCols.forEach(col => {
          const nanCount = vehicleData.filter(r => 
            r[col] === null || r[col] === undefined || r[col] === ''
          ).length;
          row[col] = (nanCount / vehicleData.length) * 100;
        });
        heatmapData.push(row);
      });
    }

    const avgCompleteness = Object.values(overallCompleteness)
      .reduce((sum, c) => sum + c.completeness_percentage, 0) / mappedCols.length;

    // Missingness correlation: for each pair of columns, correlate NaN patterns
    const missingnessCorrelation = {};
    if (mappedCols.length >= 2) {
      // Build NaN indicator arrays for each column
      const nanIndicators = {};
      mappedCols.forEach(col => {
        nanIndicators[col] = data.map(row =>
          (row[col] === null || row[col] === undefined || row[col] === '' ||
           (typeof row[col] === 'number' && isNaN(row[col]))) ? 1 : 0
        );
      });

      // Compute pairwise correlation, only keep |r| > 0.3
      for (let i = 0; i < mappedCols.length; i++) {
        for (let j = i + 1; j < mappedCols.length; j++) {
          const colA = mappedCols[i];
          const colB = mappedCols[j];
          // Only compute if at least one column has some NaNs
          const sumA = nanIndicators[colA].reduce((s, v) => s + v, 0);
          const sumB = nanIndicators[colB].reduce((s, v) => s + v, 0);
          if (sumA === 0 || sumB === 0) continue;

          try {
            const r = pearsonCorrelation(nanIndicators[colA], nanIndicators[colB]);
            if (!isNaN(r) && Math.abs(r) > 0.3) {
              missingnessCorrelation[`${colA}|${colB}`] = parseFloat(r.toFixed(3));
            }
          } catch (e) {
            // skip if correlation can't be computed
          }
        }
      }
    }

    const response = {
      overall_completeness: overallCompleteness,
      vehicle_completeness: vehicleCompleteness,
      completeness_gap_pp: completenessGap,
      heatmap_data: heatmapData,
      missingness_correlation: missingnessCorrelation,
      summary: {
        total_records: data.length,
        columns_analyzed: mappedCols.length,
        columns_with_50pct_missing: Object.values(overallCompleteness)
          .filter(c => c.nan_percentage > 50).length,
        average_completeness: avgCompleteness
      },
      insight: 'A dataset with 0% NaN can have 100% value errors. Completeness alone is a poor quality proxy.'
    };

    datasets[sessionId].pipelineResults.step4 = response;
    sessionStore.saveSession(sessionId, datasets[sessionId]);
    res.json(response);
  } catch (error) {
    console.error('Step 4 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 5: Unit Verification
app.post('/pipeline/step5/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping, columns } = datasets[sessionId];
    const domainConfig = getSessionDomain(sessionId);
    const unitRules = domainConfig.unit_detection || [];
    // Derive power params from unit_detection rules, fallback to legacy list
    const powerParams = unitRules.length > 0
      ? unitRules.map(r => r.param_key)
      : ['rx_power', 'noise_power', 'tx_power'];
    const results = {};

    powerParams.forEach(param => {
      const colName = mapping[param];
      if (!colName || !columns.includes(colName)) return;

      const colData = getNumericColumn(data, colName);
      if (colData.length === 0) return;

      const minVal = Math.min(...colData);
      const maxVal = Math.max(...colData);
      const meanVal = ss.mean(colData);

      let scale, message;
      if (minVal > 0 && maxVal < 10) {
        scale = 'linear_watts';
        message = 'Likely linear watts — needs 10*log10() conversion';
      } else if (minVal < -200) {
        scale = 'suspicious_offset';
        message = 'Suspiciously low — possible value offset error';
      } else if (minVal < 0) {
        scale = 'dbm';
        message = 'Appears to be in dBm';
      } else {
        scale = 'unknown';
        message = 'Scale unclear - manual verification recommended';
      }

      results[param] = {
        column: colName,
        min: minVal,
        max: maxVal,
        mean: meanVal,
        detected_scale: scale,
        message: message,
        histogram: histogram(colData, 20)
      };
    });

    // Path loss consistency check
    let plConsistency = null;
    const txCol = mapping.tx_power;
    const rxCol = mapping.rx_power;
    const plCol = mapping.path_loss;

    if (txCol && rxCol && plCol && 
        columns.includes(txCol) && columns.includes(rxCol) && columns.includes(plCol)) {
      const validData = data
        .map(row => ({
          tx: toNumber(row[txCol]),
          rx: toNumber(row[rxCol]),
          pl: toNumber(row[plCol])
        }))
        .filter(d => d.tx !== null && d.rx !== null && d.pl !== null);

      if (validData.length > 10) {
        const derivedPl = validData.map(d => d.tx - d.rx);
        const measuredPl = validData.map(d => d.pl);
        const corr = pearsonCorrelation(derivedPl, measuredPl);

        plConsistency = {
          correlation: corr,
          consistent: corr > 0.9,
          scatter_data: {
            derived: derivedPl.slice(0, 500),
            measured: measuredPl.slice(0, 500)
          }
        };
      }
    }

    const response = {
      power_columns: results,
      path_loss_consistency: plConsistency,
      summary: {
        columns_checked: Object.keys(results).length,
        linear_detected: Object.values(results).filter(r => r.detected_scale === 'linear_watts').length,
        dbm_confirmed: Object.values(results).filter(r => r.detected_scale === 'dbm').length,
        suspicious: Object.values(results).filter(r => 
          r.detected_scale === 'suspicious_offset' || r.detected_scale === 'unknown'
        ).length
      }
    };

    datasets[sessionId].pipelineResults.step5 = response;
    sessionStore.saveSession(sessionId, datasets[sessionId]);
    res.json(response);
  } catch (error) {
    console.error('Step 5 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Step 6: Apply Corrections
app.post('/pipeline/step6/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping, pipelineResults } = datasets[sessionId];
    const corrections = req.body;
    const cleanedData = JSON.parse(JSON.stringify(data)); // Deep copy
    const appliedCorrections = [];

    // Correction A: Offset Subtraction
    if (corrections.apply_offsets) {
      const offsets = pipelineResults.step1?.systematic_offsets || {};
      Object.entries(offsets).forEach(([param, offsetInfo]) => {
        const colName = mapping[param];
        if (colName) {
          cleanedData.forEach(row => {
            if (toNumber(row[colName]) !== null) {
              row[colName] = Number(row[colName]) + offsetInfo.offset;
            }
          });
          appliedCorrections.push({
            type: 'offset_subtraction',
            column: colName,
            offset_applied: offsetInfo.offset
          });
        }
      });
    }

    // Correction B: Unit Conversion
    if (corrections.apply_unit_conversion) {
      const step5Results = pipelineResults.step5?.power_columns || {};
      Object.entries(step5Results).forEach(([param, info]) => {
        if (info.detected_scale === 'linear_watts') {
          const colName = mapping[param];
          if (colName) {
            cleanedData.forEach(row => {
              const val = toNumber(row[colName]);
              if (val !== null && val > 0) {
                row[colName] = 10 * Math.log10(val);
              }
            });
            appliedCorrections.push({
              type: 'unit_conversion',
              column: colName,
              conversion: 'linear_to_dBm'
            });
          }
        }
      });
    }

    // Correction C: Add completeness flags
    if (corrections.add_completeness_flags) {
      Object.entries(mapping).forEach(([param, colName]) => {
        cleanedData.forEach(row => {
          row[`${colName}_is_missing`] = (row[colName] === null || row[colName] === undefined || row[colName] === '') ? 1 : 0;
        });
      });
    }

    // Correction E: Outlier flagging
    if (corrections.flag_outliers) {
      const rfParams = ['snr', 'rsrp', 'rssi', 'rx_power', 'noise_power', 'tx_power', 'path_loss'];
      cleanedData.forEach(row => row.outlier_flag = 0);
      
      rfParams.forEach(param => {
        const colName = mapping[param];
        if (colName) {
          const colData = getNumericColumn(cleanedData, colName);
          if (colData.length > 0) {
            const mean = ss.mean(colData);
            const std = ss.standardDeviation(colData);
            if (std > 0) {
              cleanedData.forEach(row => {
                const val = toNumber(row[colName]);
                if (val !== null) {
                  const zScore = Math.abs((val - mean) / std);
                  if (zScore > 3) row.outlier_flag = 1;
                }
              });
            }
          }
        }
      });
    }

    // Store cleaned data
    datasets[sessionId].cleanedData = cleanedData;
    datasets[sessionId].appliedCorrections = appliedCorrections;

    // Calculate readiness score
    const readinessScore = calculateReadinessScore(sessionId);

    res.json({
      status: 'success',
      original_shape: [data.length, Object.keys(data[0] || {}).length],
      cleaned_shape: [cleanedData.length, Object.keys(cleanedData[0] || {}).length],
      applied_corrections: appliedCorrections,
      readiness_score: readinessScore
    });
  } catch (error) {
    console.error('Step 6 error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Calculate DT-Readiness Score
function calculateReadinessScore(sessionId) {
  const { pipelineResults } = datasets[sessionId];

  // Range compliance (from step 1)
  const step1 = pipelineResults.step1 || {};
  const rangeResults = step1.results || {};
  let rangeCompliance = 0;
  const rangeValues = Object.values(rangeResults);
  if (rangeValues.length > 0) {
    rangeCompliance = rangeValues.reduce((sum, r) => sum + r.compliance_rate, 0) / rangeValues.length;
  }

  // Cross-parameter consistency (from step 2)
  const step2 = pipelineResults.step2 || {};
  const modeA = step2.mode_a || {};
  const modeB = step2.mode_b || {};
  const consistency = Math.max(
    (modeA.correlation || 0) * 100,
    (modeB.correlation || 0) * 100
  );

  // No constants (from step 3)
  const step3 = pipelineResults.step3 || {};
  const step3Summary = step3.summary || {};
  const totalParams = step3Summary.total_checked || 1;
  const constantParams = step3Summary.constant_placeholders || 0;
  const noConstants = (1 - constantParams / totalParams) * 100;

  // Completeness (from step 4)
  const step4 = pipelineResults.step4 || {};
  const completeness = step4.summary?.average_completeness || 0;

  // Unit consistency (from step 5)
  const step5 = pipelineResults.step5 || {};
  const suspicious = step5.summary?.suspicious || 0;
  const unitConsistency = suspicious === 0 ? 100 : 50;

  // Weighted average — read from domain config
  const domainConfig = getSessionDomain(sessionId);
  const rw = domainConfig.readiness_weights || {};
  const weights = {
    range: rw.range_compliance ?? 0.25,
    consistency: rw.cross_param_consistency ?? 0.25,
    constants: rw.no_placeholders ?? 0.15,
    completeness: rw.completeness ?? 0.25,
    units: rw.unit_consistency ?? 0.10
  };
  const totalScore = 
    rangeCompliance * weights.range +
    consistency * weights.consistency +
    noConstants * weights.constants +
    completeness * weights.completeness +
    unitConsistency * weights.units;

  let status, statusColor;
  if (totalScore >= 70) {
    status = 'ready';
    statusColor = 'green';
  } else if (totalScore >= 40) {
    status = 'needs_correction';
    statusColor = 'yellow';
  } else {
    status = 'not_ready';
    statusColor = 'red';
  }

  return {
    total_score: totalScore,
    status,
    status_color: statusColor,
    components: {
      range_compliance: rangeCompliance,
      cross_param_consistency: consistency,
      no_placeholders: noConstants,
      completeness,
      unit_consistency: unitConsistency
    }
  };
}

// Export CSV
app.get('/export/csv/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const cleanedData = datasets[sessionId].cleanedData || datasets[sessionId].data;
    const csv = Papa.unparse(cleanedData);

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename=cleaned_${sessionId}.csv`);
    res.send(csv);
  } catch (error) {
    res.status(500).json({ detail: error.message });
  }
});

// Export Quality Report
app.get('/export/report/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { pipelineResults, appliedCorrections, mapping, filename } = datasets[sessionId];

    const report = {
      session_id: sessionId,
      original_filename: filename,
      generated_at: new Date().toISOString(),
      column_mapping: mapping,
      pipeline_results: pipelineResults,
      applied_corrections: appliedCorrections || [],
      readiness_score: calculateReadinessScore(sessionId)
    };

    res.json(report);
  } catch (error) {
    res.status(500).json({ detail: error.message });
  }
});

// Path Loss Analysis
app.get('/path-loss-analysis/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping, columns } = datasets[sessionId];
    const distCol = mapping.distance;
    const plCol = mapping.path_loss;

    if (!distCol || !plCol || !columns.includes(distCol) || !columns.includes(plCol)) {
      return res.json({ status: 'error', reason: 'Distance or Path Loss not mapped' });
    }

    // Get valid distance/path loss pairs
    const validData = data
      .map(row => ({
        distance: toNumber(row[distCol]),
        pathLoss: toNumber(row[plCol])
      }))
      .filter(d => d.distance !== null && d.pathLoss !== null && d.distance > 0);

    if (validData.length < 10) {
      return res.json({ status: 'error', reason: 'Insufficient valid data' });
    }

    const distances = validData.map(d => d.distance);
    const pathLosses = validData.map(d => d.pathLoss);

    // 3GPP Reference models at 5.9 GHz
    const freq = 5.9e9;
    const c = 3e8;

    const refDistances = [];
    const fspl = [];
    const los = [];
    const nlos = [];

    for (let d = 10; d <= 500; d += 10) {
      refDistances.push(d);
      // FSPL
      const fsplVal = 20 * Math.log10(d) + 20 * Math.log10(freq) + 20 * Math.log10(4 * Math.PI / c);
      fspl.push(fsplVal);
      // 3GPP V2V LOS
      los.push(38.77 + 16.7 * Math.log10(d));
      // 3GPP V2V NLOS
      nlos.push(51.41 + 30 * Math.log10(d));
    }

    // Calculate MAE for each model
    const calculateMAE = (measured, predicted) => {
      let sum = 0;
      let count = 0;
      measured.forEach((m, i) => {
        const d = validData[i].distance;
        const predIdx = Math.floor(d / 10) - 1;
        if (predIdx >= 0 && predIdx < predicted.length) {
          sum += Math.abs(m - predicted[predIdx]);
          count++;
        }
      });
      return count > 0 ? sum / count : Infinity;
    };

    const maeFspl = calculateMAE(pathLosses, fspl);
    const maeLos = calculateMAE(pathLosses, los);
    const maeNlos = calculateMAE(pathLosses, nlos);

    let bestFit;
    if (maeFspl <= maeLos && maeFspl <= maeNlos) bestFit = 'FSPL';
    else if (maeLos <= maeNlos) bestFit = 'LOS';
    else bestFit = 'NLOS';

    // Binned medians
    const bins = {};
    validData.forEach(d => {
      const binCenter = Math.round(d.distance / 20) * 20;
      if (!bins[binCenter]) bins[binCenter] = [];
      bins[binCenter].push(d.pathLoss);
    });

    const binnedData = {
      bin_centers: [],
      medians: [],
      q25: [],
      q75: []
    };

    Object.entries(bins).forEach(([center, values]) => {
      if (values.length >= 3) {
        values.sort((a, b) => a - b);
        binnedData.bin_centers.push(Number(center));
        binnedData.medians.push(ss.median(values));
        binnedData.q25.push(ss.quantile(values, 0.25));
        binnedData.q75.push(ss.quantile(values, 0.75));
      }
    });

    res.json({
      scatter_data: {
        distances: distances.slice(0, 1000),
        path_loss: pathLosses.slice(0, 1000)
      },
      reference_models: {
        distance: refDistances,
        fspl,
        los,
        nlos
      },
      binned_data: binnedData,
      mae: { fspl: maeFspl, los: maeLos, nlos: maeNlos },
      best_fit: bestFit
    });
  } catch (error) {
    console.error('Path loss analysis error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Data Preview (original vs cleaned)
app.get('/preview/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    const type = req.query.type || 'original';
    const limit = Math.min(parseInt(req.query.limit) || 20, 100);

    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const source = type === 'cleaned' && datasets[sessionId].cleanedData
      ? datasets[sessionId].cleanedData
      : datasets[sessionId].data;

    const columns = type === 'cleaned' && datasets[sessionId].cleanedColumns
      ? datasets[sessionId].cleanedColumns
      : datasets[sessionId].columns;

    const rows = source.slice(0, limit);
    const modifiedColumns = datasets[sessionId].appliedCorrections
      ? Object.keys(datasets[sessionId].appliedCorrections).filter(k => datasets[sessionId].appliedCorrections[k])
      : [];

    res.json({
      columns,
      rows,
      total_rows: source.length,
      type,
      modified_columns: modifiedColumns
    });
  } catch (error) {
    res.status(500).json({ detail: error.message });
  }
});

// Column sample data (for flat-line charts in Step 3)
app.get('/column-sample/:sessionId/:columnName', (req, res) => {
  try {
    const { sessionId, columnName } = req.params;
    const limit = Math.min(parseInt(req.query.limit) || 500, 1000);

    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data } = datasets[sessionId];
    const values = data.slice(0, limit).map((row, i) => ({
      index: i,
      value: typeof row[columnName] === 'number' ? row[columnName] : parseFloat(row[columnName]) || null
    }));

    res.json({
      column: columnName,
      values,
      total_rows: data.length
    });
  } catch (error) {
    res.status(500).json({ detail: error.message });
  }
});

// ============================================================
// Custom Equations — CRUD + Validation
// ============================================================


// Parse equation preview (syntax check + variable detection)
// NOTE: This static route MUST come before /equations/:sessionId routes
app.post('/equations/parse', (req, res) => {
  try {
    const { equation } = req.body;
    const result = equationEvaluator.parseEquation(equation);
    res.json({
      valid: true,
      variables: result.variables,
      allowed_functions: [...equationEvaluator.ALLOWED_FUNCTIONS],
      constants: Object.keys(equationEvaluator.BUILTIN_CONSTANTS),
    });
  } catch (error) {
    res.json({
      valid: false,
      error: error.message,
    });
  }
});

// List all equations for a session (domain defaults + user-defined)
app.get('/equations/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const domainConfig = getSessionDomain(sessionId);
    const domainEquations = (domainConfig.reference_models || []).map(m => ({
      ...m,
      source: 'domain',
      editable: false,
    }));

    const userEquations = (datasets[sessionId].customEquations || []).map(eq => ({
      ...eq,
      source: 'user',
      editable: true,
    }));

    res.json({
      domain_equations: domainEquations,
      user_equations: userEquations,
      total: domainEquations.length + userEquations.length,
    });
  } catch (error) {
    console.error('List equations error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Add a custom equation
app.post('/equations/:sessionId', (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { name, type, equation, input_vars, measured_param, tolerance_db, variable_mapping } = req.body;

    if (!name || !equation) {
      return res.status(400).json({ detail: 'Name and equation are required' });
    }

    // Validate the equation parses correctly
    let parseResult;
    try {
      parseResult = equationEvaluator.parseEquation(equation);
    } catch (err) {
      return res.status(400).json({ detail: `Invalid equation: ${err.message}` });
    }

    const eqId = `user_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
    const newEquation = {
      id: eqId,
      name,
      type: type || 'reference_model',
      equation,
      input_vars: input_vars || parseResult.variables,
      measured_param: measured_param || null,
      tolerance_db: tolerance_db || 3,
      variable_mapping: variable_mapping || {},
      created_at: new Date().toISOString(),
    };

    if (!datasets[sessionId].customEquations) {
      datasets[sessionId].customEquations = [];
    }
    datasets[sessionId].customEquations.push(newEquation);
    sessionStore.saveSession(sessionId, datasets[sessionId]);

    res.json({
      status: 'success',
      equation: { ...newEquation, source: 'user', editable: true },
      detected_variables: parseResult.variables,
    });
  } catch (error) {
    console.error('Add equation error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Delete a custom equation
app.delete('/equations/:sessionId/:eqId', (req, res) => {
  try {
    const { sessionId, eqId } = req.params;
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const eqs = datasets[sessionId].customEquations || [];
    const idx = eqs.findIndex(eq => eq.id === eqId);
    if (idx === -1) {
      return res.status(404).json({ detail: 'Equation not found' });
    }

    eqs.splice(idx, 1);
    sessionStore.saveSession(sessionId, datasets[sessionId]);

    res.json({ status: 'success', remaining: eqs.length });
  } catch (error) {
    console.error('Delete equation error:', error);
    res.status(500).json({ detail: error.message });
  }
});

// Validate: run all equations against the dataset
app.post('/equations/:sessionId/validate', (req, res) => {
  try {
    const { sessionId } = req.params;
    if (!datasets[sessionId]) {
      return res.status(404).json({ detail: 'Session not found' });
    }

    const { data, mapping } = datasets[sessionId];
    const domainConfig = getSessionDomain(sessionId);

    // Merge domain equations + user equations
    const allEquations = [];

    // Domain reference models
    (domainConfig.reference_models || []).forEach(m => {
      allEquations.push({
        id: m.id,
        name: m.name,
        type: m.type || 'reference_model',
        equation: m.equation,
        input_vars: m.input_vars || [],
        measured_param: m.measured_param || null,
        tolerance_db: m.tolerance_db || 10,
        variable_mapping: m.variable_mapping || {},
        source: 'domain',
      });
    });

    // User equations
    (datasets[sessionId].customEquations || []).forEach(eq => {
      allEquations.push({ ...eq, source: 'user' });
    });

    // Run each equation
    const results = allEquations.map(eq => {
      const result = equationEvaluator.runValidation(eq, data, mapping);
      return { ...result, source: eq.source };
    });

    // Summary
    const passing = results.filter(r => r.status === 'pass').length;
    const marginal = results.filter(r => r.status === 'marginal').length;
    const failing = results.filter(r => r.status === 'fail').length;
    const errors = results.filter(r => r.status === 'error' || r.status === 'insufficient_data').length;

    // Store results
    datasets[sessionId].pipelineResults.equations = { results, summary: { passing, marginal, failing, errors, total: results.length } };
    sessionStore.saveSession(sessionId, datasets[sessionId]);

    res.json({
      results,
      summary: { total: results.length, passing, marginal, failing, errors },
    });
  } catch (error) {
    console.error('Validate equations error:', error);
    res.status(500).json({ detail: error.message });
  }
});


// Start server (keep reference for graceful shutdown)
const server = app.listen(PORT, () => {
  console.log(`DT-QUEST Backend running on http://localhost:${PORT}`);
});

// Graceful shutdown — release port before nodemon restarts
const shutdown = (signal) => {
  console.log(`\n[${signal}] Shutting down gracefully...`);
  server.close(() => {
    console.log('Server closed.');
    process.exit(0);
  });
  // Force exit after 3 seconds if close hangs
  setTimeout(() => process.exit(1), 3000);
};
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));
