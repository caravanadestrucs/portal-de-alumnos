import api from './index';

export const getAlumnos = async () => {
  const response = await api.get('/alumnos');
  // El backend devuelve { alumnos: [...], total, page, pages }
  return response.data.alumnos || [];
};

export const getAlumno = async (id) => {
  const response = await api.get(`/alumnos/${id}`);
  return response.data;
};

export const createAlumno = async (alumnoData) => {
  const response = await api.post('/alumnos', alumnoData);
  return response.data;
};

export const updateAlumno = async (id, alumnoData) => {
  const response = await api.put(`/alumnos/${id}`, alumnoData);
  return response.data;
};

export const deleteAlumno = async (id) => {
  const response = await api.delete(`/alumnos/${id}`);
  return response.data;
};

export const getMisDatos = async () => {
  const response = await api.get('/alumnos/mis-datos');
  return response.data;
};
