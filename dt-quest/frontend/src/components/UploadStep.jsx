import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDataset, getDomains, getPresets, getDomainParameters, setColumnMapping, setSessionDomain } from '../utils/api';

function UploadStep({ sessionId, setSessionId, datasetInfo, setDatasetInfo, mapping, setMapping, selectedDomain, setSelectedDomain, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [domains, setDomains] = useState([]);
  const [presets, setPresets] = useState({});
  const [parameterInfo, setParameterInfo] = useState({});
  const [selectedPreset, setSelectedPreset] = useState('');
  const [customParams, setCustomParams] = useState([]);
  const [customParamName, setCustomParamName] = useState('');
  const [customParamCol, setCustomParamCol] = useState('');

  // Load available domains on mount
  useEffect(() => {
    getDomains().then(setDomains).catch(console.error);
  }, []);

  // Load presets & parameter details when domain changes
  useEffect(() => {
    if (!selectedDomain) return;
    getPresets(selectedDomain).then(setPresets).catch(console.error);
    getDomainParameters(selectedDomain).then(setParameterInfo).catch(console.error);
    // Reset mapping when domain changes
    setMapping({});
    setSelectedPreset('');
  }, [selectedDomain]);

  const handleDomainChange = async (domainId) => {
    setSelectedDomain(domainId);
    // If we already have a session, notify the backend about the domain change
    if (sessionId) {
      try {
        await setSessionDomain(sessionId, domainId);
      } catch (err) {
        console.error('Failed to set domain on session:', err);
      }
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const file = acceptedFiles[0];
      const result = await uploadDataset(file);
      setSessionId(result.session_id);
      setDatasetInfo(result);
      // Set the domain on the newly created session
      if (selectedDomain) {
        await setSessionDomain(result.session_id, selectedDomain);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  }, [setSessionId, setDatasetInfo, selectedDomain]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/octet-stream': ['.parquet'],
    },
    multiple: false,
  });

  const applyPreset = (presetKey) => {
    if (!presets[presetKey] || !datasetInfo) return;
    
    const presetMapping = presets[presetKey].mappings;
    const newMapping = {};
    
    for (const [param, colName] of Object.entries(presetMapping)) {
      if (datasetInfo.column_names.includes(colName)) {
        newMapping[param] = colName;
      }
    }
    
    setMapping(newMapping);
    setSelectedPreset(presetKey);
  };

  const handleMappingChange = (param, value) => {
    if (value) {
      setMapping(prev => ({ ...prev, [param]: value }));
    } else {
      setMapping(prev => {
        const next = { ...prev };
        delete next[param];
        return next;
      });
    }
  };

  const handleAddCustomParam = () => {
    const key = customParamName.trim().toLowerCase().replace(/\s+/g, '_');
    if (!key || !customParamCol) return;
    if (mapping[key] || parameterInfo[key]) return; // don't override domain params
    setCustomParams(prev => [...prev, { key, label: customParamName.trim(), column: customParamCol }]);
    setMapping(prev => ({ ...prev, [key]: customParamCol }));
    setCustomParamName('');
    setCustomParamCol('');
  };

  const handleRemoveCustomParam = (key) => {
    setCustomParams(prev => prev.filter(p => p.key !== key));
    setMapping(prev => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleSubmitMapping = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      await setColumnMapping(sessionId, mapping);
      onComplete();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to set mapping');
    } finally {
      setLoading(false);
    }
  };

  const isValidMapping = () => {
    // At least 3 params must be mapped for any domain
    const mappedCount = Object.keys(mapping).length;
    if (mappedCount < 3) return false;

    // Domain-specific required check: at least one "required" param must be mapped
    const requiredParams = Object.entries(parameterInfo)
      .filter(([_, info]) => info.required)
      .map(([key]) => key);
    
    if (requiredParams.length > 0) {
      const mappedRequired = requiredParams.filter(k => mapping[k]);
      return mappedRequired.length >= Math.min(2, requiredParams.length);
    }
    return true;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const formatRange = (info) => {
    if (!info || !info.range) return '—';
    const r = info.range;
    const minStr = (r.min === null || r.min === undefined) ? '-∞' : String(r.min);
    const maxStr = (r.max === null || r.max === undefined) ? '∞' : String(r.max);
    return `[${minStr}, ${maxStr}] ${info.unit || ''}`.trim();
  };

  const selectedDomainInfo = domains.find(d => d.id === selectedDomain);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Step 0: Dataset Upload & Column Mapping</h2>
        <p className="text-gray-400">Select a domain, upload your dataset, and map columns to parameters</p>
      </div>

      {/* Domain Selector */}
      <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
        <h3 className="font-semibold text-white mb-3">Digital Twin Domain</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {domains.map((domain) => (
            <button
              key={domain.id}
              onClick={() => handleDomainChange(domain.id)}
              className={`
                relative p-4 rounded-xl border-2 text-left transition-all duration-200
                ${selectedDomain === domain.id
                  ? 'border-dt-accent bg-dt-accent/10 shadow-lg shadow-dt-accent/20'
                  : 'border-gray-700 bg-gray-800/50 hover:border-gray-500 hover:bg-gray-800'}
              `}
            >
              {selectedDomain === domain.id && (
                <div className="absolute top-2 right-2 w-5 h-5 rounded-full gradient-accent flex items-center justify-center">
                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              )}
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">{domain.icon}</span>
                <div>
                  <p className="font-semibold text-white">{domain.name}</p>
                  <p className="text-xs text-gray-400">{domain.parameter_count} params · {domain.preset_count} presets</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 line-clamp-2">{domain.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Upload Zone */}
      {!datasetInfo && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300
            ${isDragActive ? 'border-dt-accent bg-dt-accent/10' : 'border-gray-700 hover:border-gray-500'}
            ${loading ? 'opacity-50 pointer-events-none' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center">
              {loading ? (
                <svg className="w-8 h-8 text-dt-accent animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              )}
            </div>
            <div>
              <p className="text-lg font-medium text-white">
                {isDragActive ? 'Drop your file here' : 'Drag & drop your CSV or Parquet file'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {selectedDomainInfo ? `${selectedDomainInfo.icon} ${selectedDomainInfo.name} dataset` : 'or click to browse'}
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-dt-error/10 border border-dt-error/50 rounded-lg p-4 text-dt-error">
          {error}
        </div>
      )}

      {/* Dataset Info */}
      {datasetInfo && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
              <p className="text-sm text-gray-400">File Name</p>
              <p className="text-lg font-semibold text-white truncate">{datasetInfo.filename}</p>
            </div>
            <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
              <p className="text-sm text-gray-400">Rows</p>
              <p className="text-lg font-semibold text-white">{datasetInfo.rows.toLocaleString()}</p>
            </div>
            <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
              <p className="text-sm text-gray-400">Columns</p>
              <p className="text-lg font-semibold text-white">{datasetInfo.columns}</p>
            </div>
            <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
              <p className="text-sm text-gray-400">File Size</p>
              <p className="text-lg font-semibold text-white">{formatFileSize(datasetInfo.file_size)}</p>
            </div>
          </div>

          {/* Preview Table */}
          <div className="bg-dt-card rounded-xl border border-gray-800 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-white">Data Preview (First 10 rows)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-800/50">
                  <tr>
                    {datasetInfo.column_names.slice(0, 10).map((col, i) => (
                      <th key={i} className="px-4 py-2 text-left text-gray-400 font-medium whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                    {datasetInfo.column_names.length > 10 && (
                      <th className="px-4 py-2 text-gray-500">+{datasetInfo.column_names.length - 10} more</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {datasetInfo.preview.slice(0, 5).map((row, i) => (
                    <tr key={i} className="border-t border-gray-800">
                      {datasetInfo.column_names.slice(0, 10).map((col, j) => (
                        <td key={j} className="px-4 py-2 text-gray-300 whitespace-nowrap">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]).substring(0, 20) : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Presets */}
          {Object.keys(presets).length > 0 && (
            <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
              <h3 className="font-semibold text-white mb-1">Quick Presets</h3>
              <p className="text-xs text-gray-500 mb-3">
                {selectedDomainInfo?.icon} {selectedDomainInfo?.name} presets
              </p>
              <div className="flex gap-2 flex-wrap">
                {Object.entries(presets).map(([key, preset]) => (
                  <button
                    key={key}
                    onClick={() => applyPreset(key)}
                    className={`
                      px-4 py-2 rounded-lg text-sm font-medium transition-all
                      ${selectedPreset === key 
                        ? 'gradient-accent text-white' 
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}
                    `}
                    title={preset.description || ''}
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Column Mapping */}
          <div className="bg-dt-card rounded-xl border border-gray-800">
            <div className="px-4 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-white">Column Mapping</h3>
              <p className="text-sm text-gray-400">
                Map your dataset columns to {selectedDomainInfo?.name || 'domain'} parameters
              </p>
            </div>
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(parameterInfo).map(([param, info]) => (
                <div key={param} className="space-y-1">
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
                    {info.label || param}
                    {info.required && <span className="text-dt-error">*</span>}
                    <span className="text-xs text-gray-500">({formatRange(info)})</span>
                  </label>
                  <select
                    value={mapping[param] || ''}
                    onChange={(e) => handleMappingChange(param, e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-dt-accent"
                  >
                    <option value="">Not available</option>
                    {datasetInfo.column_names.map((col) => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Parameters */}
          <div className="bg-dt-card rounded-xl border border-gray-800">
            <div className="px-4 py-3 border-b border-gray-800">
              <h3 className="font-semibold text-white">Custom Parameters</h3>
              <p className="text-sm text-gray-400">Map additional columns not defined in the domain config</p>
            </div>
            <div className="p-4 space-y-3">
              {customParams.length > 0 && (
                <div className="space-y-2">
                  {customParams.map((cp) => (
                    <div key={cp.key} className="flex items-center gap-3 bg-gray-800/40 rounded-lg px-3 py-2">
                      <span className="text-sm text-gray-300 flex-1 font-medium">{cp.label}</span>
                      <span className="text-xs text-gray-500">→</span>
                      <span className="text-sm text-dt-accent font-mono">{cp.column}</span>
                      <button
                        onClick={() => handleRemoveCustomParam(cp.key)}
                        className="text-gray-500 hover:text-dt-error p-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Parameter name"
                  value={customParamName}
                  onChange={(e) => setCustomParamName(e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-dt-accent"
                />
                <select
                  value={customParamCol}
                  onChange={(e) => setCustomParamCol(e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-dt-accent"
                >
                  <option value="">Select column</option>
                  {datasetInfo.column_names.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
                <button
                  onClick={handleAddCustomParam}
                  disabled={!customParamName.trim() || !customParamCol}
                  className="px-4 py-2 rounded-lg text-sm font-medium gradient-accent text-white disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  + Add
                </button>
              </div>
            </div>
          </div>

          {/* Health Summary */}
          <div className="bg-dt-card rounded-xl p-4 border border-gray-800">
            <h3 className="font-semibold text-white mb-3">Dataset Health Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-400">Total Records</p>
                <p className="text-xl font-bold text-white">{datasetInfo.rows.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Columns Mapped</p>
                <p className="text-xl font-bold text-dt-success">{Object.keys(mapping).length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Columns Unmapped</p>
                <p className="text-xl font-bold text-dt-warning">
                  {datasetInfo.columns - Object.keys(mapping).length}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Active Domain</p>
                <p className="text-xl font-bold text-dt-accent">
                  {selectedDomainInfo?.icon} {selectedDomainInfo?.name || 'None'}
                </p>
              </div>
            </div>
          </div>

          {/* Validation & Next */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-400">
              {!isValidMapping() && (
                <span className="text-dt-warning">
                  ⚠️ Map at least 3 parameters (including required ones marked with *)
                </span>
              )}
            </div>
            <button
              onClick={handleSubmitMapping}
              disabled={!isValidMapping() || loading}
              className={`
                px-6 py-3 rounded-lg font-semibold transition-all
                ${isValidMapping() 
                  ? 'gradient-accent text-white hover:opacity-90' 
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'}
              `}
            >
              {loading ? 'Processing...' : 'Next Step →'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default UploadStep;
