import api from './index';

export const previewImport = async (file, tipo) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo', tipo);
  const response = await api.post('/imports/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  });
  return response.data;
};

export const executeImport = async (file, tipo) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tipo', tipo);
  const response = await api.post('/imports/execute', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return response.data;
};
