"use client";
import React, { useEffect, useState } from "react";
import { MetricsCards } from "../components/dashboard/MetricsCards";
import { AgentStatusGrid } from "../components/dashboard/AgentStatusGrid";
import { ActiveIncidents } from "../components/dashboard/ActiveIncidents";
import { LiveActivityFeed } from "../components/dashboard/LiveActivityFeed";
import { ScenarioSimulator } from "../components/payments/ScenarioSimulator";
import { fetchMetricsOverview, fetchIncidents, fetchEvents } from "../lib/api";
import { SystemMetricsOverview, IncidentItem, SystemActivityEvent } from "../types";
import { RefreshCw, AlertCircle } from "lucide-react";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<SystemMetricsOverview | null>(null);
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [events, setEvents] = useState<SystemActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [m, inc, evts] = await Promise.all([
        fetchMetricsOverview(),
        fetchIncidents(),
        fetchEvents(),
      ]);
      setMetrics(m);
      setIncidents(inc);
      setEvents(evts);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to connect to RazorAgent backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000); // 3-second live refresh
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      {/* Top Banner / Error */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/30 flex items-center justify-between text-rose-300 text-sm">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-rose-400" />
            <span>Backend Notice: {error} (Ensure FastAPI backend is running on port 8000)</span>
          </div>
          <button
            onClick={loadData}
            className="px-3 py-1 bg-rose-600/30 hover:bg-rose-600/50 rounded-lg text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Metrics */}
      <MetricsCards metrics={metrics} />

      {/* Agents Matrix */}
      <AgentStatusGrid agents={metrics?.agents || []} />

      {/* Two-column layout: Active Incidents & Scenario Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ActiveIncidents incidents={incidents} onRefresh={loadData} />
        <ScenarioSimulator onExecuted={loadData} />
      </div>

      {/* Live Activity Stream */}
      <LiveActivityFeed events={events} />
    </div>
  );
}
