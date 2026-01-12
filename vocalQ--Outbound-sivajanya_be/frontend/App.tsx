import React, { useState } from 'react';
import Navigation from './components/Sidebar';
import Overview from './components/Overview';
import RealTimeMonitor from './components/RealTimeMonitor';
import Transcripts from './components/Transcripts';
import KnowledgeBase from './components/KnowledgeBase';
import OutboundCalls from './components/OutboundCalls';
import { ViewState } from './types';
import { COLORS } from './constants';

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewState>('overview');
  const [activeSettingsTab, setActiveSettingsTab] = useState('assistant');
  const [greeting, setGreeting] = useState("Hello, thank you for calling VocalQ.ai support.");
  const [savingGreeting, setSavingGreeting] = useState(false);

  React.useEffect(() => {
    fetch('http://localhost:8000/api/v1/admin/settings/greeting')
      .then(res => res.json())
      .then(data => {
        if (data.greeting) setGreeting(data.greeting);
      })
      .catch(console.error);
  }, []);

  const saveGreeting = async (val: string) => {
    setSavingGreeting(true);
    try {
      await fetch('http://localhost:8000/api/v1/admin/settings/greeting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ greeting: val })
      });
    } catch (err) {
      console.error(err);
    } finally {
      setSavingGreeting(false);
    }
  };

  const settingsTabs = [
    { id: 'assistant', label: 'AI Assistant', icon: 'M13 10V3L4 14h7v7l9-11h-7z', color: COLORS.primary },
    { id: 'hours', label: 'Business Hours', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', color: COLORS.secondary },
    { id: 'languages', label: 'Languages', icon: 'M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5c-.356 2.06-1.356 4.12-2.703 6m-3.411-6c.356 2.06 1.356 4.12 2.703 6', color: COLORS.info },
    { id: 'reports', label: 'Reports', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', color: COLORS.warning },
  ];

  const renderSettingsContent = () => {
    switch (activeSettingsTab) {
      case 'assistant':
        return (
          <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="glass p-6 rounded-2xl border-white/5 space-y-4" style={{ borderTop: `2px solid ${COLORS.primary}33` }}>
              <h4 className="text-sm font-bold text-white mb-4">Core Voice Logic</h4>
              <div className="space-y-4">
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Greeting Message</label>
                    <span className="text-[10px] text-violet-400 font-mono">Dynamic AI</span>
                  </div>
                  <input
                    type="text"
                    className="bg-slate-950/50 border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-violet-500/50"
                    value={greeting}
                    onChange={(e) => setGreeting(e.target.value)}
                    onBlur={(e) => saveGreeting(e.target.value)}
                  />
                  {savingGreeting && <span className="text-[8px] text-emerald-400 animate-pulse">Saving to neural engine...</span>}
                </div>
              </div>
            </div>
          </div>
        );
      case 'hours':
        return (
          <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="glass p-6 rounded-2xl border-white/5" style={{ borderTop: `2px solid ${COLORS.secondary}33` }}>
              <h4 className="text-sm font-bold text-white mb-4">Operational Window</h4>
              <div className="grid grid-cols-2 gap-4">
                {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].map(day => (
                  <div key={day} className="flex items-center justify-between p-3 rounded-xl bg-slate-900/40 border border-white/5">
                    <span className="text-[11px] font-bold text-slate-300">{day}</span>
                    <span className="text-[10px] font-mono text-emerald-400">09:00 - 18:00</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      case 'languages':
        return (
          <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="glass p-6 rounded-2xl border-white/5" style={{ borderTop: `2px solid ${COLORS.info}33` }}>
              <h4 className="text-sm font-bold text-white mb-4">Global Localization</h4>
              <div className="space-y-4">
                <div className="flex flex-col gap-2">
                  <label className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Primary Language</label>
                  <div className="relative group">
                    <select className="w-full bg-slate-950/50 border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-200 focus:outline-none focus:border-violet-500/50 appearance-none cursor-pointer">
                      <option value="en-US">English (Default)</option>
                      <option value="es-MX">Spanish</option>
                      <option value="fr-FR">French</option>
                      <option value="de-DE">German</option>
                      <option value="hi-IN">Hindi</option>
                    </select>
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500 group-hover:text-slate-300">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-violet-500/5 border border-violet-500/10">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                    <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest">Active Status</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-relaxed">System is currently optimized for English voice synthesis and recognition.</p>
                </div>
              </div>
            </div>
          </div>
        );
      case 'reports':
        return (
          <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="glass p-6 rounded-2xl border-white/5" style={{ borderTop: `2px solid ${COLORS.warning}33` }}>
              <h4 className="text-sm font-bold text-white mb-4">Automated Reporting</h4>
              <div className="flex gap-4">
                <button className="flex-1 p-4 rounded-xl bg-slate-900 border border-white/5 text-center hover:bg-white/5 transition-colors">
                  <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2" style={{ color: COLORS.warning }}>Weekly PDF</div>
                  <div className="text-xs font-bold text-slate-200">Scheduled</div>
                </button>
                <button className="flex-1 p-4 rounded-xl bg-slate-900 border border-white/5 text-center hover:bg-white/5 transition-colors">
                  <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-2" style={{ color: COLORS.warning }}>Custom CSV</div>
                  <div className="text-xs font-bold text-slate-200">On-demand</div>
                </button>
              </div>
            </div>
          </div>
        );
      default: return null;
    }
  };

  const renderContent = () => {
    switch (activeView) {
      case 'overview': return <Overview />;
      case 'realtime': return <RealTimeMonitor />;
      case 'transcripts': return <Transcripts />;
      case 'knowledge': return <KnowledgeBase />;
      case 'outbound': return <OutboundCalls />;
      case 'analytics':
        return (
          <div className="flex flex-col items-center justify-center h-[50vh] text-center px-6">
            <div className="w-16 h-16 bg-indigo-600/10 rounded-2xl flex items-center justify-center mb-6 border border-indigo-500/20 relative">
              <div className="absolute inset-0 bg-indigo-500/10 blur-xl"></div>
              <svg className="w-8 h-8 text-indigo-400 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
            </div>
            <h2 className="text-lg font-bold font-display text-white mb-2 tracking-tight">Knowledge Base Synthesis</h2>
            <p className="text-[11px] text-slate-500 max-w-[200px] mx-auto leading-relaxed">Behavioral data streams are being aggregated from active nodes.</p>
          </div>
        );
      case 'settings':
        return (
          <div className="max-w-6xl mx-auto pb-20">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Settings Nav */}
              <div className="lg:col-span-1 space-y-1">
                {settingsTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveSettingsTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all border ${activeSettingsTab === tab.id
                      ? 'shadow-lg'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-white/5 border-transparent'
                      }`}
                    style={activeSettingsTab === tab.id ? {
                      backgroundColor: `${tab.color}11`,
                      borderColor: `${tab.color}33`,
                      color: tab.color
                    } : {}}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.icon} /></svg>
                    <span className="text-[11px] font-bold uppercase tracking-widest">{tab.label}</span>
                  </button>
                ))}
              </div>
              {/* Settings Content */}
              <div className="lg:col-span-3">
                {renderSettingsContent()}
              </div>
            </div>
          </div>
        );
      default: return <Overview />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#050811] selection:bg-violet-500/20 items-center overflow-x-hidden">
      <Navigation activeView={activeView} onViewChange={setActiveView} />

      <main className="w-full max-w-[480px] p-6 min-h-screen relative z-10 flex flex-col pt-10">
        <div className="fixed top-[-20%] right-[-10%] w-[800px] h-[800px] bg-violet-600/5 rounded-full blur-[140px] pointer-events-none -z-10"></div>
        <div className="fixed bottom-[-20%] left-[-10%] w-[800px] h-[800px] bg-indigo-600/5 rounded-full blur-[140px] pointer-events-none -z-10"></div>
        <div className="fixed top-[40%] left-[20%] w-[600px] h-[600px] bg-cyan-600/5 rounded-full blur-[140px] pointer-events-none -z-10"></div>

        {/* HIGH-DENSITY TOP BAR */}
        <header className="flex items-center justify-between mb-8 lg:mb-10 relative z-20">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold font-display text-white tracking-tighter leading-none">
              VocalQ<span className="text-cyan-400">.ai</span>
            </h1>
            <div className="h-3 w-[1px] bg-white/10"></div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/5 border border-white/5">
              <div className="relative flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
              </div>
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest leading-none">Live</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex bg-slate-900/40 border border-white/5 p-1 rounded-lg">
              <button className="px-3 py-1 text-[8px] font-black text-white bg-white/5 rounded-md border border-white/5 uppercase tracking-widest">Last 30D</button>
            </div>
            <div className="w-8 h-8 rounded-lg bg-slate-900 border border-white/10 flex items-center justify-center text-slate-500 hover:text-white transition-colors cursor-pointer group">
              <svg className="w-4 h-4 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            </div>
          </div>
        </header>

        <div className="max-w-[1400px] mx-auto pb-safe">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;
