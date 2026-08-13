'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';

interface CallRecord {
  id: number;
  call_id: string;
  channel: string;
  outcome: string;
  language: string;
  duration_seconds: number;
  started_at: string;
  ended_at: string;
}

interface AnalyticsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  recent_calls: CallRecord[];
  error?: string;
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/analytics?t=${Date.now()}`, { cache: 'no-store' });
      const json = await res.json();
      if (res.ok) {
        setData(json);
        setError(null);
      } else {
        setError(json.error || 'Failed to fetch analytics');
      }
    } catch (err: any) {
      setError(err.message || 'Error connecting to database');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, []);

  const getOutcomeBadge = (outcome: string) => {
    const isSuccess = outcome.toUpperCase() === 'SUCCESS';
    return isSuccess ? (
      <span className="inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
        ✓ SUCCESS
      </span>
    ) : (
      <span className="inline-flex items-center rounded-full border border-rose-500/20 bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400">
        ✗ FAILED
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
                JANMITRA CALL ANALYTICS
              </h1>
              <span className="rounded-full border border-emerald-500/30 bg-emerald-500/20 px-2.5 py-1 font-mono text-xs text-emerald-300">
                Day 8 Real-Time
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Real-time call performance metrics powered by janmitra.db
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAnalytics}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700"
            >
              🔄 Refresh
            </button>
            <Link
              href="/"
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-600/20 transition-colors hover:bg-indigo-500"
            >
              ← Back to Agent
            </Link>
          </div>
        </div>

        {/* Primary Metrics */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-sm">
            <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">TOTAL CALLS</p>
            <p className="mt-2 font-mono text-4xl font-extrabold text-white">
              {loading && !data ? '...' : (data?.total_calls ?? 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">All tracked incoming & outgoing calls</p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-sm">
            <p className="text-xs font-bold tracking-wider text-emerald-400 uppercase">
              SUCCESSFUL CALLS
            </p>
            <p className="mt-2 font-mono text-4xl font-extrabold text-emerald-400">
              {loading && !data ? '...' : (data?.successful_calls ?? 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Calls providing safe guidance or escalation
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-sm">
            <p className="text-xs font-bold tracking-wider text-rose-400 uppercase">FAILED CALLS</p>
            <p className="mt-2 font-mono text-4xl font-extrabold text-rose-400">
              {loading && !data ? '...' : (data?.failed_calls ?? 0)}
            </p>
            <p className="mt-2 text-xs text-slate-500">Incomplete or disconnected calls</p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-center text-rose-400">
            <p>Error loading analytics: {error}</p>
          </div>
        )}

        {/* Recent Call Records */}
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
          <h2 className="text-lg font-bold text-slate-200">Recent Call Logs</h2>

          {!data || data.recent_calls.length === 0 ? (
            <div className="py-8 text-center text-slate-500">
              No call records recorded yet in janmitra.db
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 bg-slate-950/80 font-mono text-xs text-slate-400 uppercase">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Room / Call ID</th>
                    <th className="px-4 py-3">Channel</th>
                    <th className="px-4 py-3">Outcome</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {data.recent_calls.map((call) => (
                    <tr key={call.id} className="transition-colors hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">#{call.id}</td>
                      <td className="px-4 py-3 font-mono text-xs text-indigo-300">
                        {call.call_id}
                      </td>
                      <td className="px-4 py-3 text-slate-300 capitalize">{call.channel}</td>
                      <td className="px-4 py-3">{getOutcomeBadge(call.outcome)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">
                        {call.duration_seconds}s
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">
                        {new Date(call.started_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
