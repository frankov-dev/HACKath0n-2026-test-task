import { useEffect, useState } from 'react';
import { api } from './api';
import { 
  LogOut, Truck, Package, Droplet, Archive, 
  AlertOctagon, CheckCircle2, Clock, Zap, MapPin, BarChart3,
  ArrowRight, History, Building2, Factory, Navigation
} from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('requests'); // Стейт для вкладок
  const [data, setData] = useState({ requests: [], points: [], transactions: [], warehouses: [], suppliers: [] });
  const [loading, setLoading] = useState(true);
  const [newReq, setNewReq] = useState({ point: '', resource_type: 'FUEL', quantity_requested: '', priority: 1, is_urgent: false });

  const fetchData = async () => {
    try {
      // Викликаємо ВСІ ендпойнти одночасно!
      const [reqData, ptsData, trxData, whData, supData] = await Promise.all([
        api.getRequests(),
        api.getPoints(),
        api.getTransactions(),
        api.getWarehouses(),
        api.getSuppliers()
      ]);
      
      setData({ requests: reqData, points: ptsData, transactions: trxData, warehouses: whData, suppliers: supData });
      
      if (ptsData.length > 0) setNewReq(prev => ({ ...prev, point: ptsData[0].id }));
    } catch (error) {
      console.error("Помилка", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    if (newReq.quantity_requested <= 0) return alert("Кількість має бути більшою за нуль!");
    if (!newReq.point) return alert("Оберіть точку доставки!");
    try {
      await api.createRequest(newReq);
      fetchData(); // Оновлює всі вкладки
      setNewReq(prev => ({ ...prev, quantity_requested: '', is_urgent: false }));
    } catch (err) {
      alert('Помилка при створенні заявки.');
    }
  };

  const getResourceIcon = (type) => {
    if (type === 'FUEL') return <Droplet className="w-5 h-5 text-blue-500" />;
    if (type === 'GOODS') return <Package className="w-5 h-5 text-amber-500" />;
    return <Archive className="w-5 h-5 text-slate-500" />;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans pb-10">
      {/* HEADER */}
      <header className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg"><Truck className="w-6 h-6" /></div>
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
          <button onClick={onLogout} className="flex items-center gap-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 px-4 py-2 rounded-xl transition-all border border-slate-700">
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-bold">Вийти</span>
          </button>
        </div>
      </header>

      {/* TABS NAVIGATION */}
      <div className="bg-white border-b border-slate-200 sticky top-[72px] z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button onClick={() => setActiveTab('requests')} className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'requests' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}>
              <Zap className="w-4 h-4" /> Оперативний Дашборд
            </button>
            <button onClick={() => setActiveTab('routes')} className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'routes' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}>
              <Navigation className="w-4 h-4" /> Маршрути та Логи
            </button>
            <button onClick={() => setActiveTab('infra')} className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'infra' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}>
              <Building2 className="w-4 h-4" /> Інфраструктура
            </button>
          </nav>
        </div>
      </div>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 mt-4">
        
        {loading ? (
          <div className="p-20 flex flex-col items-center justify-center text-blue-500 gap-4">
            <Clock className="w-10 h-10 animate-spin" />
            <p className="font-bold text-lg">Синхронізація з сервером...</p>
          </div>
        ) : (
          <>
            {/* ВКЛАДКА 1: ЗАЯВКИ (Те, що було) */}
            {activeTab === 'requests' && (
              <div className="space-y-6">
                {/* Форма створення (тільки для диспетчерів та точок) */}
                {user.role !== 'WAREHOUSE_MANAGER' && (
                  <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-50 to-white border-b border-slate-100 px-6 py-4 flex items-center gap-2">
                      <Zap className="w-5 h-5 text-blue-600" />
                      <h2 className="text-lg font-bold text-slate-800">Створити Заявку</h2>
                    </div>
                    <form onSubmit={handleCreateRequest} className="p-6 flex flex-col md:flex-row flex-wrap gap-5 items-end">
                      <div className="flex-1 min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Об'єкт (Точка)</label>
                        <select className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" value={newReq.point || ''} onChange={e => setNewReq({...newReq, point: parseInt(e.target.value)})}>
                          {data.points.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                      </div>
                      <div className="flex-1 min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Тип ресурсу</label>
                        <select className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" value={newReq.resource_type} onChange={e => setNewReq({...newReq, resource_type: e.target.value})}>
                          <option value="FUEL">⛽ Паливо</option>
                          <option value="GOODS">📦 Товари</option>
                          <option value="SUPPLIES">🔧 Матеріали</option>
                        </select>
                      </div>
                      <div className="flex-1 min-w-[100px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Кількість</label>
                        <input type="number" min="1" placeholder="Напр. 10" className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" value={newReq.quantity_requested} onChange={e => setNewReq({...newReq, quantity_requested: parseFloat(e.target.value)})} />
                      </div>
                      <div className="flex-1 min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Пріоритет</label>
                        <select className="w-full bg-slate-50 border border-slate-200 text-slate-700 py-3 px-4 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none" value={newReq.priority} onChange={e => setNewReq({...newReq, priority: parseInt(e.target.value)})}>
                          <option value={1}>🟢 Нормальний</option>
                          <option value={2}>🟡 Підвищений</option>
                          <option value={3}>🔴 Критичний</option>
                        </select>
                      </div>
                      <div className={`flex items-center gap-3 px-5 py-3 rounded-xl border cursor-pointer ${newReq.is_urgent ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`} onClick={() => setNewReq({...newReq, is_urgent: !newReq.is_urgent})}>
                        <div className={`w-5 h-5 rounded flex items-center justify-center border ${newReq.is_urgent ? 'bg-red-500 border-red-600' : 'bg-white border-slate-300'}`}>
                          {newReq.is_urgent && <CheckCircle2 className="w-4 h-4 text-white" />}
                        </div>
                        <span className={`text-sm font-bold ${newReq.is_urgent ? 'text-red-700' : 'text-slate-600'}`}>ТЕРМІНОВО</span>
                      </div>
                      <button type="submit" className="bg-blue-600 text-white px-8 py-3 rounded-xl hover:bg-blue-700 font-bold whitespace-nowrap shadow-md shadow-blue-500/20">Створити</button>
                    </form>
                  </section>
                )}

                {/* Таблиця заявок */}
                <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                  <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                    <h2 className="text-lg font-bold text-slate-800">Статус Заявок</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                          <th className="p-4 font-bold border-b border-slate-200">ID / Точка</th>
                          <th className="p-4 font-bold border-b border-slate-200">Ресурс</th>
                          <th className="p-4 font-bold border-b border-slate-200">Пріоритет</th>
                          <th className="p-4 font-bold border-b border-slate-200">Потреба</th>
                          <th className="p-4 font-bold border-b border-slate-200">Виділено</th>
                          <th className="p-4 font-bold border-b border-slate-200">Статус</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {data.requests.map(req => (
                          <tr key={req.id} className="hover:bg-slate-50/80 transition-colors">
                            <td className="p-4"><p className="font-bold text-slate-800 text-sm">{req.point}</p><p className="text-xs text-slate-400">Заявка #{req.id}</p></td>
                            <td className="p-4"><div className="flex items-center gap-2">{getResourceIcon(req.resource_type)} <span className="font-medium text-sm">{req.resource_type}</span></div></td>
                            <td className="p-4"><div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border ${req.priority === 3 || req.is_urgent ? 'bg-red-50 text-red-700 border-red-200' : req.priority === 2 ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>{req.priority_display} {req.is_urgent && '(ТЕРМІНОВО)'}</div></td>
                            <td className="p-4 font-medium">{req.quantity_requested}</td>
                            <td className="p-4 text-lg font-black text-blue-600">{req.quantity_allocated}</td>
                            <td className="p-4"><span className={`inline-flex px-3 py-1 rounded-full text-xs font-bold ${req.status === 'ALLOCATED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'}`}>{req.status_display}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </div>
            )}

            {/* ВКЛАДКА 2: МАРШРУТИ ТА ЛОГИ (Транзакції) */}
            {activeTab === 'routes' && (
              <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="px-6 py-5 border-b border-slate-100 bg-gradient-to-r from-emerald-50 to-white flex items-center gap-2">
                  <History className="w-5 h-5 text-emerald-600" />
                  <h2 className="text-lg font-bold text-slate-800">Журнал переміщення ресурсів</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                        <th className="p-4 font-bold border-b border-slate-200">Час / Тип</th>
                        <th className="p-4 font-bold border-b border-slate-200">Ресурс</th>
                        <th className="p-4 font-bold border-b border-slate-200">Звідки (Відправник)</th>
                        <th className="p-4 font-bold border-b border-slate-200 text-center">Шлях</th>
                        <th className="p-4 font-bold border-b border-slate-200">Куди (Отримувач)</th>
                        <th className="p-4 font-bold border-b border-slate-200">Примітка</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.transactions.length === 0 ? <tr><td colSpan="6" className="p-8 text-center text-slate-400">Транзакцій поки немає</td></tr> : data.transactions.map(trx => (
                        <tr key={trx.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="p-4">
                            <p className="text-xs text-slate-400 font-mono">{new Date(trx.created_at).toLocaleString('uk-UA')}</p>
                            <p className={`text-xs font-bold mt-1 ${trx.transaction_type === 'ALLOCATION' ? 'text-emerald-600' : trx.transaction_type === 'SHORTAGE' ? 'text-red-500' : 'text-amber-500'}`}>{trx.transaction_type_display}</p>
                          </td>
                          <td className="p-4">
                            <div className="flex flex-col">
                              <span className="font-black text-lg text-slate-800">{trx.quantity} од.</span>
                              <span className="text-xs text-slate-500">{trx.resource_type_display}</span>
                            </div>
                          </td>
                          <td className="p-4 font-medium text-sm text-slate-700">{trx.from_location || '-'}</td>
                          <td className="p-4 text-center">
                            <div className="flex items-center justify-center bg-slate-100 rounded-full w-8 h-8 mx-auto">
                              <ArrowRight className="w-4 h-4 text-slate-400" />
                            </div>
                          </td>
                          <td className="p-4 font-bold text-sm text-slate-800">{trx.to_location || '-'}</td>
                          <td className="p-4 text-xs text-slate-500 max-w-xs">{trx.note}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* ВКЛАДКА 3: ІНФРАСТРУКТУРА */}
            {activeTab === 'infra' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <section className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
                  <div className="flex items-center gap-2 mb-6 border-b pb-4">
                    <Building2 className="w-6 h-6 text-blue-600" />
                    <h2 className="text-xl font-bold text-slate-800">Склади (Хаби)</h2>
                  </div>
                  <div className="space-y-4">
                    {data.warehouses.map(wh => (
                      <div key={wh.id} className="p-4 border border-slate-100 rounded-2xl bg-slate-50/50">
                        <h3 className="font-bold text-lg text-slate-800">{wh.name}</h3>
                        <p className="text-sm text-slate-500 mb-3 flex items-center gap-1"><MapPin className="w-3.5 h-3.5"/> Місто: {wh.city}</p>
                        <div className="flex gap-3 flex-wrap">
                          {wh.stocks && wh.stocks.map(stock => (
                            <div key={stock.id} className="bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium">
                              {stock.resource_type_display}: <span className="font-bold text-blue-600">{stock.available_quantity} од.</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
                
                <section className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6">
                  <div className="flex items-center gap-2 mb-6 border-b pb-4">
                    <Factory className="w-6 h-6 text-amber-600" />
                    <h2 className="text-xl font-bold text-slate-800">Постачальники</h2>
                  </div>
                  <div className="space-y-4">
                    {data.suppliers.map(sup => (
                      <div key={sup.id} className="p-4 border border-slate-100 rounded-2xl bg-amber-50/30 flex items-start gap-4">
                        <div className="bg-amber-100 p-3 rounded-xl"><Factory className="w-5 h-5 text-amber-600" /></div>
                        <div>
                          <h3 className="font-bold text-lg text-slate-800">{sup.name}</h3>
                          <p className="text-sm text-slate-500 flex items-center gap-1 mt-1"><MapPin className="w-3.5 h-3.5"/> {sup.city} (Широта: {sup.latitude}, Довгота: {sup.longitude})</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}