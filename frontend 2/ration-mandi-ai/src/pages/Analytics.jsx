import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Users, Clock, Package, AlertTriangle } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';
import DashboardCard from '../components/DashboardCard';
import { getAnalytics } from '../services/api';

const LEVEL_COLORS = {
  low: '#16a34a',
  medium: '#eab308',
  high: '#dc2626',
};

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalytics().then((res) => {
      if (res.success) setData(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-40 bg-slate-100 rounded-2xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const pieData = data.stockConsumption.map((d) => ({
    name: d.item,
    value: d.consumed,
  }));
  const PIE_COLORS = ['#16a34a', '#2563eb', '#eab308', '#f97316'];

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
      <div>
        <Link
          to="/shopkeeper"
          className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Shopkeeper
        </Link>
        <h1 className="text-xl font-bold text-slate-900">AI Admin Analytics</h1>
        <p className="text-sm text-slate-500">Demo insights for ration shop operations</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3">
        <DashboardCard>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center">
              <Users className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Citizens served today</p>
              <p className="text-xl font-bold text-slate-900">{data.citizensServedToday}</p>
            </div>
          </div>
        </DashboardCard>
        <DashboardCard>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Clock className="w-5 h-5 text-gov-blue" />
            </div>
            <div>
              <p className="text-xs text-slate-500">Avg daily queue</p>
              <p className="text-xl font-bold text-slate-900">{data.averageDailyQueue}</p>
            </div>
          </div>
        </DashboardCard>
      </div>

      {/* Peak hours */}
      <DashboardCard title="Peak Hours">
        <div className="flex flex-wrap gap-2">
          {data.peakHours.map((h) => (
            <span
              key={h}
              className="bg-red-50 text-red-700 text-sm font-medium px-3 py-1.5 rounded-full border border-red-100"
            >
              {h}
            </span>
          ))}
        </div>
      </DashboardCard>

      {/* Queue by hour chart */}
      <DashboardCard title="Queue Prediction by Hour">
        <div className="h-56 -mx-1">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.queueByHour} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <XAxis dataKey="hour" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: '1px solid #e2e8f0',
                  fontSize: 12,
                }}
              />
              <Bar dataKey="queue" radius={[6, 6, 0, 0]}>
                {data.queueByHour.map((entry, i) => (
                  <Cell key={i} fill={LEVEL_COLORS[entry.level] || '#94a3b8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-4 mt-2 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-green-600" /> Low
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-yellow-500" /> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-sm bg-red-600" /> High
          </span>
        </div>
      </DashboardCard>

      {/* Stock consumption */}
      <DashboardCard title="Stock Consumption (today)">
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                label={({ name, value }) => `${name}: ${value}kg`}
                labelLine={false}
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </DashboardCard>

      {/* Frequently out of stock + predicted */}
      <div className="grid sm:grid-cols-2 gap-3">
        <DashboardCard title="Frequently Out of Stock">
          <ul className="space-y-2">
            {data.frequentlyOutOfStock.map((item) => (
              <li
                key={item}
                className="flex items-center gap-2 text-sm text-slate-700"
              >
                <AlertTriangle className="w-4 h-4 text-red-500" />
                {item}
              </li>
            ))}
          </ul>
        </DashboardCard>
        <DashboardCard title="Predicted Stock-Out">
          <ul className="space-y-2">
            {data.predictedStockOut.map((p) => (
              <li key={p.item} className="text-sm text-slate-700">
                <span className="font-medium">{p.item}</span>
                <span className="text-slate-500"> — ~{p.hours}h remaining</span>
              </li>
            ))}
          </ul>
        </DashboardCard>
      </div>

      <p className="text-xs text-center text-slate-400">
        Analytics powered by mock data · Ready for real ML backend
      </p>
    </div>
  );
}
