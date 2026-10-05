import React from 'react';
import StatusBadge from './StatusBadge';

export default function QueueIndicator({ queue, queueLevel, size = 'md', showEstimate = false }) {
  const isLarge = size === 'lg';

  return (
    <div className={`flex flex-col ${isLarge ? 'items-center' : 'items-start'} gap-1`}>
      <div className={`flex items-baseline gap-2 ${isLarge ? 'justify-center' : ''}`}>
        <span
          className={`font-bold text-slate-900 ${isLarge ? 'text-4xl' : 'text-xl'}`}
        >
          {queue}
        </span>
        <span className={`text-slate-500 ${isLarge ? 'text-lg' : 'text-sm'}`}>people</span>
      </div>
      <StatusBadge status={queueLevel} type="queue" size={isLarge ? 'md' : 'sm'} />
      {showEstimate && (
        <p className="text-sm text-slate-600 mt-1">
          Est. wait:{' '}
          <span className="font-medium">
            {queueLevel === 'low'
              ? '10–15 min'
              : queueLevel === 'medium'
                ? '25–40 min'
                : '45–60+ min'}
          </span>
        </p>
      )}
    </div>
  );
}
