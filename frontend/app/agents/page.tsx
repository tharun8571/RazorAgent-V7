"use client";
import React, { useState, useEffect } from "react";
import { fetchAgents, fetchAgentDetails } from "../../lib/api";
import { Bot, Shield, Wrench, RefreshCw, Eye, LifeBuoy, ExternalLink, Activity, Terminal } from "lucide-react";

const AGENT_ROLES = [
  { id: "payment_agent", name: "Payment Agent", icon: Bot, desc: "Evaluates incoming request context, intent, customer profile, and currency validity via Groq." },
  { id: "risk_agent", name: "Risk Agent", icon: Shield, desc: "Performs continuous risk scoring over velocity, device signals, and financial anomalies via Groq." },
  { id: "executor_agent", name: "Executor Agent", icon: Wrench, desc: "Selects registered tools (orders, captures, refunds) and prepares execution payloads via Groq." },
  { id: "reconciliation_agent", name: "Reconciliation Agent", icon: RefreshCw, desc: "Cross-checks internal database records, Razorpay API states, and webhooks to detect delta desync." },
  { id: "monitor_agent", name: "Monitor Agent", icon: Eye, desc: "Supervises overall execution, diagnoses root causes, assesses severity, and identifies anomalies." },
  { id: "recovery_agent", name: "Recovery Agent", icon: LifeBuoy, desc: "Formulates autonomous recovery plans and determines whether Human-in-the-Loop approval is required." },
];

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("payment_agent");
  const [agentDetails, setAgentDetails] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAgents = async () => {
    try {
      const data = await fetchAgents();
      setAgents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetails = async (name: string) => {
    try {
      const det = await fetchAgentDetails(name);
      setAgentDetails(det);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadAgents();
    loadDetails(selectedAgent);
  }, [selectedAgent]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Autonomous Agents Matrix</h1>
        <p className="text-xs text-slate-400">
          Inspect individual LLM agent reasoning, execution traces, and telemetry
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Selector List */}
        <div className="glass-panel p-4 rounded-2xl border border-border/80 space-y-2 lg:col-span-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-2 block mb-2">
            Active Multi-Agent Nodes
          </span>
          {AGENT_ROLES.map((role) => {
            const Icon = role.icon;
            const isSelected = selectedAgent === role.id;
            const stats = agents.find((a) => a.agent_name === role.id);

            return (
              <button
                key={role.id}
                onClick={() => setSelectedAgent(role.id)}
                className={`w-full p-3 rounded-xl text-left transition-all flex items-center justify-between ${
                  isSelected
                    ? "bg-primary-600/15 border border-primary-500/30 text-white"
                    : "text-slate-400 hover:text-slate-200 hover:bg-surface-hover/50 border border-transparent"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${isSelected ? "bg-primary-600 text-white" : "bg-slate-800 text-slate-400"}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">{role.name}</h3>
                    <p className="text-[10px] text-slate-400">Runs: {stats?.invocations ?? 0}</p>
                  </div>
                </div>
                <span className="h-2 w-2 rounded-full bg-accent-emerald shadow-[0_0_6px_#10b981]" />
              </button>
            );
          })}
        </div>

        {/* Selected Agent Inspector */}
        <div className="glass-panel p-6 rounded-2xl border border-border/80 lg:col-span-2 space-y-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white">
                  {AGENT_ROLES.find((r) => r.id === selectedAgent)?.name}
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-accent-emerald border border-emerald-500/20 font-bold">
                  {agentDetails?.status || "HEALTHY"}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {AGENT_ROLES.find((r) => r.id === selectedAgent)?.desc}
              </p>
            </div>

            {agentDetails?.langsmith_url && (
              <a
                href={agentDetails.langsmith_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 rounded-xl bg-slate-900 border border-border hover:border-primary-500 text-primary-400 hover:text-primary-300 text-xs font-semibold flex items-center space-x-1.5 transition"
              >
                <span>LangSmith Trace</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>

          {/* Stats Bar */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-border text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Invocations</span>
              <span className="text-lg font-bold text-white font-mono">{agentDetails?.invocations ?? 0}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-border text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Errors / Retries</span>
              <span className="text-lg font-bold text-accent-rose font-mono">{agentDetails?.errors ?? 0}</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-900/70 border border-border text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">LLM Reasoning Engine</span>
              <span className="text-xs font-bold text-primary-400 font-mono">Groq (qwen3.8-27b)</span>
            </div>
          </div>

          {/* Recent Decision */}
          <div className="p-4 rounded-xl bg-slate-950/60 border border-border space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Current Reasoning Output
            </span>
            <p className="text-xs text-slate-300 italic leading-relaxed">
              "{agentDetails?.last_decision || "Agent is standing by."}"
            </p>
          </div>

          {/* Recent Events Log */}
          <div className="space-y-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
              Recent Agent Activity Events
            </span>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-border max-h-48 overflow-y-auto space-y-2 font-mono text-xs text-slate-300">
              {agentDetails?.recent_events?.length === 0 ? (
                <p className="text-slate-500 text-center py-4">No events logged for this node.</p>
              ) : (
                agentDetails?.recent_events?.map((ev: any) => (
                  <div key={ev.event_id} className="flex items-center justify-between border-b border-border/30 pb-1 text-[11px]">
                    <span className="text-accent-cyan">{ev.event_type}</span>
                    <span className="text-slate-500">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
