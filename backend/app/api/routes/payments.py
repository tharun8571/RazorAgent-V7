import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from sqlalchemy.future import select
from app.db.models import Payment
from app.db.repositories.payments import PaymentRepository
from app.db.repositories.agents import AgentRepository
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.graph.workflow import run_payment_workflow
from app.graph.state import RazorAgentState
from app.policies.idempotency import enforce_idempotency
from app.core.security import generate_id, verify_razorpay_webhook_signature
from app.core.logging import logger
from app.core.config import settings
from app.core.exceptions import IdempotencyViolationError, WebhookSignatureError

router = APIRouter()


@router.post("/create-order", response_model=Dict[str, Any])
async def create_payment_order(
    req: PaymentCreateRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Initiates payment workflow:
    1. Deterministic idempotency verification
    2. Persists initial payment entity in database
    3. Triggers LangGraph multi-agent orchestration (Payment -> Risk -> Safety -> Executor -> Reconciliation -> Monitor)
    4. Returns complete execution result with AI decisions and trace info.
    """
    # 1. Idempotency Check
    try:
        await enforce_idempotency(session, req.idempotency_key)
    except IdempotencyViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    payment_id = generate_id("pay")
    request_id = generate_id("req")

    payment_repo = PaymentRepository(session)
    agent_repo = AgentRepository(session)

    # Explicit dispute_count and error_code from request/metadata
    dispute_count = req.dispute_count if req.dispute_count is not None else (req.metadata or {}).get("dispute_count", 0)
    error_code = req.error_code or (req.metadata or {}).get("error_code")

    # 2. Persist Initial Payment
    payment = await payment_repo.create_payment(
        payment_id=payment_id,
        customer_id=req.customer_id,
        amount=req.amount,
        currency=req.currency,
        idempotency_key=req.idempotency_key,
        method=req.method,
        error_code=error_code,
        dispute_count=dispute_count,
        metadata=req.metadata,
    )
    await session.commit()

    # 3. Create Agent Run Record
    await agent_repo.create_run(
        run_id=generate_id("run"),
        request_id=request_id,
        payment_id=payment_id,
        current_agent="payment_agent"
    )
    await session.commit()

    # 4. Prepare Initial LangGraph State
    initial_state: RazorAgentState = {
        "request_id": request_id,
        "payment_id": payment_id,
        "customer_id": req.customer_id,
        "amount": req.amount,
        "currency": req.currency,
        "idempotency_key": req.idempotency_key,
        "method": req.method,
        "payment_context": {
            "customer_id": req.customer_id,
            "description": req.description,
            "metadata": req.metadata,
            "error_code": error_code,
            "dispute_count": dispute_count,
        },
        "workflow_status": "RUNNING",
        "retry_count": 0,
        "events": [],
        "errors": [],
    }

    # 5. Run LangGraph Multi-Agent Orchestration
    final_state = await run_payment_workflow(initial_state)

    # 6. Fetch updated record
    updated_payment = await payment_repo.get_by_id(payment_id)

    return {
        "payment_id": payment_id,
        "request_id": request_id,
        "order_id": final_state.get("order_id"),
        "status": updated_payment.status if updated_payment else "created",
        "workflow_status": final_state.get("workflow_status"),
        "requires_human_approval": final_state.get("requires_human_approval", False),
        "incident_id": final_state.get("incident_id"),
        "risk_assessment": final_state.get("risk_assessment"),
        "payment_decision": final_state.get("payment_decision"),
        "execution_result": final_state.get("execution_result"),
        "reconciliation_result": final_state.get("reconciliation_result"),
        "monitoring_decision": final_state.get("monitoring_decision"),
        "errors": final_state.get("errors", []),
    }


@router.post("/run-test", response_model=Dict[str, Any])
async def run_test_transaction(
    amount: float = 500.0,
    currency: str = "INR",
    customer_id: str = "cust_test_001",
    method: str = "upi",
    session: AsyncSession = Depends(get_db),
):
    """
    Fires a REAL end-to-end test transaction through the full multi-agent pipeline:
    1. Creates a real Razorpay order via the API (test mode)
    2. Routes through all agents: Payment -> Risk -> Safety -> Executor -> Reconciliation -> Monitor
    3. Uses ChatNVIDIA (moonshotai/kimi-k3) for all agent reasoning
    4. Traces everything to LangSmith
    No manual test cases or mocks — real API keys required.
    """
    import uuid
    idempotency_key = f"test_{uuid.uuid4().hex[:12]}"
    payment_id = generate_id("pay")
    request_id = generate_id("req")

    payment_repo = PaymentRepository(session)
    agent_repo = AgentRepository(session)

    dispute_count = 0
    error_code = None

    await payment_repo.create_payment(
        payment_id=payment_id,
        customer_id=customer_id,
        amount=amount,
        currency=currency,
        idempotency_key=idempotency_key,
        method=method,
        error_code=error_code,
        dispute_count=dispute_count,
        metadata={"source": "run-test-endpoint", "test": True},
    )
    await session.commit()

    await agent_repo.create_run(
        run_id=generate_id("run"),
        request_id=request_id,
        payment_id=payment_id,
        current_agent="payment_agent"
    )
    await session.commit()

    initial_state: RazorAgentState = {
        "request_id": request_id,
        "payment_id": payment_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "idempotency_key": idempotency_key,
        "method": method,
        "payment_context": {
            "customer_id": customer_id,
            "description": "Test Transaction",
            "metadata": {"source": "run-test-endpoint", "test": True},
            "error_code": error_code,
            "dispute_count": dispute_count,
        },
        "workflow_status": "RUNNING",
        "retry_count": 0,
        "events": [],
        "errors": [],
    }

    final_state = await run_payment_workflow(initial_state)
    updated_payment = await payment_repo.get_by_id(payment_id)

    return {
        "payment_id": payment_id,
        "request_id": request_id,
        "order_id": final_state.get("order_id"),
        "status": updated_payment.status if updated_payment else "created",
        "workflow_status": final_state.get("workflow_status"),
        "requires_human_approval": final_state.get("requires_human_approval", False),
        "incident_id": final_state.get("incident_id"),
        "risk_assessment": final_state.get("risk_assessment"),
        "payment_decision": final_state.get("payment_decision"),
        "execution_result": final_state.get("execution_result"),
        "reconciliation_result": final_state.get("reconciliation_result"),
        "monitoring_decision": final_state.get("monitoring_decision"),
        "errors": final_state.get("errors", []),
        "groq_model": settings.GROQ_MODEL,
        "razorpay_mode": "test",
    }


@router.post("/webhook")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    session: AsyncSession = Depends(get_db),
):
    """
    Secure Razorpay Webhook Handler:
    1. Verifies HMAC-SHA256 signature
    2. Persists payment event
    3. Updates payment state
    """
    raw_body = await request.body()
    try:
        verify_razorpay_webhook_signature(raw_body, x_razorpay_signature)
    except WebhookSignatureError as e:
        logger.warning(f"Rejected unverified webhook: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        body_json = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = body_json.get("event", "unknown")
    payload_data = body_json.get("payload", {})
    payment_entity = payload_data.get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id") or generate_id("pay_web")

    repo = PaymentRepository(session)
    await repo.add_event(
        event_id=generate_id("evt_web"),
        payment_id=payment_id,
        event_type=f"webhook.{event_type}",
        source="webhook",
        payload=body_json
    )
    await session.commit()

    return {"status": "received", "event": event_type, "payment_id": payment_id}


@router.get("/", response_model=List[Dict[str, Any]])
async def list_payments(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
):
    """Lists recent payment transactions."""
    repo = PaymentRepository(session)
    payments = await repo.list_payments(limit=limit, offset=offset)
    return [
        {
            "payment_id": p.payment_id,
            "order_id": p.order_id,
            "customer_id": p.customer_id,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "method": p.method,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "idempotency_key": p.idempotency_key,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in payments
    ]


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Retrieves payment details by ID."""
    repo = PaymentRepository(session)
    payment = await repo.get_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "method": payment.method,
        "risk_score": payment.risk_score,
        "risk_level": payment.risk_level,
        "idempotency_key": payment.idempotency_key,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
    }
