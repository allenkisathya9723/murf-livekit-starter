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
        <span className="inline-flex items-center rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-0.5 text-xs font-semibold text-red-400">
          {urgency}
        </span>
      );
    }
    if (u === 'medium') {
      return (
        <span className="inline-flex items-center rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400">
          {urgency}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400">
        {urgency}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'OPEN') {
      return (
        <span className="inline-flex items-center rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-400">
          ● OPEN
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-md border border-zinc-500/20 bg-zinc-500/10 px-2 py-1 text-xs font-medium text-zinc-400">
        {status}
      </span>
    );
  };

  return (
    <main className="min-h-screen bg-slate-950 p-6 font-sans text-slate-100 md:p-12">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-6 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-white">
                JanMitra Human Help Dashboard
              </h1>
              <span className="rounded-full border border-indigo-500/30 bg-indigo-500/20 px-2.5 py-1 font-mono text-xs text-indigo-300">
                Day 7 Escalations
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Live human-support requests created with explicit user permission
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchEscalations}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700"
            >
              🔄 Refresh
            </button>
            <Link
              href="/analytics"
              className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700"
            >
              📊 Call Analytics
            </Link>
            <Link
              href="/"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-600/20 transition-colors hover:bg-indigo-500"
            >
              ← Back to Agent
            </Link>
          </div>
        </div>

        {/* Status Bar */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <p className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              Total Escalations
            </p>
            <p className="mt-1 text-2xl font-bold text-white">{escalations.length}</p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <p className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              Open Requests
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-400">
              {escalations.filter((e) => e.status === 'OPEN').length}
            </p>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
            <p className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              Database Status
            </p>
            <p className="mt-2 flex items-center gap-2 text-sm font-semibold text-slate-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" /> Connected
              (janmitra.db)
            </p>
          </div>
        </div>

        {/* Table / List */}
        {loading && escalations.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 py-12 text-center">
            <p className="text-slate-400">Loading escalations...</p>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-center text-red-400">
            <p>Error loading escalations: {error}</p>
          </div>
        ) : escalations.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 py-16 text-center">
            <div className="mb-3 text-4xl">📋</div>
            <h3 className="text-lg font-medium text-slate-300">No Escalation Requests Yet</h3>
            <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
              When a user asks for a medical diagnosis or reports a red-flag symptom and grants
              permission, requests will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {escalations.map((item) => (
              <div
                key={item.reference_id}
                className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/80 p-6 shadow-sm transition-all hover:border-slate-700"
              >
                <div className="flex flex-col justify-between gap-2 border-b border-slate-800/80 pb-3 md:flex-row md:items-center">
                  <div className="flex items-center gap-3">
                    <span className="rounded border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 font-mono text-sm font-bold text-indigo-400">
                      {item.reference_id}
                    </span>
                    {getStatusBadge(item.status)}
                    {getUrgencyBadge(item.urgency)}
                  </div>
                  <span className="font-mono text-xs text-slate-400">
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                      Reason
                    </p>
                    <p className="mt-0.5 font-medium text-slate-200">{item.reason}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                      Language & Follow-up
                    </p>
                    <p className="mt-0.5 text-slate-200">
                      {item.language} • Preferred via {item.preferred_follow_up}
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                      Summary
                    </p>
                    <p className="mt-0.5 rounded-lg border border-slate-800/50 bg-slate-950/50 p-3 text-slate-300">
                      {item.summary}
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                      What Agent Checked
                    </p>
                    <p className="mt-0.5 rounded-lg border border-slate-800/50 bg-slate-950/50 p-3 text-slate-300">
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
