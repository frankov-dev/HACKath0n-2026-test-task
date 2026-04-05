import { useState, useEffect } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';
import { api } from './api';

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Якщо в браузері є токен, пробуємо дістати дані користувача
      api.getMe()
        .then(data => setUser(data))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center bg-gray-100 font-bold text-xl text-blue-600">Завантаження системи...</div>;
  }

  // Якщо юзер є — показуємо Дашборд. Якщо ні — сторінку Логіну.
  return user ? <Dashboard user={user} onLogout={handleLogout} /> : <Login onLogin={setUser} />;
}