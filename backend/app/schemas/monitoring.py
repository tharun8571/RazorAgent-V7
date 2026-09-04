from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AgentStatusInfo(BaseModel):
    agent_name: str
    status: str = "HEALTHY"  # HEALTHY, BUSY, PAUSED, ERROR
    current_task: Optional[str] = None
    last_active: datetime
    success_rate: float = 1.0
    total_invocations: int = 0
    avg_latency_ms: float = 0.0
    recent_decision_summary: Optional[str] = None
    langsmith_trace_url: Optional[str] = None


class SystemMetricsOverview(BaseModel):
    system_status: str = "HEALTHY"  # HEALTHY, DEGRADED, INCIDENT_ACTIVE
    total_payments: int = 0
    successful_payments: int = 0
    failed_payments: int = 0
    success_rate_percentage: float = 100.0
    recovery_rate_percentage: float = 100.0
    active_incidents_count: int = 0
    total_incidents_count: int = 0
    avg_payment_latency_ms: float = 120.0
    agents: List[AgentStatusInfo] = Field(default_factory=list)


class SystemActivityEvent(BaseModel):
    event_id: str
    timestamp: datetime
    request_id: Optional[str] = None
    agent_name: str
    event_type: str
    severity: str
    message: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class EvaluationScenarioRequest(BaseModel):
    scenario_type: str = Field(
        ...,
        description="Type of test scenario to simulate",
        json_schema_extra={"example": "normal_payment"} # normal_payment, high_risk_fraud, gateway_timeout, reconciliation_mismatch, retry_loop, llm_outage
    )
    customer_id: Optional[str] = "test_cust_01"
    amount: Optional[float] = 2500.0
    custom_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
