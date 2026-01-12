
import React from 'react';
import KPICard from './KPICard';
import { api } from '../services/api';
import { COLORS } from '../constants';
import {
  CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, BarChart, Bar, XAxis
} from 'recharts';

const Overview: React.FC = () => {
  const [businessStats, setBusinessStats] = React.useState<any[]>([
    { label: 'Total Inbound', value: '0', change: 0, trend: 'up' },
    { label: 'Answered Calls', value: '0', change: 0, trend: 'up' },
    { label: 'Missed Calls', value: '0', change: 0, trend: 'down' },
    { label: 'Avg Duration', value: '0s', change: 0, trend: 'up' },
  ]);
  const [intentDistribution, setIntentDistribution] = React.useState<any[]>([]);
  const [hourWiseCalls, setHourWiseCalls] = React.useState<any[]>([]);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getAnalytics();

        // Transform for Business Stats
        const stats = [
          { label: 'Total Inbound', value: data.total_calls.toLocaleString(), change: 0, trend: 'up' as const },
          { label: 'Answered Calls', value: data.completed_calls.toLocaleString(), change: 0, trend: 'up' as const },
          { label: 'Missed Calls', value: data.missed_calls.toLocaleString(), change: 0, trend: 'down' as const },
          { label: 'Avg Duration', value: `${Math.round(data.avg_duration)}s`, change: 0, trend: 'up' as const },
        ];
        setBusinessStats(stats);

        // Transform for Intent Distribution
        const intents = Object.entries(data.intent_distribution).map(([name, value]) => ({ name, value }));
        setIntentDistribution(intents);

        // Transform for Peak Window
        setHourWiseCalls(data.calls_by_hour);

      } catch (error) {
        console.error("Failed to load analytics", error);
      }
    };
    fetchData();
  }, []);

  const PIE_COLORS = [COLORS.deep, COLORS.secondary, COLORS.success, COLORS.warning, COLORS.danger];

  return (
    <div className="space-y-6 pb-20 animate-in fade-in duration-700">

      {/* SECTION 1: CALL-LEVEL METRICS */}
      <section>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {businessStats.map((stat, idx) => (
            <KPICard key={idx} {...stat} />
          ))}
        </div>

        <div className="mt-6">
          <div className="glass p-5 rounded-2xl border-white/5 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 blur-[80px] pointer-events-none"></div>
            <h3 className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-5">Peak Window</h3>
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourWiseCalls}>
                  <XAxis dataKey="name" stroke="#475569" fontSize={9} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '10px' }} />
                  <Bar dataKey="value" fill={COLORS.secondary} radius={[4, 4, 0, 0]} barSize={10} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* COMPACT INTENT & HEALTH SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="glass p-5 rounded-2xl border-white/5 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-32 h-32 bg-violet-500/5 blur-[80px] pointer-events-none"></div>
          <h2 className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-5">Intent Profile</h2>
          <div className="h-[180px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={intentDistribution}
                  cx="50%" cy="50%"
                  innerRadius={50} outerRadius={70}
                  paddingAngle={5} dataKey="value"
                >
                  {intentDistribution.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', fontSize: '9px' }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '9px', fontWeight: 'bold', textTransform: 'uppercase' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-3">
          <div className="glass p-4 rounded-xl border-white/5 flex flex-col justify-center text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-violet-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Confidence</p>
            <div className="text-xl font-bold font-display text-violet-400">92.4%</div>
          </div>
          <div className="glass p-4 rounded-xl border-white/5 flex flex-col justify-center text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Success</p>
            <div className="text-xl font-bold font-display text-emerald-400">98.4%</div>
          </div>
          <div className="glass p-4 rounded-xl border-white/5 flex flex-col justify-center text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Latency</p>
            <div className="text-xl font-bold font-display text-amber-500">342ms</div>
          </div>
          <div className="glass p-4 rounded-xl border-white/5 flex flex-col justify-center text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p className="text-[8px] font-black text-slate-600 uppercase tracking-widest mb-1">Growth</p>
            <div className="text-xl font-bold font-display text-cyan-400">+12%</div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Overview;
