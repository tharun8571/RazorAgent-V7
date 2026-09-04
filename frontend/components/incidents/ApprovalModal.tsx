"use client";
import React, { useState } from "react";
import { AlertOctagon, CheckCircle, XCircle, ShieldAlert, FileText, ArrowRight, UserCheck } from "lucide-react";
import { IncidentItem } from "../../types";
import { approveIncident, rejectIncident } from "../../lib/api";

interface Props {
  incident: IncidentItem | null;
  onClose: () => void;
  onRefresh: () => void;
}

export const ApprovalModal: React.FC<Props> = ({ incident, onClose, onRefresh }) => {
  const [operatorName, setOperatorName] = useState("operator:alex");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!incident) return null;

  const plan = incident.recovery_plan || {};

  const handleApprove = async () => {
    try {
      setSubmitting(true);
      setError(null);
      await approveIncident(
        incident.incident_id,
        operatorName,
        reason || "Approved by operator"
      );
      onRefresh();
      onClose();
    } catch (err: any) {
      setError(err.message || "Approval execution failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!reason) {
      setError("Please provide a rejection rationale.");
      return;
    }
    try {
      setSubmitting(true);
      setError(null);
      await rejectIncident(incident.incident_id, operatorName, reason);
      onRefresh();
      onClose();
    } catch (err: any) {
      setError(err.message || "Rejection failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="glass-panel-glow w-full max-w-2xl rounded-2xl p-6 space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-border/60 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-accent-rose/10 border border-accent-rose/30">
              <ShieldAlert className="h-6 w-6 text-accent-rose" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-accent-rose/20 text-accent-rose font-bold">
                  {incident.severity}
                </span>
                <span className="text-xs text-slate-400 font-mono">{incident.incident_id}</span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1">{incident.title}</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Root Cause & Evidence */}
        <div className="space-y-4 text-sm">
          <div>
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                AI Root Cause Diagnosis
              </h4>
              <span className="text-[10px] font-mono text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded border border-primary-500/20">
                LLM: Groq (qwen3.8-27b)
              </span>
            </div>
            <div className="text-slate-200 bg-slate-900/80 p-3.5 rounded-xl border border-border/80 font-mono text-xs leading-relaxed space-y-1 min-w-0 overflow-hidden break-words">
              <p className="text-slate-200 whitespace-pre-wrap break-words text-[11px]">
                {incident.root_cause
                  ? incident.root_cause
                      .replace(/Error code: \d+ - /g, "")
                      .replace(/\{'error': \{'message': '/g, "")
                      .replace(/'\}\}/g, "")
                  : "No root cause diagnosed."}
              </p>
            </div>
          </div>

          {incident.evidence && Object.keys(incident.evidence).length > 0 && (
            <div className="min-w-0 overflow-hidden space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Telemetry Evidence
              </h4>
              <pre className="text-xs font-mono bg-slate-950 p-3 rounded-xl border border-border text-slate-300 overflow-x-auto max-w-full whitespace-pre-wrap break-words">
                {JSON.stringify(incident.evidence, null, 2)}
              </pre>
            </div>
          )}

          {/* AI Recommended Recovery Plan */}
          <div className="p-4 rounded-xl bg-primary-950/40 border border-primary-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-primary-400">
                Proposed Recovery Action
              </span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-primary-500/20 text-primary-300">
                {plan.action || "no_action"}
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{plan.reason}</p>
            {plan.verification_plan && (
              <p className="text-xs text-slate-400 font-mono mt-1">
                Verification: {plan.verification_plan}
              </p>
            )}
          </div>

          {/* Operator Sign-off inputs - only for pending review */}
          {incident.status === "AWAITING_APPROVAL" || incident.human_review_required ? (
            <div className="space-y-3 pt-2">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Operator Identity
                </label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Operator Decision Note / Reason
                </label>
                <textarea
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="State your review rationale for audit trail..."
                  className="w-full bg-slate-900 border border-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                />
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                  {error}
                </div>
              )}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-900 border border-border text-xs text-slate-400 font-mono flex items-center justify-between">
              <span>Status: <strong className="text-slate-200 uppercase">{incident.status}</strong></span>
              <span>Resolution: {incident.recovery_plan?.action || "Self-healing or operator closed"}</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-border/60">
          <button
            onClick={onClose}
            disabled={submitting}
            className="px-5 py-2 text-sm font-medium text-slate-300 hover:text-white rounded-xl bg-slate-800 hover:bg-slate-700 transition"
          >
            Close
          </button>
          {(incident.status === "AWAITING_APPROVAL" || incident.human_review_required) && (
            <>
              <button
                onClick={handleReject}
                disabled={submitting}
                className="px-4 py-2 text-sm font-semibold bg-rose-600/20 text-rose-400 border border-rose-500/30 hover:bg-rose-600/30 rounded-xl transition flex items-center space-x-1.5"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject Plan</span>
              </button>
              <button
                onClick={handleApprove}
                disabled={submitting}
                className="px-5 py-2 text-sm font-semibold bg-primary-600 hover:bg-primary-500 text-white rounded-xl shadow-lg shadow-primary-600/30 transition flex items-center space-x-1.5"
              >
                <CheckCircle className="h-4 w-4" />
                <span>{submitting ? "Executing..." : "Approve & Execute"}</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
