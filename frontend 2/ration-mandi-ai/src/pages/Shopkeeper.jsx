import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Store,
  CheckCircle2,
  BarChart3,
  LogIn,
} from 'lucide-react';
import { getShops, updateShopStatus } from '../services/api';

const STOCK_OPTIONS = [
  { value: 'available', label: 'Available', color: 'bg-green-100 text-green-800 border-green-300' },
  { value: 'low', label: 'Low', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  { value: 'out_of_stock', label: 'Out of Stock', color: 'bg-red-100 text-red-800 border-red-300' },
];

const QUEUE_LEVELS = [
  { value: 'low', label: '🟢 Low', color: 'border-green-400 bg-green-50' },
  { value: 'medium', label: '🟡 Medium', color: 'border-yellow-400 bg-yellow-50' },
  { value: 'high', label: '🔴 High', color: 'border-red-400 bg-red-50' },
];

export default function Shopkeeper() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [shops, setShops] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [stock, setStock] = useState({ rice: 'available', wheat: 'available', dal: 'available', sugar: 'available' });
  const [queue, setQueue] = useState(10);
  const [queueLevel, setQueueLevel] = useState('low');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [shopIdInput, setShopIdInput] = useState('102');

  useEffect(() => {
    if (loggedIn) {
      getShops().then((res) => {
        if (res.success) {
          setShops(res.data);
          const first = res.data[0];
          if (first) {
            setSelectedId(first.shopId);
            setStock({ ...first.stock });
            setQueue(first.queue);
            setQueueLevel(first.queueLevel);
          }
        }
      });
    }
  }, [loggedIn]);

  const handleSelectShop = (id) => {
    const shop = shops.find((s) => s.shopId === Number(id));
    if (!shop) return;
    setSelectedId(shop.shopId);
    setStock({ ...shop.stock });
    setQueue(shop.queue);
    setQueueLevel(shop.queueLevel);
    setMessage('');
  };

  const handleLogin = (e) => {
    e.preventDefault();
    // Demo login — accept any shop id that exists
    const id = Number(shopIdInput);
    setLoggedIn(true);
    setSelectedId(id);
  };

  const handleUpdate = async () => {
    setSaving(true);
    setMessage('');
    const res = await updateShopStatus({
      shopId: selectedId,
      stock,
      queue: Number(queue),
      queueLevel,
    });
    setSaving(false);
    if (res.success) {
      setMessage(res.message || 'Status updated successfully.');
      // Refresh list
      const list = await getShops();
      if (list.success) setShops(list.data);
    } else {
      setMessage(res.error || 'Update failed.');
    }
  };

  // ── Login screen ──────────────────────────────────────────
  if (!loggedIn) {
    return (
      <div className="max-w-md mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl border border-slate-200 card-shadow-lg p-6 space-y-5">
          <div className="text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-3">
              <Store className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Shopkeeper Login</h1>
            <p className="text-sm text-slate-500 mt-1">
              Update live stock & queue for your ration shop
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Shop ID
              </label>
              <input
                type="text"
                value={shopIdInput}
                onChange={(e) => setShopIdInput(e.target.value)}
                placeholder="e.g. 102"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <p className="text-xs text-slate-400 mt-1">
                Demo: try 102, 87, 215, 54 or 301
              </p>
            </div>
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3.5 rounded-xl transition-colors"
            >
              <LogIn className="w-4 h-4" />
              Login
            </button>
          </form>

          <p className="text-xs text-center text-slate-400">
            No real authentication in demo mode
          </p>
        </div>
      </div>
    );
  }

  // ── Dashboard ─────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Shopkeeper Dashboard</h1>
          <p className="text-sm text-slate-500">Update live status for your shop</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/analytics"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-gov-blue bg-blue-50 px-3 py-1.5 rounded-lg"
          >
            <BarChart3 className="w-4 h-4" />
            Analytics
          </Link>
          <button
            onClick={() => setLoggedIn(false)}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Shop selector */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">
          Select Shop
        </label>
        <select
          value={selectedId || ''}
          onChange={(e) => handleSelectShop(e.target.value)}
          className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {shops.map((s) => (
            <option key={s.shopId} value={s.shopId}>
              {s.name} ({s.area})
            </option>
          ))}
        </select>
      </div>

      {/* Stock update */}
      <section className="bg-white rounded-2xl border border-slate-200 card-shadow p-5 space-y-4">
        <h2 className="font-semibold text-slate-800">Stock Status</h2>
        {['rice', 'wheat', 'dal', 'sugar'].map((item) => (
          <div key={item}>
            <p className="text-sm font-medium text-slate-700 capitalize mb-1.5">
              {item}
            </p>
            <div className="flex flex-wrap gap-2">
              {STOCK_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setStock((prev) => ({ ...prev, [item]: opt.value }))}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all ${
                    stock[item] === opt.value
                      ? opt.color + ' ring-2 ring-offset-1 ring-slate-300'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* Queue update */}
      <section className="bg-white rounded-2xl border border-slate-200 card-shadow p-5 space-y-4">
        <h2 className="font-semibold text-slate-800">Current Queue</h2>

        <div>
          <p className="text-sm text-slate-600 mb-2">Queue level</p>
          <div className="flex flex-wrap gap-2">
            {QUEUE_LEVELS.map((lvl) => (
              <button
                key={lvl.value}
                type="button"
                onClick={() => setQueueLevel(lvl.value)}
                className={`px-4 py-2.5 rounded-xl text-sm font-medium border-2 transition-all ${
                  queueLevel === lvl.value
                    ? lvl.color + ' ring-2 ring-offset-1 ring-slate-300'
                    : 'bg-white border-slate-200 text-slate-600'
                }`}
              >
                {lvl.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-slate-600 mb-1">
            Approximate number of people
          </label>
          <input
            type="number"
            min={0}
            max={100}
            value={queue}
            onChange={(e) => setQueue(e.target.value)}
            className="w-full sm:w-40 px-4 py-3 rounded-xl border border-slate-200 text-lg font-semibold focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <span className="ml-2 text-sm text-slate-500">people</span>
        </div>
      </section>

      {/* Success message */}
      {message && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-800 rounded-xl px-4 py-3 text-sm font-medium">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          {message}
        </div>
      )}

      {/* Update button */}
      <button
        onClick={handleUpdate}
        disabled={saving}
        className="w-full bg-green-600 hover:bg-green-700 active:bg-green-800 disabled:opacity-60 text-white font-semibold text-lg py-4 rounded-2xl transition-colors shadow-md"
      >
        {saving ? 'Updating…' : 'Update Live Status'}
      </button>

      <p className="text-xs text-center text-slate-400">
        Changes appear instantly on the Citizen Dashboard (Demo Mode)
      </p>
    </div>
  );
}
