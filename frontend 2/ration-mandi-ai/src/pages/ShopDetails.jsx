import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Clock,
  Navigation,
  RefreshCw,
} from 'lucide-react';
import StockStatus from '../components/StockStatus';
import QueueIndicator from '../components/QueueIndicator';
import PredictionCard from '../components/PredictionCard';
import AIRecommendation from '../components/AIRecommendation';
import LiveIndicator from '../components/LiveIndicator';
import {
  getShopById,
  simulateLiveChange,
} from '../services/api';

export default function ShopDetails() {
  const { shopId } = useParams();
  const [shop, setShop] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  const load = () => {
    setLoading(true);
    getShopById(shopId).then((res) => {
      if (res.success) setShop(res.data);
      setLoading(false);
    });
  };

  useEffect(() => {
    load();
  }, [shopId]);

  const handleSimulate = async () => {
    setSimulating(true);
    const res = await simulateLiveChange(shopId);
    if (res.success) setShop(res.data);
    setSimulating(false);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        <div className="h-8 w-32 bg-slate-100 rounded animate-pulse" />
        <div className="h-48 bg-slate-100 rounded-2xl animate-pulse" />
        <div className="h-64 bg-slate-100 rounded-2xl animate-pulse" />
      </div>
    );
  }

  if (!shop) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-center">
        <p className="text-slate-600 font-medium">Shop not found</p>
        <Link to="/shops" className="text-green-700 text-sm mt-2 inline-block">
          ← Back to shops
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
      {/* Back + header */}
      <div>
        <Link
          to="/shops"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-3"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to shops
        </Link>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">{shop.name}</h1>
            <div className="flex items-center gap-1 mt-1 text-sm text-slate-500">
              <MapPin className="w-3.5 h-3.5 text-saffron" />
              {shop.distance} · {shop.area}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">{shop.address}</p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <LiveIndicator />
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                shop.isOpen
                  ? 'bg-green-100 text-green-700'
                  : 'bg-slate-100 text-slate-600'
              }`}
            >
              {shop.isOpen ? 'Open' : 'Closed'}
            </span>
          </div>
        </div>
      </div>

      {/* Live Status section */}
      <section className="bg-white rounded-2xl border border-slate-200 card-shadow p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-800">Live Shop Status</h2>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Clock className="w-3 h-3" />
            {shop.lastUpdated}
          </div>
        </div>

        {/* Queue big number */}
        <div className="bg-slate-50 rounded-xl p-4 mb-4 text-center">
          <p className="text-xs text-slate-500 mb-1 uppercase tracking-wide">
            Current Queue
          </p>
          <QueueIndicator
            queue={shop.queue}
            queueLevel={shop.queueLevel}
            size="lg"
            showEstimate
          />
        </div>

        {/* Stock */}
        <div>
          <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide font-medium">
            Stock Status
          </p>
          <StockStatus stock={shop.stock} layout="grid" />
        </div>

        {/* Opening hours */}
        <p className="text-xs text-slate-400 mt-4">
          Hours: {shop.openingHours}
        </p>
      </section>

      {/* AI Recommendation - prominent */}
      <AIRecommendation prediction={shop.aiPrediction} shopName={shop.name} />

      {/* AI Predictions detail */}
      <PredictionCard prediction={shop.aiPrediction} />

      {/* Demo controls */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <p className="text-xs font-medium text-amber-800 mb-2">Demo Mode</p>
        <button
          onClick={handleSimulate}
          disabled={simulating}
          className="inline-flex items-center gap-2 text-sm font-medium bg-amber-100 hover:bg-amber-200 text-amber-900 px-3 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : ''}`} />
          Simulate live change (queue ↑ / stock ↓)
        </button>
      </div>

      {/* Directions */}
      <a
        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          shop.name + ' ' + shop.address
        )}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3.5 rounded-xl transition-colors"
      >
        <Navigation className="w-4 h-4" />
        Get Directions
      </a>
    </div>
  );
}
