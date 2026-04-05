import { useEffect, useState } from 'react';
import { api } from './api';
import { 
  LogOut, Truck, Package, Droplet, Archive, 
  AlertOctagon, CheckCircle2, Clock, Zap, MapPin, BarChart3,
  ArrowRight, History, Building2, Factory, Navigation, Trash2, Info, AlertTriangle, Database
} from 'lucide-react';

export default function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('requests');
  const [data, setData] = useState({ requests: [], points: [], transactions: [], warehouses: [], suppliers: [] });
  const [detailedWarehouses, setDetailedWarehouses] = useState([]); // Для повних даних по складах
  const [loading, setLoading] = useState(true);
  const [newReq, setNewReq] = useState({ point: '', resource_type: 'FUEL', quantity_requested: '', priority: 1, is_urgent: false });

  const isDispatcher = user.role === 'DISPATCHER';
  const isPointManager = user.role === 'DELIVERY_POINT_MANAGER';
  const isWarehouse = user.role === 'WAREHOUSE_MANAGER';

  const fetchData = async () => {
    try {
      const [reqData, ptsData, trxData, whData, supData] = await Promise.all([
        api.getRequests(), api.getPoints(), api.getTransactions(), api.getWarehouses(), api.getSuppliers()
      ]);
      setData({ requests: reqData, points: ptsData, transactions: trxData, warehouses: whData, suppliers: supData });
      if (ptsData.length > 0) setNewReq(prev => ({ ...prev, point: ptsData[0].id }));

      // Дозавантажуємо деталі по кожному складу (щоб мати 100% інформації про залишки)
      if (whData.length > 0) {
        const detailsPromises = whData.map(wh => api.getWarehouse(wh.id).catch(() => wh));
        const detailed = await Promise.all(detailsPromises);
        setDetailedWarehouses(detailed);
      }
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
    if (!window.confirm('Ви впевнені, що хочете скасувати цю заявку?')) return;
    try { await api.deleteRequest(id); fetchData(); } catch (err) { alert('Помилка видалення.'); }
  };

  const getResourceIcon = (type) => {
    if (type === 'FUEL') return <Droplet className="w-5 h-5 text-blue-500" />;
    if (type === 'GOODS') return <Package className="w-5 h-5 text-amber-500" />;
    return <Archive className="w-5 h-5 text-slate-500" />;
  };

  const shortages = data.transactions.filter(t => t.transaction_type === 'SHORTAGE');
  const criticalRequests = data.requests.filter(r => r.status === 'PARTIAL' || r.is_urgent);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans pb-10 overflow-x-hidden">
      {/* ХЕДЕР */}
      <header className="bg-slate-900 text-white px-4 md:px-6 py-3 md:py-4 flex flex-wrap justify-between items-center sticky top-0 z-50 shadow-lg gap-2">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg"><Truck className="w-5 h-5 md:w-6 md:h-6" /></div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight leading-tight">Logistics Hub</h1>
            <p className="text-[10px] md:text-xs text-blue-300 font-medium tracking-wider uppercase">
              {isDispatcher ? 'Диспетчерський центр' : isPointManager ? 'Управління точкою' : 'Складський термінал'}
            </p>
          </div>
        </div>
        <button onClick={onLogout} className="flex items-center gap-2 bg-slate-800 hover:bg-red-500/20 hover:text-red-400 px-3 py-2 rounded-xl border border-slate-700 transition">
          <LogOut className="w-4 h-4" /> <span className="text-sm font-bold hidden md:inline">Вийти</span>
        </button>
      </header>

      {/* НАВІГАЦІЯ */}
      <div className="bg-white border-b border-slate-200 sticky top-[60px] md:top-[72px] z-40 shadow-sm overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-6 md:space-x-8 min-w-max">
            {!isWarehouse && (
              <button onClick={() => setActiveTab('requests')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'requests' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                <Zap className="w-4 h-4"/> {isDispatcher ? 'Глобальні заявки' : 'Мої замовлення'}
              </button>
            )}
            <button onClick={() => setActiveTab('routes')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'routes' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
              <Navigation className="w-4 h-4"/> {isWarehouse ? 'Журнал видачі' : 'Логістика / Маршрути'}
            </button>
            {!isPointManager && (
              <button onClick={() => setActiveTab('infra')} className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === 'infra' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                <Database className="w-4 h-4"/> Інфраструктура (Усі дані)
              </button>
            )}
          </nav>
        </div>
      </div>

      <main className="p-4 md:p-8 max-w-7xl mx-auto space-y-6 md:space-y-8 mt-2 md:mt-4">
        {loading ? <div className="text-center p-20 text-blue-500"><Clock className="w-10 h-10 animate-spin mx-auto mb-4" />Оновлення...</div> : (
          <>
        

            {/* ВКЛАДКА 1: ЗАЯВКИ */}
            {activeTab === 'requests' && (
              <div className="space-y-6 animate-fade-in">
                {user.role !== 'WAREHOUSE_MANAGER' && (
                  <section className="bg-white rounded-2xl md:rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="bg-blue-50/80 border-b border-blue-100 px-4 md:px-6 py-3 md:py-4 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-blue-600" />
                        <h2 className="text-base md:text-lg font-bold text-slate-800">Створити Заявку</h2>
                      </div>
                    </div>
                    <form onSubmit={handleCreateRequest} className="p-4 md:p-6 grid grid-cols-1 md:flex md:flex-wrap gap-4 md:gap-5 items-end">
                      <div className="flex-1 min-w-full md:min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5">Об'єкт (Точка)</label>
                        <select className="w-full border border-slate-200 p-3 rounded-xl bg-slate-50" value={newReq.point || ''} onChange={e => setNewReq({...newReq, point: parseInt(e.target.value)})}>
                          {data.points.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                        </select>
                      </div>
                      <div className="flex-1 min-w-full md:min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5">Ресурс</label>
                        <select className="w-full border border-slate-200 p-3 rounded-xl bg-slate-50" value={newReq.resource_type} onChange={e => setNewReq({...newReq, resource_type: e.target.value})}>
                          <option value="FUEL">⛽ Паливо</option><option value="GOODS">📦 Товари</option><option value="SUPPLIES">🔧 Матеріали</option>
                        </select>
                      </div>
                      <div className="flex-1 min-w-full md:min-w-[100px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5">Кількість</label>
                        <input type="number" min="1" className="w-full border border-slate-200 p-3 rounded-xl bg-slate-50" placeholder="0" value={newReq.quantity_requested} onChange={e => setNewReq({...newReq, quantity_requested: parseFloat(e.target.value)})} />
                      </div>
                      <div className="flex-1 min-w-full md:min-w-[150px]">
                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5">Пріоритет</label>
                        <select className="w-full border border-slate-200 p-3 rounded-xl bg-slate-50" value={newReq.priority} onChange={e => setNewReq({...newReq, priority: parseInt(e.target.value)})}>
                          <option value={1}>🟢 Нормальний</option><option value={2}>🟡 Підвищений</option><option value={3}>🔴 Критичний</option>
                        </select>
                      </div>
                      <div className="flex-1 min-w-full md:min-w-max flex gap-3">
                        <div className={`flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition ${newReq.is_urgent ? 'bg-red-50 border-red-300 text-red-700 shadow-inner' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'}`} onClick={() => setNewReq({...newReq, is_urgent: !newReq.is_urgent})}>
                          <span className="font-black text-sm uppercase">Терміново</span>
                        </div>
                        <button type="submit" className="flex-[2] md:flex-none bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 transition shadow-md md:w-auto w-full">Створити</button>
                      </div>
                    </form>
                  </section>
                )}

                <section className="bg-transparent md:bg-white md:rounded-3xl md:shadow-sm md:border md:border-slate-100 overflow-hidden">
                  <div className="hidden md:flex px-6 py-4 border-b border-slate-100 bg-slate-50 justify-between items-center"><h2 className="text-lg font-bold text-slate-800">Журнал Заявок</h2></div>
                  
                  {/* Десктоп Таблиця */}
                  <div className="hidden md:block overflow-x-auto">
                    <table className="min-w-full text-left">
                      <thead className="bg-white text-xs uppercase text-slate-400 border-b">
                        <tr><th className="p-4">Об'єкт</th><th className="p-4">Ресурс / Потреба</th><th className="p-4 text-center">Виділено Алгоритмом</th><th className="p-4">Статус</th><th className="p-4"></th></tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50 bg-white">
                        {data.requests.map(req => (
                          <tr key={req.id} className="hover:bg-slate-50 transition">
                            <td className="p-4"><p className="font-bold text-slate-800">{req.point}</p><p className="text-[10px] text-slate-400">ID: {req.id}</p></td>
                            <td className="p-4"><div className="flex items-center gap-2 mb-1">{getResourceIcon(req.resource_type)} <span className="font-medium text-sm">{req.resource_type}</span></div><span className="text-xs text-slate-500">Запит: {req.quantity_requested} од.</span></td>
                            <td className="p-4 text-center"><span className={`text-xl font-black ${req.quantity_allocated === 0 ? 'text-red-500' : req.quantity_allocated < req.quantity_requested ? 'text-amber-500' : 'text-emerald-600'}`}>{req.quantity_allocated}</span></td>
                            <td className="p-4"><div className="flex flex-col gap-1 items-start"><span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase ${req.status === 'ALLOCATED' ? 'bg-emerald-100 text-emerald-700' : req.status === 'PARTIAL' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'}`}>{req.status_display}</span></div></td>
                            <td className="p-4 text-right">{(req.status === 'PENDING' || req.status === 'PARTIAL') && !isWarehouse && (<button onClick={() => handleDeleteRequest(req.id)} className="p-2 text-slate-400 hover:bg-red-50 hover:text-red-500 rounded-lg transition"><Trash2 className="w-4 h-4" /></button>)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Мобільні Картки */}
                  <div className="md:hidden space-y-4">
                    {data.requests.map(req => (
                      <div key={req.id} className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden">
                        <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${req.status === 'ALLOCATED' ? 'bg-emerald-500' : req.status === 'PARTIAL' ? 'bg-amber-500' : 'bg-slate-300'}`}></div>
                        <div className="flex justify-between items-start mb-3 pl-2">
                          <div><p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">#{req.id} • {req.point}</p><div className="flex items-center gap-1.5 font-bold text-slate-800">{getResourceIcon(req.resource_type)} {req.resource_type}</div></div>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${req.status === 'ALLOCATED' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-800'}`}>{req.status_display}</span>
                        </div>
                        <div className="bg-slate-50 rounded-xl p-3 flex justify-between items-center ml-2 border border-slate-100">
                          <div className="text-center"><p className="text-[10px] text-slate-500 font-medium uppercase mb-0.5">Потреба</p><p className="font-bold text-slate-700">{req.quantity_requested}</p></div>
                          <ArrowRight className="w-4 h-4 text-slate-300" />
                          <div className="text-center"><p className="text-[10px] text-slate-500 font-medium uppercase mb-0.5">Виділено</p><p className={`font-black text-lg ${req.quantity_allocated >= req.quantity_requested ? 'text-emerald-600' : 'text-amber-500'}`}>{req.quantity_allocated}</p></div>
                        </div>
                        <div className="mt-3 pl-2 flex justify-between items-center">
                          <div className="flex gap-1">{req.priority === 3 && <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-1 rounded">КРИТИЧНО</span>}{req.is_urgent && <span className="text-[10px] font-bold text-purple-600 bg-purple-50 px-2 py-1 rounded">ТЕРМІНОВО</span>}</div>
                          {(req.status === 'PENDING' || req.status === 'PARTIAL') && !isWarehouse && (<button onClick={() => handleDeleteRequest(req.id)} className="text-red-500 p-1 bg-red-50 rounded"><Trash2 className="w-4 h-4" /></button>)}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {/* ВКЛАДКА 2: МАРШРУТИ */}
            {activeTab === 'routes' && (
              <section className="space-y-4 animate-fade-in">
                {data.transactions.map(trx => {
                  const isShortage = trx.transaction_type === 'SHORTAGE';
                  const isAlloc = trx.transaction_type === 'ALLOCATION';
                  return (
                    <div key={trx.id} className={`bg-white rounded-2xl p-4 md:p-5 border-l-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:shadow-md ${isShortage ? 'border-red-500 bg-red-50/30' : isAlloc ? 'border-emerald-500' : 'border-amber-500'}`}>
                      <div className="flex items-start gap-4 md:w-1/3">
                        <div className={`p-3 rounded-full shrink-0 ${isShortage ? 'bg-red-100 text-red-600' : isAlloc ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'}`}>
                          {isShortage ? <AlertTriangle className="w-5 h-5"/> : isAlloc ? <CheckCircle2 className="w-5 h-5"/> : <History className="w-5 h-5"/>}
                        </div>
                        <div><p className={`text-xs font-bold uppercase tracking-wider mb-1 ${isShortage ? 'text-red-600' : isAlloc ? 'text-emerald-600' : 'text-amber-600'}`}>{trx.transaction_type_display}</p><p className="font-black text-lg text-slate-800 leading-none">{trx.quantity} <span className="text-sm font-medium text-slate-500">{trx.resource_type_display}</span></p></div>
                      </div>
                      <div className="bg-slate-50 rounded-xl p-3 flex-1 flex items-center justify-between border border-slate-100">
                        <div className="flex flex-col"><span className="text-[10px] uppercase text-slate-400 font-bold mb-1">Джерело</span><span className="text-sm font-bold text-slate-700 flex items-center gap-1"><Building2 className="w-3.5 h-3.5 text-blue-500"/> {trx.from_location || 'Загальний пул'}</span></div>
                        <ArrowRight className={`w-5 h-5 mx-2 ${isShortage ? 'text-red-300' : 'text-emerald-400'}`} />
                        <div className="flex flex-col text-right"><span className="text-[10px] uppercase text-slate-400 font-bold mb-1">Призначення</span><span className="text-sm font-bold text-slate-700 flex items-center justify-end gap-1"><MapPin className="w-3.5 h-3.5 text-red-500"/> {trx.to_location || '-'}</span></div>
                      </div>
                      <div className="md:w-1/4 text-right"><p className="text-xs text-slate-500 italic">"{trx.note}"</p></div>
                    </div>
                  );
                })}
              </section>
            )}

            {/* ВКЛАДКА 3: ДЕТАЛЬНА ІНФРАСТРУКТУРА (ВСІ ДАНІ НА ДОЛОНІ) */}
            {activeTab === 'infra' && (
              <div className="space-y-8 animate-fade-in">
                
                {/* 1. СКЛАДИ */}
                <section>
                  <div className="flex items-center gap-2 mb-4 px-2">
                    <Building2 className="w-6 h-6 text-blue-600" />
                    <h2 className="text-xl font-bold text-slate-800">Складські Хаби (Деталі залишків)</h2>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
                    {(detailedWarehouses.length > 0 ? detailedWarehouses : data.warehouses).map(wh => (
                      <div key={wh.id} className="bg-white rounded-3xl p-5 md:p-6 border border-slate-100 shadow-sm flex flex-col relative overflow-hidden">
                        <div className="absolute -right-10 -top-10 w-32 h-32 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-5"></div>
                        
                        <div className="flex justify-between items-start mb-4 relative z-10">
                          <div>
                            <h3 className="font-extrabold text-lg text-slate-800">{wh.name}</h3>
                            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1"><MapPin className="w-3 h-3 text-red-400"/> {wh.city}</p>
                          </div>
                          <span className="bg-blue-50 text-blue-700 text-[10px] font-bold px-2.5 py-1 rounded-full border border-blue-100">ID: {wh.id}</span>
                        </div>

                        <div className="bg-slate-50 p-3.5 rounded-2xl mb-5 text-xs space-y-2.5 border border-slate-100 relative z-10">
                          <p className="flex justify-between items-center"><span className="text-slate-500 font-medium">GPS Координати:</span> <span className="font-mono text-slate-700 bg-white px-2 py-1 rounded border border-slate-100">{wh.latitude}, {wh.longitude}</span></p>
                          <p className="flex justify-between items-center"><span className="text-slate-500 font-medium">Постачальник:</span> <span className="font-bold text-amber-700">{wh.supplier?.name || 'Не закріплено'}</span></p>
                        </div>

                        <div className="flex-1 relative z-10">
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5"><Archive className="w-4 h-4 text-emerald-500"/> Фактичні залишки на складі</h4>
                          {wh.stocks && wh.stocks.length > 0 ? (
                            <div className="space-y-3.5">
                              {wh.stocks.map(stock => {
                                const percentage = (stock.available_quantity / stock.actual_quantity) * 100;
                                return (
                                  <div key={stock.id}>
                                    <div className="flex justify-between text-xs mb-1.5 items-end">
                                      <span className="font-bold text-slate-700">{stock.resource_type_display}</span>
                                      <span className="font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{stock.available_quantity} / <span className="text-slate-400 font-medium">{stock.actual_quantity}</span></span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
                                      <div className={`h-2 rounded-full transition-all duration-1000 ${percentage < 20 ? 'bg-red-500' : percentage < 50 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${percentage}%` }}></div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <div className="bg-slate-50 rounded-xl p-4 text-center border border-dashed border-slate-200">
                              <p className="text-xs text-slate-400 italic">Дані про запаси відсутні</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* 2. ТОЧКИ ДОСТАВКИ (КЛІЄНТИ) */}
                  <section>
                    <div className="flex items-center gap-2 mb-4 px-2">
                      <MapPin className="w-6 h-6 text-red-500" />
                      <h2 className="text-xl font-bold text-slate-800">Точки видачі (Клієнти / АЗС)</h2>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {data.points.map(pt => (
                        <div key={pt.id} className="bg-white rounded-2xl p-4 md:p-5 border border-slate-100 shadow-sm flex flex-col hover:border-red-200 transition">
                          <h3 className="font-bold text-slate-800 text-lg">{pt.name}</h3>
                          <p className="text-xs text-slate-500 flex items-center gap-1 mt-1 mb-4"><MapPin className="w-3 h-3 text-slate-400"/> {pt.city}</p>
                          <div className="mt-auto bg-red-50/50 p-3 rounded-xl border border-red-100">
                            <p className="text-[10px] text-red-800 uppercase font-bold mb-1">Координати для навігації:</p>
                            <p className="font-mono text-sm text-slate-700 bg-white px-2 py-1 rounded shadow-sm inline-block">{pt.latitude}, {pt.longitude}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>

                  {/* 3. ПОСТАЧАЛЬНИКИ */}
                  <section>
                    <div className="flex items-center gap-2 mb-4 px-2">
                      <Factory className="w-6 h-6 text-amber-600" />
                      <h2 className="text-xl font-bold text-slate-800">Постачальники ресурсів</h2>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {data.suppliers.map(sup => (
                        <div key={sup.id} className="bg-white rounded-2xl p-4 md:p-5 border border-slate-100 shadow-sm flex flex-col hover:border-amber-200 transition">
                          <h3 className="font-bold text-slate-800 text-lg">{sup.name}</h3>
                          <p className="text-xs text-slate-500 flex items-center gap-1 mt-1 mb-4"><MapPin className="w-3 h-3 text-slate-400"/> {sup.city}</p>
                          <div className="mt-auto bg-amber-50 p-3 rounded-xl border border-amber-100">
                            <p className="text-[10px] text-amber-800 uppercase font-bold mb-1">Розташування заводу:</p>
                            <p className="font-mono text-sm text-slate-700 bg-white px-2 py-1 rounded shadow-sm inline-block">{sup.latitude}, {sup.longitude}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}