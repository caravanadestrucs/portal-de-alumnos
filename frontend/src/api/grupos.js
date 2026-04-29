import api from './index';

export const getGrupos = async (params = {}) => {
  const response = await api.get('/grupos', { params });
  return response.data.grupos || [];
};

export const getGrupo = async (id) => {
  const response = await api.get(`/grupos/${id}`);
  return response.data;
};

export const createGrupo = async (data) => {
  const response = await api.post('/grupos', data);
  return response.data;
};

export const updateGrupo = async (id, data) => {
  const response = await api.put(`/grupos/${id}`, data);
  return response.data;
};

export const deleteGrupo = async (id) => {
  const response = await api.delete(`/grupos/${id}`);
  return response.data;
};

// Integrantes
export const getIntegrantes = async (grupoId) => {
  const response = await api.get(`/grupos/${grupoId}/integrantes`);
  return response.data.integrantes || [];
};

export const addIntegrante = async (grupoId, alumnoId) => {
  const response = await api.post(`/grupos/${grupoId}/integrantes`, { alumno_id: alumnoId });
  return response.data;
};

export const removeIntegrante = async (grupoId, alumnoId) => {
  const response = await api.delete(`/grupos/${grupoId}/integrantes/${alumnoId}`);
  return response.data;
};

export const addIntegrantesBulk = async (grupoId, alumnoIds) => {
  const response = await api.post(`/grupos/${grupoId}/integrantes/bulk`, { alumno_ids: alumnoIds });
  return response.data;
};