import api from './index';

export const getSedes = async (params = {}) => {
  const response = await api.get('/sedes', { params });
  return response.data;
};

export const getSede = async (id) => {
  const response = await api.get(`/sedes/${id}`);
  return response.data;
};

export const createSede = async (data) => {
  const response = await api.post('/sedes', data);
  return response.data;
};

export const updateSede = async (id, data) => {
  const response = await api.put(`/sedes/${id}`, data);
  return response.data;
};

export const deleteSede = async (id) => {
  const response = await api.delete(`/sedes/${id}`);
  return response.data;
};
