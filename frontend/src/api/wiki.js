import api from './index';

export const getWikiPages = async (params = {}) => {
  const response = await api.get('/wiki/pages', { params });
  return response.data;
};

export const getWikiPage = async (id) => {
  const response = await api.get(`/wiki/pages/${id}`);
  return response.data;
};

export const createWikiPage = async (data) => {
  const response = await api.post('/wiki/pages', data);
  return response.data;
};

export const updateWikiPage = async (id, data) => {
  const response = await api.put(`/wiki/pages/${id}`, data);
  return response.data;
};

export const deleteWikiPage = async (id) => {
  const response = await api.delete(`/wiki/pages/${id}`);
  return response.data;
};

export const getWikiHistory = async (id) => {
  const response = await api.get(`/wiki/pages/${id}/history`);
  return response.data;
};

export const uploadAttachment = async (pageId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/wiki/pages/${pageId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const listAttachments = async (pageId) => {
  const response = await api.get(`/wiki/pages/${pageId}/attachments`);
  return response.data;
};

export const getAttachment = async (attachmentId) => {
  const response = await api.get(`/wiki/attachments/${attachmentId}`, { responseType: 'blob' });
  return response.data;
};
