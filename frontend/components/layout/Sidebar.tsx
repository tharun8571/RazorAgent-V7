"use client";
import React from "react";
import Link from "next/navigation";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CreditCard,
  Bot,
  AlertTriangle,
  Activity,
  GitGraph,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Command Center", href: "/", icon: LayoutDashboard },
  { name: "Payments Studio", href: "/payments", icon: CreditCard },
  { name: "Agents Matrix", href: "/agents", icon: Bot },
  { name: "Incident Center", href: "/incidents", icon: AlertTriangle },
  { name: "Telemetry & Events", href: "/monitoring", icon: Activity },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border bg-surface/30 flex flex-col justify-between py-6 px-4 shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div className="px-3">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Navigation
          </p>
        </div>

        <nav className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? "bg-primary-600/15 text-primary-400 border border-primary-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-surface-hover/60"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-primary-400" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </a>
            );
          })}
        </nav>
      </div>

      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-border/80 space-y-2">
        <div className="flex items-center space-x-2">
          <GitGraph className="h-4 w-4 text-accent-cyan" />
          <span className="text-xs font-semibold text-slate-200">LangGraph v0.0.31</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          StateGraph routing with Groq (qwen3.8-27b) reasoning &amp; fail-safe human escalation.
        </p>
      </div>
    </aside>
  );
};
