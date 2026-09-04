"use client";
import React from "react";
import { ShieldCheck, Activity, Terminal, ExternalLink, Cpu } from "lucide-react";

interface HeaderProps {
  systemStatus?: string;
}

export const Header: React.FC<HeaderProps> = ({ systemStatus = "HEALTHY" }) => {
  const isHealthy = systemStatus === "HEALTHY";
  const isDegraded = systemStatus === "DEGRADED";

  return (
    <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-primary-600 to-accent-cyan flex items-center justify-center shadow-lg shadow-primary-500/20">
          <Cpu className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-bold tracking-tight text-white">RAZORAGENT V7</h1>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-primary-500/10 text-primary-400 border border-primary-500/20">
              Autonomous
            </span>
          </div>
          <p className="text-xs text-slate-400">LLM Multi-Agent Operations &amp; Self-Healing</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Live System Status Pill */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-border">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              isHealthy
                ? "bg-accent-emerald shadow-[0_0_8px_#10b981]"
                : isDegraded
                ? "bg-accent-amber shadow-[0_0_8px_#f59e0b]"
                : "bg-accent-rose shadow-[0_0_8px_#f43f5e] animate-pulse"
            }`}
          />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-200">
            {systemStatus}
          </span>
        </div>

        {/* LangSmith Observatory Link */}
        <a
          href="https://smith.langchain.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center space-x-1.5 text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg bg-surface border border-border hover:border-primary-500/40 transition-all duration-150"
        >
          <span>LangSmith Tracing</span>
          <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
        </a>
      </div>
    </header>
  );
};
