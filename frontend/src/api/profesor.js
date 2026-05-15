import api from '../api';

export const getMisAsignaciones = async (profesorId) => {
  const res = await api.get(`/profesor/mis-asignaciones`, {
    params: { profesor_id: profesorId }
  });
  return res.data;
};

export const getGrupoCalificaciones = async (asignacionId) => {
  const res = await api.get(`/profesor/asignacion/${asignacionId}/calificaciones`);
  return res.data;
};

export const updateCalificacionProfesor = async (asignacionId, data) => {
  const res = await api.put(`/profesor/asignacion/${asignacionId}/calificaciones`, data);
  return res.data;
};
