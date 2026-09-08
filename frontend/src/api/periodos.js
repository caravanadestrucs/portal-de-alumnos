import api from './index';

export const getPeriodos = async (params = {}) => {
  const response = await api.get('/periodos', { params });
  return response.data;
};

export const createPeriodo = async (data) => {
  const response = await api.post('/periodos', data);
  return response.data;
};

export const updatePeriodo = async (id, data) => {
  const response = await api.put(`/periodos/${id}`, data);
  return response.data;
};

export const deletePeriodo = async (id) => {
  const response = await api.delete(`/periodos/${id}`);
  return response.data;
};
