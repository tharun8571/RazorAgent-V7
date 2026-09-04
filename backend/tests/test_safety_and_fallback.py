import pytest
from unittest.mock import AsyncMock, patch
from app.graph.nodes import _handle_llm_failure, payment_node, safety_boundary_node
from app.graph.state import RazorAgentState
from app.policies.safety import validate_transaction_safety, check_retry_limit
from app.policies.idempotency import enforce_idempotency
from app.db.repositories.payments import PaymentRepository
from app.core.exceptions import SafetyPolicyViolation, IdempotencyViolationError, LLMUnavailableError


@pytest.mark.asyncio
async def test_groq_failure_zero_fake_intelligence_escalation():
    """
    CRITICAL TEST: When Groq fails, the system must NOT fabricate a fake agent answer.
    It must record the failure, create an incident, pause the workflow, and escalate to human.
    """
    initial_state: RazorAgentState = {
        "request_id": "req_test_llm_fail",
        "payment_id": "pay_test_01",
        "customer_id": "cust_fail",
        "amount": 2500.0,
        "currency": "INR",
        "workflow_status": "RUNNING",
        "errors": [],
    }

    # Simulate LLM failure
    state = await _handle_llm_failure(
        initial_state,
        agent_name="payment_agent",
        error_msg="Groq API connection timeout (503 Service Unavailable)"
    )

    # Assertions
    assert state["workflow_status"] == "PAUSED_FOR_HUMAN"
    assert state["requires_human_approval"] is True
    assert state["current_agent"] == "payment_agent"
    assert any("LLM unavailable" in err for err in state["errors"])
    assert state.get("incident_id") is not None


@pytest.mark.asyncio
async def test_deterministic_safety_limits():
    """
    Test deterministic bounds: Excessive amount or negative amount must be blocked.
    """
    # 1. Negative amount
    with pytest.raises(SafetyPolicyViolation):
        validate_transaction_safety(-100.0, "INR")

    # 2. Exceeds ceiling
    with pytest.raises(SafetyPolicyViolation):
        validate_transaction_safety(999999999.0, "INR")

    # 3. Valid amount passes
    assert validate_transaction_safety(1500.0, "INR") is True

    # 4. Retry limit
    with pytest.raises(SafetyPolicyViolation):
        check_retry_limit(5)


@pytest.mark.asyncio
async def test_idempotency_enforcement(test_session):
    """
    Test duplicate payment prevention via idempotency keys.
    """
    repo = PaymentRepository(test_session)
    idempotency_key = "test_idem_unique_123"

    # Create initial payment
    await repo.create_payment(
        payment_id="pay_idem_01",
        customer_id="cust_01",
        amount=500.0,
        currency="INR",
        idempotency_key=idempotency_key
    )
    await test_session.commit()

    # Re-using the same key must raise IdempotencyViolationError
    with pytest.raises(IdempotencyViolationError):
        await enforce_idempotency(test_session, idempotency_key)
