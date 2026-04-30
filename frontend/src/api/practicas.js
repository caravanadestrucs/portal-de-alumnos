import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getPracticasByAlumno = async (alumnoId) => {
  const response = await api.get(`${API_URL}/practicas/alumno/${alumnoId}`);
  return response.data.practicas || [];
};

export const getAllPracticas = async () => {
  const response = await api.get(`${API_URL}/practicas`);
  return response.data;
};

export const createPractica = async (data) => {
  const response = await api.post(`${API_URL}/practicas`, data);
  return response.data;
};

export const updatePractica = async (id, data) => {
  const response = await api.put(`${API_URL}/practicas/${id}`, data);
  return response.data;
};

export const deletePractica = async (id) => {
  const response = await api.delete(`${API_URL}/practicas/${id}`);
  return response.data;
};