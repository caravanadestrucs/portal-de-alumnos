import api from './index';

export const getAlumnosBoletas = async (params = {}) => {
  const response = await api.get('/boletas/alumnos', { params });
  return response.data;
};

export const descargarBoleta = async (alumnoId) => {
  const response = await api.get(`/boletas/download/${alumnoId}`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const disposition = response.headers['content-disposition'];
  let filename = `BOLETA_${alumnoId}.docx`;
  if (disposition) {
    const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match) filename = match[1].replace(/['"]/g, '');
  }
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const descargarBoletasMultiples = async (alumnoIds) => {
  const response = await api.get('/boletas/download-multiple', {
    params: { alumno_ids: alumnoIds.join(',') },
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const disposition = response.headers['content-disposition'];
  let filename = `BOLETAS.zip`;
  if (disposition) {
    const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match) filename = match[1].replace(/['"]/g, '');
  }
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const previewBoleta = async (alumnoId) => {
  const response = await api.get(`/boletas/preview/${alumnoId}`);
  return response.data;
};
