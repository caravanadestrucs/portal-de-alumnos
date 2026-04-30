import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getAsignaciones = async (params = {}) => {
  const response = await api.get(`${API_URL}/asignaciones`, { params });
  return response.data.asignaciones || [];
};

export const getAsignacion = async (id) => {
  const response = await api.get(`${API_URL}/asignaciones/${id}`);
  return response.data.asignacion;
};

export const createAsignacion = async (data) => {
  const response = await api.post(`${API_URL}/asignaciones`, data);
  return response.data;
};

export const updateAsignacion = async (id, data) => {
  const response = await api.put(`${API_URL}/asignaciones/${id}`, data);
  return response.data;
};

export const deleteAsignacion = async (id) => {
  const response = await api.delete(`${API_URL}/asignaciones/${id}`);
  return response.data;
};

export const puedeEditar = async (id) => {
  const response = await api.get(`${API_URL}/asignaciones/${id}/puede-editar`);
  return response.data;
};

export const getAsignacionesActuales = async (profesorId) => {
  const response = await api.get(`${API_URL}/asignaciones/profesor/${profesorId}/actuales`);
  return response.data;
};