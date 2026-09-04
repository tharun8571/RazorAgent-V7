import React from "react";
import { CreditCard, CheckCircle2, RefreshCw, AlertOctagon, Clock } from "lucide-react";
import { SystemMetricsOverview } from "../../types";

interface Props {
  metrics: SystemMetricsOverview | null;
}

export const MetricsCards: React.FC<Props> = ({ metrics }) => {
  const cards = [
    {
      title: "Total Payments",
      value: metrics ? metrics.total_payments.toLocaleString() : "—",
      sub: `${metrics?.successful_payments || 0} Successful`,
      icon: CreditCard,
      color: "text-primary-400",
      bg: "bg-primary-500/10",
      border: "border-primary-500/20",
    },
    {
      title: "Payment Success Rate",
      value: metrics ? `${metrics.success_rate_percentage}%` : "—",
      sub: `${metrics?.failed_payments || 0} Blocked / Failed`,
      icon: CheckCircle2,
      color: "text-accent-emerald",
      bg: "bg-accent-emerald/10",
      border: "border-accent-emerald/20",
    },
    {
      title: "Self-Healing Recovery Rate",
      value: metrics ? `${metrics.recovery_rate_percentage}%` : "—",
      sub: "Autonomous & HITL",
      icon: RefreshCw,
      color: "text-accent-cyan",
      bg: "bg-accent-cyan/10",
      border: "border-accent-cyan/20",
    },
    {
      title: "Active Incidents",
      value: metrics ? metrics.active_incidents_count.toString() : "0",
      sub: `${metrics?.total_incidents_count || 0} Total Logged`,
      icon: AlertOctagon,
      color: metrics && metrics.active_incidents_count > 0 ? "text-accent-rose" : "text-slate-400",
      bg: metrics && metrics.active_incidents_count > 0 ? "bg-accent-rose/10" : "bg-slate-800/40",
      border: metrics && metrics.active_incidents_count > 0 ? "border-accent-rose/30" : "border-border",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`glass-panel p-5 rounded-2xl border ${c.border} transition-all duration-200 hover:translate-y-[-2px]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {c.title}
              </span>
              <div className={`p-2 rounded-xl ${c.bg}`}>
                <Icon className={`h-4 w-4 ${c.color}`} />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-2xl font-bold text-white tracking-tight">{c.value}</span>
            </div>
            <p className="mt-1 text-xs text-slate-400">{c.sub}</p>
          </div>
        );
      })}
    </div>
  );
};
