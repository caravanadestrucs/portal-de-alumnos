import api from './index';

export const getMaterias = async (params = {}) => {
  const response = await api.get(`/materias`, { params });
  // El backend devuelve { materias: [...] }
  return response.data.materias || [];
};

export const getMateriasByCarrera = async (carreraId) => {
  // Try preferred by-carrera endpoint, fallback to query param
  try {
    const response = await api.get(`/materias/by-carrera/${carreraId}`);
    return response.data.materias || [];
  } catch (e) {
    // fallback to query param if by-carrera not available
    const response = await api.get(`/materias`, { params: { carrera_id: carreraId, per_page: 0 } });
    return response.data.materias || [];
  }
};

export const getMateria = async (id) => {
  const response = await api.get(`/materias/${id}`);
  return response.data;
};

export const createMateria = async (materiaData) => {
  const response = await api.post(`/materias`, materiaData);
  return response.data;
};

export const updateMateria = async (id, materiaData) => {
  const response = await api.put(`/materias/${id}`, materiaData);
  return response.data;
};

export const deleteMateria = async (id) => {
  const response = await api.delete(`/materias/${id}`);
  return response.data;
};
