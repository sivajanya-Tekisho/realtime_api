
import React, { useState, useEffect } from 'react';
import { COLORS } from '../constants';
import { api } from '../services/api';

interface KnowledgeDoc {
    id: string;
    text: string;
    metadata: {
        source: string;
        chunk: number;
        type: string;
    };
}

const KnowledgeBase: React.FC = () => {
    const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchDocs = async () => {
        setLoading(true);
        try {
            // Fetch from the new Vapi-synced endpoint
            const response = await fetch('http://localhost:8000/api/v1/vapi/knowledge');
            const data = await response.json();

            if (data.success && data.files) {
                // Map Vapi files to our display format
                const vapiDocs = data.files.map((file: any) => ({
                    id: file.id,
                    text: `Vapi Neural Node: ${file.originalName}`,
                    metadata: {
                        source: file.originalName,
                        chunk: 0,
                        type: 'vapi_knowledge',
                        vapi_id: file.id,
                        createdAt: file.createdAt
                    }
                }));
                setDocs(vapiDocs);
            } else {
                setDocs([]);
            }
        } catch (err) {
            setError('Failed to sync with Vapi Neural Base');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocs();
    }, []);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/v1/admin/knowledge/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Upload failed');

            await fetchDocs();
        } catch (err) {
            setError('Upload failed. Ensure backend is running and key is valid.');
        } finally {
            setUploading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            // Extract doc_id from composite ID (format: "doc_id_idx")
            const doc_id = id.includes('_') ? id.split('_').slice(0, -1).join('_') : id;

            await fetch(`http://localhost:8000/api/v1/admin/knowledge/${doc_id}`, {
                method: 'DELETE',
            });

            // Refresh the list after deletion
            await fetchDocs();
        } catch (err) {
            setError('Failed to delete document');
        }
    };

    return (
        <div className="space-y-6 pb-20 animate-in fade-in duration-700">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold font-display text-white tracking-tight">Knowledge</h2>
                    <p className="text-[11px] text-slate-500 mt-1 uppercase font-bold tracking-widest">Neural Asset Repository</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/5 rounded-lg">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">{docs.length} Segments</span>
                </div>
            </div>

            {/* Upload Zone HIDDEN per user request */}
            {/* 
            <div className="glass p-6 rounded-[2rem] border-dashed border-2 border-white/10 hover:border-violet-500/30 transition-all group relative overflow-hidden">
                <input
                    type="file"
                    onChange={handleFileUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer z-10"
                    accept=".pdf,.txt"
                />
                <div className="flex flex-col items-center justify-center text-center space-y-4 py-4">
                    <div className="w-14 h-14 rounded-2xl bg-violet-600/10 flex items-center justify-center border border-violet-500/20 group-hover:bg-violet-600/20 transition-all">
                        {uploading ? (
                            <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                            <svg className="w-6 h-6 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        )}
                    </div>
                    <div>
                        <p className="text-sm font-bold text-white">Upload Training Data</p>
                        <p className="text-[10px] text-slate-500 mt-1 uppercase font-bold tracking-widest">PDF / TXT (10MB Limit)</p>
                    </div>
                </div>
            </div>
            */}

            <div className="p-4 bg-violet-500/5 border border-violet-500/10 rounded-2xl">
                <p className="text-[10px] text-slate-500 uppercase font-black tracking-[0.2em] mb-1">Knowledge Management</p>
                <p className="text-xs text-slate-300">Knowledge is managed directly via the Vapi Dashboard for maximum performance and security.</p>
            </div>

            {error && (
                <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-[10px] font-bold uppercase flex items-center gap-3">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    {error}
                </div>
            )}

            {/* Knowledge List (Card Style for Mobile) */}
            <div className="space-y-4">
                <div className="flex items-center justify-between px-2">
                    <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Context Registry</h3>
                    <button onClick={fetchDocs} className="text-[9px] font-black text-violet-400 uppercase tracking-widest hover:text-white transition-colors">Refresh Nodes</button>
                </div>

                <div className="space-y-3">
                    {loading ? (
                        <div className="p-12 text-center">
                            <div className="w-8 h-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Indexing neural patterns...</span>
                        </div>
                    ) : docs.length === 0 ? (
                        <div className="glass p-12 rounded-[2rem] border-white/5 text-center">
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest italic leading-loose">No knowledge indexed.<br />Upload data to initialize RAG.</p>
                        </div>
                    ) : (
                        docs.map((doc) => (
                            <div key={doc.id} className="glass p-5 rounded-2xl border-white/5 hover:border-white/10 transition-all group relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/5 blur-[40px] pointer-events-none"></div>

                                <div className="flex items-start justify-between mb-3 relative z-10">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-slate-950 border border-white/5 flex items-center justify-center">
                                            {doc.metadata?.source?.endsWith('.pdf') ? (
                                                <svg className="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                                            ) : (
                                                <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                            )}
                                        </div>
                                        <div>
                                            <p className="text-[11px] font-bold text-white truncate max-w-[200px] mb-1">{doc.metadata?.source || 'Untitled'}</p>
                                            <span className="px-2 py-0.5 rounded bg-violet-500/10 text-[8px] font-mono text-violet-400 border border-violet-500/20">Segment #{doc.metadata.chunk}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(doc.id)}
                                        className="p-2 rounded-lg bg-rose-500/5 hover:bg-rose-500/20 text-rose-400 transition-all"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                    </button>
                                </div>
                                <div className="bg-black/20 rounded-xl p-3 border border-white/5 relative z-10 transition-colors group-hover:border-white/10">
                                    <p className="text-[10px] text-slate-400 line-clamp-3 italic leading-relaxed">
                                        "{doc.text}"
                                    </p>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default KnowledgeBase;
