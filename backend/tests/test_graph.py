import pytest
from unittest.mock import AsyncMock, patch
from app.graph.workflow import run_payment_workflow
from app.graph.state import RazorAgentState
from app.schemas.agent import PaymentDecision, RiskAssessment, ExecutorDecision, ReconciliationResult
from app.schemas.incident import MonitoringDecision
from app.db.database import init_db


@pytest.mark.asyncio
async def test_full_langgraph_workflow_success_path():
    await init_db()

    initial_state: RazorAgentState = {
        "request_id": "req_graph_test_01",
        "payment_id": "pay_graph_01",
        "customer_id": "cust_graph_user",
        "amount": 2499.0,
        "currency": "INR",
        "idempotency_key": "idem_graph_01",
        "method": "upi",
        "workflow_status": "RUNNING",
        "retry_count": 0,
        "events": [],
        "errors": [],
    }

    # Mock all agents to verify graph topology, state mutations, and transitions
    mock_pay_dec = PaymentDecision(
        decision="PROCEED",
        reasoning_summary="Valid order parameters",
        confidence=0.99,
        required_information=[],
        recommended_next_step="risk_assessment",
        tags=["graph_test"]
    )
    mock_risk = RiskAssessment(
        risk_score=0.1,
        risk_level="LOW",
        risk_factors=[],
        reasoning_summary="Clean risk profile",
        recommended_action="APPROVE",
        confidence=0.99
    )
    mock_exec = ExecutorDecision(
        tool_to_execute="create_payment_order",
        tool_arguments={"amount": 2499.0},
        reasoning_summary="Creating order on Razorpay",
        confidence=0.99
    )
    mock_recon = ReconciliationResult(
        status="MATCHED",
        mismatch_type=None,
        likely_cause="State aligned",
        recommended_action="RESOLVE",
        confidence=0.99
    )
    mock_mon = MonitoringDecision(
        system_status="HEALTHY",
        anomaly_detected=False,
        severity="LOW",
        root_cause="All operations nominal",
        recommended_recovery="No recovery required",
        confidence=0.99,
        human_intervention_required=False
    )

    with patch("app.agents.payment_agent.PaymentAgent.evaluate_payment", new_callable=AsyncMock) as p_mock, \
         patch("app.agents.risk_agent.RiskAgent.evaluate_risk", new_callable=AsyncMock) as r_mock, \
         patch("app.agents.executor_agent.ExecutorAgent.decide_execution", new_callable=AsyncMock) as e_mock, \
         patch("app.agents.reconciliation_agent.ReconciliationAgent.reconcile", new_callable=AsyncMock) as rec_mock, \
         patch("app.agents.monitor_agent.MonitorAgent.monitor_system", new_callable=AsyncMock) as m_mock:

        p_mock.return_value = mock_pay_dec
        r_mock.return_value = mock_risk
        e_mock.return_value = mock_exec
        rec_mock.return_value = mock_recon
        m_mock.return_value = mock_mon

        final_state = await run_payment_workflow(initial_state)

        assert final_state["workflow_status"] == "COMPLETED"
        assert final_state["payment_decision"]["decision"] == "PROCEED"
        assert final_state["risk_assessment"]["risk_level"] == "LOW"
        assert final_state["order_id"] is not None
        assert final_state["monitoring_decision"]["system_status"] == "HEALTHY"
