import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine } from 'recharts';
import { runStep3, getColumnSample } from '../utils/api';

function ConstantCheck({ sessionId, results, onComplete }) {
  const [data, setData] = useState(results || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedParam, setExpandedParam] = useState(null);
  const [sampleData, setSampleData] = useState({});
  const [sampleLoading, setSampleLoading] = useState(null);

  useEffect(() => {
    if (!data && sessionId) {
      runAnalysis();
    }
  }, [sessionId]);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runStep3(sessionId);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = async (param, columnName) => {
    if (expandedParam === param) {
      setExpandedParam(null);
      return;
    }
    setExpandedParam(param);

    // Lazy-load sample data if not already fetched
    if (!sampleData[param]) {
      setSampleLoading(param);
      try {
        const result = await getColumnSample(sessionId, columnName, 500);
        setSampleData(prev => ({ ...prev, [param]: result.values }));
      } catch (err) {
        console.error('Failed to load sample:', err);
      } finally {
        setSampleLoading(null);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <svg className="w-12 h-12 text-dt-accent animate-spin mx-auto mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-400">Screening for constant/placeholder values...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-dt-error/10 border border-dt-error/50 rounded-lg p-4 text-dt-error">
        {error}
        <button onClick={runAnalysis} className="ml-4 underline">Retry</button>
      </div>
    );
  }

  if (!data) return null;

  const { results: paramResults, summary } = data;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 3: Constant-Value Screening</h2>
        <p className="text-gray-400">Flag parameters where ≥95% of values are identical — likely hardcoded placeholders</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Parameters Checked</p>
          <p className="text-3xl font-bold text-white">{summary.total_checked}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Valid Parameters</p>
          <p className="text-3xl font-bold text-dt-success">{summary.valid_params}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Constant Placeholders</p>
          <p className="text-3xl font-bold text-dt-error">{summary.constant_placeholders}</p>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="font-semibold text-white">Parameter Analysis</h3>
          <p className="text-xs text-gray-500 mt-1">Click a row to see the time-series pattern</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Column</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Mode Value</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Mode %</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Unique Values</th>
                <th className="px-4 py-3 text-left text-gray-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {Object.entries(paramResults).map(([param, info]) => (
                <tr key={param}>
                  <td colSpan={5} className="p-0">
                    <button
                      onClick={() => toggleExpand(param, info.column)}
                      className={`w-full text-left hover:bg-gray-800/30 transition-colors ${
                        expandedParam === param ? 'bg-gray-800/20' : ''
                      }`}
                    >
                      <div className="flex">
                        <div className="px-4 py-3 text-white font-medium flex items-center gap-2 w-1/5">
                          <svg
                            className={`w-3 h-3 text-gray-500 transition-transform ${expandedParam === param ? 'rotate-90' : ''}`}
                            fill="currentColor" viewBox="0 0 20 20"
                          >
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                          {info.column}
                        </div>
                        <div className="px-4 py-3 text-gray-300 font-mono text-xs w-1/5">
                          {typeof info.mode_value === 'number' ? info.mode_value.toFixed(4) : String(info.mode_value).substring(0, 30)}
                        </div>
                        <div className="px-4 py-3 w-1/5">
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full ${info.is_constant_placeholder ? 'bg-dt-error' : 'bg-dt-success'}`}
                                style={{ width: `${Math.min(info.mode_percentage, 100)}%` }}
                              />
                            </div>
                            <span className={info.is_constant_placeholder ? 'text-dt-error' : 'text-gray-300'}>
                              {info.mode_percentage.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <div className="px-4 py-3 text-gray-300 w-1/5">{info.unique_values.toLocaleString()}</div>
                        <div className="px-4 py-3 w-1/5">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            info.is_constant_placeholder 
                              ? 'bg-dt-error/20 text-dt-error' 
                              : 'bg-dt-success/20 text-dt-success'
                          }`}>
                            {info.status}
                          </span>
                        </div>
                      </div>
                    </button>

                    {/* Expandable mini chart */}
                    {expandedParam === param && (
                      <div className="px-6 pb-4 bg-gray-800/10">
                        <div className="bg-gray-900/50 rounded-lg p-3 border border-gray-700/50">
                          <p className="text-xs text-gray-500 mb-2">
                            Time-series view (first {sampleData[param]?.length || '...'} samples)
                          </p>
                          {sampleLoading === param ? (
                            <div className="h-[120px] flex items-center justify-center text-gray-500 text-sm">
                              Loading sample data...
                            </div>
                          ) : sampleData[param] ? (
                            <div className="h-[120px]">
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={sampleData[param]} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
                                  <XAxis dataKey="index" stroke="#4b5563" fontSize={9} tickCount={5} />
                                  <YAxis stroke="#4b5563" fontSize={9} width={50} />
                                  <ReferenceLine
                                    y={typeof info.mode_value === 'number' ? info.mode_value : undefined}
                                    stroke="#6b7280" strokeDasharray="3 3"
                                    label={{ value: 'Mode', fill: '#6b7280', fontSize: 9 }}
                                  />
                                  <Line
                                    dataKey="value"
                                    stroke={info.is_constant_placeholder ? '#ef4444' : '#10b981'}
                                    dot={false}
                                    strokeWidth={1.5}
                                    isAnimationActive={false}
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          ) : (
                            <div className="h-[120px] flex items-center justify-center text-gray-500 text-sm">
                              No data available
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Warning for constant placeholders */}
      {summary.constant_placeholders > 0 && (
        <div className="bg-dt-error/10 border border-dt-error/50 rounded-xl p-4">
          <h3 className="font-semibold text-dt-error mb-2">⚠️ Constant Placeholders Detected</h3>
          <p className="text-gray-300 text-sm">
            The following parameters have ≥95% identical values, indicating they may be hardcoded placeholders
            rather than actual measurements. These should be excluded from analysis or replaced with valid data.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(paramResults)
              .filter(([_, info]) => info.is_constant_placeholder)
              .map(([param, info]) => (
                <span key={param} className="px-3 py-1 bg-dt-error/20 text-dt-error rounded-full text-sm">
                  {info.column}: {typeof info.mode_value === 'number' ? info.mode_value.toFixed(2) : info.mode_value}
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Next Button */}
      <div className="flex justify-end">
        <button
          onClick={() => onComplete(data)}
          className="px-6 py-3 rounded-lg font-semibold gradient-accent text-white hover:opacity-90 transition-all"
        >
          Next Step →
        </button>
      </div>
    </div>
  );
}

export default ConstantCheck;
