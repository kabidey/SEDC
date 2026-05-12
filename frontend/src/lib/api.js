import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('smifs_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      // Token expired or invalid
      const path = window.location.pathname;
      if (!path.startsWith('/login')) {
        localStorage.removeItem('smifs_token');
        localStorage.removeItem('smifs_user');
        if (path !== '/login') window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
