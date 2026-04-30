import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getGrupos = async (params = {}) => {
  const response = await api.get(`${API_URL}/grupos`, { params });
  return response.data.grupos || [];
};

export const getGrupo = async (id) => {
  const response = await api.get(`${API_URL}/grupos/${id}`);
  return response.data;
};

export const createGrupo = async (data) => {
  const response = await api.post(`${API_URL}/grupos`, data);
  return response.data;
};

export const updateGrupo = async (id, data) => {
  const response = await api.put(`${API_URL}/grupos/${id}`, data);
  return response.data;
};

export const deleteGrupo = async (id) => {
  const response = await api.delete(`${API_URL}/grupos/${id}`);
  return response.data;
};

// Integrantes
export const getIntegrantes = async (grupoId) => {
  const response = await api.get(`${API_URL}/grupos/${grupoId}/integrantes`);
  return response.data.integrantes || [];
};

export const addIntegrante = async (grupoId, alumnoId) => {
  const response = await api.post(`${API_URL}/grupos/${grupoId}/integrantes`, { alumno_id: alumnoId });
  return response.data;
};

export const removeIntegrante = async (grupoId, alumnoId) => {
  const response = await api.delete(`${API_URL}/grupos/${grupoId}/integrantes/${alumnoId}`);
  return response.data;
};

export const addIntegrantesBulk = async (grupoId, alumnoIds) => {
  const response = await api.post(`${API_URL}/grupos/${grupoId}/integrantes/bulk`, { alumno_ids: alumnoIds });
  return response.data;
};