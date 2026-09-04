"use client";
import React, { useState, useEffect } from "react";
import { fetchIncidents } from "../../lib/api";
import { IncidentItem } from "../../types";
import { ApprovalModal } from "../../components/incidents/ApprovalModal";
import { AlertOctagon, ShieldAlert, CheckCircle, RefreshCw, UserCheck, ExternalLink, Filter } from "lucide-react";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentItem[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadIncidents = async () => {
    try {
      const data = await fetchIncidents(statusFilter || undefined);
      setIncidents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [statusFilter]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Incident Command Center</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-400 font-mono border border-primary-500/20 font-normal">
              LLM: Groq (qwen3.8-27b)
            </span>
          </h1>
          <p className="text-xs text-slate-400">
            Supervisor anomaly diagnosis, self-healing audits, and Human-in-the-Loop review
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-border text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-primary-500 font-mono"
          >
            <option value="">All Statuses</option>
            <option value="AWAITING_APPROVAL">Awaiting Approval (HITL)</option>
            <option value="OPEN">Open</option>
            <option value="RESOLVED">Resolved</option>
            <option value="REJECTED">Rejected</option>
          </select>
          <button
            onClick={loadIncidents}
            className="p-2 rounded-xl bg-slate-900 border border-border hover:bg-slate-800 text-slate-300 transition"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {incidents.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl border border-border/80 text-center space-y-3">
            <CheckCircle className="h-8 w-8 text-accent-emerald mx-auto" />
            <h3 className="text-sm font-bold text-white">No Incidents Found</h3>
            <p className="text-xs text-slate-400">
              No matching incidents logged. Autonomous self-healing loop is operating normally.
            </p>
          </div>
        ) : (
          incidents.map((inc) => {
            const isPending = inc.status === "AWAITING_APPROVAL" || inc.human_review_required;
            const isResolved = inc.status === "RESOLVED";

            return (
              <div
                key={inc.incident_id}
                onClick={() => setSelectedIncident(inc)}
                className="glass-panel p-6 rounded-2xl border border-border/80 hover:border-primary-500/40 transition-all space-y-4 cursor-pointer group"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <span
                      className={`text-xs font-mono font-bold px-2.5 py-1 rounded-lg uppercase ${
                        inc.severity === "CRITICAL"
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : inc.severity === "HIGH"
                          ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                          : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      }`}
                    >
                      {inc.severity}
                    </span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-bold text-white group-hover:text-primary-300 transition-colors">{inc.title}</h3>
                        <span className="text-xs font-mono text-slate-400">({inc.incident_id})</span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        Detected by {inc.detected_by} • {new Date(inc.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span
                      className={`text-xs font-mono font-bold px-3 py-1 rounded-full uppercase ${
                        isPending
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse"
                          : isResolved
                          ? "bg-emerald-500/10 text-accent-emerald border border-emerald-500/30"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {inc.status}
                    </span>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedIncident(inc);
                      }}
                      className="px-4 py-1.5 text-xs font-semibold bg-primary-600 hover:bg-primary-500 text-white rounded-xl shadow-lg shadow-primary-600/20 transition flex items-center space-x-1.5"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      <span>{isPending ? "Review & Authorize" : "Read Full Diagnosis"}</span>
                    </button>
                  </div>
                </div>

                {/* Diagnosis and Plan Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="p-3.5 rounded-xl bg-slate-950/70 border border-border/70 space-y-1 min-w-0 overflow-hidden">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                        AI Root Cause Analysis
                      </span>
                      <span className="text-[9px] font-mono text-primary-400 bg-primary-500/10 px-1.5 py-0.5 rounded border border-primary-500/20">
                        Groq qwen3.8-27b
                      </span>
                    </div>
                    <p className="text-slate-200 leading-relaxed break-words whitespace-pre-wrap text-[11px] font-mono">
                      {inc.root_cause
                        ? inc.root_cause
                            .replace(/Error code: \d+ - /g, "")
                            .replace(/\{'error': \{'message': '/g, "")
                            .replace(/'\}\}/g, "")
                        : "Pending diagnosis"}
                    </p>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950/70 border border-border/70 space-y-1 min-w-0 overflow-hidden">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-primary-400 block">
                      Recovery Plan ({inc.recovery_plan?.action || "No action"})
                    </span>
                    <p className="text-slate-300 leading-relaxed break-words whitespace-pre-wrap text-[11px]">
                      {inc.recovery_plan?.reason || "Autonomous standby"}
                    </p>
                  </div>
                </div>

                {/* Trace Link */}
                {inc.langsmith_trace_url && (
                  <div className="pt-2 border-t border-border/40 flex justify-end">
                    <a
                      href={inc.langsmith_trace_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-primary-400 hover:text-primary-300 font-mono flex items-center space-x-1"
                    >
                      <span>Inspect LangSmith Incident Trace</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {selectedIncident && (
        <ApprovalModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onRefresh={loadIncidents}
        />
      )}
    </div>
  );
}
