import { useState } from 'react';
import { api } from './api';
import { Truck, Lock, User, ArrowRight, Zap } from 'lucide-react';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const data = await api.login(username, password);
      localStorage.setItem('token', data.token);
      onLogin(data.user);
    } catch (err) {
      setError('Невірний логін або пароль');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center relative overflow-hidden">
      
      {/* Фоновий малюнок складу та неонових ліній (замість картинки використовуємо SVG для гнучкості) */}
      <svg className="absolute inset-0 w-full h-full opacity-30" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="neonGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
        {/* Приклад фонових ліній, можна додати більше */}
        <path d="M0 100 Q 250 50 500 100 T 1000 100" stroke="url(#neonGradient)" strokeWidth="2" fill="none" className="animate-dash" />
        <path d="M0 200 Q 300 250 600 200 T 1200 200" stroke="url(#neonGradient)" strokeWidth="1.5" fill="none" className="animate-dash" style={{animationDelay: '-2s'}} />
      </svg>

      {/* Головна панель (скломорфізм) */}
      <div className="glass-panel p-10 rounded-3xl w-full max-w-lg relative z-10 border border-white/10 neon-glow">
        
        {/* Заголовок та Лого */}
        <div className="flex flex-col items-center mb-10 text-center">
          <div className="bg-blue-600/20 p-4 rounded-2xl border border-blue-500/30 mb-5 neon-glow">
            <Truck className="w-10 h-10 text-blue-400" />
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Logistics Hub</h1>
          <p className="text-blue-200 text-sm mt-2 uppercase tracking-widest font-medium">Система Розумного Розподілу</p>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500/50 p-4 mb-8 rounded-xl backdrop-blur-sm text-center">
            <p className="text-red-300 text-sm font-medium">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-blue-300" />
            </div>
            <input 
              type="text" 
              placeholder="Логін диспетчера" 
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-white placeholder:text-slate-500 hover:bg-white/10"
              value={username} onChange={e => setUsername(e.target.value)}
            />
          </div>

          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-blue-300" />
            </div>
            <input 
              type="password" 
              placeholder="Пароль доступу" 
              className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-white placeholder:text-slate-500 hover:bg-white/10"
              value={password} onChange={e => setPassword(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 bg-blue-600/80 text-white py-4 rounded-2xl hover:bg-blue-600 hover:shadow-lg hover:shadow-blue-600/50 font-bold transition-all disabled:opacity-70 border border-blue-500/50 neon-glow"
          >
            {isLoading ? 'Підключення...' : 'Увійти в систему'}
            {!isLoading && <ArrowRight className="w-5 h-5" />}
          </button>
        </form>

        <div className="mt-10 pt-6 border-t border-white/10 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>AI-Warriors-test-task© 2026 Logistics Hub Inc.</span>
        </div>
      </div>
    </div>
  );
}