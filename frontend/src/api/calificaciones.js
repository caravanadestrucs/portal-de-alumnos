import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getCalificacionesByAlumno = async (alumnoId) => {
  // Backend returns: { alumno: {...}, calificaciones: [...], total: N }
  const response = await api.get(`${API_URL}/calificaciones/alumnos/${alumnoId}`);
  return response.data.calificaciones || [];
};

export const createCalificacion = async (calificacionData) => {
  const response = await api.post(`${API_URL}/calificaciones`, calificacionData);
  return response.data;
};

export const updateCalificacion = async (id, calificacionData) => {
  const response = await api.put(`${API_URL}/calificaciones/${id}`, calificacionData);
  return response.data;
};

export const getHistorial = async (alumnoId) => {
  const response = await api.get(`${API_URL}/calificaciones/alumnos/${alumnoId}`);
  return response.data;
};
