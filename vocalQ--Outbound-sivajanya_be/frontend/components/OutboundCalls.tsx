import React, { useState, useEffect } from 'react';
import { COLORS } from '../constants';

const OutboundCalls: React.FC = () => {
    const [phoneNumbers, setPhoneNumbers] = useState('');
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const fetchStatus = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/v1/outbound/status');
            const data = await res.json();
            setStatus(data);
        } catch (err) {
            console.error('Failed to fetch outbound status', err);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const startCalls = async () => {
        setLoading(true);
        setMessage('');
        try {
            const numbers = phoneNumbers.split(',').map(n => n.trim()).filter(n => n);
            const res = await fetch('http://localhost:8000/api/v1/outbound/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_numbers: numbers })
            });
            const data = await res.json();
            setMessage(data.message);
            setPhoneNumbers('');
        } catch (err) {
            setMessage('Error starting calls');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="glass p-8 rounded-3xl border-white/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 blur-3xl -z-10 group-hover:bg-indigo-500/20 transition-colors"></div>

                <h3 className="text-xl font-bold text-white mb-2 tracking-tight">Outbound Campaigns</h3>
                <p className="text-xs text-slate-400 mb-6">Queue sequential AI-driven calls to your contact list.</p>

                <div className="space-y-4">
                    <div className="flex flex-col gap-2">
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none">Phone Numbers (Comma separated)</label>
                        <textarea
                            className="bg-slate-950/50 border border-white/10 rounded-2xl px-4 py-4 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/50 min-h-[120px] transition-all"
                            placeholder="+1234567890, +1987654321..."
                            value={phoneNumbers}
                            onChange={(e) => setPhoneNumbers(e.target.value)}
                        />
                    </div>

                    <button
                        onClick={startCalls}
                        disabled={loading || !phoneNumbers.trim()}
                        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold py-4 rounded-2xl text-xs uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20"
                    >
                        {loading ? 'Processing...' : 'Start Outbound Batch'}
                    </button>

                    {message && (
                        <p className="text-[10px] text-emerald-400 font-medium text-center animate-pulse">
                            {message}
                        </p>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="glass p-6 rounded-2xl border-white/5">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Engine Status</span>
                        <div className={`h-2 w-2 rounded-full ${status?.is_running ? 'bg-emerald-500 animate-pulse' : 'bg-slate-600'}`}></div>
                    </div>
                    <p className="text-lg font-bold text-white mb-1">
                        {status?.is_running ? 'Active Calling' : 'System Idle'}
                    </p>
                    <p className="text-[10px] text-slate-500">
                        {status?.queue_size || 0} numbers remaining in queue
                    </p>
                </div>

                <div className="glass p-6 rounded-2xl border-white/5">
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-4">Current Session</span>
                    <p className="text-xs font-mono text-indigo-400 truncate mb-1">
                        {status?.current_call_sid || 'None'}
                    </p>
                    <p className="text-[10px] text-slate-500">
                        Active Call SID
                    </p>
                </div>
            </div>
        </div>
    );
};

export default OutboundCalls;
