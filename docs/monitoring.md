# RazorAgent V7 — Monitoring, Telemetry & LangSmith Guide

## Observability Architecture

RazorAgent V7 incorporates multi-layer observability across the runtime lifecycle:

1. **LangSmith Distributed Tracing**:
   - Every LangGraph StateGraph invocation creates a root trace tagged with `razoragent-v7`, `env:development`, and the customer ID.
   - Child runs capture Groq LLM calls, tool executions, latency, token usage, and structured outputs.
   - Secrets (`GROQ_API_KEY`, `RAZORPAY_KEY_SECRET`, card tokens) are automatically sanitized and never reach trace payloads.

2. **Redis Streams (`agent_events_stream`)**:
   - Real-time agent event propagation to support live frontend event timelines.
   - Falls back gracefully to in-memory event buffers when Redis is offline.

3. **Persistent Incident Auditing**:
   - Every anomalous condition detected by the Monitor Agent or Safety Boundary produces an `Incident` row in PostgreSQL.
   - Operators can review root causes, telemetry evidence, and proposed recovery actions with one-click sign-off.
