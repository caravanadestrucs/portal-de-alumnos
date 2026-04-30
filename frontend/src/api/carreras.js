import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getCarreras = async () => {
  const response = await api.get(`${API_URL}/carreras`);
  // El backend devuelve { carreras: [...] }
  return response.data.carreras || [];
};

export const getCarrera = async (id) => {
  const response = await api.get(`${API_URL}/carreras/${id}`);
  return response.data;
};

export const createCarrera = async (carreraData) => {
  const response = await api.post(`${API_URL}/carreras`, carreraData);
  return response.data;
};

export const updateCarrera = async (id, carreraData) => {
  const response = await api.put(`${API_URL}/carreras/${id}`, carreraData);
  return response.data;
};

export const deleteCarrera = async (id) => {
  const response = await api.delete(`${API_URL}/carreras/${id}`);
  return response.data;
};

export const getMateriasByCarrera = async (carreraId) => {
  const response = await api.get(`${API_URL}/carreras/${carreraId}/materias`);
  return response.data;
};
