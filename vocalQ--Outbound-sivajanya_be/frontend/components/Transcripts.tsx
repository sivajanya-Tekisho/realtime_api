
import React, { useState } from 'react';
import { api } from '../services/api';
import { CallMetric } from '../types';

const Transcripts: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCall, setSelectedCall] = useState<CallMetric | null>(null);
  const [calls, setCalls] = useState<CallMetric[]>([]);

  React.useEffect(() => {
    api.getCalls().then(data => {
      const sorted = [...data].sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setCalls(sorted);
    }).catch(console.error);
  }, []);

  React.useEffect(() => {
    if (selectedCall && !selectedCall.transcript) {
      api.getCallDetails(selectedCall.id).then(details => {
        if (details) setSelectedCall(details);
      });
    }
  }, [selectedCall?.id]);

  const filteredCalls = calls.filter(call =>
    (call.caller && call.caller.includes(searchTerm)) ||
    (call.intent && call.intent.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const ConversationView = ({ call }: { call: CallMetric }) => (
    <div className="flex flex-col h-full bg-[#050811]">
      {/* Header */}
      <div className="p-6 border-b border-white/10 flex justify-between items-center bg-slate-900/60 sticky top-0 z-20 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSelectedCall(null)}
            className="p-2.5 rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div>
            <h3 className="text-lg font-bold font-display text-white">{call.caller}</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[10px] text-slate-500 font-bold uppercase">
                {new Date(call.timestamp).toLocaleString([], { month: '2-digit', day: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true })}
              </span>
              <span className="w-1 h-1 rounded-full bg-slate-700"></span>
              <span className="text-[10px] font-bold text-violet-400 uppercase tracking-widest">{call.intent}</span>
            </div>
          </div>
        </div>
        <div className="hidden sm:flex flex-col items-end">
          <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-wider ${call.sentiment === 'positive' ? 'bg-emerald-500/10 text-emerald-500' :
            call.sentiment === 'negative' ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-500/10 text-slate-500'
            }`}>
            {call.sentiment} Sentiment
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-10 scrollbar-hide">
        <div className="max-w-3xl mx-auto space-y-10 pb-20">

          {/* AI Neural Summary */}
          <div className="p-6 rounded-[1.5rem] bg-gradient-to-br from-violet-600/10 to-indigo-600/5 border border-violet-500/20 shadow-lg">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-lg bg-violet-600 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              </div>
              <h4 className="text-[10px] font-black text-violet-400 uppercase tracking-[0.2em]">Call Summary</h4>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed font-medium">"{call.summary || 'Summary processing...'}"</p>
          </div>

          {/* Chat Bubbles */}
          <div className="space-y-6">
            {call.transcript && call.transcript.length > 0 ? (
              call.transcript.map((part, idx) => (
                <div key={idx} className={`flex flex-col ${part.speaker === 'ai' ? 'items-start' : 'items-end'}`}>
                  <div className={`relative max-w-[90%] sm:max-w-[80%] p-4 rounded-2xl transition-all ${part.speaker === 'ai'
                    ? 'bg-slate-800/60 rounded-tl-none border border-white/5 text-slate-200 shadow-sm'
                    : 'bg-violet-600 rounded-tr-none text-white shadow-xl shadow-violet-900/30'
                    }`}>
                    <p className="text-sm leading-relaxed">{part.text}</p>
                    <div className={`mt-2 flex items-center gap-2 opacity-50 ${part.speaker === 'ai' ? 'justify-start' : 'justify-end'}`}>
                      <span className="text-[8px] font-bold uppercase tracking-widest">{part.speaker === 'ai' ? 'VocalQ AI' : 'Customer'}</span>
                      <span className="w-1 h-1 rounded-full bg-current opacity-30"></span>
                      <span className="text-[8px] font-mono">
                        {new Date(part.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-10">
                <p className="text-slate-500 text-sm">No transcript available for this record.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-white/10 bg-slate-950/90 backdrop-blur-md sticky bottom-0">
        <div className="max-w-3xl mx-auto grid grid-cols-2 gap-4">
          <button className="py-3.5 bg-white/5 hover:bg-white/10 text-slate-300 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all border border-white/5">
            Export Transcript
          </button>
          <button className="py-3.5 bg-violet-600 hover:bg-violet-500 text-white rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all shadow-xl shadow-violet-600/30">
            Sync to CRM
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-full relative pb-20 lg:pb-0">
      <div className="flex flex-col lg:flex-row gap-8 h-full">
        {/* List Pane */}
        <div className={`w-full lg:w-1/3 flex flex-col gap-6 ${selectedCall ? 'hidden lg:flex' : 'flex'}`}>
          <div className="space-y-4">
            <h2 className="text-2xl font-bold font-display text-white tracking-tight">Call Records</h2>
            <div className="relative group">
              <svg className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
              <input
                type="text"
                placeholder="Search identity or intent..."
                className="bg-slate-900/60 border border-white/10 rounded-[1.2rem] pl-11 pr-4 py-4 w-full text-sm text-slate-200 focus:outline-none focus:border-violet-500/50 transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-3 overflow-y-auto scrollbar-hide">
            {filteredCalls.map((call) => (
              <div
                key={call.id}
                onClick={() => setSelectedCall(call)}
                className={`p-5 rounded-[1.5rem] border transition-all cursor-pointer relative overflow-hidden group ${selectedCall?.id === call.id
                  ? 'bg-violet-600/10 border-violet-500/40 shadow-2xl shadow-violet-900/40'
                  : 'bg-slate-900/40 border-white/5 hover:border-white/10'
                  }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <p className="text-sm font-bold text-white group-hover:text-violet-400 transition-colors">{call.caller}</p>
                    <p className="text-[10px] text-slate-500 font-bold mt-1 uppercase tracking-widest">{call.status} • {call.duration}s</p>
                  </div>
                  <div className={`px-2 py-0.5 rounded-lg text-[8px] font-black uppercase tracking-widest ${call.intent === 'appointment' ? 'bg-cyan-500/10 text-cyan-500' : 'bg-violet-500/10 text-violet-500'
                    }`}>
                    {call.intent}
                  </div>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 italic leading-relaxed">"{call.summary}"</p>
              </div>
            ))}
          </div>
        </div>

        {/* Detail Pane (Conversation UI) */}
        <div className={`fixed inset-0 lg:relative lg:flex-1 lg:inset-auto z-[120] lg:z-10 ${selectedCall ? 'flex' : 'hidden lg:flex'}`}>
          <div className="w-full h-full glass lg:rounded-[2.5rem] overflow-hidden border-white/5 lg:border flex flex-col shadow-2xl">
            {selectedCall ? (
              <ConversationView call={selectedCall} />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-12 space-y-6">
                <div className="w-20 h-20 bg-slate-900/80 rounded-[2rem] flex items-center justify-center text-slate-800 border border-white/5">
                  <svg className="w-10 h-10 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" /></svg>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-bold font-display text-white tracking-tight">Communications Node</h3>
                  <p className="text-sm text-slate-500 max-w-xs mx-auto">Select a call record from the archives to review the AI-synthesized transcript and neural recap.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Transcripts;
