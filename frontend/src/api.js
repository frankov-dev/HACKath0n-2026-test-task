const API_URL = 'http://127.0.0.1:8000/api';

const request = async (endpoint, options = {}) => {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Token ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
  
  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/';
  }
  
  if (!response.ok) throw new Error('Помилка запиту');
  return response.json();
};

export const api = {
  login: (username, password) => request('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),
  getMe: () => request('/auth/me/'),
  getRequests: () => request('/requests/'),
  getPoints: () => request('/points/'),
  getTransactions: () => request('/transactions/'), // НОВЕ: Транзакції (Маршрути)
  getWarehouses: () => request('/warehouses/'),     // НОВЕ: Склади
  getSuppliers: () => request('/suppliers/'),       // НОВЕ: Постачальники
  createRequest: (data) => request('/requests/', { method: 'POST', body: JSON.stringify(data) }),
  getNearestWarehouses: (lat, lng, resourceType) => 
    request(`/warehouses/nearest/?resource_type=${resourceType}&latitude=${lat}&longitude=${lng}&limit=5`),
};