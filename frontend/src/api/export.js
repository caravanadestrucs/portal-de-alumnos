import api from './index';

const API_URL = import.meta.env.VITE_API_URL;

export const downloadSQL = async () => {
  const response = await api.get(`${API_URL}/export/sql`, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadExcel = async () => {
  const response = await api.get(`${API_URL}/export/excel`, {
    responseType: 'blob',
  });
  return response.data;
};
