'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';

interface Escalation {
  reference_id: string;
  created_at: string;
  caller_id: string;
  reason: string;
  summary: string;
  what_checked: string;
  urgency: string;
  language: string;
  preferred_follow_up: string;
  status: string;
}

export default function EscalationsDashboard() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEscalations = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/escalations');
      const data = await res.json();
      if (res.ok) {
        setEscalations(data.escalations || []);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch escalations');
      }
    } catch (err: any) {
      setError(err.message || 'Error connecting to database');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
    const interval = setInterval(fetchEscalations, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const getUrgencyBadge = (urgency: string) => {
    const u = urgency.toLowerCase();
    if (u === 'critical' || u === 'high') {
      return (
        <span className="inline-flex items-center rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-400 border border-red-500/20">
          {urgency}
        </span>
      );
    }
    if (u === 'medium') {
      return (
        <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400 border border-amber-500/20">
          {urgency}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
        {urgency}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'OPEN') {
      return (
        <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
          ● OPEN
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-md bg-zinc-500/10 px-2 py-1 text-xs font-medium text-zinc-400 border border-zinc-500/20">
        {status}
      </span>
    );
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-white">
                JanMitra Human Help Dashboard
              </h1>
              <span className="bg-indigo-500/20 text-indigo-300 text-xs font-mono px-2.5 py-1 rounded-full border border-indigo-500/30">
                Day 7 Escalations
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Live human-support requests created with explicit user permission
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchEscalations}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 flex items-center gap-2"
            >
              🔄 Refresh
            </button>
            <Link
              href="/"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-indigo-600/20"
            >
              ← Back to Agent
            </Link>
          </div>
        </div>

        {/* Status Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Escalations</p>
            <p className="text-2xl font-bold text-white mt-1">{escalations.length}</p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Open Requests</p>
            <p className="text-2xl font-bold text-emerald-400 mt-1">
              {escalations.filter((e) => e.status === 'OPEN').length}
            </p>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Database Status</p>
            <p className="text-sm font-semibold text-slate-300 mt-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" /> Connected (janmitra.db)
            </p>
          </div>
        </div>

        {/* Table / List */}
        {loading && escalations.length === 0 ? (
          <div className="text-center py-12 bg-slate-900/40 rounded-xl border border-slate-800">
            <p className="text-slate-400">Loading escalations...</p>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center text-red-400">
            <p>Error loading escalations: {error}</p>
          </div>
        ) : escalations.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/40 rounded-xl border border-slate-800">
            <div className="text-4xl mb-3">📋</div>
            <h3 className="text-lg font-medium text-slate-300">No Escalation Requests Yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
              When a user asks for a medical diagnosis or reports a red-flag symptom and grants permission, requests will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {escalations.map((item) => (
              <div
                key={item.reference_id}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-6 transition-all space-y-4 shadow-sm"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded border border-indigo-500/20">
                      {item.reference_id}
                    </span>
                    {getStatusBadge(item.status)}
                    {getUrgencyBadge(item.urgency)}
                  </div>
                  <span className="text-xs text-slate-400 font-mono">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Reason</p>
                    <p className="text-slate-200 font-medium mt-0.5">{item.reason}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Language & Follow-up</p>
                    <p className="text-slate-200 mt-0.5">
                      {item.language} • Preferred via {item.preferred_follow_up}
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Summary</p>
                    <p className="text-slate-300 mt-0.5 bg-slate-950/50 p-3 rounded-lg border border-slate-800/50">
                      {item.summary}
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">What Agent Checked</p>
                    <p className="text-slate-300 mt-0.5 bg-slate-950/50 p-3 rounded-lg border border-slate-800/50">
                      {item.what_checked}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
