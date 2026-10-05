import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bot, ChevronRight } from 'lucide-react';
import PredictionCard from '../components/PredictionCard';
import AIRecommendation from '../components/AIRecommendation';
import { getShops } from '../services/api';

export default function Predictions() {
  const [shops, setShops] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getShops().then((res) => {
      if (res.success) {
        setShops(res.data.filter((s) => s.isOpen));
        if (res.data.length) setSelected(res.data[0]);
      }
      setLoading(false);
    });
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Bot className="w-5 h-5 text-gov-blue" />
          AI Predictions
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Select a shop to see queue & stock forecasts and best visit time.
        </p>
      </div>

      {/* Shop selector */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
        {loading
          ? [1, 2, 3].map((i) => (
              <div
                key={i}
                className="shrink-0 h-10 w-32 bg-slate-100 rounded-full animate-pulse"
              />
            ))
          : shops.map((s) => (
              <button
                key={s.shopId}
                onClick={() => setSelected(s)}
                className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                  selected?.shopId === s.shopId
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-green-300'
                }`}
              >
                #{s.shopId}
              </button>
            ))}
      </div>

      {selected && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600 font-medium">{selected.name}</p>
            <Link
              to={`/shop/${selected.shopId}`}
              className="text-sm text-green-700 font-medium inline-flex items-center gap-0.5"
            >
              Details <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <AIRecommendation
            prediction={selected.aiPrediction}
            shopName={selected.name}
          />
          <PredictionCard prediction={selected.aiPrediction} />
        </>
      )}

      <p className="text-xs text-slate-400 italic text-center">
        Predictions are estimates based on historical and current shop data.
        Demo Data — not connected to live ML backend yet.
      </p>
    </div>
  );
}
