"use client";
import React, { useState, useEffect } from "react";
import { fetchEvents, fetchHealth } from "../../lib/api";
import { SystemActivityEvent } from "../../types";
import { Activity, Radio, RefreshCw, Server, Zap, Shield, Cpu } from "lucide-react";

export default function MonitoringPage() {
  const [events, setEvents] = useState<SystemActivityEvent[]>([]);
  const [health, setHealth] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [evts, h] = await Promise.all([fetchEvents(100), fetchHealth()]);
      setEvents(evts);
      setHealth(h);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Telemetry &amp; Event Stream</h1>
          <p className="text-xs text-slate-400">
            Real-time multi-agent activity log propagated via Redis Streams &amp; DB persistence
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-xl bg-slate-900 border border-border hover:bg-slate-800 text-slate-300 transition"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Subsystem Health Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-2xl border border-border/80 space-y-1">
          <div className="flex items-center space-x-2 text-primary-400">
            <Cpu className="h-4 w-4" />
            <span className="text-[11px] font-bold uppercase">Groq LLM Engine</span>
          </div>
          <p className="text-sm font-bold text-white font-mono">{health?.components?.groq_llm?.model || "qwen/qwen3.8-27b"}</p>
          <span className="text-[10px] text-accent-emerald font-semibold">Status: {health?.components?.groq_llm?.status || "CONFIGURED"}</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-border/80 space-y-1">
          <div className="flex items-center space-x-2 text-accent-cyan">
            <Radio className="h-4 w-4" />
            <span className="text-[11px] font-bold uppercase">Redis Stream</span>
          </div>
          <p className="text-sm font-bold text-white font-mono">agent_events_stream</p>
          <span className="text-[10px] text-accent-emerald font-semibold">{health?.components?.redis?.status || "CONNECTED"}</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-border/80 space-y-1">
          <div className="flex items-center space-x-2 text-accent-emerald">
            <Server className="h-4 w-4" />
            <span className="text-[11px] font-bold uppercase">Database State</span>
          </div>
          <p className="text-sm font-bold text-white font-mono">AsyncSQLAlchemy</p>
          <span className="text-[10px] text-accent-emerald font-semibold">Engine: {health?.components?.database?.engine || "Active"}</span>
        </div>

        <div className="glass-panel p-4 rounded-2xl border border-border/80 space-y-1">
          <div className="flex items-center space-x-2 text-accent-purple">
            <Zap className="h-4 w-4" />
            <span className="text-[11px] font-bold uppercase">LangSmith Tracing</span>
          </div>
          <p className="text-sm font-bold text-white font-mono">razoragent-v7</p>
          <span className="text-[10px] text-accent-emerald font-semibold">Project Active</span>
        </div>
      </div>

      {/* Real-Time Event Log */}
      <div className="glass-panel p-6 rounded-2xl border border-border/80 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <Activity className="h-4 w-4 text-accent-cyan" />
            <span>Real-Time Stream Log ({events.length} Events)</span>
          </h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-400 font-mono border border-primary-500/20">
            LLM: Groq (qwen/qwen3.8-27b)
          </span>
        </div>

        <div className="space-y-2.5 font-mono text-xs max-h-[550px] overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-slate-500 text-center py-12">Waiting for agent activity stream...</p>
          ) : (
            events.map((e) => (
              <div
                key={e.event_id}
                className="p-4 rounded-xl bg-slate-950/80 border border-border/60 space-y-2 hover:border-border transition-colors min-w-0 overflow-hidden"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <span className="text-primary-400 font-bold">[{e.agent_name}]</span>
                    <span className="text-white font-semibold">{e.event_type}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${
                        e.severity === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-400"
                          : e.severity === "WARN"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {e.severity}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-primary-500/10 text-primary-300 font-mono border border-primary-500/20">
                      Groq (qwen/qwen3.8-27b)
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 shrink-0">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center justify-between flex-wrap gap-2">
                  <span>Req ID: <code className="text-slate-200">{e.request_id || "N/A"}</code></span>
                  <span>Evt ID: <code className="text-slate-400">{e.event_id}</code></span>
                </div>

                {/* Transaction Info Payload Inspector */}
                {e.payload && Object.keys(e.payload).length > 0 && (
                  <div className="p-3 rounded-lg bg-slate-900/90 border border-border/50 text-[11px] font-mono space-y-1 text-slate-300 overflow-x-auto max-w-full">
                    <span className="text-[9px] font-bold uppercase text-slate-400 block tracking-wider">Transaction Payload Info</span>
                    <pre className="whitespace-pre-wrap break-words text-slate-200">
                      {JSON.stringify(e.payload, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
