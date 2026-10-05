import React from 'react';

const styles = {
  available: 'bg-green-100 text-green-800 border-green-200',
  low: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  out_of_stock: 'bg-red-100 text-red-800 border-red-200',
  low_queue: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-red-100 text-red-800 border-red-200',
};

const labels = {
  available: 'Available',
  low: 'Low Stock',
  out_of_stock: 'Out of Stock',
  low_queue: 'Low',
  medium: 'Medium',
  high: 'High',
};

const dots = {
  available: '🟢',
  low: '🟡',
  out_of_stock: '🔴',
  low_queue: '🟢',
  medium: '🟡',
  high: '🔴',
};

export default function StatusBadge({ status, type = 'stock', size = 'md' }) {
  const key = type === 'queue' && status === 'low' ? 'low_queue' : status;
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${styles[key] || styles.medium} ${sizeClass}`}
    >
      <span aria-hidden="true">{dots[key] || '⚪'}</span>
      {labels[key] || status}
    </span>
  );
}
