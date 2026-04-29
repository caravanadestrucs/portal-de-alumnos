import api from './index';

// Get current assignments for a professor
export const getMisAsignaciones = async (profesorId) => {
  const response = await api.get(`/asignaciones/profesor/${profesorId}/actuales`);
  return response.data;
};

// Get all assignments for a professor (no filter by date)
export const getTodasMisAsignaciones = async (profesorId) => {
  const response = await api.get('/asignaciones', { params: { profesor_id: profesorId } });
  return response.data.asignaciones || [];
};

// Get group members (students) with their grades
export const getGrupoCalificaciones = async (asignacionId) => {
  const response = await api.get(`/profesor/asignacion/${asignacionId}/calificaciones`);
  return response.data;
};

// Update a student's grade for a specific assignment
export const updateCalificacionProfesor = async (asignacionId, data) => {
  const response = await api.put(`/profesor/asignacion/${asignacionId}/calificaciones`, data);
  return response.data;
};