import api from './index';

export const getAsignaciones = async (params = {}) => {
  const response = await api.get('/asignaciones', { params });
  return response.data.asignaciones || [];
};

export const getAsignacion = async (id) => {
  const response = await api.get(`/asignaciones/${id}`);
  return response.data.asignacion;
};

export const createAsignacion = async (data) => {
  const response = await api.post('/asignaciones', data);
  return response.data;
};

export const updateAsignacion = async (id, data) => {
  const response = await api.put(`/asignaciones/${id}`, data);
  return response.data;
};

export const deleteAsignacion = async (id) => {
  const response = await api.delete(`/asignaciones/${id}`);
  return response.data;
};

export const puedeEditar = async (id) => {
  const response = await api.get(`/asignaciones/${id}/puede-editar`);
  return response.data;
};

export const getAsignacionesActuales = async (profesorId) => {
  const response = await api.get(`/asignaciones/profesor/${profesorId}/actuales`);
  return response.data;
};