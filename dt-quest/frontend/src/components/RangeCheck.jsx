import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { runStep1 } from '../utils/api';

function RangeCheck({ sessionId, results, onComplete, domainName }) {
  const [data, setData] = useState(results || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedParam, setSelectedParam] = useState(null);

  useEffect(() => {
    if (!data && sessionId) {
      runAnalysis();
    }
  }, [sessionId]);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runStep1(sessionId);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pass': return '#10b981';
      case 'outliers_present': return '#f59e0b';
      case 'systematic_error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'pass': return 'PASS';
      case 'outliers_present': return 'Outliers Present';
      case 'systematic_error': return 'Systematic Error';
      default: return 'Unknown';
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
          <p className="text-gray-400">Running {domainName || 'domain'} range validation...</p>
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

  const complianceData = Object.entries(data.results).map(([param, info]) => ({
    param: info.column,
    compliance: info.compliance_rate,
    status: info.status,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 1: Range Validation</h2>
        <p className="text-gray-400">Check every mapped parameter against {domainName || 'domain'} physical bounds</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Passing Parameters</p>
          <p className="text-3xl font-bold text-dt-success">{data.summary.passing}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Outliers Present</p>
          <p className="text-3xl font-bold text-dt-warning">{data.summary.outliers}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Systematic Errors</p>
          <p className="text-3xl font-bold text-dt-error">{data.summary.systematic_errors}</p>
        </div>
      </div>

      {/* Compliance Bar Chart */}
      <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
        <h3 className="font-semibold text-white mb-4">Compliance Rates by Parameter</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={complianceData} layout="vertical" margin={{ left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" domain={[0, 100]} stroke="#9ca3af" tickFormatter={(v) => `${v}%`} />
              <YAxis type="category" dataKey="param" stroke="#9ca3af" width={90} tick={{ fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }}
                formatter={(value) => [`${value.toFixed(1)}%`, 'Compliance']}
              />
              <ReferenceLine x={95} stroke="#10b981" strokeDasharray="3 3" label={{ value: '95%', position: 'top', fill: '#10b981' }} />
              <ReferenceLine x={5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: '5%', position: 'top', fill: '#ef4444' }} />
              <Bar dataKey="compliance" radius={[0, 4, 4, 0]}>
                {complianceData.map((entry, index) => (
                  <Cell key={index} fill={getStatusColor(entry.status)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Parameter Details */}
      <div className="bg-dt-card rounded-xl border border-gray-800">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="font-semibold text-white">Parameter Details</h3>
        </div>
        <div className="divide-y divide-gray-800">
          {Object.entries(data.results).map(([param, info]) => (
            <div 
              key={param} 
              className="p-4 hover:bg-gray-800/50 cursor-pointer transition-colors"
              onClick={() => setSelectedParam(selectedParam === param ? null : param)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getStatusColor(info.status) }}
                  />
                  <div>
                    <p className="font-medium text-white">{info.column}</p>
                    <p className="text-sm text-gray-400">
                      {info.unit} • Valid range: [{info.valid_range.min}, {info.valid_range.max}]
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold" style={{ color: getStatusColor(info.status) }}>
                    {getStatusLabel(info.status)}
                  </p>
                  <p className="text-sm text-gray-400">{info.compliance_rate.toFixed(1)}% in range</p>
                </div>
              </div>

              {selectedParam === param && (
                <div className="mt-4 pt-4 border-t border-gray-700 space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">Total Non-NaN</p>
                      <p className="text-white font-medium">{info.total_non_nan.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">In Range</p>
                      <p className="text-dt-success font-medium">{info.in_range_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Out of Range</p>
                      <p className="text-dt-error font-medium">{info.out_of_range_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Actual Range</p>
                      <p className="text-white font-medium">
                        [{info.actual_range.min.toFixed(2)}, {info.actual_range.max.toFixed(2)}]
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">Mean</p>
                      <p className="text-white font-medium">{info.mean.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-gray-400">Std Dev</p>
                      <p className="text-white font-medium">{info.std.toFixed(2)}</p>
                    </div>
                  </div>

                  {/* Distribution Histogram */}
                  {info.histogram && info.histogram.counts.length > 0 && (() => {
                    const histData = info.histogram.counts.map((count, i) => {
                      const binStart = info.histogram.bins[i];
                      const binEnd = info.histogram.bins[i + 1] || binStart;
                      const binMid = (binStart + binEnd) / 2;
                      const inValid = binMid >= info.valid_range.min && binMid <= info.valid_range.max;
                      return {
                        bin: binMid,
                        binLabel: binMid.toFixed(1),
                        count,
                        fill: inValid ? '#10b981' : '#ef4444',
                      };
                    });
                    return (
                      <div>
                        <p className="text-sm text-gray-400 mb-2">Value Distribution</p>
                        <div className="h-48 bg-gray-900/50 rounded-lg p-2">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={histData} margin={{ top: 5, right: 10, bottom: 25, left: 10 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                              <XAxis
                                dataKey="bin"
                                type="number"
                                domain={['dataMin', 'dataMax']}
                                stroke="#9ca3af"
                                tick={{ fontSize: 10 }}
                                label={{ value: `Value (${info.unit})`, position: 'bottom', offset: 10, fill: '#9ca3af', fontSize: 11 }}
                              />
                              <YAxis
                                stroke="#9ca3af"
                                tick={{ fontSize: 10 }}
                                label={{ value: 'Count', angle: -90, position: 'insideLeft', offset: 5, fill: '#9ca3af', fontSize: 11 }}
                              />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151', fontSize: 12 }}
                                formatter={(value) => [value.toLocaleString(), 'Count']}
                                labelFormatter={(v) => `Value: ${Number(v).toFixed(2)}`}
                              />
                              <ReferenceLine x={info.valid_range.min} stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" label={{ value: 'Min', position: 'top', fill: '#10b981', fontSize: 10 }} />
                              <ReferenceLine x={info.valid_range.max} stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" label={{ value: 'Max', position: 'top', fill: '#10b981', fontSize: 10 }} />
                              <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                                {histData.map((entry, i) => (
                                  <Cell key={i} fill={entry.fill} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Systematic Offsets */}
      {Object.keys(data.systematic_offsets).length > 0 && (
        <div className="bg-dt-error/10 border border-dt-error/50 rounded-xl p-4">
          <h3 className="font-semibold text-dt-error mb-2">⚠️ Systematic Value Errors Detected</h3>
          <p className="text-gray-300 text-sm mb-3">
            These parameters have &lt;5% compliance, indicating systematic offset errors:
          </p>
          <div className="space-y-2">
            {Object.entries(data.systematic_offsets).map(([param, info]) => (
              <div key={param} className="bg-gray-800/50 rounded-lg p-3 flex justify-between items-center">
                <span className="text-white">{param}</span>
                <span className="text-dt-warning">
                  Suggested offset: {info.offset > 0 ? '+' : ''}{info.offset.toFixed(2)}
                </span>
              </div>
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

export default RangeCheck;
