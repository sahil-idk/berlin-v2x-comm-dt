import { useState, useEffect } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell,
} from 'recharts';
import { discoverStep2, runStep2 } from '../utils/api';
import { LoadingSpinner, ErrorAlert, NextButton, StepHeader, ChartCard } from './shared';

// ── Criticality badge ──────────────────────────────────────
function CriticalityBadge({ level }) {
  const styles = {
    required: 'bg-red-500/20 text-red-400 border-red-500/40',
    recommended: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    optional: 'bg-gray-600/20 text-gray-400 border-gray-600/40',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${styles[level] || styles.optional}`}>
      {level}
    </span>
  );
}

// ── Status badge for check results ─────────────────────────
function StatusBadge({ status }) {
  const map = {
    pass: { label: 'Pass', cls: 'bg-dt-success/20 text-dt-success border-dt-success/40' },
    marginal: { label: 'Marginal', cls: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' },
    warning: { label: 'Warning', cls: 'bg-dt-warning/20 text-dt-warning border-dt-warning/40' },
    fail: { label: 'Fail', cls: 'bg-dt-error/20 text-dt-error border-dt-error/40' },
    error: { label: 'Error', cls: 'bg-gray-600/20 text-gray-400 border-gray-600/40' },
    insufficient_data: { label: 'No Data', cls: 'bg-gray-600/20 text-gray-400 border-gray-600/40' },
  };
  const m = map[status] || map.error;
  return <span className={`text-xs px-2 py-0.5 rounded-full border ${m.cls}`}>{m.label}</span>;
}

// ── Null action selector ───────────────────────────────────
const NULL_ACTIONS = [
  { value: 'keep', label: 'Keep as-is' },
  { value: 'remove', label: 'Remove Row' },
  { value: 'impute_mean', label: 'Impute (Mean)' },
  { value: 'impute_median', label: 'Impute (Median)' },
  { value: 'exclude', label: 'Exclude Column' },
];

// ── Main Component ─────────────────────────────────────────
function ConsistencyCheck({ sessionId, results, onComplete, domainName }) {
  // Discovery state
  const [discovery, setDiscovery] = useState(null);
  const [discovering, setDiscovering] = useState(false);

  // User selections
  const [selectedChecks, setSelectedChecks] = useState(new Set());
  const [promotedAutoChecks, setPromotedAutoChecks] = useState(new Set());
  const [nullActions, setNullActions] = useState({}); // { paramKey: action }

  // Validation results state
  const [validationData, setValidationData] = useState(results || null);
  const [running, setRunning] = useState(false);

  const [error, setError] = useState(null);
  const [activePanel, setActivePanel] = useState('discovery'); // discovery | integrity | results

  // Run discovery on mount
  useEffect(() => {
    if (sessionId && !discovery && !results) {
      runDiscovery();
    } else if (results) {
      // If we already have results, skip discovery
      setActivePanel('results');
    }
  }, [sessionId]);

  const runDiscovery = async () => {
    setDiscovering(true);
    setError(null);
    try {
      const disc = await discoverStep2(sessionId);
      setDiscovery(disc);

      // Pre-select all applicable checks
      const ids = new Set((disc.applicable_checks || []).map(c => c.id));
      setSelectedChecks(ids);

      // Pre-set null actions based on criticality
      const actions = {};
      if (disc.integrity?.column_stats) {
        for (const [param, stat] of Object.entries(disc.integrity.column_stats)) {
          if (stat.null_count === 0) continue;
          // Default: required → remove, recommended → keep, optional → exclude
          if (stat.criticality === 'required') actions[param] = 'remove';
          else if (stat.criticality === 'optional') actions[param] = 'exclude';
          else actions[param] = 'keep';
        }
      }
      setNullActions(actions);
    } catch (err) {
      setError(err.response?.data?.detail || 'Discovery failed');
    } finally {
      setDiscovering(false);
    }
  };

  const runValidation = async () => {
    setRunning(true);
    setError(null);
    try {
      // Build null strategies with column names
      const nullStrategies = {};
      for (const [param, action] of Object.entries(nullActions)) {
        if (action && action !== 'keep') {
          const colName = discovery?.integrity?.column_stats?.[param]?.column;
          if (colName) {
            nullStrategies[param] = { action, column: colName };
          }
        }
      }

      // Build promoted auto-detected checks
      const autoChecks = [];
      if (discovery?.auto_detected) {
        for (const auto of discovery.auto_detected) {
          const key = `${auto.param_a}__${auto.param_b}`;
          if (promotedAutoChecks.has(key)) {
            autoChecks.push(auto);
          }
        }
      }

      const config = {
        selected_checks: [...selectedChecks],
        null_strategies: nullStrategies,
        auto_detected_checks: autoChecks,
      };

      const result = await runStep2(sessionId, config);
      setValidationData(result);
      setActivePanel('results');
    } catch (err) {
      setError(err.response?.data?.detail || 'Validation failed');
    } finally {
      setRunning(false);
    }
  };

  // ── Loading / Error states ──
  if (discovering) return <LoadingSpinner message="Discovering applicable consistency checks..." />;
  if (error && !discovery && !validationData) {
    return <ErrorAlert message={error} onRetry={runDiscovery} />;
  }

  // If we have cached results and no discovery, show results directly
  if (!discovery && validationData) {
    return (
      <div className="space-y-6">
        <StepHeader step={2} title="Cross-Parameter Consistency" description={`Adaptive consistency checks for ${domainName || 'domain'} data`} />
        <ResultsPanel data={validationData} />
        <NextButton onClick={() => onComplete(validationData)} />
      </div>
    );
  }

  if (!discovery) return null;

  // ── Tab navigation ──
  const tabs = [
    { id: 'discovery', label: 'Check Discovery', icon: '1' },
    { id: 'integrity', label: 'Row Integrity', icon: '2' },
    { id: 'results', label: 'Validation Results', icon: '3', disabled: !validationData },
  ];

  return (
    <div className="space-y-6">
      <StepHeader
        step={2}
        title="Cross-Parameter Consistency"
        description={`Adaptive consistency checks for ${domainName || 'domain'} data`}
      />

      {/* Tab Bar */}
      <div className="flex gap-2 border-b border-gray-800 pb-0">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && setActivePanel(tab.id)}
            disabled={tab.disabled}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-all ${
              activePanel === tab.id
                ? 'bg-dt-card text-white border border-gray-700 border-b-transparent -mb-px'
                : tab.disabled
                ? 'text-gray-600 cursor-not-allowed'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <span className="inline-flex items-center gap-2">
              <span className={`w-5 h-5 rounded-full text-xs flex items-center justify-center ${
                activePanel === tab.id ? 'bg-dt-accent text-white' : 'bg-gray-700 text-gray-400'
              }`}>{tab.icon}</span>
              {tab.label}
            </span>
          </button>
        ))}
      </div>

      {error && <ErrorAlert message={error} onRetry={activePanel === 'discovery' ? runDiscovery : runValidation} />}

      {/* Panel A: Check Discovery */}
      {activePanel === 'discovery' && (
        <DiscoveryPanel
          discovery={discovery}
          selectedChecks={selectedChecks}
          setSelectedChecks={setSelectedChecks}
          promotedAutoChecks={promotedAutoChecks}
          setPromotedAutoChecks={setPromotedAutoChecks}
        />
      )}

      {/* Panel B: Row Integrity */}
      {activePanel === 'integrity' && (
        <IntegrityPanel
          integrity={discovery.integrity}
          nullActions={nullActions}
          setNullActions={setNullActions}
        />
      )}

      {/* Panel C: Validation Results */}
      {activePanel === 'results' && validationData && (
        <ResultsPanel data={validationData} />
      )}

      {/* Action buttons */}
      <div className="flex justify-between items-center">
        {activePanel === 'discovery' && (
          <div className="text-sm text-gray-400">
            {selectedChecks.size} check{selectedChecks.size !== 1 ? 's' : ''} selected
            {promotedAutoChecks.size > 0 && ` + ${promotedAutoChecks.size} auto-detected`}
          </div>
        )}
        {activePanel !== 'discovery' && <div />}

        <div className="flex gap-3">
          {activePanel === 'discovery' && (
            <button
              onClick={() => setActivePanel('integrity')}
              className="px-5 py-2.5 rounded-lg font-medium bg-gray-700 text-white hover:bg-gray-600 transition-all"
            >
              Review Integrity
            </button>
          )}
          {activePanel === 'integrity' && (
            <button
              onClick={() => setActivePanel('discovery')}
              className="px-5 py-2.5 rounded-lg font-medium bg-gray-700 text-white hover:bg-gray-600 transition-all"
            >
              Back to Checks
            </button>
          )}
          {(activePanel === 'discovery' || activePanel === 'integrity') && (
            <button
              onClick={runValidation}
              disabled={running || selectedChecks.size === 0}
              className="px-6 py-2.5 rounded-lg font-semibold gradient-accent text-white hover:opacity-90 transition-all disabled:opacity-50"
            >
              {running ? 'Running Checks...' : 'Run Validation'}
            </button>
          )}
          {activePanel === 'results' && validationData && (
            <NextButton onClick={() => onComplete(validationData)} />
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// Panel A: Check Discovery
// ══════════════════════════════════════════════════════════════
function DiscoveryPanel({ discovery, selectedChecks, setSelectedChecks, promotedAutoChecks, setPromotedAutoChecks }) {
  const toggleCheck = (id) => {
    setSelectedChecks(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAutoCheck = (key) => {
    setPromotedAutoChecks(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Applicable Checks */}
      <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <h3 className="font-semibold text-white">Applicable Consistency Checks</h3>
          <span className="text-xs text-gray-400">{discovery.applicable_checks?.length || 0} available</span>
        </div>
        <div className="divide-y divide-gray-800/50">
          {(discovery.applicable_checks || []).length === 0 ? (
            <div className="px-4 py-6 text-center text-gray-500">
              No applicable checks found for the current column mapping.
            </div>
          ) : (
            discovery.applicable_checks.map(check => (
              <label
                key={check.id}
                className="flex items-start gap-3 px-4 py-3 hover:bg-gray-800/30 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedChecks.has(check.id)}
                  onChange={() => toggleCheck(check.id)}
                  className="mt-1 w-4 h-4 rounded border-gray-600 bg-gray-800 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{check.name}</span>
                    <CriticalityBadge level={check.criticality} />
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-300">{check.type}</span>
                  </div>
                  <p className="text-sm text-gray-400 mt-0.5">{check.description}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Parameters: {check.required_params?.join(', ')}
                  </p>
                </div>
              </label>
            ))
          )}
        </div>
      </div>

      {/* Unavailable Checks */}
      {(discovery.unavailable_checks || []).length > 0 && (
        <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden opacity-70">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="font-semibold text-gray-400">Unavailable Checks</h3>
          </div>
          <div className="divide-y divide-gray-800/50">
            {discovery.unavailable_checks.map(check => (
              <div key={check.id} className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 font-medium">{check.name}</span>
                  <CriticalityBadge level={check.criticality} />
                </div>
                <p className="text-sm text-red-400/70 mt-0.5">{check.reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Auto-Detected Correlations */}
      {(discovery.auto_detected || []).length > 0 && (
        <div className="bg-dt-card rounded-xl border border-dt-accent/30 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800 flex items-center gap-2">
            <span className="text-dt-accent text-lg">AI</span>
            <h3 className="font-semibold text-white">Auto-Detected Correlations</h3>
            <span className="text-xs text-gray-400 ml-auto">Click to promote to active checks</span>
          </div>
          <div className="divide-y divide-gray-800/50">
            {discovery.auto_detected.map(auto => {
              const key = `${auto.param_a}__${auto.param_b}`;
              const promoted = promotedAutoChecks.has(key);
              return (
                <label
                  key={key}
                  className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors ${
                    promoted ? 'bg-dt-accent/5' : 'hover:bg-gray-800/30'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={promoted}
                    onChange={() => toggleAutoCheck(key)}
                    className="mt-1 w-4 h-4 rounded border-gray-600 bg-gray-800 text-dt-accent focus:ring-dt-accent"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-white">{auto.param_a}</span>
                      <span className="text-gray-500">vs</span>
                      <span className="font-medium text-white">{auto.param_b}</span>
                      <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                        Math.abs(auto.correlation) > 0.7 ? 'bg-dt-success/20 text-dt-success' : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        r = {auto.correlation.toFixed(3)}
                      </span>
                      <span className="text-xs text-gray-500">({auto.direction})</span>
                    </div>
                    <p className="text-sm text-gray-400 mt-0.5">{auto.suggestion}</p>
                    <p className="text-xs text-gray-500">Sample: {auto.sample_size?.toLocaleString()} rows</p>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// Panel B: Row Integrity
// ══════════════════════════════════════════════════════════════
function IntegrityPanel({ integrity, nullActions, setNullActions }) {
  if (!integrity) return <div className="text-gray-500 text-center py-8">No integrity data available.</div>;

  const columns = Object.entries(integrity.column_stats || {});
  const columnsWithNulls = columns.filter(([, s]) => s.null_count > 0);

  return (
    <div className="space-y-6">
      {/* Global integrity score */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Total Rows</p>
          <p className="text-3xl font-bold text-white">{integrity.total_rows?.toLocaleString()}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Complete Rows</p>
          <p className="text-3xl font-bold text-dt-success">{integrity.complete_rows?.toLocaleString()}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Integrity Score</p>
          <p className={`text-3xl font-bold ${
            integrity.integrity_score >= 90 ? 'text-dt-success' :
            integrity.integrity_score >= 50 ? 'text-dt-warning' : 'text-dt-error'
          }`}>{integrity.integrity_score?.toFixed(1)}%</p>
        </div>
      </div>

      {/* Per-column null stats with action dropdowns */}
      <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="font-semibold text-white">Column Null Analysis</h3>
          <p className="text-xs text-gray-400 mt-1">Configure how to handle null values for each parameter</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Parameter</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Column</th>
                <th className="px-4 py-2 text-right text-gray-400 font-medium">Null Count</th>
                <th className="px-4 py-2 text-right text-gray-400 font-medium">Null %</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Criticality</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Completeness</th>
                <th className="px-4 py-2 text-left text-gray-400 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {columns.map(([param, stat]) => (
                <tr key={param} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-4 py-2 font-medium text-white">{param}</td>
                  <td className="px-4 py-2 text-gray-400 font-mono text-xs">{stat.column}</td>
                  <td className="px-4 py-2 text-right font-mono text-gray-300">
                    {stat.null_count.toLocaleString()}
                  </td>
                  <td className={`px-4 py-2 text-right font-mono ${
                    stat.null_pct === 0 ? 'text-dt-success' :
                    stat.null_pct > 30 ? 'text-dt-error' : 'text-dt-warning'
                  }`}>
                    {stat.null_pct.toFixed(1)}%
                  </td>
                  <td className="px-4 py-2">
                    <CriticalityBadge level={stat.criticality} />
                  </td>
                  <td className="px-4 py-2 w-32">
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          stat.completeness_pct >= 90 ? 'bg-dt-success' :
                          stat.completeness_pct >= 50 ? 'bg-dt-warning' : 'bg-dt-error'
                        }`}
                        style={{ width: `${stat.completeness_pct}%` }}
                      />
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    {stat.null_count > 0 ? (
                      <select
                        value={nullActions[param] || 'keep'}
                        onChange={(e) => setNullActions(prev => ({ ...prev, [param]: e.target.value }))}
                        className="bg-gray-800 border border-gray-600 rounded-md px-2 py-1 text-xs text-gray-200 focus:border-dt-accent focus:ring-1 focus:ring-dt-accent"
                      >
                        {NULL_ACTIONS.map(a => (
                          <option key={a.value} value={a.value}>{a.label}</option>
                        ))}
                      </select>
                    ) : (
                      <span className="text-xs text-dt-success">No nulls</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick summary of chosen actions */}
      {columnsWithNulls.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-4 text-sm text-gray-300">
          <span className="font-medium text-white">Null handling summary: </span>
          {Object.entries(nullActions).filter(([, a]) => a !== 'keep').length === 0
            ? 'No actions configured — all nulls will be kept as-is.'
            : Object.entries(nullActions).filter(([, a]) => a !== 'keep').map(([p, a]) =>
                `${p}: ${a.replace('_', ' ')}`
              ).join(' | ')
          }
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// Panel C: Validation Results
// ══════════════════════════════════════════════════════════════
function ResultsPanel({ data }) {
  if (!data) return null;

  // Handle legacy format (skipped)
  if (data.status === 'skipped') {
    return (
      <div className="bg-dt-warning/10 border border-dt-warning/50 rounded-xl p-6">
        <p className="text-dt-warning font-medium">Check Skipped</p>
        <p className="text-gray-300 mt-2">{data.reason}</p>
      </div>
    );
  }

  const summary = data.summary;
  const checkResults = data.check_results || [];

  // If no check_results but has legacy mode_a/mode_b, show legacy view
  if (checkResults.length === 0 && data.mode_a) {
    return <LegacyResultView data={data} />;
  }

  return (
    <div className="space-y-6">
      {/* Overall verdict banner */}
      {summary && (
        <div className={`rounded-xl p-5 border ${
          summary.overall_status === 'all_pass' ? 'bg-dt-success/10 border-dt-success/50' :
          summary.overall_status === 'issues_found' ? 'bg-dt-error/10 border-dt-error/50' :
          summary.overall_status === 'warnings' ? 'bg-dt-warning/10 border-dt-warning/50' :
          summary.overall_status === 'no_checks' ? 'bg-gray-800 border-gray-700' :
          'bg-yellow-500/10 border-yellow-500/50'
        }`}>
          <div className="flex items-center justify-between">
            <h3 className={`text-lg font-bold ${
              summary.overall_status === 'all_pass' ? 'text-dt-success' :
              summary.overall_status === 'issues_found' ? 'text-dt-error' :
              summary.overall_status === 'warnings' ? 'text-dt-warning' :
              'text-gray-400'
            }`}>
              {summary.overall_status === 'all_pass' && 'All Checks Passed'}
              {summary.overall_status === 'issues_found' && 'Issues Found'}
              {summary.overall_status === 'warnings' && 'Warnings Detected'}
              {summary.overall_status === 'marginal' && 'Marginal Results'}
              {summary.overall_status === 'no_checks' && 'No Checks Executed'}
            </h3>
            <div className="flex gap-3 text-sm">
              {summary.passing > 0 && <span className="text-dt-success">{summary.passing} passed</span>}
              {summary.marginal > 0 && <span className="text-yellow-400">{summary.marginal} marginal</span>}
              {summary.warnings > 0 && <span className="text-dt-warning">{summary.warnings} warnings</span>}
              {summary.failing > 0 && <span className="text-dt-error">{summary.failing} failed</span>}
            </div>
          </div>
        </div>
      )}

      {/* Null handling report */}
      {data.null_handling && (data.null_handling.removed_rows > 0 || Object.keys(data.null_handling.imputed_cells || {}).length > 0) && (
        <div className="bg-gray-800/50 rounded-lg p-4 text-sm">
          <span className="font-medium text-white">Null handling applied: </span>
          {data.null_handling.removed_rows > 0 && (
            <span className="text-dt-warning">{data.null_handling.removed_rows} rows removed. </span>
          )}
          {Object.entries(data.null_handling.imputed_cells || {}).map(([param, info]) => (
            <span key={param} className="text-gray-300">
              {param}: {info.count} cells imputed ({info.method}, value={info.fill_value}).{' '}
            </span>
          ))}
          {(data.null_handling.excluded_columns || []).length > 0 && (
            <span className="text-gray-400">
              Excluded: {data.null_handling.excluded_columns.join(', ')}
            </span>
          )}
        </div>
      )}

      {/* Integrity summary */}
      {data.integrity && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
            <p className="text-sm text-gray-400">Working Rows</p>
            <p className="text-2xl font-bold text-white">{data.integrity.total_rows?.toLocaleString()}</p>
          </div>
          <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
            <p className="text-sm text-gray-400">Complete Rows</p>
            <p className="text-2xl font-bold text-dt-success">{data.integrity.complete_rows?.toLocaleString()}</p>
          </div>
          <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
            <p className="text-sm text-gray-400">Integrity Score</p>
            <p className={`text-2xl font-bold ${
              data.integrity.integrity_score >= 90 ? 'text-dt-success' :
              data.integrity.integrity_score >= 50 ? 'text-dt-warning' : 'text-dt-error'
            }`}>{data.integrity.integrity_score?.toFixed(1)}%</p>
          </div>
        </div>
      )}

      {/* Individual check result cards */}
      {checkResults.map((result, idx) => (
        <CheckResultCard key={result.check_id || idx} result={result} />
      ))}
    </div>
  );
}

// ── Individual check result card ───────────────────────────
function CheckResultCard({ result }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(prev => !prev)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-800/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <StatusBadge status={result.status} />
          <span className="font-semibold text-white">{result.check_name || result.check_id}</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-300">{result.type}</span>
          {result.source === 'auto_detected' && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-dt-accent/20 text-dt-accent">auto-detected</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {result.type === 'correlation' && result.correlation !== undefined && (
            <span className="text-sm font-mono text-gray-400">r = {result.correlation?.toFixed(3)}</span>
          )}
          {result.type === 'relationship' && result.mode_a?.correlation !== undefined && (
            <span className="text-sm font-mono text-gray-400">r = {result.mode_a.correlation?.toFixed(3)}</span>
          )}
          <span className="text-gray-500 text-xs">{result.valid_rows?.toLocaleString()} rows</span>
          <svg className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-4 py-4 border-t border-gray-800 space-y-4">
          {/* Verdict message */}
          {result.verdict && (
            <p className="text-sm text-gray-300">{result.verdict.message}</p>
          )}

          {/* Relationship check details */}
          {result.type === 'relationship' && result.mode_a && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ModeCard mode={result.mode_a} label="Mode A" color="#4f46e5" />
              {result.mode_b && result.mode_b.status !== 'not_applicable' && (
                <ModeCard mode={result.mode_b} label="Mode B" color="#f59e0b" />
              )}
            </div>
          )}

          {/* Correlation check details */}
          {result.type === 'correlation' && result.scatter_data && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400">Correlation</p>
                    <p className={`text-xl font-bold ${
                      Math.abs(result.correlation) > 0.7 ? 'text-dt-success' :
                      Math.abs(result.correlation) > 0.3 ? 'text-dt-warning' : 'text-dt-error'
                    }`}>{result.correlation?.toFixed(4)}</p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400">Direction</p>
                    <p className={`text-xl font-bold ${result.direction_match ? 'text-dt-success' : 'text-dt-error'}`}>
                      {result.actual_direction} {result.direction_match ? '(expected)' : `(expected ${result.expected_direction})`}
                    </p>
                  </div>
                </div>
              </div>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="x" name={result.scatter_data.x_label} stroke="#9ca3af" fontSize={10}
                      label={{ value: result.scatter_data.x_label, position: 'bottom', fill: '#9ca3af', fontSize: 10 }} />
                    <YAxis dataKey="y" name={result.scatter_data.y_label} stroke="#9ca3af" fontSize={10}
                      label={{ value: result.scatter_data.y_label, angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }} />
                    <Scatter
                      data={result.scatter_data.x.map((x, i) => ({ x, y: result.scatter_data.y[i] }))}
                      fill="#4f46e5" opacity={0.5}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Mode card for relationship checks ──────────────────────
function ModeCard({ mode, label, color }) {
  const scatterData = mode.scatter_data?.derived?.map((d, i) => ({
    derived: d,
    measured: mode.scatter_data.measured[i],
  })) || [];

  return (
    <div className="bg-gray-800/30 rounded-lg p-3">
      <h4 className="font-medium text-white text-sm mb-2">{label}: {mode.name}</h4>
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="bg-gray-800/50 rounded p-2">
          <p className="text-xs text-gray-400">Correlation</p>
          <p className={`text-lg font-bold ${(mode.correlation || 0) > 0.9 ? 'text-dt-success' : (mode.correlation || 0) > 0.5 ? 'text-dt-warning' : 'text-dt-error'}`}>
            {(mode.correlation || 0).toFixed(3)}
          </p>
        </div>
        <div className="bg-gray-800/50 rounded p-2">
          <p className="text-xs text-gray-400">Within tolerance</p>
          <p className={`text-lg font-bold ${(mode.pct_within_tolerance || 0) > 90 ? 'text-dt-success' : (mode.pct_within_tolerance || 0) > 50 ? 'text-dt-warning' : 'text-dt-error'}`}>
            {(mode.pct_within_tolerance || 0).toFixed(1)}%
          </p>
        </div>
      </div>
      {scatterData.length > 0 && (
        <div className="h-36">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 5, right: 5, bottom: 15, left: 15 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="derived" stroke="#9ca3af" fontSize={9} label={{ value: 'Derived', position: 'bottom', fill: '#9ca3af', fontSize: 9 }} />
              <YAxis dataKey="measured" stroke="#9ca3af" fontSize={9} label={{ value: 'Measured', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 9 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }} />
              <Scatter data={scatterData.slice(0, 200)} fill={color} opacity={0.5} />
              <ReferenceLine segment={[{ x: -20, y: -20 }, { x: 40, y: 40 }]} stroke="#10b981" strokeDasharray="3 3" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ── Legacy result view (backward compat) ───────────────────
function LegacyResultView({ data }) {
  const modeA = data.mode_a;
  const modeB = data.mode_b;
  const verdict = data.verdict;

  const scatterDataA = modeA?.scatter_data?.derived?.map((d, i) => ({
    derived: d, measured: modeA.scatter_data.measured[i],
  })) || [];

  const scatterDataB = modeB?.scatter_data?.derived?.map((d, i) => ({
    derived: d, measured: modeB.scatter_data.measured[i],
  })) || [];

  return (
    <div className="space-y-6">
      {verdict && (
        <div className={`rounded-xl p-6 border ${
          verdict.status === 'dBm_confirmed' ? 'bg-dt-success/10 border-dt-success/50' :
          verdict.status === 'linear_detected' ? 'bg-dt-warning/10 border-dt-warning/50' :
          'bg-gray-800 border-gray-700'
        }`}>
          <h3 className={`text-xl font-bold ${
            verdict.status === 'dBm_confirmed' ? 'text-dt-success' :
            verdict.status === 'linear_detected' ? 'text-dt-warning' : 'text-gray-400'
          }`}>{verdict.message}</h3>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {modeA && <ModeCard mode={{...modeA, pct_within_tolerance: modeA.pct_within_3dB || modeA.pct_within_tolerance}} label="Mode A" color="#4f46e5" />}
        {modeB && modeB.status !== 'not_applicable' && (
          <ModeCard mode={{...modeB, pct_within_tolerance: modeB.pct_within_3dB || modeB.pct_within_tolerance}} label="Mode B" color="#f59e0b" />
        )}
      </div>
    </div>
  );
}

export default ConsistencyCheck;
