export interface AgentStatusInfo {
  agent_name: string;
  status: "HEALTHY" | "BUSY" | "PAUSED" | "ERROR";
  current_task?: string;
  last_active: string;
  success_rate: number;
  total_invocations: number;
  avg_latency_ms: number;
  recent_decision_summary?: string;
  langsmith_trace_url?: string;
}

export interface SystemMetricsOverview {
  system_status: "HEALTHY" | "DEGRADED" | "INCIDENT_ACTIVE";
  total_payments: number;
  successful_payments: number;
  failed_payments: number;
  success_rate_percentage: number;
  recovery_rate_percentage: number;
  active_incidents_count: number;
  total_incidents_count: number;
  avg_payment_latency_ms: number;
  agents: AgentStatusInfo[];
}

export interface PaymentItem {
  payment_id: string;
  order_id?: string;
  customer_id: string;
  amount: number;
  currency: string;
  status: string;
  method?: string;
  risk_score: number;
  risk_level: string;
  idempotency_key: string;
  created_at: string;
}

export interface IncidentItem {
  incident_id: string;
  title: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  status: "OPEN" | "INVESTIGATING" | "AWAITING_APPROVAL" | "MITIGATING" | "RESOLVED" | "REJECTED";
  detected_by: string;
  root_cause?: string;
  evidence?: Record<string, any>;
  recovery_plan?: {
    action?: string;
    reason?: string;
    expected_effect?: string;
    risk?: string;
    requires_human_approval?: boolean;
    verification_plan?: string;
    action_parameters?: Record<string, any>;
  };
  recovery_result?: Record<string, any>;
  human_review_required: boolean;
  created_at: string;
  resolved_at?: string;
  langsmith_trace_url?: string;
}

export interface SystemActivityEvent {
  event_id: string;
  timestamp: string;
  request_id?: string;
  agent_name: string;
  event_type: string;
  severity: "DEBUG" | "INFO" | "WARN" | "ERROR" | "CRITICAL";
  payload: Record<string, any>;
}
