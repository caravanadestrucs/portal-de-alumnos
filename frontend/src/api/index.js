import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Request to:', config.url, 'Token exists:', !!token);
    } else {
      console.log('Request to:', config.url, 'NO token');
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - just pass through, NO auto-logout
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Just log and reject - don't modify localStorage
    const status = error.response?.status;
    const url = error.config?.url;
    console.log('API Error:', status, 'URL:', url);
    if (status === 401) {
      console.log('Got 401 - token may be invalid');
    }
    return Promise.reject(error);
  }
);

export default api;