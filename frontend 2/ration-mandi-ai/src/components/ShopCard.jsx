import React from 'react';
import { MapPin, Clock, ChevronRight } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { Link } from 'react-router-dom';

const itemLabels = { rice: 'Rice', wheat: 'Wheat', dal: 'Dal', sugar: 'Sugar' };

export default function ShopCard({ shop }) {
  const stockEntries = Object.entries(shop.stock || {});

  return (
    <article className="bg-white rounded-2xl border border-slate-200 card-shadow p-4 active:scale-[0.99] transition-transform">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <h3 className="font-semibold text-slate-900 text-base leading-tight">
            {shop.name}
          </h3>
          <div className="flex items-center gap-1 mt-1 text-sm text-slate-500">
            <MapPin className="w-3.5 h-3.5 text-saffron" />
            <span>{shop.distance} away</span>
            <span className="text-slate-300">·</span>
            <span>{shop.area}</span>
          </div>
        </div>
        {!shop.isOpen && (
          <span className="shrink-0 text-xs font-medium bg-slate-100 text-slate-600 px-2 py-1 rounded-full">
            Closed
          </span>
        )}
      </div>

      {/* Stock summary */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {stockEntries.map(([key, status]) => (
          <span
            key={key}
            className="inline-flex items-center gap-1 text-xs bg-slate-50 border border-slate-100 rounded-full px-2 py-0.5"
          >
            <span>
              {status === 'available' ? '🟢' : status === 'low' ? '🟡' : '🔴'}
            </span>
            {itemLabels[key]}
          </span>
        ))}
      </div>

      {/* Queue row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-600">Queue:</span>
          <StatusBadge status={shop.queueLevel} type="queue" size="sm" />
          <span className="text-sm font-medium text-slate-800">
            {shop.queue} people
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Clock className="w-3 h-3" />
          <span>Updated {shop.lastUpdated}</span>
        </div>
        <Link
          to={`/shop/${shop.shopId}`}
          className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:text-primary-dark"
        >
          View Details
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </article>
  );
}
