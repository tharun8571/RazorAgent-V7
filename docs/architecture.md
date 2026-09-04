# RazorAgent V7 — System Architecture

## Overview
RazorAgent V7 is an enterprise-grade, autonomous payment operations and self-healing platform. It employs an LLM-driven multi-agent mesh orchestrated by LangGraph, powered by Groq's high-speed inference, observed with LangSmith tracing, and integrated with Razorpay Test Mode for payment gateway operations.

```text
                                  +---------------------------------------+
                                  |              Next.js UI               |
                                  |       (Operator Control Center)       |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |          FastAPI REST API             |
                                  |   (Health, Payments, Incidents, SSE)  |
                                  +-------------------+-------------------+
                                                      |
                                                      v
+---------------------------------------------------------------------------------------------------------+
|                                    LangGraph Multi-Agent StateGraph                                     |
|                                                                                                         |
|    +---------------+      +------------+      +-------------------+      +-------------------------+    |
|    | Payment Agent | ---> | Risk Agent | ---> | Safety Boundary   | ---> | Executor Agent          |    |
|    |    (Groq)     |      |   (Groq)   |      |  (Deterministic)  |      |   (Registered Tools)    |    |
|    +---------------+      +------------+      +-------------------+      +------------+------------+    |
|                                                                                       |                 |
|                                                                                       v                 |
|    +---------------+      +----------------+      +----------------+     +-------------------------+    |
|    | Verification  | <--- | Recovery Agent | <--- |  Monitor Agent | <-- | Reconciliation Agent   |    |
|    |    & End      |      |     (Groq)     |      | (LLM Supervisor|     |         (Groq)          |    |
|    +---------------+      +----------------+      +----------------+     +-------------------------+    |
+---------------------------------------------------------------------------------------------------------+
               |                                 |                                 |
               v                                 v                                 v
    +--------------------+            +--------------------+            +--------------------+
    |     PostgreSQL     |            |    Redis Streams   |            |     LangSmith      |
    |  Persistent State  |            |   & Distributed    |            | Distributed Trace  |
    |    & Audit Trail   |            |       Locks        |            |   & Observability  |
    +--------------------+            +--------------------+            +--------------------+
```

## Core Architectural Invariants

### 1. Zero Fake Intelligence
- Agents do not use static if/else heuristics as intelligence.
- Reasoning, classification, anomaly diagnosis, and recovery planning are derived through Groq with Pydantic structured schemas (`with_structured_output`).

### 2. Strict Infrastructure & Safety Boundaries
- When Groq is unreachable or fails schema validation, the system **never** fabricates AI responses.
- Instead, the infrastructure detects LLM failure, pauses the AI-dependent workflow, creates an emergency incident in PostgreSQL/Redis, and escalates to human operators.

### 3. Financial Safety & Idempotency
- All operations require unique idempotency keys.
- Deterministic safety policies enforce transaction ceilings and maximum retry limits before any tool touches Razorpay.
