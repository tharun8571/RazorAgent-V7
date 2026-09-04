import React from "react";
import { Bot, Shield, Wrench, RefreshCw, Eye, LifeBuoy, ExternalLink, Zap } from "lucide-react";
import { AgentStatusInfo } from "../../types";

interface Props {
  agents: AgentStatusInfo[];
}

const AGENT_META: Record<string, { label: string; icon: any; role: string; color: string }> = {
  payment_agent: {
    label: "Payment Agent",
    icon: Bot,
    role: "Intent & Context Reasoning",
    color: "from-indigo-500 to-blue-600",
  },
  risk_agent: {
    label: "Risk Agent",
    icon: Shield,
    role: "Contextual Risk Scoring",
    color: "from-amber-500 to-orange-600",
  },
  executor_agent: {
    label: "Executor Agent",
    icon: Wrench,
    role: "Tool Selection & Gateway Execution",
    color: "from-cyan-500 to-teal-600",
  },
  reconciliation_agent: {
    label: "Reconciliation Agent",
    icon: RefreshCw,
    role: "Cross-Record Ledger Alignment",
    color: "from-emerald-500 to-green-600",
  },
  monitor_agent: {
    label: "Monitor Agent",
    icon: Eye,
    role: "Supervisory Anomaly Diagnosis",
    color: "from-purple-500 to-indigo-600",
  },
  recovery_agent: {
    label: "Recovery Agent",
    icon: LifeBuoy,
    role: "Autonomous Mitigation & HITL Planning",
    color: "from-rose-500 to-pink-600",
  },
};

export const AgentStatusGrid: React.FC<Props> = ({ agents }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Autonomous Agent Matrix</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-400 font-mono border border-primary-500/20">
              Groq (qwen3.8-27b) Powered
            </span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time multi-agent supervisor status and reasoning decisions
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const meta = AGENT_META[agent.agent_name] || {
            label: agent.agent_name,
            icon: Bot,
            role: "Multi-agent node",
            color: "from-slate-600 to-slate-700",
          };
          const Icon = meta.icon;
          const isError = agent.status === "ERROR";
          const isHealthy = agent.status === "HEALTHY";

          return (
            <div
              key={agent.agent_name}
              className="glass-panel p-5 rounded-2xl border border-border/80 hover:border-border transition-all duration-200 flex flex-col justify-between space-y-4 group"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2.5 rounded-xl bg-gradient-to-tr ${meta.color} shadow-md`}>
                    <Icon className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white group-hover:text-primary-300 transition-colors">
                      {meta.label}
                    </h3>
                    <p className="text-[11px] text-slate-400">{meta.role}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900/80 border border-border">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isHealthy
                        ? "bg-accent-emerald shadow-[0_0_6px_#10b981]"
                        : isError
                        ? "bg-accent-rose animate-ping"
                        : "bg-accent-amber"
                    }`}
                  />
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
                    {agent.status}
                  </span>
                </div>
              </div>

              {/* Recent Decision Box */}
              <div className="p-3 rounded-xl bg-slate-950/60 border border-border/50 text-xs space-y-1">
                <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">
                  Latest Reasoning Output
                </span>
                <p className="text-slate-300 line-clamp-2 leading-relaxed italic">
                  "{agent.recent_decision_summary || "Standing by for transaction events..."}"
                </p>
              </div>

              {/* Metrics & Trace Link Footer */}
              <div className="pt-2 border-t border-border/40 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center space-x-3 font-mono text-[11px]">
                  <span>Runs: {agent.total_invocations}</span>
                  <span>•</span>
                  <span>SR: {Math.round(agent.success_rate * 100)}%</span>
                </div>

                {agent.langsmith_trace_url && (
                  <a
                    href={agent.langsmith_trace_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-primary-400 hover:text-primary-300 transition-colors"
                  >
                    <span>Trace</span>
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
