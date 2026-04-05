import { useEffect, useState } from 'react';
import { api } from './api';
import { 
  LogOut, Truck, Package, Droplet, Archive, 
  AlertOctagon, CheckCircle2, Clock, Zap, MapPin, BarChart3,
  ArrowRight, History, Building2, Factory, Navigation, Trash2, Info
} from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('requests');
  const [data, setData] = useState({ requests: [], points: [], transactions: [], warehouses: [], suppliers: [] });
  const [loading, setLoading] = useState(true);
  const [newReq, setNewReq] = useState({ point: '', resource_type: 'FUEL', quantity_requested: '', priority: 1, is_urgent: false });
  
  // Нові стейти для ефекту наведення
  const [hoveredItem, setHoveredItem] = useState(null); 
  const [detailsCache, setDetailsCache] = useState({}); // Кеш, щоб не спамити бекенд запитами

  const fetchData = async () => {
    try {
      const [reqData, ptsData, trxData, whData, supData] = await Promise.all([
        api.getRequests(), api.getPoints(), api.getTransactions(), api.getWarehouses(), api.getSuppliers()
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
      fetchData();
      setNewReq(prev => ({ ...prev, quantity_requested: '', is_urgent: false }));
    } catch (err) { alert('Помилка при створенні заявки.'); }
  };

  const handleDeleteRequest = async (id) => {
    if (!window.confirm('Ви впевнені, що хочете скасувати цю заявку? Ресурси будуть звільнені.')) return;
    try {
      await api.deleteRequest(id);
      fetchData(); 
    } catch (err) { alert('Не вдалося скасувати заявку.'); }
  };

  // ФУНКЦІЯ ДЛЯ ОБРОБКИ НАВЕДЕННЯ (HOVER)
  const handleHoverItem = async (type, item) => {
    // Одразу показуємо базову інфу і стан завантаження
    setHoveredItem({ type, id: item.id, basic: item, loading: true });
    
    if (type === 'Склад') {
      if (detailsCache[`wh_${item.id}`]) {
        // Якщо вже завантажували цей склад - беремо з кешу моментально
        setHoveredItem({ type, id: item.id, basic: item, loading: false, detailed: detailsCache[`wh_${item.id}`] });
      } else {
        try {
          const detailedData = await api.getWarehouse(item.id);
          setDetailsCache(prev => ({...prev, [`wh_${item.id}`]: detailedData})); // Зберігаємо в кеш
          // Оновлюємо стейт, тільки якщо курсор досі на цьому ж об'єкті
          setHoveredItem(prev => (prev && prev.id === item.id) ? { type, id: item.id, basic: item, loading: false, detailed: detailedData } : prev);
        } catch (e) {
          setHoveredItem(prev => (prev && prev.id === item.id) ? { type, id: item.id, basic: item, loading: false, error: true } : prev);
        }
      }
    } else if (type === 'Постачальник') {
      // Для постачальника у нас вже є всі дані з загального списку
      setHoveredItem({ type, id: item.id, basic: item, loading: false, detailed: item });
    }
  };

  const getResourceIcon = (type) => {
    if (type === 'FUEL') return <Droplet className="w-5 h-5 text-blue-500" />;
    if (type === 'GOODS') return <Package className="w-5 h-5 text-amber-500" />;
    return <Archive className="w-5 h-5 text-slate-500" />;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans pb-10 overflow-x-hidden">
      <header className="bg-slate-900 text-white px-6 py-4 flex justify-between items-center sticky top-0 z-50 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg"><Truck className="w-6 h-6" /></div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Logistics Hub</h1>
            <p className="text-xs text-slate-400 font-medium tracking-wider uppercase">{user.role}</p>
          </div>
        </div>
        <button onClick={onLogout} className="flex items-center gap-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 px-4 py-2 rounded-xl border border-slate-700 transition">
          <LogOut className="w-4 h-4" /> <span className="text-sm font-bold">Вийти</span>
        </button>
      </header>

      <div className="bg-white border-b border-slate-200 sticky top-[72px] z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8">
            <button onClick={() => setActiveTab('requests')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${activeTab === 'requests' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}><Zap className="w-4 h-4"/> Заявки</button>
            <button onClick={() => setActiveTab('routes')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${activeTab === 'routes' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}><Navigation className="w-4 h-4"/> Маршрути</button>
            <button onClick={() => setActiveTab('infra')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${activeTab === 'infra' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}><Building2 className="w-4 h-4"/> Інфраструктура</button>
          </nav>
        </div>
      </div>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-8 mt-4">
        {loading ? <div className="text-center p-20 text-blue-500"><Clock className="w-10 h-10 animate-spin mx-auto mb-4" />Синхронізація з сервером...</div> : (
          <>
            {/* ВКЛАДКА 1: ЗАЯВКИ */}
            {activeTab === 'requests' && (
              <div className="space-y-6 animate-fade-in">
                {user.role !== 'WAREHOUSE_MANAGER' && (
                  <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="bg-blue-50 border-b border-slate-100 px-6 py-4"><h2 className="font-bold text-slate-800">Створити Заявку</h2></div>
                    <form onSubmit={handleCreateRequest} className="p-6 flex flex-wrap gap-5 items-end">
                      <div className="flex-1 min-w-[150px]"><label className="block text-xs font-bold text-slate-500 mb-2">Об'єкт</label><select className="w-full border p-3 rounded-xl" value={newReq.point || ''} onChange={e => setNewReq({...newReq, point: parseInt(e.target.value)})}>{data.points.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
                      <div className="flex-1 min-w-[150px]"><label className="block text-xs font-bold text-slate-500 mb-2">Ресурс</label><select className="w-full border p-3 rounded-xl" value={newReq.resource_type} onChange={e => setNewReq({...newReq, resource_type: e.target.value})}><option value="FUEL">Паливо</option><option value="GOODS">Товари</option><option value="SUPPLIES">Матеріали</option></select></div>
                      <div className="flex-1 min-w-[100px]"><label className="block text-xs font-bold text-slate-500 mb-2">Кількість</label><input type="number" min="1" className="w-full border p-3 rounded-xl" value={newReq.quantity_requested} onChange={e => setNewReq({...newReq, quantity_requested: parseFloat(e.target.value)})} /></div>
                      <div className="flex-1 min-w-[150px]"><label className="block text-xs font-bold text-slate-500 mb-2">Пріоритет</label><select className="w-full border p-3 rounded-xl" value={newReq.priority} onChange={e => setNewReq({...newReq, priority: parseInt(e.target.value)})}><option value={1}>Нормальний</option><option value={2}>Підвищений</option><option value={3}>Критичний</option></select></div>
                      <div className={`flex items-center gap-3 px-5 py-3 rounded-xl border cursor-pointer transition ${newReq.is_urgent ? 'bg-red-50 border-red-200 text-red-700' : 'bg-slate-50 hover:bg-slate-100'}`} onClick={() => setNewReq({...newReq, is_urgent: !newReq.is_urgent})}><span className="font-bold">ТЕРМІНОВО</span></div>
                      <button type="submit" className="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-blue-700 transition shadow-md">Створити</button>
                    </form>
                  </section>
                )}

                <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-x-auto">
                  <table className="min-w-full text-left">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b">
                      <tr><th className="p-4">Точка</th><th className="p-4">Ресурс</th><th className="p-4">Запрошено / Виділено</th><th className="p-4">Статус</th><th className="p-4">Дії</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.requests.map(req => (
                        <tr key={req.id} className="hover:bg-slate-50/50 transition">
                          <td className="p-4 font-bold text-sm">{req.point} <span className="text-xs text-slate-400 block">#{req.id}</span></td>
                          <td className="p-4 flex items-center gap-2">{getResourceIcon(req.resource_type)} {req.resource_type}</td>
                          <td className="p-4"><span className="text-slate-500">{req.quantity_requested} од.</span> <ArrowRight className="inline w-4 h-4 mx-2 text-slate-300"/> <span className="font-black text-blue-600">{req.quantity_allocated} од.</span></td>
                          <td className="p-4"><span className={`px-3 py-1 rounded-full text-xs font-bold ${req.status === 'ALLOCATED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'}`}>{req.status_display}</span></td>
                          <td className="p-4">
                            {(req.status === 'PENDING' || req.status === 'PARTIAL') && user.role !== 'WAREHOUSE_MANAGER' && (
                              <button onClick={() => handleDeleteRequest(req.id)} className="p-2 bg-red-50 text-red-500 rounded-lg hover:bg-red-500 hover:text-white transition" title="Скасувати">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              </div>
            )}

            {/* ВКЛАДКА 2: МАРШРУТИ */}
            {activeTab === 'routes' && (
              <section className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-x-auto animate-fade-in">
                <table className="min-w-full text-left">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500 border-b">
                    <tr><th className="p-4">Тип</th><th className="p-4">Ресурс</th><th className="p-4">МАРШРУТ (Звідки <ArrowRight className="inline w-3 h-3"/> Куди)</th><th className="p-4">Примітка</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.transactions.map(trx => (
                      <tr key={trx.id} className="hover:bg-slate-50/50 transition">
                        <td className="p-4"><p className={`text-xs font-bold ${trx.transaction_type === 'ALLOCATION' ? 'text-emerald-600' : trx.transaction_type === 'SHORTAGE' ? 'text-red-500' : 'text-amber-500'}`}>{trx.transaction_type_display}</p></td>
                        <td className="p-4 font-black text-slate-800">{trx.quantity} од.<br/><span className="text-xs text-slate-500 font-normal">{trx.resource_type_display}</span></td>
                        <td className="p-4">
                          <div className="flex items-center gap-3 bg-slate-50 p-2 rounded-xl border border-slate-100 w-max">
                            <span className="font-medium text-sm text-slate-600 flex items-center gap-1"><Building2 className="w-3 h-3"/> {trx.from_location || 'Система'}</span>
                            <ArrowRight className="w-4 h-4 text-blue-500" />
                            <span className="font-bold text-sm text-slate-800 flex items-center gap-1"><MapPin className="w-3 h-3 text-red-500"/> {trx.to_location || '-'}</span>
                          </div>
                        </td>
                        <td className="p-4 text-xs text-slate-500">{trx.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            )}

            {/* ВКЛАДКА 3: ІНФРАСТРУКТУРА (НОВИЙ ДИЗАЙН З HOVER) */}
            {activeTab === 'infra' && (
              <div className="flex flex-col lg:flex-row gap-6 items-start animate-fade-in">
                
                {/* ЛІВА ЧАСТИНА: Списки (Займає 1/3 екрану) */}
                <div className="w-full lg:w-1/3 space-y-6">
                  <section className="bg-white rounded-3xl shadow-sm border border-slate-100 p-5">
                    <h2 className="text-lg font-bold text-slate-800 mb-4 border-b pb-2 flex items-center gap-2"><Building2 className="w-5 h-5 text-blue-600"/> Склади</h2>
                    {/* Список зі скролом, якщо складів багато */}
                    <div className="space-y-3 max-h-[40vh] overflow-y-auto pr-2">
                      {data.warehouses.map(wh => (
                        <div 
                          key={wh.id} 
                          onMouseEnter={() => handleHoverItem('Склад', wh)} 
                          className={`p-4 border rounded-2xl cursor-pointer transition-all ${hoveredItem?.id === wh.id && hoveredItem?.type === 'Склад' ? 'bg-blue-50 border-blue-300 shadow-md transform scale-[1.02]' : 'bg-slate-50 border-slate-100 hover:bg-slate-100'}`}
                        >
                          <h3 className="font-bold text-slate-800">{wh.name}</h3>
                          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><MapPin className="w-3 h-3"/> {wh.city}</p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="bg-white rounded-3xl shadow-sm border border-slate-100 p-5">
                    <h2 className="text-lg font-bold text-slate-800 mb-4 border-b pb-2 flex items-center gap-2"><Factory className="w-5 h-5 text-amber-600"/> Постачальники</h2>
                    <div className="space-y-3 max-h-[30vh] overflow-y-auto pr-2">
                      {data.suppliers.map(sup => (
                        <div 
                          key={sup.id} 
                          onMouseEnter={() => handleHoverItem('Постачальник', sup)} 
                          className={`p-4 border rounded-2xl cursor-pointer transition-all ${hoveredItem?.id === sup.id && hoveredItem?.type === 'Постачальник' ? 'bg-amber-50 border-amber-300 shadow-md transform scale-[1.02]' : 'bg-slate-50 border-slate-100 hover:bg-slate-100'}`}
                        >
                          <h3 className="font-bold text-slate-800">{sup.name}</h3>
                          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1"><MapPin className="w-3 h-3"/> {sup.city}</p>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>

                {/* ПРАВА ЧАСТИНА: Детальна інформація (Займає 2/3 екрану і "прилипає" при скролі) */}
                <div className="w-full lg:w-2/3 sticky top-[150px]">
                  {hoveredItem ? (
                    <div className="bg-white rounded-3xl shadow-xl border border-slate-100 p-8 min-h-[500px] transition-all relative overflow-hidden">
                        
                        {/* Декоративний задній фон */}
                        <div className={`absolute -right-20 -top-20 w-64 h-64 rounded-full mix-blend-multiply filter blur-3xl opacity-10 ${hoveredItem.type === 'Склад' ? 'bg-blue-500' : 'bg-amber-500'}`}></div>
                        
                        {hoveredItem.loading ? (
                            <div className="flex flex-col items-center justify-center h-full pt-40 text-blue-500">
                                <Clock className="w-10 h-10 animate-spin mb-4" />
                                <p className="font-bold">Миттєве завантаження деталей...</p>
                            </div>
                        ) : (
                            <div className="relative z-10 animate-fade-in">
                                <div className="flex items-center gap-4 mb-6 border-b pb-6">
                                    <div className={`p-4 rounded-2xl ${hoveredItem.type === 'Склад' ? 'bg-blue-100 text-blue-600' : 'bg-amber-100 text-amber-600'}`}>
                                        {hoveredItem.type === 'Склад' ? <Building2 className="w-8 h-8" /> : <Factory className="w-8 h-8" />}
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-extrabold text-slate-800">{hoveredItem.basic.name}</h2>
                                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold mt-2 ${hoveredItem.type === 'Склад' ? 'bg-blue-50 text-blue-600 border border-blue-200' : 'bg-amber-50 text-amber-600 border border-amber-200'}`}>
                                            {hoveredItem.type}
                                        </span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-6 mb-8">
                                    <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Розташування</p>
                                        <p className="font-medium flex items-center gap-2"><MapPin className="w-4 h-4 text-red-500"/> {hoveredItem.detailed?.city || hoveredItem.basic.city}</p>
                                    </div>
                                    <div className="bg-slate-50 p-4 rounded-2xl border border-slate-100">
                                        <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Координати (GPS)</p>
                                        <p className="font-mono text-sm text-slate-700">{hoveredItem.detailed?.latitude || hoveredItem.basic.latitude}, {hoveredItem.detailed?.longitude || hoveredItem.basic.longitude}</p>
                                    </div>
                                </div>

                                {/* Виводимо запаси, якщо це склад */}
                                {hoveredItem.type === 'Склад' && hoveredItem.detailed?.stocks && (
                                    <div className="animate-fade-in">
                                        <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2"><Archive className="w-5 h-5 text-emerald-500"/> Наявні ресурси в реальному часі</h3>
                                        {hoveredItem.detailed.stocks.length === 0 ? (
                                            <p className="text-slate-500 italic p-4 bg-slate-50 rounded-xl">Склад наразі порожній</p>
                                        ) : (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {hoveredItem.detailed.stocks.map(stock => (
                                                    <div key={stock.id} className="bg-white border border-slate-200 p-4 rounded-2xl shadow-sm hover:shadow-md transition">
                                                        <div className="flex justify-between items-center mb-2">
                                                            <span className="font-bold text-slate-700">{stock.resource_type_display}</span>
                                                            <span className="text-xs font-bold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-lg">Вільних: {stock.available_quantity}</span>
                                                        </div>
                                                        <div className="w-full bg-slate-100 rounded-full h-2.5 mb-2 overflow-hidden">
                                                            <div className="bg-blue-500 h-2.5 rounded-full transition-all duration-1000" style={{ width: `${(stock.available_quantity / stock.actual_quantity) * 100}%` }}></div>
                                                        </div>
                                                        <p className="text-xs text-slate-500 text-right">Загальний об'єм: <span className="font-bold">{stock.actual_quantity} од.</span></p>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Інформація про прив'язаного постачальника */}
                                {hoveredItem.type === 'Склад' && hoveredItem.detailed?.supplier && (
                                    <div className="mt-8 bg-gradient-to-r from-amber-50 to-white p-5 rounded-2xl border border-amber-100 animate-fade-in">
                                        <h3 className="text-sm font-bold text-amber-800 mb-2 flex items-center gap-2"><Factory className="w-4 h-4"/> Прив'язаний постачальник</h3>
                                        <p className="font-medium text-slate-800">{hoveredItem.detailed.supplier.name} <span className="text-slate-500 text-sm font-normal">({hoveredItem.detailed.supplier.city})</span></p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                  ) : (
                    // СТАН "ПУСТО" - Коли користувач ще нікуди не навів
                    <div className="bg-slate-50 border-2 border-dashed border-slate-200 rounded-3xl h-[500px] flex flex-col items-center justify-center text-slate-400 transition-all hover:border-blue-300 hover:bg-blue-50/50">
                        <Info className="w-16 h-16 mb-4 text-slate-300" />
                        <h3 className="text-xl font-bold text-slate-500 mb-2">Детальна інформація</h3>
                        <p className="max-w-xs text-center text-sm">Просто наведіть курсор на будь-який склад або постачальника зі списку зліва, щоб миттєво побачити статистику тут.</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}