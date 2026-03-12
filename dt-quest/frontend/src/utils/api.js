import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getDomains = async () => {
  const response = await api.get('/domains');
  return response.data;
};

export const setSessionDomain = async (sessionId, domainId) => {
  const response = await api.post(`/session/${sessionId}/domain`, { domainId });
  return response.data;
};

export const getPresets = async (domainId) => {
  const response = await api.get('/presets', { params: domainId ? { domain: domainId } : {} });
  return response.data;
};

export const getParameterRanges = async (domainId) => {
  const response = await api.get('/parameter-ranges', { params: domainId ? { domain: domainId } : {} });
  return response.data;
};

export const getDomainParameters = async (domainId) => {
  const response = await api.get(`/domain/${domainId}/parameters`);
  return response.data;
};


export const setColumnMapping = async (sessionId, mapping) => {
  const response = await api.post(`/mapping/${sessionId}`, mapping);
  return response.data;
};

export const runStep1 = async (sessionId) => {
  const response = await api.post(`/pipeline/step1/${sessionId}`);
  return response.data;
};

export const discoverStep2 = async (sessionId) => {
  const response = await api.post(`/pipeline/step2/${sessionId}/discover`);
  return response.data;
};

export const runStep2 = async (sessionId, config = {}) => {
  const response = await api.post(`/pipeline/step2/${sessionId}`, config);
  return response.data;
};

export const runStep3 = async (sessionId) => {
  const response = await api.post(`/pipeline/step3/${sessionId}`);
  return response.data;
};

export const runStep4 = async (sessionId) => {
  const response = await api.post(`/pipeline/step4/${sessionId}`);
  return response.data;
};

export const runStep5 = async (sessionId) => {
  const response = await api.post(`/pipeline/step5/${sessionId}`);
  return response.data;
};

export const applyCorrections = async (sessionId, corrections) => {
  const response = await api.post(`/pipeline/step6/${sessionId}`, corrections);
  return response.data;
};

export const getReadinessScore = async (sessionId) => {
  const response = await api.get(`/pipeline/readiness/${sessionId}`);
  return response.data;
};

export const getPathLossAnalysis = async (sessionId) => {
  const response = await api.get(`/path-loss-analysis/${sessionId}`);
  return response.data;
};

export const exportCsv = (sessionId) => {
  window.open(`${API_BASE}/export/csv/${sessionId}`, '_blank');
};

export const getQualityReport = async (sessionId) => {
  const response = await api.get(`/export/report/${sessionId}`);
  return response.data;
};

export const getDataPreview = async (sessionId, type = 'original', limit = 20) => {
  const response = await api.get(`/preview/${sessionId}`, { params: { type, limit } });
  return response.data;
};

export const getColumnSample = async (sessionId, columnName, limit = 500) => {
  const response = await api.get(`/column-sample/${sessionId}/${encodeURIComponent(columnName)}`, { params: { limit } });
  return response.data;
};

export const getSessions = async () => {
  const response = await api.get('/sessions');
  return response.data;
};

export const deleteSessionApi = async (sessionId) => {
  const response = await api.delete(`/sessions/${sessionId}`);
  return response.data;
};

// Custom Equations
export const getEquations = async (sessionId) => {
  const response = await api.get(`/equations/${sessionId}`);
  return response.data;
};

export const addEquation = async (sessionId, equation) => {
  const response = await api.post(`/equations/${sessionId}`, equation);
  return response.data;
};

export const deleteEquationApi = async (sessionId, eqId) => {
  const response = await api.delete(`/equations/${sessionId}/${eqId}`);
  return response.data;
};

export const validateEquations = async (sessionId) => {
  const response = await api.post(`/equations/${sessionId}/validate`);
  return response.data;
};

export const parseEquationApi = async (equation) => {
  const response = await api.post('/equations/parse', { equation });
  return response.data;
};

export default api;
