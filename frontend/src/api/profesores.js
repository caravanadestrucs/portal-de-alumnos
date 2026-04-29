import api from './index';

export const getProfesores = async () => {
  const response = await api.get('/profesores');
  return response.data.profesores || [];
};

export const getProfesor = async (id) => {
  const response = await api.get(`/profesores/${id}`);
  return response.data.profesor;
};

export const createProfesor = async (data) => {
  const response = await api.post('/profesores', data);
  return response.data;
};

export const updateProfesor = async (id, data) => {
  const response = await api.put(`/profesores/${id}`, data);
  return response.data;
};

export const deleteProfesor = async (id) => {
  const response = await api.delete(`/profesores/${id}`);
  return response.data;
};