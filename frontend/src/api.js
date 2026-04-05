const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

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
  
  // Якщо це DELETE запит (статус 204 No Content), просто повертаємо успіх
  if (response.status === 204) return { success: true };
  
  return response.json();
};

export const api = {
  login: (username, password) => request('/auth/login/', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request('/auth/logout/', { method: 'POST' }), // Справжній логаут на бекенді
  getMe: () => request('/auth/me/'),
  
  // Робота з заявками
  getRequests: () => request('/requests/'),
  getRequest: (id) => request(`/requests/${id}/`),
  createRequest: (data) => request('/requests/', { method: 'POST', body: JSON.stringify(data) }),
  updateRequest: (id, data) => request(`/requests/${id}/`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteRequest: (id) => request(`/requests/${id}/`, { method: 'DELETE' }), // Скасування заявки
  
  // Інфраструктура та Логи
  getPoints: () => request('/points/'),
  getTransactions: () => request('/transactions/'),
  getTransaction: (id) => request(`/transactions/${id}/`), // Деталі транзакції
  getWarehouses: () => request('/warehouses/'),
  getWarehouse: (id) => request(`/warehouses/${id}/`), // Деталі складу
  getSuppliers: () => request('/suppliers/'),
};