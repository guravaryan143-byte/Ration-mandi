import React, { useEffect, useState } from 'react';
import { Search, Filter } from 'lucide-react';
import ShopCard from '../components/ShopCard';
import LiveIndicator from '../components/LiveIndicator';
import { getShops } from '../services/api';
import { areas } from '../data/mockData';

export default function Shops() {
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [area, setArea] = useState('All Areas');
  const [maxDistance, setMaxDistance] = useState(10);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    getShops({ area, maxDistance }).then((res) => {
      if (res.success) {
        let data = res.data;
        if (search.trim()) {
          const q = search.toLowerCase();
          data = data.filter(
            (s) =>
              s.name.toLowerCase().includes(q) ||
              s.area.toLowerCase().includes(q) ||
              String(s.shopId).includes(q)
          );
        }
        setShops(data);
      }
      setLoading(false);
    });
  }, [area, maxDistance, search]);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Nearby Ration Shops</h1>
        <LiveIndicator />
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="search"
          placeholder="Search by shop number or area…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-3 py-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={area}
            onChange={(e) => setArea(e.target.value)}
            className="text-sm bg-transparent focus:outline-none text-slate-700"
          >
            {areas.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-3 py-2">
          <select
            value={maxDistance}
            onChange={(e) => setMaxDistance(Number(e.target.value))}
            className="text-sm bg-transparent focus:outline-none text-slate-700"
          >
            <option value={2}>Within 2 km</option>
            <option value={5}>Within 5 km</option>
            <option value={10}>Within 10 km</option>
          </select>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 bg-slate-100 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : shops.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <p className="font-medium">No shops found</p>
          <p className="text-sm mt-1">Try changing filters or search term.</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-slate-400">
            {shops.length} shop{shops.length !== 1 ? 's' : ''} found · Demo Data
          </p>
          {shops.map((shop) => (
            <ShopCard key={shop.shopId} shop={shop} />
          ))}
        </div>
      )}
    </div>
  );
}
