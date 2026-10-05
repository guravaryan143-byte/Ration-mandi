import React from 'react';

export default function DashboardCard({ title, children, className = '', action }) {
  return (
    <div className={`bg-white rounded-2xl border border-slate-200 card-shadow ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          {title && <h3 className="font-semibold text-slate-800 text-sm">{title}</h3>}
          {action}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
