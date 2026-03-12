import { useState, useEffect } from 'react';
import ReadinessGauge from './ReadinessGauge';
import { applyCorrections, exportCsv, getQualityReport, getDataPreview } from '../utils/api';

function CleanExport({ sessionId, pipelineResults, readinessScore, onComplete, domainName }) {
  const [corrections, setCorrections] = useState({
    apply_offsets: false,
    apply_unit_conversion: false,
    add_completeness_flags: true,
    filter_columns: false,
    flag_outliers: true,
  });
  const [loading, setLoading] = useState(false);
  const [applied, setApplied] = useState(null);
  const [error, setError] = useState(null);
  const [previewTab, setPreviewTab] = useState('original');
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    if (applied && sessionId) {
      fetchPreview(previewTab);
    }
  }, [applied, previewTab]);

  const fetchPreview = async (type) => {
    setPreviewLoading(true);
    try {
      const data = await getDataPreview(sessionId, type, 20);
      setPreviewData(data);
    } catch (err) {
      console.error('Preview fetch failed:', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const hasOffsets = Object.keys(pipelineResults.step1?.systematic_offsets || {}).length > 0;
  const hasLinear = (pipelineResults.step5?.summary?.linear_detected || 0) > 0;

  const handleApplyCorrections = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await applyCorrections(sessionId, corrections);
      setApplied(result);
      onComplete(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to apply corrections');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    exportCsv(sessionId);
  };

  const handleExportReport = async () => {
    try {
      const report = await getQualityReport(sessionId);
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dt_quest_report_${sessionId}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to generate report');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 6: Clean & Export</h2>
        <p className="text-gray-400">Apply corrections, review dataset quality, and export cleaned data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Corrections Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-dt-card rounded-xl border border-gray-800">
            <div className="px-4 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-white">Corrections Panel</h3>
              <p className="text-sm text-gray-400">Select corrections to apply (opt-in)</p>
            </div>
            <div className="p-4 space-y-4">
              {/* Correction A */}
              <label className={`flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                corrections.apply_offsets ? 'bg-dt-accent/10 border-dt-accent/50' : 'bg-gray-800/30 border-gray-700'
              } ${!hasOffsets ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <input
                  type="checkbox"
                  checked={corrections.apply_offsets}
                  onChange={(e) => setCorrections(prev => ({ ...prev, apply_offsets: e.target.checked }))}
                  disabled={!hasOffsets}
                  className="mt-1 w-5 h-5 rounded border-gray-600 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-white">Correction A: Offset Subtraction</p>
                  <p className="text-sm text-gray-400">
                    Apply suggested offsets from range validation to fix systematic value errors
                  </p>
                  {hasOffsets && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {Object.entries(pipelineResults.step1?.systematic_offsets || {}).map(([param, info]) => (
                        <span key={param} className="px-2 py-1 bg-dt-warning/20 text-dt-warning rounded text-xs">
                          {param}: {info.offset > 0 ? '+' : ''}{info.offset.toFixed(1)} offset
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </label>

              {/* Correction B */}
              <label className={`flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                corrections.apply_unit_conversion ? 'bg-dt-accent/10 border-dt-accent/50' : 'bg-gray-800/30 border-gray-700'
              } ${!hasLinear ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <input
                  type="checkbox"
                  checked={corrections.apply_unit_conversion}
                  onChange={(e) => setCorrections(prev => ({ ...prev, apply_unit_conversion: e.target.checked }))}
                  disabled={!hasLinear}
                  className="mt-1 w-5 h-5 rounded border-gray-600 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-white">Correction B: Unit Conversion</p>
                  <p className="text-sm text-gray-400">
                    Convert linear watts to dBm using 10*log10() for columns detected as linear scale
                  </p>
                </div>
              </label>

              {/* Correction C */}
              <label className={`flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                corrections.add_completeness_flags ? 'bg-dt-accent/10 border-dt-accent/50' : 'bg-gray-800/30 border-gray-700'
              }`}>
                <input
                  type="checkbox"
                  checked={corrections.add_completeness_flags}
                  onChange={(e) => setCorrections(prev => ({ ...prev, add_completeness_flags: e.target.checked }))}
                  className="mt-1 w-5 h-5 rounded border-gray-600 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-white">Correction C: Completeness Flagging</p>
                  <p className="text-sm text-gray-400">
                    Add flag columns for missing values and vehicle completeness scores (no imputation)
                  </p>
                </div>
              </label>

              {/* Correction D */}
              <label className={`flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                corrections.filter_columns ? 'bg-dt-accent/10 border-dt-accent/50' : 'bg-gray-800/30 border-gray-700'
              }`}>
                <input
                  type="checkbox"
                  checked={corrections.filter_columns}
                  onChange={(e) => setCorrections(prev => ({ ...prev, filter_columns: e.target.checked }))}
                  className="mt-1 w-5 h-5 rounded border-gray-600 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-white">Correction D: Column Selection</p>
                  <p className="text-sm text-gray-400">
                    Remove unmapped columns, keep only mapped parameters and generated flags
                  </p>
                </div>
              </label>

              {/* Correction E */}
              <label className={`flex items-start gap-4 p-4 rounded-lg border transition-colors cursor-pointer ${
                corrections.flag_outliers ? 'bg-dt-accent/10 border-dt-accent/50' : 'bg-gray-800/30 border-gray-700'
              }`}>
                <input
                  type="checkbox"
                  checked={corrections.flag_outliers}
                  onChange={(e) => setCorrections(prev => ({ ...prev, flag_outliers: e.target.checked }))}
                  className="mt-1 w-5 h-5 rounded border-gray-600 text-dt-accent focus:ring-dt-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-white">Correction E: Outlier Flagging</p>
                  <p className="text-sm text-gray-400">
                    Add outlier_flag column for records with z-score {">"} 3 (not dropped, just flagged)
                  </p>
                </div>
              </label>
            </div>

            {error && (
              <div className="p-4 border-t border-gray-800">
                <div className="bg-dt-error/10 border border-dt-error/50 rounded-lg p-3 text-dt-error text-sm">
                  {error}
                </div>
              </div>
            )}

            <div className="p-4 border-t border-gray-800">
              <button
                onClick={handleApplyCorrections}
                disabled={loading}
                className="w-full px-6 py-3 rounded-lg font-semibold gradient-accent text-white hover:opacity-90 transition-all disabled:opacity-50"
              >
                {loading ? 'Applying Corrections...' : 'Apply Selected Corrections'}
              </button>
            </div>
          </div>

          {/* Applied Corrections Result */}
          {applied && (
            <div className="bg-dt-success/10 border border-dt-success/50 rounded-xl p-4">
              <h3 className="font-semibold text-dt-success mb-3">✓ Corrections Applied</h3>
              <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                <div>
                  <p className="text-gray-400">Original Shape</p>
                  <p className="text-white font-mono">{applied.original_shape.join(' × ')}</p>
                </div>
                <div>
                  <p className="text-gray-400">Cleaned Shape</p>
                  <p className="text-white font-mono">{applied.cleaned_shape.join(' × ')}</p>
                </div>
              </div>
              {applied.applied_corrections.length > 0 && (
                <div className="space-y-2">
                  <p className="text-gray-400 text-sm">Applied:</p>
                  {applied.applied_corrections.map((c, i) => (
                    <div key={i} className="bg-gray-800/50 rounded px-3 py-2 text-sm text-gray-300">
                      {c.type.replace(/_/g, ' ')}: {c.column}
                      {c.std_preserved !== undefined && (
                        <span className={c.std_preserved ? 'text-dt-success' : 'text-dt-warning'}>
                          {' '}(σ {c.std_preserved ? 'preserved' : 'changed'})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Before/After Data Preview */}
          {applied && (
            <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                <h3 className="font-semibold text-white">Data Preview</h3>
                <div className="flex bg-gray-800 rounded-lg p-0.5">
                  <button
                    onClick={() => setPreviewTab('original')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      previewTab === 'original'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    Original Data
                  </button>
                  <button
                    onClick={() => setPreviewTab('cleaned')}
                    className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                      previewTab === 'cleaned'
                        ? 'bg-dt-accent text-white'
                        : 'text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    Cleaned Data
                  </button>
                </div>
              </div>

              {previewLoading ? (
                <div className="p-8 text-center text-gray-400">
                  <svg className="w-6 h-6 animate-spin mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Loading preview...
                </div>
              ) : previewData ? (
                <div className="overflow-x-auto">
                  <div className="text-xs text-gray-500 px-4 py-2 border-b border-gray-800">
                    Showing {previewData.rows.length} of {previewData.total_rows.toLocaleString()} rows
                    {previewData.columns.length > 10 && ` · ${previewData.columns.length - 10} more columns`}
                  </div>
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-gray-800/50">
                        {previewData.columns.slice(0, 10).map((col) => (
                          <th
                            key={col}
                            className={`px-3 py-2 text-left text-gray-400 font-medium whitespace-nowrap ${
                              previewData.modified_columns?.includes(col) ? 'bg-yellow-500/10 text-yellow-400' : ''
                            }`}
                          >
                            {col}
                            {previewData.modified_columns?.includes(col) && ' ✎'}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.rows.map((row, i) => (
                        <tr key={i} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                          {previewData.columns.slice(0, 10).map((col) => (
                            <td
                              key={col}
                              className={`px-3 py-1.5 text-gray-300 whitespace-nowrap font-mono ${
                                previewData.modified_columns?.includes(col) ? 'bg-yellow-500/5' : ''
                              }`}
                            >
                              {row[col] !== null && row[col] !== undefined
                                ? typeof row[col] === 'number'
                                  ? row[col].toFixed ? row[col].toFixed(4) : row[col]
                                  : String(row[col]).slice(0, 20)
                                : '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </div>
          )}

          {/* Export Buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleExportCSV}
              disabled={!applied}
              className="flex-1 px-6 py-4 rounded-xl font-semibold bg-dt-success text-white hover:bg-dt-success/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Cleaned CSV
            </button>
            <button
              onClick={handleExportReport}
              disabled={!applied}
              className="flex-1 px-6 py-4 rounded-xl font-semibold bg-dt-accent text-white hover:bg-dt-accent/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download Quality Report
            </button>
          </div>
        </div>

        {/* Readiness Score Panel */}
        <div className="space-y-6">
          <div className="bg-dt-card rounded-xl border border-gray-800 p-6">
            <h3 className="font-semibold text-white mb-4 text-center">DT-Readiness Score</h3>
            <div className="flex justify-center mb-6">
              <div className="transform scale-150">
                <ReadinessGauge score={applied?.readiness_score || readinessScore} />
              </div>
            </div>
            
            {(applied?.readiness_score || readinessScore) && (
              <div className="space-y-3 mt-6">
                {Object.entries((applied?.readiness_score || readinessScore).components).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className="h-full rounded-full transition-all"
                          style={{ 
                            width: `${Math.min(value, 100)}%`,
                            backgroundColor: value >= 70 ? '#10b981' : value >= 40 ? '#f59e0b' : '#ef4444'
                          }}
                        />
                      </div>
                      <span className="text-white font-mono w-12 text-right">{value.toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Key Findings */}
          <div className="bg-dt-card rounded-xl border border-gray-800 p-4">
            <h3 className="font-semibold text-white mb-3">Key Findings</h3>
            <div className="space-y-2 text-sm">
              {pipelineResults.step1?.summary?.systematic_errors > 0 && (
                <div className="flex items-start gap-2 text-dt-error">
                  <span>❌</span>
                  <span>{pipelineResults.step1.summary.systematic_errors} systematic value error(s)</span>
                </div>
              )}
              {pipelineResults.step2?.verdict?.status === 'linear_detected' && (
                <div className="flex items-start gap-2 text-dt-warning">
                  <span>⚠️</span>
                  <span>Representation error detected (linear scale)</span>
                </div>
              )}
              {pipelineResults.step3?.summary?.constant_placeholders > 0 && (
                <div className="flex items-start gap-2 text-dt-warning">
                  <span>⚠️</span>
                  <span>{pipelineResults.step3.summary.constant_placeholders} constant placeholder(s)</span>
                </div>
              )}
              {(pipelineResults.step4?.summary?.average_completeness || 0) < 90 && (
                <div className="flex items-start gap-2 text-dt-warning">
                  <span>⚠️</span>
                  <span>Low average completeness ({(pipelineResults.step4?.summary?.average_completeness || 0).toFixed(1)}%)</span>
                </div>
              )}
              {(pipelineResults.step1?.summary?.passing || 0) === (pipelineResults.step1?.summary?.total_params || 0) && (
                <div className="flex items-start gap-2 text-dt-success">
                  <span>✓</span>
                  <span>All parameters within {domainName || 'domain'} ranges</span>
                </div>
              )}
              {pipelineResults.step2?.verdict?.status === 'dBm_confirmed' && (
                <div className="flex items-start gap-2 text-dt-success">
                  <span>✓</span>
                  <span>Cross-parameter consistency confirmed</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CleanExport;
