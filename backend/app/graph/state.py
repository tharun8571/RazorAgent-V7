from typing import Optional, Dict, Any, List, TypedDict


class RazorAgentState(TypedDict, total=False):
    """
    Shared orchestration state across all LangGraph nodes in RazorAgent V7.
    Strictly free of API keys or raw secrets.
    """
    # Core Identifiers
    request_id: str
    payment_id: Optional[str]
    order_id: Optional[str]
    customer_id: str
    amount: float
    currency: str
    idempotency_key: str
    method: Optional[str]

    # Structured Agent Reasoning Outputs
    payment_context: Dict[str, Any]
    payment_decision: Optional[Dict[str, Any]]
    risk_assessment: Optional[Dict[str, Any]]
    executor_decision: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]
    reconciliation_result: Optional[Dict[str, Any]]
    monitoring_decision: Optional[Dict[str, Any]]
    recovery_plan: Optional[Dict[str, Any]]
    recovery_result: Optional[Dict[str, Any]]

    # Workflow & Incident Tracking
    current_agent: str
    workflow_status: str  # RUNNING, APPROVED, BLOCKED_RISK, PAUSED_FOR_HUMAN, COMPLETED, FAILED, RECOVERED
    requires_human_approval: bool
    incident_id: Optional[str]
    retry_count: int
    events: List[Dict[str, Any]]
    errors: List[str]
    trace_id: Optional[str]
