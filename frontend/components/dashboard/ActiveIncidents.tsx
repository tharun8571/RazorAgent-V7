"use client";
import React, { useState } from "react";
import { AlertOctagon, AlertTriangle, ShieldCheck, ArrowRight, UserCheck } from "lucide-react";
import { IncidentItem } from "../../types";
import { ApprovalModal } from "../incidents/ApprovalModal";

interface Props {
  incidents: IncidentItem[];
  onRefresh: () => void;
}

export const ActiveIncidents: React.FC<Props> = ({ incidents, onRefresh }) => {
  const [selectedIncident, setSelectedIncident] = useState<IncidentItem | null>(null);

  const active = incidents.filter(
    (i) => i.status === "OPEN" || i.status === "AWAITING_APPROVAL" || i.status === "INVESTIGATING"
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Active Incidents &amp; Escalations</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary-500/10 text-primary-400 font-mono border border-primary-500/20">
              LLM: Groq (qwen3.8-27b)
            </span>
            {active.length > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-accent-rose/15 text-accent-rose font-mono border border-accent-rose/30">
                {active.length} Action Required
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400">
            Supervisor anomaly alerts and pending human approval actions
          </p>
        </div>
      </div>

      {active.length === 0 ? (
        <div className="glass-panel p-8 rounded-2xl border border-border/80 text-center space-y-3">
          <div className="inline-flex p-3 rounded-full bg-accent-emerald/10 border border-accent-emerald/20 text-accent-emerald">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-bold text-white">System Fully Nominal</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Zero active incidents or blocked transactions. Monitor Agent is supervising real-time traffic.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {active.map((inc) => {
            const isAwaitingApproval = inc.status === "AWAITING_APPROVAL" || inc.human_review_required;
            return (
              <div
                key={inc.incident_id}
                onClick={() => setSelectedIncident(inc)}
                className="glass-panel p-4 rounded-2xl border border-accent-rose/30 hover:border-accent-rose/50 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer group"
              >
                <div className="space-y-1.5 flex-1 min-w-0 overflow-hidden">
                  <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-accent-rose/20 text-accent-rose uppercase shrink-0">
                      {inc.severity}
                    </span>
                    <span className="text-xs font-mono text-slate-400 shrink-0">{inc.incident_id}</span>
                    <span className="text-xs text-slate-500">•</span>
                    <span className="text-xs text-slate-400 font-medium truncate">By {inc.detected_by}</span>
                  </div>
                  <h4 className="text-sm font-bold text-white group-hover:text-primary-300 transition-colors break-words">{inc.title}</h4>
                  <div className="p-2.5 rounded-xl bg-slate-950/70 border border-border/60 text-xs text-slate-300 font-mono space-y-1 overflow-hidden min-w-0">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block tracking-wider">Root Cause Analysis</span>
                    <p className="line-clamp-2 leading-relaxed text-slate-200 break-words whitespace-pre-wrap text-[11px]">
                      {inc.root_cause ? inc.root_cause.replace(/Error code: \d+ - /g, "").replace(/\{'error': \{'message': '/g, "").replace(/'\}\}/g, "") : "No details provided."}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  {isAwaitingApproval ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedIncident(inc);
                      }}
                      className="px-4 py-2 text-xs font-semibold rounded-xl bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-600/20 transition flex items-center space-x-1.5"
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      <span>Review &amp; Sign-off</span>
                    </button>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedIncident(inc);
                      }}
                      className="px-3 py-1.5 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition flex items-center space-x-1"
                    >
                      <span>Read Details</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedIncident && (
        <ApprovalModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onRefresh={onRefresh}
        />
      )}
    </div>
  );
};
