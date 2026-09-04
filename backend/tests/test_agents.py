import pytest
from unittest.mock import AsyncMock, patch
from app.agents.payment_agent import PaymentAgent
from app.agents.risk_agent import RiskAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reconciliation_agent import ReconciliationAgent
from app.agents.monitor_agent import MonitorAgent
from app.agents.recovery_agent import RecoveryAgent
from app.schemas.agent import PaymentDecision, RiskAssessment, ExecutorDecision, ReconciliationResult
from app.schemas.incident import MonitoringDecision, RecoveryPlan


@pytest.mark.asyncio
async def test_payment_agent_structured_reasoning():
    agent = PaymentAgent()
    mock_decision = PaymentDecision(
        decision="PROCEED",
        reasoning_summary="Valid domestic payment request with complete parameters.",
        confidence=0.98,
        required_information=[],
        recommended_next_step="risk_assessment",
        tags=["domestic", "upi"]
    )

    with patch.object(agent, "invoke_structured", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_decision
        res = await agent.evaluate_payment({"amount": 1499.0, "currency": "INR", "method": "upi"})
        assert res.decision == "PROCEED"
        assert res.confidence == 0.98


@pytest.mark.asyncio
async def test_risk_agent_structured_assessment():
    agent = RiskAgent()
    mock_assessment = RiskAssessment(
        risk_score=0.15,
        risk_level="LOW",
        risk_factors=[],
        reasoning_summary="Standard customer profile with low amount.",
        recommended_action="APPROVE",
        confidence=0.95
    )

    with patch.object(agent, "invoke_structured", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_assessment
        res = await agent.evaluate_risk({"amount": 1499.0, "customer_id": "cust_123"})
        assert res.risk_level == "LOW"
        assert res.recommended_action == "APPROVE"


@pytest.mark.asyncio
async def test_monitor_agent_anomaly_diagnosis():
    agent = MonitorAgent()
    mock_mon = MonitoringDecision(
        system_status="DEGRADED",
        anomaly_detected=True,
        anomaly_type="RETRY_LOOP",
        severity="MEDIUM",
        root_cause="Payment gateway transient 504 timeout causing retry loop.",
        evidence={"retry_count": 3},
        recommended_recovery="Pause executor agent and inspect endpoint.",
        confidence=0.92,
        human_intervention_required=False
    )

    with patch.object(agent, "invoke_structured", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_mon
        res = await agent.monitor_system({"retry_count": 3, "errors": ["Gateway timeout"]})
        assert res.anomaly_detected is True
        assert res.anomaly_type == "RETRY_LOOP"


@pytest.mark.asyncio
async def test_recovery_agent_plan_creation():
    agent = RecoveryAgent()
    mock_plan = RecoveryPlan(
        action="pause_agent",
        reason="Prevent further cascade while provider is recovering.",
        expected_effect="Isolates failing component.",
        risk="LOW",
        requires_human_approval=False,
        verification_plan="Wait 30s and poll health endpoint.",
        action_parameters={"agent_name": "executor_agent"}
    )

    mon_decision = MonitoringDecision(
        system_status="DEGRADED",
        anomaly_detected=True,
        root_cause="Provider timeout",
        severity="MEDIUM",
        confidence=0.9,
        recommended_recovery="Pause agent"
    )

    with patch.object(agent, "invoke_structured", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_plan
        res = await agent.plan_recovery(monitoring_decision=mon_decision, incident_context={})
        assert res.action == "pause_agent"
