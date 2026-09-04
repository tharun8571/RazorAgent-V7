# RazorAgent V7

**RazorAgent V7** is an autonomous, LLM-driven multi-agent payment operations and self-healing platform. It demonstrates true multi-agent intelligence where reasoning, diagnosis, risk classification, and recovery planning are performed by LLMs rather than hard-coded heuristics.

---

## 1. Core Design Principles

### No Fake Agent System
All agents (`PaymentAgent`, `RiskAgent`, `ExecutorAgent`, `ReconciliationAgent`, `MonitorAgent`, `RecoveryAgent`) utilize Groq with Pydantic structured outputs (`with_structured_output`). The intelligence is genuinely LLM-driven.

### Fail-Safe Infrastructure Boundary
If Groq is unreachable, encounters rate limits, or fails schema validation:
- **Zero fake intelligence**: The system **never** silently replaces the LLM with `if/else` decision trees.
- **Fail-safe escalation**: The infrastructure halts the AI-dependent decision, records structured logs, creates an emergency incident in the database, preserves transaction state, and escalates to a human operator.

---

## 2. Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), aiosqlite / asyncpg
- **AI & Orchestration**: LangGraph StateGraph, LangChain, Groq LLM (`llama-3.3-70b-versatile`)
- **Observability**: LangSmith Distributed Tracing
- **Payments**: Razorpay API (Test Mode & Sandbox Simulation)
- **Event Streaming & Caching**: Redis Streams & Distributed Locks (with resilient in-memory fallback)
- **Testing**: pytest, pytest-asyncio, pytest-mock, pytest-cov

---

## 3. Project Directory Structure

```text
razoragent-v7/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py        # /health endpoint
│   │   │   │   ├── payments.py      # /payments/create-order, /payments/webhook
│   │   │   │   ├── agents.py        # /agents matrix & details
│   │   │   │   ├── incidents.py     # /incidents query, approve, reject
│   │   │   │   └── monitoring.py    # /monitoring overview, events, simulate
│   │   │   └── dependencies.py
│   │   ├── agents/
│   │   │   ├── base.py              # Centralized Groq caller & LangSmith metadata
│   │   │   ├── payment_agent.py     # Intent & parameter reasoning
│   │   │   ├── risk_agent.py        # Continuous risk assessment & signal synthesis
│   │   │   ├── executor_agent.py    # Registered tool selection
│   │   │   ├── reconciliation_agent.py # Ledger cross-matching
│   │   │   ├── monitor_agent.py     # LLM supervisor & root cause diagnosis
│   │   │   └── recovery_agent.py    # LLM recovery planning & HITL triggers
│   │   ├── graph/
│   │   │   ├── state.py             # RazorAgentState TypedDict
│   │   │   ├── nodes.py             # StateGraph nodes & LLM fail-safe escalation
│   │   │   ├── routing.py           # Conditional routing edges
│   │   │   └── workflow.py          # StateGraph assembly & compilation
│   │   ├── tools/
│   │   │   ├── razorpay/            # Orders, Payments, Refunds tools
│   │   │   ├── database_tools.py    # DB queries & updates
│   │   │   ├── redis_tools.py       # Distributed locks & event streaming
│   │   │   └── notification_tools.py # Operator alerts
│   │   ├── policies/
│   │   │   ├── safety.py            # Monetary ceilings & retry limits
│   │   │   ├── authorization.py     # HITL mandatory triggers
│   │   │   └── idempotency.py       # Duplicate payment prevention
│   │   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── db/                      # SQLAlchemy models & repositories
│   │   └── core/                    # Config, logging, security, LLM factory
│   ├── tests/
│   │   ├── test_agents.py
│   │   ├── test_graph.py
│   │   ├── test_payments.py
│   │   ├── test_monitoring.py
│   │   └── test_safety_and_fallback.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── page.tsx                 # Command Center Dashboard
│   │   ├── payments/page.tsx        # Payments Studio & Ledger
│   │   ├── agents/page.tsx          # Agent Matrix & Trace Inspector
│   │   ├── incidents/page.tsx       # Incident Command Center (HITL)
│   │   └── monitoring/page.tsx      # Real-Time Telemetry & Event Stream
│   ├── components/
│   ├── lib/api.ts                   # Backend API client
│   └── package.json
├── docs/                            # Architecture, Agent Design, Monitoring, API specs
├── docker-compose.yml
├── pytest.ini
└── README.md
```

---

## 4. Quick Start & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- (Optional) Docker & Docker Compose

### 1. Backend Setup

```bash
# In project root
python -m venv .venv
.venv\Scripts\activate      # Windows (or source .venv/bin/activate on Linux/Mac)

pip install -r backend/requirements.txt
```

Create `backend/.env` from `.env.example`:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_your_langsmith_api_key_here
LANGSMITH_PROJECT=razoragent-v7

RAZORPAY_KEY_ID=rzp_test_mockKeyId123
RAZORPAY_KEY_SECRET=mockKeySecret123456789
RAZORPAY_WEBHOOK_SECRET=mockWebhookSecretXYZ

DATABASE_URL=sqlite+aiosqlite:///./razoragent.db
REDIS_URL=redis://localhost:6379/0
```

Run Backend:
```bash
# From workspace root with PYTHONPATH
python -m uvicorn app.main:app --app-dir backend --port 8000 --reload
```
Backend API will be live at `http://localhost:8000`.
Swagger docs: `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Frontend Dashboard will be live at `http://localhost:3000`.

### 3. Run Automated Tests

```bash
pytest backend/tests -v
```
All 11 unit & integration test suites will execute and validate:
- Groq structured outputs
- LangGraph multi-agent orchestration
- Zero fake intelligence fail-safe human escalation
- Razorpay tool execution & webhook HMAC verification
- Deterministic monetary bounds & idempotency guards
- Incident lifecycle & Human-in-the-Loop review

---

## 5. End-to-End Demonstration Guide

1. **Nominal Payment Flow**:
   - Navigate to `http://localhost:3000/payments`
   - Enter Customer ID and Amount (e.g. ₹2,499) -> Click **Execute Payment Flow**.
   - Inspect the live reasoning output from Payment Agent -> Risk Agent -> Executor Agent -> Reconciliation Agent -> Monitor Agent.

2. **Self-Healing Incident & HITL Review**:
   - On the Command Center (`http://localhost:3000/`), find the **Scenario Simulator**.
   - Click **Run Scenario** on *Reconciliation Desync*.
   - The Monitor Agent detects the anomaly, proposes a rollback recovery plan, and creates an incident marked `AWAITING_APPROVAL`.
   - Click **Review & Sign-off** -> Provide operator notes -> Click **Approve & Execute**.
   - The system executes the refund/rollback, updates the database, and resolves the incident.

3. **LLM Outage Fail-Safe Verification (No Fake AI)**:
   - Click **Run Scenario** on *LLM Outage Test*.
   - Observe that the platform refuses to fake agent intelligence, pauses execution, creates an emergency incident, and demands human operator sign-off.
