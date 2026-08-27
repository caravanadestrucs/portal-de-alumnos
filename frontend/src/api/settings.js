import api from './index';

export const getSettings = async () => {
  const response = await api.get('/config');
  return response.data;
};

export const updateSettings = async (data) => {
  const response = await api.put('/config', data);
  return response.data;
};

export const testEmail = async (toEmail) => {
  const response = await api.post('/config/test', { to_email: toEmail });
  return response.data;
};

// Calendario de pagos CRUD wiring — stub conectado a /config/calendario (key-value)
// TODO S3 full: backend endpoint dedicado /api/calendario si escala
export const getPaymentCalendar = async () => {
  const response = await api.get('/config');
  return response.data?.config?.calendario_pagos || [];
};

export const createPaymentEntry = async (data) => {
  const response = await api.post('/config/calendario', data);
  return response.data;
};

export const updatePaymentEntry = async (id, data) => {
  const response = await api.put(`/config/calendario/${id}`, data);
  return response.data;
};

export const deletePaymentEntry = async (id) => {
  const response = await api.delete(`/config/calendario/${id}`);
  return response.data;
};
