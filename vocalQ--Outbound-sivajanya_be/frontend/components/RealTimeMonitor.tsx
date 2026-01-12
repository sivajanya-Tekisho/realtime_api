
import React, { useState } from 'react';
import { api } from '../services/api';
import { COLORS } from '../constants';
import { CallMetric } from '../types';

const AudioVisualizer = ({ active, color = COLORS.secondary }: { active: boolean, color?: string }) => (
  <div className="flex items-end gap-[1px] h-3 px-1">
    {[...Array(6)].map((_, i) => (
      <div
        key={i}
        className="w-[1px] rounded-full transition-all duration-300"
        style={{
          backgroundColor: color,
          height: active ? `${30 + Math.random() * 70}%` : '2px',
          animation: active ? `wave ${0.4 + Math.random()}s ease-in-out infinite` : 'none',
          animationDelay: `${i * 0.1}s`
        }}
      ></div>
    ))}
  </div>
);

const RealTimeMonitor: React.FC = () => {
  const [activeCalls, setActiveCalls] = useState<CallMetric[]>([]);

  React.useEffect(() => {
    const fetchActive = async () => {
      try {
        const calls = await api.getActiveCalls();
        setActiveCalls(calls);
      } catch (e) {
        console.error(e);
      }
    };

    fetchActive();
    const interval = setInterval(fetchActive, 5000);
    return () => clearInterval(interval);
  }, []);
  const [monitoringId, setMonitoringId] = useState<string | null>(null);
  const [overridingId, setOverridingId] = useState<string | null>(null);

  return (
    <div className="space-y-4 animate-in fade-in duration-500 pb-20 lg:pb-0">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold font-display text-white tracking-tight">Live Ops</h2>
        <div className="flex items-center gap-2 px-3 py-1 bg-slate-900/50 border border-white/5 rounded-lg">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
          </span>
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">{activeCalls.length} Nodes</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeCalls.map((call) => {
          const isMonitoring = monitoringId === call.id;
          const isOverriding = overridingId === call.id;

          return (
            <div
              key={call.id}
              className={`glass p-4 rounded-2xl border-t-2 transition-all duration-300 relative overflow-hidden ${isMonitoring ? 'border-t-emerald-500' : isOverriding ? 'border-t-rose-500' : 'border-t-cyan-500'
                }`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-colors ${isOverriding ? 'bg-rose-500/20 border-rose-500/30 text-rose-400' : 'bg-slate-950 border-white/5 text-slate-500'
                    }`}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-white leading-tight">{call.caller}</h4>
                    <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{isOverriding ? 'Override' : call.intent}</span>
                  </div>
                </div>
                <div className="text-[10px] font-mono text-violet-400 font-bold">03:42</div>
              </div>

              <div className="bg-black/20 rounded-xl p-3 border border-white/5 mb-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">Neural Stream</span>
                  <AudioVisualizer active={true} color={isOverriding ? COLORS.danger : isMonitoring ? COLORS.success : COLORS.secondary} />
                </div>
                <p className="text-[10px] text-slate-400 italic line-clamp-1">
                  {call.transcript && call.transcript.length > 0
                    ? `"${call.transcript[call.transcript.length - 1].text}"`
                    : "Listening for input..."}
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setMonitoringId(isMonitoring ? null : call.id)}
                  className={`flex-1 group py-2 rounded-lg border transition-all ${isMonitoring ? 'bg-emerald-500 border-emerald-400' : 'bg-white/5 border-white/5 hover:bg-white/10'
                    }`}
                >
                  <div className={`text-[9px] font-black uppercase tracking-tighter ${isMonitoring ? 'text-white' : 'text-slate-300'}`}>Monitor</div>
                  <div className={`text-[7px] font-bold uppercase opacity-60 ${isMonitoring ? 'text-white' : 'text-slate-500'}`}>Listen Only</div>
                </button>
                <button
                  onClick={() => setOverridingId(isOverriding ? null : call.id)}
                  className={`flex-1 group py-2 rounded-lg border transition-all ${isOverriding ? 'bg-rose-600 border-rose-500' : 'bg-white/5 border-white/5 hover:bg-white/10'
                    }`}
                >
                  <div className={`text-[9px] font-black uppercase tracking-tighter ${isOverriding ? 'text-white' : 'text-slate-300'}`}>Control</div>
                  <div className={`text-[7px] font-bold uppercase opacity-60 ${isOverriding ? 'text-white' : 'text-slate-500'}`}>Barge-In</div>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RealTimeMonitor;
