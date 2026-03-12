import { useState, useEffect } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, LineChart, Legend, ReferenceLine, ComposedChart, Area } from 'recharts';
import { getPathLossAnalysis } from '../utils/api';

function PathLossPlot({ sessionId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (sessionId) {
      loadData();
    }
  }, [sessionId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getPathLossAnalysis(sessionId);
      if (result.status === 'error') {
        setError(result.reason);
      } else {
        setData(result);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load path loss data');
    } finally {
      setLoading(false);
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
          <p className="text-gray-400">Loading path loss analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="p-2 rounded-lg hover:bg-gray-800">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h2 className="text-2xl font-bold text-white">Path Loss Validation</h2>
        </div>
        <div className="bg-dt-error/10 border border-dt-error/50 rounded-lg p-4 text-dt-error">
          {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  // Prepare scatter data
  const scatterData = data.scatter_data.distances.map((d, i) => ({
    distance: d,
    path_loss: data.scatter_data.path_loss[i],
  }));

  // Prepare reference model lines
  const referenceData = data.reference_models.distance.map((d, i) => ({
    distance: d,
    fspl: data.reference_models.fspl[i],
    los: data.reference_models.los[i],
    nlos: data.reference_models.nlos[i],
  }));

  // Prepare binned data with IQR
  const binnedData = data.binned_data.bin_centers.map((d, i) => ({
    distance: d,
    median: data.binned_data.medians[i],
    q25: data.binned_data.q25[i],
    q75: data.binned_data.q75[i],
    range: data.binned_data.medians[i] ? [data.binned_data.q25[i], data.binned_data.q75[i]] : null,
  })).filter(d => d.median !== null);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-gray-800">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h2 className="text-2xl font-bold text-white">Path Loss Validation</h2>
          <p className="text-gray-400">Compare measured path loss against 3GPP reference models</p>
        </div>
      </div>

      {/* MAE Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
          <p className="text-sm text-gray-400">Best Fit Model</p>
          <p className="text-2xl font-bold text-dt-accent">{data.best_fit}</p>
        </div>
        <div className={`bg-dt-card rounded-xl p-4 border ${data.best_fit === 'FSPL' ? 'border-dt-success' : 'border-gray-800'}`}>
          <p className="text-sm text-gray-400">FSPL MAE</p>
          <p className="text-2xl font-bold text-white">{data.mae.fspl.toFixed(2)} dB</p>
        </div>
        <div className={`bg-dt-card rounded-xl p-4 border ${data.best_fit === 'LOS' ? 'border-dt-success' : 'border-gray-800'}`}>
          <p className="text-sm text-gray-400">LOS MAE</p>
          <p className="text-2xl font-bold text-white">{data.mae.los.toFixed(2)} dB</p>
        </div>
        <div className={`bg-dt-card rounded-xl p-4 border ${data.best_fit === 'NLOS' ? 'border-dt-success' : 'border-gray-800'}`}>
          <p className="text-sm text-gray-400">NLOS MAE</p>
          <p className="text-2xl font-bold text-white">{data.mae.nlos.toFixed(2)} dB</p>
        </div>
      </div>

      {/* Main Chart */}
      <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
        <h3 className="font-semibold text-white mb-4">Path Loss vs Distance</h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="distance" 
                type="number"
                stroke="#9ca3af" 
                domain={[0, 500]}
                label={{ value: 'Distance (m)', position: 'bottom', offset: 40, fill: '#9ca3af' }}
              />
              <YAxis 
                stroke="#9ca3af" 
                domain={[60, 180]}
                label={{ value: 'Path Loss (dB)', angle: -90, position: 'insideLeft', offset: -40, fill: '#9ca3af' }}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #374151' }}
                formatter={(value, name) => [value?.toFixed(2) + ' dB', name]}
              />
              <Legend verticalAlign="top" height={36} />
              
              {/* Measured data scatter */}
              <Scatter 
                name="Measured" 
                data={scatterData.slice(0, 500)} 
                dataKey="path_loss"
                fill="#4f46e5" 
                opacity={0.3}
              />
              
              {/* Binned median with IQR */}
              <Line 
                name="Binned Median" 
                data={binnedData} 
                dataKey="median" 
                stroke="#ffffff" 
                strokeWidth={3}
                dot={{ fill: '#ffffff', r: 4 }}
              />
              
              {/* Reference models */}
              <Line 
                name="FSPL" 
                data={referenceData} 
                dataKey="fspl" 
                stroke="#10b981" 
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
              <Line 
                name="3GPP LOS" 
                data={referenceData} 
                dataKey="los" 
                stroke="#f59e0b" 
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
              <Line 
                name="3GPP NLOS" 
                data={referenceData} 
                dataKey="nlos" 
                stroke="#ef4444" 
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Model Info */}
      <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
        <h3 className="font-semibold text-white mb-4">3GPP Reference Models (5.9 GHz)</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-0.5 bg-dt-success"></div>
              <span className="text-dt-success font-medium">FSPL</span>
            </div>
            <p className="text-gray-400 font-mono text-xs">
              PL = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
            </p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-0.5 bg-dt-warning"></div>
              <span className="text-dt-warning font-medium">3GPP V2V LOS</span>
            </div>
            <p className="text-gray-400 font-mono text-xs">
              PL = 38.77 + 16.7*log10(d)
            </p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-0.5 bg-dt-error"></div>
              <span className="text-dt-error font-medium">3GPP V2V NLOS</span>
            </div>
            <p className="text-gray-400 font-mono text-xs">
              PL = 51.41 + 30*log10(d)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PathLossPlot;
