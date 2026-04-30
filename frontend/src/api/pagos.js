import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const getPagosByAlumno = async (alumnoId) => {
  const response = await api.get(`${API_URL}/pagos/alumnos/${alumnoId}`);
  // API returns { notas: [...], resumen: {...}, alumno: {...} }
  return response.data.notas || [];
};

export const getAlumnosConPagosPendientes = async () => {
  const response = await api.get(`${API_URL}/pagos/alumnos-pendientes`);
  return response.data;
};

export const createPago = async (pagoData) => {
  const response = await api.post(`${API_URL}/pagos`, pagoData);
  return response.data.nota;
};

export const updatePago = async (id, pagoData) => {
  const response = await api.put(`${API_URL}/pagos/${id}`, pagoData);
  return response.data;
};

export const togglePagoStatus = async (id, options = {}) => {
  const response = await api.patch(`${API_URL}/pagos/toggle-pagado/${id}`, options);
  return response.data;
};

export const deletePago = async (id) => {
  const response = await api.delete(`${API_URL}/pagos/${id}`);
  return response.data;
};