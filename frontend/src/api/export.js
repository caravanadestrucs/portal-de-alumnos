import api from './index';

export const downloadSQL = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const url = params ? `/export/sql?${params}` : `/export/sql`;
  const response = await api.get(url, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadExcel = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const url = params ? `/export/excel?${params}` : `/export/excel`;
  const response = await api.get(url, {
    responseType: 'blob',
  });
  return response.data;
};

// filters example: { carrera_id, periodo, carrera }
// TODO: backend wire filtros en export routes
