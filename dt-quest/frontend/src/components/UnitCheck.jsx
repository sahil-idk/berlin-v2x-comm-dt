import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import { runStep5 } from '../utils/api';

function UnitCheck({ sessionId, results, onComplete, domainName }) {
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
      const result = await runStep5(sessionId);
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getScaleColor = (scale) => {
    switch (scale) {
      case 'dbm': return '#10b981';
      case 'linear_watts': return '#f59e0b';
      case 'suspicious_offset': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getScaleIcon = (scale) => {
    switch (scale) {
      case 'dbm': return '✓';
      case 'linear_watts': return '⚠️';
      case 'suspicious_offset': return '❌';
      default: return '?';
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
          <p className="text-gray-400">Verifying unit scales...</p>
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

  const { power_columns, path_loss_consistency, summary } = data;

  const plScatter = path_loss_consistency?.scatter_data?.derived.map((d, i) => ({
    derived: d,
    measured: path_loss_consistency.scatter_data.measured[i],
  })) || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 5: Unit Verification</h2>
        <p className="text-gray-400">Check power values for scale (linear watts vs. dBm) and verify path loss consistency</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Columns Checked</p>
          <p className="text-3xl font-bold text-white">{summary.columns_checked}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">dBm Confirmed</p>
          <p className="text-3xl font-bold text-dt-success">{summary.dbm_confirmed}</p>
        </div>
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Linear Detected</p>
          <p className="text-3xl font-bold text-dt-warning">{summary.linear_detected}</p>
        </div>
      </div>

      {/* Scale Indicators */}
      <div className="bg-dt-card rounded-xl border border-gray-800">
        <div className="px-4 py-3 border-b border-gray-800">
          <h3 className="font-semibold text-white">Power Column Scale Detection</h3>
        </div>
        <div className="p-4 space-y-4">
          {Object.entries(power_columns).map(([param, info]) => (
            <div 
              key={param} 
              className="bg-gray-800/50 rounded-xl p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{getScaleIcon(info.detected_scale)}</span>
                  <div>
                    <p className="font-medium text-white">{info.column}</p>
                    <p className="text-sm text-gray-400">{info.message}</p>
                  </div>
                </div>
                <span 
                  className="px-3 py-1 rounded-full text-sm font-medium"
                  style={{ 
                    backgroundColor: getScaleColor(info.detected_scale) + '20',
                    color: getScaleColor(info.detected_scale)
                  }}
                >
                  {info.detected_scale.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Min</p>
                  <p className="text-white font-mono">{info.min.toExponential(2)}</p>
                </div>
                <div>
                  <p className="text-gray-400">Max</p>
                  <p className="text-white font-mono">{info.max.toExponential(2)}</p>
                </div>
                <div>
                  <p className="text-gray-400">Mean</p>
                  <p className="text-white font-mono">{info.mean.toExponential(2)}</p>
                </div>
              </div>

              {/* Mini Histogram */}
              <div className="mt-4 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={info.histogram.counts.map((count, i) => ({ bin: i, count }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis hide />
                    <YAxis hide />
                    <Bar dataKey="count" fill={getScaleColor(info.detected_scale)} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Path Loss Consistency */}
      {path_loss_consistency && path_loss_consistency.status !== 'error' && (
        <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
          <h3 className="font-semibold text-white mb-4">Path Loss Consistency Check</h3>
          <p className="text-sm text-gray-400 mb-4">
            Verifying: Path Loss ≈ Tx_Power - Rx_Power
          </p>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-sm text-gray-400">Correlation (r)</p>
              <p className={`text-2xl font-bold ${path_loss_consistency.correlation > 0.9 ? 'text-dt-success' : path_loss_consistency.correlation > 0.5 ? 'text-dt-warning' : 'text-dt-error'}`}>
                {path_loss_consistency.correlation.toFixed(3)}
              </p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-sm text-gray-400">Consistent</p>
              <p className={`text-2xl font-bold ${path_loss_consistency.consistent ? 'text-dt-success' : 'text-dt-error'}`}>
                {path_loss_consistency.consistent ? 'Yes' : 'No'}
              </p>
            </div>
          </div>

          {plScatter.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="derived" name="Derived PL" stroke="#9ca3af" label={{ value: 'Derived Path Loss (dB)', position: 'bottom', fill: '#9ca3af' }} />
                  <YAxis dataKey="measured" name="Measured PL" stroke="#9ca3af" label={{ value: 'Measured Path Loss (dB)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }} />
                  <Scatter data={plScatter.slice(0, 300)} fill="#4f46e5" opacity={0.6} />
                  <ReferenceLine segment={[{ x: 50, y: 50 }, { x: 180, y: 180 }]} stroke="#10b981" strokeDasharray="3 3" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Warning for linear columns */}
      {summary.linear_detected > 0 && (
        <div className="bg-dt-warning/10 border border-dt-warning/50 rounded-xl p-4">
          <h3 className="font-semibold text-dt-warning mb-2">⚠️ Linear Scale Detected</h3>
          <p className="text-gray-300 text-sm">
            Some power columns appear to be in linear watts rather than dBm. 
            A 10*log10() conversion may be needed before use in path loss models.
          </p>
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

export default UnitCheck;
