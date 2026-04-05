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
      api.getMe()
        .then(data => setUser(data))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout(); // Інвалідуємо токен на бекенді!
    } catch (error) {
      console.error("Помилка при логауті на сервері", error);
    } finally {
      localStorage.removeItem('token'); // Видаляємо локально
      setUser(null);
    }
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center bg-slate-900 font-bold text-xl text-blue-500">Завантаження системи...</div>;
  }

  return user ? <Dashboard user={user} onLogout={handleLogout} /> : <Login onLogin={setUser} />;
}