import React from 'react';
import { Link } from 'react-router-dom';
import { Store, Bot, Users, Shield } from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-xl font-bold text-slate-900">About Ration Mandi AI</h1>

      <p className="text-slate-600 text-sm leading-relaxed">
        Ration Mandi AI helps low-income families avoid wasted trips to
        government ration shops. Citizens can check live stock availability,
        current queue length, and AI-powered predictions for the best time to
        visit — all before leaving home.
      </p>

      <div className="grid gap-3">
        {[
          {
            icon: Store,
            title: 'Live Shop Status',
            desc: 'Real-time stock and queue updates from shopkeepers.',
          },
          {
            icon: Bot,
            title: 'AI Predictions',
            desc: 'Queue forecasts, stock-out risk and recommended visit windows.',
          },
          {
            icon: Users,
            title: 'Built for Citizens',
            desc: 'Mobile-first, large text, minimal typing — works for rural users.',
          },
          {
            icon: Shield,
            title: 'Civic Trust',
            desc: 'Clean design suitable for government and public-service use.',
          },
        ].map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="flex gap-3 bg-white rounded-xl border border-slate-200 p-4 card-shadow"
          >
            <div className="shrink-0 w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
              <Icon className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">{title}</h3>
              <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-sm text-slate-600">
        <p className="font-medium text-slate-800 mb-1">For Shopkeepers</p>
        <p>
          Shop staff can update stock levels and queue counts in seconds so
          citizens always see accurate information.
        </p>
        <Link
          to="/shopkeeper"
          className="inline-block mt-2 text-green-700 font-semibold text-sm"
        >
          Go to Shopkeeper Dashboard →
        </Link>
      </div>

      <p className="text-xs text-slate-400 text-center">
        Hackathon prototype · Demo Data · Ready for Python FastAPI ML backend
      </p>
    </div>
  );
}
