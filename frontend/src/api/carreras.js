import api from './index';

export const getCarreras = async () => {
  const response = await api.get('/carreras');
  // El backend devuelve { carreras: [...] }
  return response.data.carreras || [];
};

export const getCarrera = async (id) => {
  const response = await api.get(`/carreras/${id}`);
  return response.data;
};

export const createCarrera = async (carreraData) => {
  const response = await api.post('/carreras', carreraData);
  return response.data;
};

export const updateCarrera = async (id, carreraData) => {
  const response = await api.put(`/carreras/${id}`, carreraData);
  return response.data;
};

export const deleteCarrera = async (id) => {
  const response = await api.delete(`/carreras/${id}`);
  return response.data;
};

export const getMateriasByCarrera = async (carreraId) => {
  const response = await api.get(`/carreras/${carreraId}/materias`);
  return response.data;
};
