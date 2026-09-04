"use client";
import React, { useState } from "react";
import { Play, Sparkles, AlertTriangle, ShieldCheck, RefreshCw, Cpu, CheckCircle2 } from "lucide-react";
import { runSimulationScenario } from "../../lib/api";

interface Props {
  onExecuted?: () => void;
}

const SCENARIOS = [
  {
    id: "normal_payment",
    label: "Nominal Flow",
    desc: "Standard payment passing Payment -> Risk -> Executor -> Reconcile -> Monitor",
    icon: CheckCircle2,
    badge: "Clean Pass",
    badgeColor: "text-accent-emerald bg-accent-emerald/10 border-accent-emerald/20",
  },
  {
    id: "high_risk_fraud",
    label: "High Risk Fraud Attempt",
    desc: "Simulates suspicious velocity signals triggering LLM Risk Agent block/HITL review",
    icon: ShieldCheck,
    badge: "Risk Agent Block",
    badgeColor: "text-accent-amber bg-accent-amber/10 border-accent-amber/20",
  },
  {
    id: "reconciliation_mismatch",
    label: "Reconciliation Desync",
    desc: "Simulates gateway delta; Monitor Agent diagnoses root cause & Recovery plans rollback",
    icon: RefreshCw,
    badge: "Self-Healing Loop",
    badgeColor: "text-accent-cyan bg-accent-cyan/10 border-accent-cyan/20",
  },
  {
    id: "llm_outage",
    label: "LLM Outage Test (No Fake AI)",
    desc: "Simulates LLM provider outage -> Proves zero fake intelligence & halts for human escalation",
    icon: Cpu,
    badge: "Safety Boundary",
    badgeColor: "text-accent-rose bg-accent-rose/10 border-accent-rose/20",
  },
];

export const ScenarioSimulator: React.FC<Props> = ({ onExecuted }) => {
  const [running, setRunning] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any | null>(null);

  const handleRun = async (scenarioId: string) => {
    try {
      setRunning(scenarioId);
      setLastResult(null);
      const res = await runSimulationScenario(scenarioId);
      setLastResult(res);
      if (onExecuted) onExecuted();
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
          <Sparkles className="h-4 w-4 text-primary-400" />
          <span>Interactive Multi-Agent Scenario Simulator</span>
        </h2>
        <p className="text-xs text-slate-400">
          Inject real-world operational edge-cases into the LangGraph state machine
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {SCENARIOS.map((sc) => {
          const Icon = sc.icon;
          const isRunning = running === sc.id;

          return (
            <div
              key={sc.id}
              className="glass-panel p-4 rounded-2xl border border-border/80 hover:border-primary-500/40 transition-all flex flex-col justify-between space-y-3 group"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className="h-4 w-4 text-slate-300 group-hover:text-primary-400 transition-colors" />
                    <span className="text-sm font-bold text-white">{sc.label}</span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${sc.badgeColor}`}>
                    {sc.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{sc.desc}</p>
              </div>

              <button
                onClick={() => handleRun(sc.id)}
                disabled={Boolean(running)}
                className="w-full py-2 px-3 rounded-xl bg-slate-900 hover:bg-primary-600 border border-border hover:border-primary-500 text-xs font-semibold text-white transition-all flex items-center justify-center space-x-1.5 shadow-sm"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>{isRunning ? "Simulating in LangGraph..." : "Run Scenario"}</span>
              </button>
            </div>
          );
        })}
      </div>

      {lastResult && (
        <div className="glass-panel-glow p-4 rounded-2xl border border-primary-500/30 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-primary-400">
              Simulation Execution Output: {lastResult.scenario}
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-primary-500/20 text-primary-300 font-bold">
              Status: {lastResult.workflow_status || lastResult.status}
            </span>
          </div>
          <pre className="text-xs font-mono bg-slate-950 p-3 rounded-xl border border-border text-slate-300 max-h-60 overflow-y-auto">
            {JSON.stringify(lastResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
