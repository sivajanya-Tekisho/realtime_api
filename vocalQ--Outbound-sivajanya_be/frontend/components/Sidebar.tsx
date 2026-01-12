
import React from 'react';
import { ViewState } from '../types';
import { Icons, COLORS } from '../constants';

interface NavigationProps {
  activeView: ViewState;
  onViewChange: (view: ViewState) => void;
}

const Navigation: React.FC<NavigationProps> = ({ activeView, onViewChange }) => {
  const menuItems = [
    { id: 'overview', label: 'Home', icon: Icons.Dashboard, color: COLORS.primary },
    { id: 'outbound', label: 'Outbound', icon: Icons.Phone, color: COLORS.deep },
    { id: 'realtime', label: 'Live Monitor', icon: Icons.Live, color: COLORS.secondary },
    { id: 'transcripts', label: 'Call Logs', icon: Icons.Transcripts, color: COLORS.warning },
    { id: 'knowledge', label: 'Knowledge', icon: Icons.Knowledge, color: COLORS.info },
    { id: 'settings', label: 'Settings', icon: Icons.Settings, color: COLORS.muted },
  ];

  return (
    <>
      {/* Bottom Navigation (Enforced for all views) */}
      <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-[480px] z-[100] glass px-4 py-3 border-t border-white/10 flex items-center justify-between shadow-2xl pb-safe">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id as ViewState)}
              className="relative flex-1 flex flex-col items-center gap-1 p-2"
            >
              <Icon className={`w-5 h-5 ${isActive ? '' : 'opacity-40'}`} style={{ color: isActive ? item.color : '#64748b' }} />
              <span className={`text-[8px] font-black uppercase tracking-wider ${isActive ? '' : 'text-slate-600'}`} style={{ color: isActive ? item.color : undefined }}>
                {item.label}
              </span>
              {isActive && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-[2.5px] rounded-full shadow-lg" style={{ backgroundColor: item.color }}></div>
              )}
            </button>
          );
        })}
      </nav>

    </>
  );
};

export default Navigation;
