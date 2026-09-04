# RazorAgent V7 — Multi-Agent Design Specification

## Agent Specifications

### 1. Payment Agent
- **Module**: `app.agents.payment_agent.py`
- **Output Schema**: `PaymentDecision`
- **Responsibilities**: Analyzes transaction context, customer metadata, and currency parameters. Evaluates operational readiness and decides whether to proceed to risk assessment or request missing data.

### 2. Risk Agent
- **Module**: `app.agents.risk_agent.py`
- **Output Schema**: `RiskAssessment`
- **Responsibilities**: Synthesizes velocity signals, device context, and transaction magnitude to assign a continuous risk score (0.0 to 1.0) and categorical risk level (LOW, MEDIUM, HIGH, CRITICAL).

### 3. Executor Agent
- **Module**: `app.agents.executor_agent.py`
- **Output Schema**: `ExecutorDecision`
- **Responsibilities**: Selects the appropriate registered payment tool (`create_payment_order`, `fetch_payment`, `capture_payment`, `create_refund`) and drafts arguments. Tool calls pass deterministic idempotency and safety limits before execution.

### 4. Reconciliation Agent
- **Module**: `app.agents.reconciliation_agent.py`
- **Output Schema**: `ReconciliationResult`
- **Responsibilities**: Cross-checks internal database records, Razorpay API states, and webhooks to detect delta desyncs, missing webhooks, or amount discrepancies.

### 5. Monitor Agent (LLM Supervisor)
- **Module**: `app.agents.monitor_agent.py`
- **Output Schema**: `MonitoringDecision`
- **Responsibilities**: The supervisor of the platform. Synthesizes runtime logs, retry history, errors, and agent decisions to answer: *What is happening? Is this normal? What is the root cause? How severe is it?*

### 6. Recovery Agent
- **Module**: `app.agents.recovery_agent.py`
- **Output Schema**: `RecoveryPlan`
- **Responsibilities**: Takes the Monitor Agent's diagnosis and formulates an optimal mitigation plan (`pause_agent`, `retry_operation`, `rollback_safe_operation`, `request_human_approval`). Enforces human sign-off for financial or high-risk actions.
