import { SystemMetricsOverview, PaymentItem, IncidentItem, SystemActivityEvent, AgentStatusInfo } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}

export async function fetchMetricsOverview(): Promise<SystemMetricsOverview> {
  const res = await fetch(`${API_BASE_URL}/monitoring/overview`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch metrics overview");
  return res.json();
}

export async function fetchPayments(limit = 50): Promise<PaymentItem[]> {
  const res = await fetch(`${API_BASE_URL}/payments/?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch payments");
  return res.json();
}

export async function createPaymentOrder(data: {
  customer_id: string;
  amount: number;
  currency?: string;
  method?: string;
  idempotency_key: string;
  description?: string;
  metadata?: Record<string, any>;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/payments/create-order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || err.error || "Failed to create payment order");
  }
  return res.json();
}

export async function fetchAgents(): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/agents/`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch agents");
  return res.json();
}

export async function fetchAgentDetails(agentName: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agents/${agentName}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch agent ${agentName}`);
  return res.json();
}

export async function fetchIncidents(status?: string, severity?: string): Promise<IncidentItem[]> {
  let url = `${API_BASE_URL}/incidents/?limit=50`;
  if (status) url += `&status=${encodeURIComponent(status)}`;
  if (severity) url += `&severity=${encodeURIComponent(severity)}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch incidents");
  return res.json();
}

export async function fetchIncidentDetails(incidentId: string): Promise<IncidentItem> {
  const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch incident details");
  return res.json();
}

export async function approveIncident(incidentId: string, operatorName: string, reason: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operator_name: operatorName, reason }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Approval failed");
  }
  return res.json();
}

export async function rejectIncident(incidentId: string, operatorName: string, reason: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operator_name: operatorName, reason }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Rejection failed");
  }
  return res.json();
}

export async function fetchEvents(limit = 50): Promise<SystemActivityEvent[]> {
  const res = await fetch(`${API_BASE_URL}/monitoring/events?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function runSimulationScenario(scenarioType: string, customParams: Record<string, any> = {}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/monitoring/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_type: scenarioType,
      customer_id: "cust_sim_01",
      amount: 1499.0,
      custom_params: customParams,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Simulation failed");
  }
  return res.json();
}
