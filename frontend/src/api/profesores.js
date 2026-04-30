import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getProfesores = async () => {
  const response = await api.get(`${API_URL}/profesores`);
  return response.data.profesores || [];
};

export const getProfesor = async (id) => {
  const response = await api.get(`${API_URL}/profesores/${id}`);
  return response.data.profesor;
};

export const createProfesor = async (data) => {
  const response = await api.post(`${API_URL}/profesores`, data);
  return response.data;
};

export const updateProfesor = async (id, data) => {
  const response = await api.put(`${API_URL}/profesores/${id}`, data);
  return response.data;
};

export const deleteProfesor = async (id) => {
  const response = await api.delete(`${API_URL}/profesores/${id}`);
  return response.data;
};