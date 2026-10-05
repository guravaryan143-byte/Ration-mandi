import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Search, Bot, Clock, Package } from 'lucide-react';
import ShopCard from '../components/ShopCard';
import LiveIndicator from '../components/LiveIndicator';
import { getShops } from '../services/api';

export default function Home() {
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getShops({ maxDistance: 5 }).then((res) => {
      if (res.success) setShops(res.data.slice(0, 3));
      setLoading(false);
    });
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Hero */}
      <section className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 bg-green-50 text-green-800 text-xs font-medium px-3 py-1 rounded-full border border-green-100">
          <LiveIndicator />
          <span>Demo Data</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-tight">
          Know before you go.
        </h1>
        <p className="text-slate-600 text-sm sm:text-base max-w-md mx-auto">
          Check live stock, queue length and AI-recommended visit times for
          government ration shops near you.
        </p>
      </section>

      {/* Primary CTA */}
      <Link
        to="/shops"
        className="flex items-center justify-center gap-3 w-full bg-green-600 hover:bg-green-700 active:bg-green-800 text-white font-semibold text-lg py-4 px-6 rounded-2xl shadow-md transition-colors"
      >
        <MapPin className="w-5 h-5" />
        📍 Find Nearby Ration Shops
      </Link>

      {/* Quick info cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-slate-200 p-3 text-center card-shadow">
          <Package className="w-5 h-5 text-green-600 mx-auto mb-1" />
          <p className="text-xs text-slate-500">Live Stock</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 text-center card-shadow">
          <Clock className="w-5 h-5 text-saffron mx-auto mb-1" />
          <p className="text-xs text-slate-500">Queue Status</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 text-center card-shadow">
          <Bot className="w-5 h-5 text-gov-blue mx-auto mb-1" />
          <p className="text-xs text-slate-500">AI Predict</p>
        </div>
      </div>

      {/* Nearby preview */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-800">Nearby Shops</h2>
          <Link to="/shops" className="text-sm text-green-700 font-medium">
            See all
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div
                key={i}
                className="h-36 bg-slate-100 rounded-2xl animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {shops.map((shop) => (
              <ShopCard key={shop.shopId} shop={shop} />
            ))}
          </div>
        )}
      </section>

      {/* How it works */}
      <section className="bg-white rounded-2xl border border-slate-200 p-5 card-shadow">
        <h2 className="font-semibold text-slate-800 mb-3">How it works</h2>
        <ol className="space-y-3 text-sm text-slate-600">
          <li className="flex gap-3">
            <span className="shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">
              1
            </span>
            Select your area or search nearby ration shops.
          </li>
          <li className="flex gap-3">
            <span className="shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">
              2
            </span>
            See live stock availability and current queue length.
          </li>
          <li className="flex gap-3">
            <span className="shrink-0 w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-bold flex items-center justify-center">
              3
            </span>
            Use AI predictions to choose the best time to visit.
          </li>
        </ol>
      </section>
    </div>
  );
}
