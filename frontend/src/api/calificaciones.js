import api from './index';

export const getCalificacionesByAlumno = async (alumnoId) => {
  // Backend returns: { alumno: {...}, calificaciones: [...], total: N }
  const response = await api.get(`/calificaciones/alumnos/${alumnoId}`);
  return response.data.calificaciones || [];
};

export const createCalificacion = async (calificacionData) => {
  const response = await api.post('/calificaciones', calificacionData);
  return response.data;
};

export const updateCalificacion = async (id, calificacionData) => {
  const response = await api.put(`/calificaciones/${id}`, calificacionData);
  return response.data;
};

export const getHistorial = async (alumnoId) => {
  const response = await api.get(`/calificaciones/alumnos/${alumnoId}`);
  return response.data;
};
