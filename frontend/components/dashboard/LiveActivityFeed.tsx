import React from "react";
import { Activity, Radio, Clock } from "lucide-react";
import { SystemActivityEvent } from "../../types";

interface Props {
  events: SystemActivityEvent[];
}

export const LiveActivityFeed: React.FC<Props> = ({ events }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <Radio className="h-4 w-4 text-accent-cyan animate-pulse" />
            <span>Live Agent Event Stream</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time telemetry and state transitions propagated via Redis Streams
          </p>
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-border/80 p-4 max-h-[360px] overflow-y-auto space-y-2.5 font-mono text-xs">
        {events.length === 0 ? (
          <p className="text-slate-500 text-center py-6">No recent events captured.</p>
        ) : (
          events.slice(0, 15).map((evt) => {
            const isCritical = evt.severity === "CRITICAL" || evt.severity === "ERROR";
            const isWarn = evt.severity === "WARN";

            return (
              <div
                key={evt.event_id}
                className={`p-2.5 rounded-xl border transition-colors ${
                  isCritical
                    ? "bg-rose-950/30 border-rose-500/30 text-rose-300"
                    : isWarn
                    ? "bg-amber-950/30 border-amber-500/30 text-amber-300"
                    : "bg-slate-900/60 border-border/60 text-slate-300 hover:bg-slate-900"
                } flex items-start justify-between gap-3`}
              >
                <div className="space-y-0.5 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white">[{evt.agent_name}]</span>
                    <span className="text-primary-400">{evt.event_type}</span>
                  </div>
                  {evt.request_id && (
                    <div className="text-[10px] text-slate-400">
                      Req: {evt.request_id}
                    </div>
                  )}
                </div>

                <span className="text-[10px] text-slate-400 shrink-0">
                  {new Date(evt.timestamp).toLocaleTimeString()}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
