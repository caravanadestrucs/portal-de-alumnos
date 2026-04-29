import api from './index';

export const getPracticasByAlumno = async (alumnoId) => {
  const response = await api.get(`/practicas/alumno/${alumnoId}`);
  return response.data.practicas || [];
};

export const getAllPracticas = async () => {
  const response = await api.get('/practicas');
  return response.data;
};

export const createPractica = async (data) => {
  const response = await api.post('/practicas', data);
  return response.data;
};

export const updatePractica = async (id, data) => {
  const response = await api.put(`/practicas/${id}`, data);
  return response.data;
};

export const deletePractica = async (id) => {
  const response = await api.delete(`/practicas/${id}`);
  return response.data;
};