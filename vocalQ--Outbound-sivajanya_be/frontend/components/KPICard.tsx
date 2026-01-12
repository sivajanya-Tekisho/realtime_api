
import React from 'react';
import { BusinessMetric } from '../types';
import { COLORS } from '../constants';

const KPICard: React.FC<BusinessMetric> = ({ label, value, change, trend }) => {
  // Assign semantic colors based on labels
  const getAccentColor = () => {
    if (label.includes('Inbound')) return COLORS.primary;
    if (label.includes('Answered')) return COLORS.success;
    if (label.includes('Missed')) return COLORS.danger;
    if (label.includes('Duration')) return COLORS.secondary;
    return COLORS.primary;
  };

  const accentColor = getAccentColor();

  return (
    <div 
      className="glass group relative p-4 rounded-xl border border-white/5 overflow-hidden transition-all duration-300 hover:shadow-[0_0_20px_rgba(255,255,255,0.05)] active:scale-[0.98]"
      style={{ borderLeft: `2px solid ${accentColor}33` }}
    >
      <div className="flex justify-between items-center relative z-10">
        <div className="space-y-0.5">
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest leading-none">{label}</p>
          <h3 className="text-xl font-bold font-display text-white tracking-tight">{value}</h3>
        </div>
        <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[9px] font-bold border ${
          trend === 'up' ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' : 'text-rose-400 border-rose-500/20 bg-rose-500/5'
        }`}>
          {trend === 'up' ? '↑' : '↓'} {change}%
        </div>
      </div>
      
      <div 
        className="absolute -bottom-4 -right-4 w-12 h-12 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition-opacity"
        style={{ backgroundColor: accentColor }}
      ></div>
    </div>
  );
};

export default KPICard;
