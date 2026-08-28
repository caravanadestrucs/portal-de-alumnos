import api from './index';

export const getCalificacionesByAlumno = async (alumnoId, params = {}) => {
  // Backend returns: { alumno: {...}, calificaciones: [...], materias: [...], total, total_materias, materias_con_calificacion }
  const response = await api.get(`/calificaciones/alumnos/${alumnoId}`, { params });
  return response.data;
};

export const createCalificacion = async (calificacionData) => {
  const response = await api.post(`/calificaciones`, calificacionData);
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

export const bulkUpdateCalificaciones = (payload) => api.put('/calificaciones/bulk', { calificaciones: payload });
