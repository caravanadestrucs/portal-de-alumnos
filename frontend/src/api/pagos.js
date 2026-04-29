import api from './index';

export const getPagosByAlumno = async (alumnoId) => {
  const response = await api.get(`/pagos/alumnos/${alumnoId}`);
  // API returns { notas: [...], resumen: {...}, alumno: {...} }
  return response.data.notas || [];
};

export const getAlumnosConPagosPendientes = async () => {
  const response = await api.get('/pagos/alumnos-pendientes');
  return response.data;
};

export const createPago = async (pagoData) => {
  const response = await api.post('/pagos', pagoData);
  return response.data.nota;
};

export const updatePago = async (id, pagoData) => {
  const response = await api.put(`/pagos/${id}`, pagoData);
  return response.data;
};

export const togglePagoStatus = async (id, options = {}) => {
  const response = await api.patch(`/pagos/toggle-pagado/${id}`, options);
  return response.data;
};

export const deletePago = async (id) => {
  const response = await api.delete(`/pagos/${id}`);
  return response.data;
};