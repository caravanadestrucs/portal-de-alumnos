import api from './index';

export const getSettings = async () => {
  const response = await api.get('/config');
  return response.data;
};

export const updateSettings = async (data) => {
  const response = await api.put('/config', data);
  return response.data;
};

export const testEmail = async () => {
  const response = await api.post('/config/test');
  return response.data;
};
