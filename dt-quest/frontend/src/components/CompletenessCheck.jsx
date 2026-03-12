import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { runStep4 } from '../utils/api';

function CompletenessCheck({ sessionId, results, onComplete }) {
  const [data, setData] = useState(results || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!data && sessionId) {
      runAnalysis();
    }
  }, [sessionId]);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await runStep4(sessionId);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getCompletenessColor = (pct) => {
    if (pct >= 90) return '#10b981';
    if (pct >= 50) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <svg className="w-12 h-12 text-dt-accent animate-spin mx-auto mb-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="text-gray-400">Analyzing completeness patterns...</p>
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

  const columnData = Object.entries(data.overall_completeness).map(([col, info]) => ({
    column: col.length > 15 ? col.substring(0, 15) + '...' : col,
    fullName: col,
    completeness: info.completeness_percentage,
    nanCount: info.nan_count,
  }));

  const vehicleData = Object.entries(data.vehicle_completeness || {}).map(([id, info]) => ({
    vehicle: String(id).length > 10 ? String(id).substring(0, 10) + '...' : id,
    fullId: id,
    completeness: info.completeness_rate,
    records: info.total_records,
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 4: Completeness Profiling</h2>
        <p className="text-gray-400">Compute per-vehicle, per-parameter NaN rates and detect structured missingness</p>
      </div>

      {/* Insight Banner */}
      <div className="bg-dt-accent/10 border border-dt-accent/50 rounded-xl p-4">
        <p className="text-dt-accent font-medium">💡 Key Insight</p>
        <p className="text-gray-300 text-sm mt-1">{data.insight}</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Total Records</p>
          <p className="text-2xl font-bold text-white">{data.summary.total_records.toLocaleString()}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Avg Completeness</p>
          <p className="text-2xl font-bold" style={{ color: getCompletenessColor(data.summary.average_completeness) }}>
            {data.summary.average_completeness.toFixed(1)}%
          </p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Completeness Gap</p>
          <p className="text-2xl font-bold text-dt-warning">{data.completeness_gap_pp.toFixed(1)}pp</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">&gt;50% Missing</p>
          <p className="text-2xl font-bold text-dt-error">{data.summary.columns_with_50pct_missing}</p>
        </div>
      </div>

      {/* Column Completeness Chart */}
      <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
        <h3 className="font-semibold text-white mb-4">Completeness by Column</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={columnData} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="column" stroke="#9ca3af" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
              <YAxis stroke="#9ca3af" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }}
                formatter={(value, name, props) => [`${value.toFixed(1)}%`, 'Completeness']}
                labelFormatter={(label, payload) => payload[0]?.payload?.fullName || label}
              />
              <Bar dataKey="completeness" radius={[4, 4, 0, 0]}>
                {columnData.map((entry, index) => (
                  <Cell key={index} fill={getCompletenessColor(entry.completeness)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Vehicle Completeness */}
      {vehicleData.length > 0 && (
        <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
          <h3 className="font-semibold text-white mb-4">Completeness by Vehicle</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={vehicleData.slice(0, 20)} margin={{ left: 10, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="vehicle" stroke="#9ca3af" tick={{ fontSize: 10 }} />
                <YAxis stroke="#9ca3af" domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }}
                  formatter={(value) => [`${value.toFixed(1)}%`, 'Completeness']}
                />
                <Bar dataKey="completeness" radius={[4, 4, 0, 0]}>
                  {vehicleData.map((entry, index) => (
                    <Cell key={index} fill={getCompletenessColor(entry.completeness)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Heatmap */}
      {data.heatmap_data && data.heatmap_data.length > 0 && (
        <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
          <h3 className="font-semibold text-white mb-4">Missingness Heatmap (Vehicle × Column)</h3>
          <p className="text-sm text-gray-400 mb-4">Cells colored by NaN percentage. White = 0%, Dark red = 100%</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="px-2 py-1 text-left text-gray-400">Vehicle</th>
                  {Object.keys(data.overall_completeness).map((col) => (
                    <th key={col} className="px-2 py-1 text-gray-400 whitespace-nowrap">
                      {col.substring(0, 8)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.heatmap_data.map((row, i) => (
                  <tr key={i}>
                    <td className="px-2 py-1 text-gray-300 whitespace-nowrap">{row.vehicle_id}</td>
                    {Object.keys(data.overall_completeness).map((col) => {
                      const nanPct = row[col] || 0;
                      const intensity = Math.min(nanPct / 100, 1);
                      return (
                        <td 
                          key={col} 
                          className="px-2 py-1"
                          style={{ 
                            backgroundColor: `rgba(239, 68, 68, ${intensity})`,
                          }}
                          title={`${col}: ${nanPct.toFixed(1)}% missing`}
                        >
                          &nbsp;
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Missingness Correlations */}
      <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="font-semibold text-white">Missingness Correlations</h3>
          <p className="text-xs text-gray-500 mt-1">Column pairs where missing values tend to occur together</p>
        </div>
        {data.missingness_correlation && Object.keys(data.missingness_correlation).length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Param A</th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Param B</th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Correlation</th>
                  <th className="px-4 py-3 text-left text-gray-400 font-medium">Interpretation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {Object.entries(data.missingness_correlation)
                  .sort(([, a], [, b]) => Math.abs(b) - Math.abs(a))
                  .map(([pair, r]) => {
                    const [colA, colB] = pair.split('|');
                    const absR = Math.abs(r);
                    return (
                      <tr key={pair} className="hover:bg-gray-800/30">
                        <td className="px-4 py-3 text-white font-mono text-xs">{colA}</td>
                        <td className="px-4 py-3 text-white font-mono text-xs">{colB}</td>
                        <td className="px-4 py-3">
                          <span className={`font-bold ${absR > 0.7 ? 'text-dt-error' : 'text-dt-warning'}`}>
                            {r.toFixed(3)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-400 text-xs">
                          {absR > 0.7 ? '🔴 Always missing together' : '🟡 Often missing together'}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4 text-center">
            <span className="text-dt-success text-sm">✓ No structured missingness patterns detected</span>
          </div>
        )}
      </div>

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

export default CompletenessCheck;
