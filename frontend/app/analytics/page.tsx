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
      const res = await fetch('/api/analytics');
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
      <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
        ✓ SUCCESS
      </span>
    ) : (
      <span className="inline-flex items-center rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold text-rose-400 border border-rose-500/20">
        ✗ FAILED
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
                JANMITRA CALL ANALYTICS
              </h1>
              <span className="bg-emerald-500/20 text-emerald-300 text-xs font-mono px-2.5 py-1 rounded-full border border-emerald-500/30">
                Day 8 Real-Time
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Real-time call performance metrics powered by janmitra.db
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAnalytics}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700 flex items-center gap-2"
            >
              🔄 Refresh
            </button>
            <Link
              href="/escalations"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition-colors border border-slate-700"
            >
              📋 Day 7 Escalations
            </Link>
            <Link
              href="/"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors shadow-lg shadow-indigo-600/20"
            >
              ← Back to Agent
            </Link>
          </div>
        </div>

        {/* Primary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">TOTAL CALLS</p>
            <p className="text-4xl font-extrabold text-white mt-2 font-mono">
              {loading && !data ? '...' : data?.total_calls ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">All tracked incoming & outgoing calls</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
            <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider">SUCCESSFUL CALLS</p>
            <p className="text-4xl font-extrabold text-emerald-400 mt-2 font-mono">
              {loading && !data ? '...' : data?.successful_calls ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">Calls providing safe guidance or escalation</p>
          </div>

          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-sm">
            <p className="text-xs font-bold text-rose-400 uppercase tracking-wider">FAILED CALLS</p>
            <p className="text-4xl font-extrabold text-rose-400 mt-2 font-mono">
              {loading && !data ? '...' : data?.failed_calls ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-2">Incomplete or disconnected calls</p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-6 text-center text-rose-400">
            <p>Error loading analytics: {error}</p>
          </div>
        )}

        {/* Recent Call Records */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-bold text-slate-200">Recent Call Logs</h2>

          {!data || data.recent_calls.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No call records recorded yet in janmitra.db
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 border-b border-slate-800 font-mono">
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
                    <tr key={call.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">#{call.id}</td>
                      <td className="px-4 py-3 font-mono text-xs text-indigo-300">{call.call_id}</td>
                      <td className="px-4 py-3 capitalize text-slate-300">{call.channel}</td>
                      <td className="px-4 py-3">{getOutcomeBadge(call.outcome)}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">{call.duration_seconds}s</td>
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
