# RazorAgent V7 — REST API Specification

## Endpoints Summary

### Health
- `GET /health` — Returns status of Groq LLM, LangSmith, Razorpay, Redis, and Database.

### Payments
- `POST /api/v1/payments/create-order` — Initiates multi-agent payment workflow.
- `POST /api/v1/payments/webhook` — Secure Razorpay webhook receiver with HMAC-SHA256 signature verification.
- `GET /api/v1/payments/` — Lists payments.
- `GET /api/v1/payments/{payment_id}` — Gets payment details.

### Agents
- `GET /api/v1/agents/` — Returns matrix of all 6 agents, health status, invocation count, and latest decisions.
- `GET /api/v1/agents/{agent_name}` — Gets detailed status and event logs for a specific agent.

### Incidents (Human-in-the-Loop)
- `GET /api/v1/incidents/` — Lists incidents with status/severity filters.
- `GET /api/v1/incidents/{incident_id}` — Returns full incident details, AI root cause diagnosis, evidence, and recovery plan.
- `POST /api/v1/incidents/{incident_id}/approve` — Operator approves AI recovery plan (executes action & resolves incident).
- `POST /api/v1/incidents/{incident_id}/reject` — Operator rejects AI recovery plan with rationale.

### Monitoring & Telemetry
- `GET /api/v1/monitoring/overview` — Platform metrics overview (success rate, recovery rate, active incidents).
- `GET /api/v1/monitoring/events` — Recent streaming activity events.
- `POST /api/v1/monitoring/simulate` — Simulator for real-world edge cases (fraud, mismatch, LLM outage).
