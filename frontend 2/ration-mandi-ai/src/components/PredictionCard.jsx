import React from 'react';
import { Bot } from 'lucide-react';

export default function PredictionCard({ prediction }) {
  if (!prediction) return null;

  return (
    <section className="bg-white rounded-2xl border border-slate-200 card-shadow overflow-hidden">
      <div className="bg-slate-50 border-b border-slate-100 px-4 py-3 flex items-center gap-2">
        <Bot className="w-5 h-5 text-gov-blue" />
        <h3 className="font-semibold text-slate-800">🤖 AI Predictions</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Expected Queue */}
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Expected Queue
          </p>
          <p className="text-base text-slate-800">
            Approximately{' '}
            <span className="font-semibold">
              {prediction.expectedQueueAt5PM} people
            </span>{' '}
            at 5:00 PM
          </p>
        </div>

        {/* Stock-Out Prediction */}
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Stock-Out Prediction
          </p>
          <p className="text-base text-slate-800">
            {prediction.stockOutItem ? (
              <>
                <span className="capitalize font-semibold">
                  {prediction.stockOutItem}
                </span>{' '}
                may run low within approximately{' '}
                <span className="font-semibold">
                  {prediction.stockOutHours} hours
                </span>
                .
              </>
            ) : (
              'No significant stock-out risk expected soon.'
            )}
          </p>
        </div>

        {/* Recommended Visit Time */}
        <div className="bg-green-50 rounded-xl p-3 border border-green-100">
          <p className="text-xs font-medium text-green-700 uppercase tracking-wide mb-1">
            Recommended Visit Time
          </p>
          <p className="text-lg font-bold text-green-800">
            🟢 {prediction.recommendedTime}
          </p>
          <div className="flex gap-4 mt-2 text-sm text-slate-600">
            <span>
              Queue: <strong className="capitalize">{prediction.recommendedQueue}</strong>
            </span>
            <span>
              Stock: <strong>Available</strong>
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-400 italic">
          Predictions are estimates based on historical and current shop data.
        </p>
      </div>
    </section>
  );
}
