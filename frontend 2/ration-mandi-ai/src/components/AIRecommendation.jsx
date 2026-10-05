import React from 'react';
import { Star, Navigation } from 'lucide-react';

export default function AIRecommendation({ prediction, shopName }) {
  if (!prediction) return null;

  return (
    <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-5 card-shadow-lg">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
          <Star className="w-4 h-4 text-white fill-white" />
        </div>
        <h3 className="font-bold text-green-900 text-lg">Best Time to Visit</h3>
      </div>

      <p className="text-2xl font-bold text-slate-900 mb-3">
        {prediction.recommendedTime}
      </p>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-white/70 rounded-xl p-3 border border-green-100">
          <p className="text-xs text-slate-500 mb-0.5">Queue</p>
          <p className="font-semibold text-green-700 capitalize">
            🟢 {prediction.recommendedQueue}
          </p>
        </div>
        <div className="bg-white/70 rounded-xl p-3 border border-green-100">
          <p className="text-xs text-slate-500 mb-0.5">Stock</p>
          <p className="font-semibold text-green-700">🟢 Available</p>
        </div>
      </div>

      <p className="text-sm text-slate-600 mb-4">
        Estimated waiting time:{' '}
        <span className="font-semibold text-slate-800">
          {prediction.recommendedWait}
        </span>
      </p>

      <a
        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          shopName || 'Government Ration Shop'
        )}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center gap-2 w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
      >
        <Navigation className="w-4 h-4" />
        Get Directions
      </a>
    </div>
  );
}
