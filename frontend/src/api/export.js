import api from './index';

export const downloadSQL = async () => {
  const response = await api.get('/export/sql', {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadExcel = async () => {
  const response = await api.get('/export/excel', {
    responseType: 'blob',
  });
  return response.data;
};
