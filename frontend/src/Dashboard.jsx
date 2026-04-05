import { useEffect, useState } from 'react';
import { api } from './api';
import { 
  LogOut, Truck, Package, Droplet, Archive, 
  AlertOctagon, CheckCircle2, Clock, Zap, MapPin, BarChart3 
} from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newReq, setNewReq] = useState({ resource_type: 'FUEL', quantity_requested: '', priority: 1, is_urgent: false });

  const fetchRequests = async () => {
    try {
      const data = await api.getRequests();
      setRequests(data);
    } catch (error) {
      console.error("Помилка", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequests(); }, []);

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    if (newReq.quantity_requested <= 0) return alert("Кількість має бути більшою за нуль!");
    try {
      await api.createRequest(newReq);
      fetchRequests();
      setNewReq({ ...newReq, quantity_requested: '', is_urgent: false });
    } catch (err) {
      alert('Помилка при створенні заявки.');
    }
  };

  // Рахуємо статистику для красивих віджетів
  const totalRequests = requests.length;
  const criticalRequests = requests.filter(r => r.priority === 3 || r.is_urgent).length;
  const allocatedRequests = requests.filter(r => r.status === 'ALLOCATED').length;

  // Допоміжні функції для дизайну
  const getResourceIcon = (type) => {
    if (type === 'FUEL') return <Droplet className="w-5 h-5 text-blue-500" />;
    if (type === 'GOODS') return <Package className="w-5 h-5 text-amber-500" />;
    return <Archive className="w-5 h-5 text-slate-500" />;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
      {/* Верхня панель (Навігація) */}
      <header className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Logistics Hub</h1>
            <p className="text-xs text-slate-400 font-medium tracking-wider uppercase">
              {user.role === 'DISPATCHER' ? 'Головний диспетчер' : user.role === 'DELIVERY_POINT_MANAGER' ? 'Менеджер точки' : 'Склад'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-full border border-slate-700">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-sm font-medium">{user.username}</span>
          </div>
          <button onClick={onLogout} className="flex items-center gap-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 px-4 py-2 rounded-xl transition-all border border-slate-700 hover:border-red-500/30">
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-bold">Вийти</span>
          </button>
        </div>
      </header>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Віджети статистики */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex items-center gap-4">
            <div className="bg-blue-50 p-4 rounded-xl text-blue-600"><BarChart3 className="w-8 h-8" /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Всього заявок</p>
              <h3 className="text-3xl font-extrabold text-slate-800">{totalRequests}</h3>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex items-center gap-4">
            <div className="bg-red-50 p-4 rounded-xl text-red-600"><AlertOctagon className="w-8 h-8" /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Критичні / Термінові</p>
              <h3 className="text-3xl font-extrabold text-slate-800">{criticalRequests}</h3>
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 flex items-center gap-4">
            <div className="bg-emerald-50 p-4 rounded-xl text-emerald-600"><CheckCircle2 className="w-8 h-8" /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Успішно розподілено</p>
              <h3 className="text-3xl font-extrabold text-slate-800">{allocatedRequests}</h3>
            </div>
          </div>
        </div>

        {/* Форма створення запиту */}
        {user.role !== 'WAREHOUSE_MANAGER' && (
          <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="bg-blue-50/50 border-b border-slate-100 px-6 py-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <h2 className="text-lg font-bold text-slate-800">Нова заявка на постачання</h2>
            </div>
            <form onSubmit={handleCreateRequest} className="p-6 flex flex-col md:flex-row gap-5 items-end">
              <div className="flex-1 w-full">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Тип ресурсу</label>
                <select className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition" value={newReq.resource_type} onChange={e => setNewReq({...newReq, resource_type: e.target.value})}>
                  <option value="FUEL">⛽ Паливо</option>
                  <option value="GOODS">📦 Товари</option>
                  <option value="SUPPLIES">🔧 Витратні матеріали</option>
                </select>
              </div>
              <div className="flex-1 w-full">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Кількість</label>
                <input type="number" min="1" placeholder="Напр. 100" className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition" value={newReq.quantity_requested} onChange={e => setNewReq({...newReq, quantity_requested: parseFloat(e.target.value)})} />
              </div>
              <div className="flex-1 w-full">
                <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Пріоритет</label>
                <select className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition" value={newReq.priority} onChange={e => setNewReq({...newReq, priority: parseInt(e.target.value)})}>
                  <option value={1}>🟢 Нормальний</option>
                  <option value={2}>🟡 Підвищений</option>
                  <option value={3}>🔴 Критичний</option>
                </select>
              </div>
              
              <div className={`flex items-center gap-3 px-5 py-3 rounded-xl border cursor-pointer transition-all ${newReq.is_urgent ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`} onClick={() => setNewReq({...newReq, is_urgent: !newReq.is_urgent})}>
                <div className={`w-5 h-5 rounded flex items-center justify-center border ${newReq.is_urgent ? 'bg-red-500 border-red-600' : 'bg-white border-slate-300'}`}>
                  {newReq.is_urgent && <CheckCircle2 className="w-4 h-4 text-white" />}
                </div>
                <span className={`text-sm font-bold ${newReq.is_urgent ? 'text-red-700' : 'text-slate-600'}`}>ТЕРМІНОВО</span>
              </div>

              <button type="submit" className="bg-blue-600 text-white px-8 py-3 rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/30 font-bold transition-all">
                Створити
              </button>
            </form>
          </section>
        )}

        {/* Таблиця заявок */}
        <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <h2 className="text-lg font-bold text-slate-800">Журнал перерозподілу</h2>
          </div>
          
          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-10 flex flex-col items-center justify-center text-slate-400 gap-3">
                <Clock className="w-8 h-8 animate-spin" />
                <p className="font-medium">Оновлення бази даних...</p>
              </div>
            ) : (
              <table className="min-w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                    <th className="p-4 font-bold border-b border-slate-200">ID / Точка</th>
                    <th className="p-4 font-bold border-b border-slate-200">Ресурс</th>
                    <th className="p-4 font-bold border-b border-slate-200">Пріоритет</th>
                    <th className="p-4 font-bold border-b border-slate-200">Потреба</th>
                    <th className="p-4 font-bold border-b border-slate-200">Виділено</th>
                    <th className="p-4 font-bold border-b border-slate-200">Статус алгоритму</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {requests.length === 0 ? (
                    <tr><td colSpan="6" className="p-8 text-center text-slate-400 font-medium">Активних заявок немає</td></tr>
                  ) : requests.map(req => (
                    <tr key={req.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="bg-slate-100 p-2 rounded-lg text-slate-500"><MapPin className="w-4 h-4" /></div>
                          <div>
                            <p className="font-bold text-slate-800 text-sm">{req.point}</p>
                            <p className="text-xs text-slate-400">Заявка #{req.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          {getResourceIcon(req.resource_type)}
                          <span className="font-medium text-slate-700 text-sm">
                            {req.resource_type === 'FUEL' ? 'Паливо' : req.resource_type === 'GOODS' ? 'Товари' : 'Матеріали'}
                          </span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border ${
                          req.priority === 3 || req.is_urgent ? 'bg-red-50 text-red-700 border-red-200' : 
                          req.priority === 2 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}>
                          {req.priority === 3 || req.is_urgent ? <AlertOctagon className="w-3.5 h-3.5" /> : null}
                          {req.priority_display} {req.is_urgent && '(ТЕРМІНОВО)'}
                        </div>
                      </td>
                      <td className="p-4 font-medium text-slate-600">{req.quantity_requested} од.</td>
                      <td className="p-4">
                        <span className={`text-lg font-black ${req.quantity_allocated >= req.quantity_requested ? 'text-emerald-600' : req.quantity_allocated > 0 ? 'text-amber-500' : 'text-slate-400'}`}>
                          {req.quantity_allocated}
                        </span>
                        <span className="text-xs text-slate-400 ml-1">од.</span>
                      </td>
                      <td className="p-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${
                          req.status === 'ALLOCATED' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' : 
                          req.status === 'PARTIAL' ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}>
                          {req.status === 'ALLOCATED' && <CheckCircle2 className="w-3.5 h-3.5 mr-1" />}
                          {req.status_display}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}