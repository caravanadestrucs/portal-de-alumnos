import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getMaterias = async () => {
  const response = await api.get(`${API_URL}/materias`);
  // El backend devuelve { materias: [...] }
  return response.data.materias || [];
};

export const getMateria = async (id) => {
  const response = await api.get(`${API_URL}/materias/${id}`);
  return response.data;
};

export const createMateria = async (materiaData) => {
  const response = await api.post(`${API_URL}/materias`, materiaData);
  return response.data;
};

export const updateMateria = async (id, materiaData) => {
  const response = await api.put(`${API_URL}/materias/${id}`, materiaData);
  return response.data;
};

export const deleteMateria = async (id) => {
  const response = await api.delete(`${API_URL}/materias/${id}`);
  return response.data;
};
