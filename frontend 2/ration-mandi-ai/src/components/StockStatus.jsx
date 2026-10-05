import React from 'react';
import StatusBadge from './StatusBadge';

const itemLabels = {
  rice: 'Rice',
  wheat: 'Wheat',
  dal: 'Dal',
  sugar: 'Sugar',
};

export default function StockStatus({ stock, layout = 'grid' }) {
  if (!stock) return null;

  const items = Object.entries(stock);

  if (layout === 'list') {
    return (
      <div className="space-y-2">
        {items.map(([key, status]) => (
          <div key={key} className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">{itemLabels[key] || key}</span>
            <StatusBadge status={status} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(([key, status]) => (
        <div
          key={key}
          className="flex flex-col items-start gap-1 rounded-lg bg-slate-50 p-2.5 border border-slate-100"
        >
          <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">
            {itemLabels[key] || key}
          </span>
          <StatusBadge status={status} size="sm" />
        </div>
      ))}
    </div>
  );
}
