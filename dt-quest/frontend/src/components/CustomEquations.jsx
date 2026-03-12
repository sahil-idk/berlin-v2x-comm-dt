import { useState, useEffect, useCallback } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { getEquations, addEquation, deleteEquationApi, validateEquations, parseEquationApi } from '../utils/api';
import { StepHeader, ChartCard, LoadingSpinner, SummaryCard } from './shared';

const STATUS_STYLES = {
  pass:     { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'Pass' },
  marginal: { bg: 'bg-yellow-500/10',  border: 'border-yellow-500/30',  text: 'text-yellow-400',  label: 'Marginal' },
  fail:     { bg: 'bg-red-500/10',     border: 'border-red-500/30',     text: 'text-red-400',     label: 'Fail' },
  error:    { bg: 'bg-gray-500/10',    border: 'border-gray-500/30',    text: 'text-gray-400',    label: 'Error' },
  insufficient_data: { bg: 'bg-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400', label: 'No Data' },
};

function CustomEquations({ sessionId, onBack, mapping }) {
  const [equations, setEquations] = useState({ domain_equations: [], user_equations: [] });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState(null);

  // Add form state
  const [formName, setFormName] = useState('');
  const [formType, setFormType] = useState('reference_model');
  const [formEquation, setFormEquation] = useState('');
  const [formMeasuredParam, setFormMeasuredParam] = useState('');
  const [formTolerance, setFormTolerance] = useState(10);
  const [formVarMapping, setFormVarMapping] = useState({});
  const [parseResult, setParseResult] = useState(null);
  const [parseError, setParseError] = useState(null);

  // Load equations on mount
  const loadEquations = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await getEquations(sessionId);
      setEquations(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => { loadEquations(); }, [loadEquations]);

  // Live equation parsing
  useEffect(() => {
    if (!formEquation.trim()) {
      setParseResult(null);
      setParseError(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const result = await parseEquationApi(formEquation);
        if (result.valid) {
          setParseResult(result);
          setParseError(null);
          // Initialize variable mapping for detected variables
          const newMapping = {};
          result.variables.forEach(v => {
            newMapping[v] = formVarMapping[v] || '';
          });
          setFormVarMapping(newMapping);
        } else {
          setParseResult(null);
          setParseError(result.error);
        }
      } catch {
        setParseError('Failed to parse');
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [formEquation]);

  // Submit new equation
  const handleAdd = async () => {
    if (!formName || !formEquation) return;
    try {
      await addEquation(sessionId, {
        name: formName,
        type: formType,
        equation: formEquation,
        measured_param: formMeasuredParam || null,
        tolerance_db: Number(formTolerance),
        variable_mapping: formVarMapping,
      });
      setShowAddForm(false);
      resetForm();
      loadEquations();
    } catch (err) {
      setParseError(err.response?.data?.detail || err.message);
    }
  };

  const handleDelete = async (eqId) => {
    try {
      await deleteEquationApi(sessionId, eqId);
      loadEquations();
      if (results) {
        setResults(prev => ({
          ...prev,
          results: prev.results.filter(r => r.id !== eqId),
        }));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const handleValidate = async () => {
    setValidating(true);
    setError(null);
    try {
      const data = await validateEquations(sessionId);
      setResults(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setValidating(false);
    }
  };

  const resetForm = () => {
    setFormName('');
    setFormType('reference_model');
    setFormEquation('');
    setFormMeasuredParam('');
    setFormTolerance(10);
    setFormVarMapping({});
    setParseResult(null);
    setParseError(null);
  };

  // Available mapped parameter keys for dropdowns
  const mappedParams = Object.keys(mapping || {});

  if (loading) return <LoadingSpinner message="Loading equations..." />;

  const allEquations = [...equations.domain_equations, ...equations.user_equations];
  const totalEqs = allEquations.length;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <StepHeader
          title="Custom Validation Equations"
          description="Define and apply custom physics/propagation models to validate your dataset"
        />
        <button onClick={onBack} className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors">
          ← Back
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-3 underline">Dismiss</button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard label="Domain Models" value={equations.domain_equations.length} icon="📐" color="text-blue-400" />
        <SummaryCard label="User Equations" value={equations.user_equations.length} icon="✏️" color="text-purple-400" />
        <SummaryCard label="Total" value={totalEqs} icon="ƒ" color="text-white" />
        {results && (
          <SummaryCard
            label="Passing"
            value={`${results.summary.passing}/${results.summary.total}`}
            icon="✓"
            color={results.summary.failing > 0 ? 'text-yellow-400' : 'text-emerald-400'}
          />
        )}
      </div>

      {/* Equation Library */}
      <ChartCard title="Equation Library" subtitle={`${totalEqs} equation(s) available`}>
        <div className="space-y-3">
          {allEquations.length === 0 && (
            <p className="text-gray-500 text-center py-8">No equations defined. Add one below or switch to a domain with reference models.</p>
          )}

          {allEquations.map(eq => (
            <div key={eq.id} className={`rounded-lg border p-4 ${eq.source === 'domain' ? 'border-blue-500/20 bg-blue-500/5' : 'border-purple-500/20 bg-purple-500/5'}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${eq.source === 'domain' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}>
                      {eq.source === 'domain' ? 'Domain' : 'Custom'}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300">
                      {eq.type === 'reference_model' ? 'Reference Model' : eq.type === 'constraint' ? 'Constraint' : 'Relationship'}
                    </span>
                    <h4 className="font-medium text-white">{eq.name}</h4>
                  </div>
                  <code className="text-sm text-emerald-400 bg-gray-900 px-3 py-1.5 rounded block mt-2 font-mono">
                    {eq.equation}
                  </code>
                  {eq.measured_param && (
                    <p className="text-xs text-gray-500 mt-1">Compared against: <span className="text-gray-400">{eq.measured_param}</span></p>
                  )}
                </div>
                {eq.editable && (
                  <button
                    onClick={() => handleDelete(eq.id)}
                    className="text-gray-500 hover:text-red-400 transition-colors ml-3 p-1"
                    title="Delete equation"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Show result if validation ran */}
              {results && (() => {
                const r = results.results.find(res => res.id === eq.id);
                if (!r) return null;
                const style = STATUS_STYLES[r.status] || STATUS_STYLES.error;
                return (
                  <div className={`mt-3 p-3 rounded-lg ${style.bg} border ${style.border}`}>
                    <div className="flex items-center gap-4 flex-wrap">
                      <span className={`font-semibold ${style.text}`}>{style.label}</span>
                      {r.mae !== undefined && <span className="text-sm text-gray-300">MAE: <strong>{r.mae} dB</strong></span>}
                      {r.rmse !== undefined && <span className="text-sm text-gray-300">RMSE: <strong>{r.rmse} dB</strong></span>}
                      {r.r_squared !== undefined && <span className="text-sm text-gray-300">R²: <strong>{r.r_squared}</strong></span>}
                      {r.pct_within_tolerance !== undefined && <span className="text-sm text-gray-300">Within ±{r.tolerance_db}dB: <strong>{r.pct_within_tolerance}%</strong></span>}
                      {r.pass_rate !== undefined && <span className="text-sm text-gray-300">Pass rate: <strong>{r.pass_rate}%</strong></span>}
                      {r.valid_count !== undefined && <span className="text-xs text-gray-500">({r.valid_count} pts)</span>}
                      {r.error && <span className="text-sm text-gray-400">{r.error}</span>}
                    </div>
                  </div>
                );
              })()}
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mt-4 pt-4 border-t border-gray-800">
          <button
            onClick={() => { setShowAddForm(!showAddForm); if (showAddForm) resetForm(); }}
            className="px-4 py-2 rounded-lg font-medium bg-purple-600/20 text-purple-400 border border-purple-500/30 hover:bg-purple-600/30 transition-colors"
          >
            {showAddForm ? '✕ Cancel' : '+ Add Equation'}
          </button>
          <button
            onClick={handleValidate}
            disabled={validating || totalEqs === 0}
            className="px-6 py-2 rounded-lg font-semibold gradient-accent text-white hover:opacity-90 transition-all disabled:opacity-50"
          >
            {validating ? 'Validating...' : '▶ Run All Validations'}
          </button>
        </div>
      </ChartCard>

      {/* Add Equation Form */}
      {showAddForm && (
        <ChartCard title="New Equation" subtitle="Define a custom validation equation">
          <div className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Equation Name</label>
              <input
                type="text"
                value={formName}
                onChange={e => setFormName(e.target.value)}
                placeholder="e.g., My UAV Path Loss Model"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none"
              />
            </div>

            {/* Type */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Type</label>
              <select
                value={formType}
                onChange={e => setFormType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none"
              >
                <option value="reference_model">Reference Model (MAE comparison)</option>
                <option value="relationship">Relationship Check (derivation)</option>
                <option value="constraint">Constraint (boolean per-row)</option>
              </select>
            </div>

            {/* Equation */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Equation</label>
              <input
                type="text"
                value={formEquation}
                onChange={e => setFormEquation(e.target.value)}
                placeholder="e.g., 51.41 + 30*log10(d)"
                className={`w-full bg-gray-900 border rounded-lg px-3 py-2 text-emerald-400 font-mono text-sm focus:outline-none ${
                  parseError ? 'border-red-500' : parseResult ? 'border-emerald-500' : 'border-gray-700'
                }`}
              />
              {parseError && <p className="text-xs text-red-400 mt-1">⚠ {parseError}</p>}
              {parseResult && (
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs text-emerald-400">✓ Valid</span>
                  <span className="text-xs text-gray-500">
                    Variables: {parseResult.variables.length > 0 ? parseResult.variables.join(', ') : 'none'}
                  </span>
                </div>
              )}
              <p className="text-xs text-gray-600 mt-1">
                Available: log10, log, sqrt, pow, abs, exp, sin, cos, tan, pi, c (speed of light)
              </p>
            </div>

            {/* Variable Mapping */}
            {parseResult && parseResult.variables.length > 0 && (
              <div>
                <label className="block text-sm text-gray-400 mb-2">Variable Mapping</label>
                <div className="space-y-2">
                  {parseResult.variables.map(v => (
                    <div key={v} className="flex items-center gap-3">
                      <code className="text-sm text-emerald-400 bg-gray-900 px-2 py-1 rounded w-24 text-center">{v}</code>
                      <span className="text-gray-500">→</span>
                      <select
                        value={formVarMapping[v] || ''}
                        onChange={e => setFormVarMapping(prev => ({ ...prev, [v]: e.target.value }))}
                        className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-white text-sm flex-1 focus:border-purple-500 focus:outline-none"
                      >
                        <option value="">Select dataset column...</option>
                        {mappedParams.map(p => (
                          <option key={p} value={p}>{p} ({mapping[p]})</option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Measured Parameter (for reference_model and relationship) */}
            {formType !== 'constraint' && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Compare Against (measured column)</label>
                <select
                  value={formMeasuredParam}
                  onChange={e => setFormMeasuredParam(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none"
                >
                  <option value="">Select parameter...</option>
                  {mappedParams.map(p => (
                    <option key={p} value={p}>{p} ({mapping[p]})</option>
                  ))}
                </select>
              </div>
            )}

            {/* Tolerance */}
            {formType !== 'constraint' && (
              <div>
                <label className="block text-sm text-gray-400 mb-1">Tolerance (dB)</label>
                <input
                  type="number"
                  value={formTolerance}
                  onChange={e => setFormTolerance(e.target.value)}
                  className="w-32 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-purple-500 focus:outline-none"
                />
              </div>
            )}

            {/* Submit */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleAdd}
                disabled={!formName || !formEquation || parseError}
                className="px-6 py-2 rounded-lg font-semibold bg-purple-600 text-white hover:bg-purple-500 transition-colors disabled:opacity-40"
              >
                Add Equation
              </button>
              <button
                onClick={() => { setShowAddForm(false); resetForm(); }}
                className="px-4 py-2 rounded-lg text-gray-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </ChartCard>
      )}

      {/* Scatter Plots for Results */}
      {results && results.results.filter(r => r.scatter_sample).length > 0 && (
        <ChartCard title="Predicted vs Measured" subtitle="Scatter plots for reference model validations">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {results.results.filter(r => r.scatter_sample).map(r => (
              <div key={r.id} className="bg-gray-900/50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-white mb-3">{r.name}</h4>
                <ResponsiveContainer width="100%" height={250}>
                  <ScatterChart margin={{ top: 10, right: 10, bottom: 30, left: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis
                      type="number"
                      dataKey="predicted"
                      name="Predicted"
                      tick={{ fontSize: 11, fill: '#999' }}
                      label={{ value: 'Predicted (dB)', position: 'bottom', offset: 15, fill: '#666', fontSize: 11 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="measured"
                      name="Measured"
                      tick={{ fontSize: 11, fill: '#999' }}
                      label={{ value: 'Measured (dB)', angle: -90, position: 'left', offset: 20, fill: '#666', fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333', borderRadius: '8px' }}
                      formatter={(val) => `${val} dB`}
                    />
                    <ReferenceLine
                      segment={[
                        { x: Math.min(...r.scatter_sample.predicted), y: Math.min(...r.scatter_sample.predicted) },
                        { x: Math.max(...r.scatter_sample.predicted), y: Math.max(...r.scatter_sample.predicted) },
                      ]}
                      stroke="#666"
                      strokeDasharray="5 5"
                      label=""
                    />
                    <Scatter
                      data={r.scatter_sample.predicted.map((p, i) => ({
                        predicted: p,
                        measured: r.scatter_sample.measured[i],
                      }))}
                      fill={r.status === 'pass' ? '#10b981' : r.status === 'marginal' ? '#f59e0b' : '#ef4444'}
                      fillOpacity={0.6}
                      r={2}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>MAE: {r.mae} dB</span>
                  <span>R²: {r.r_squared}</span>
                  <span>ρ: {r.correlation}</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      )}
    </div>
  );
}

export default CustomEquations;
