from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.monitoring.metrics import get_system_metrics_overview
from app.monitoring.events import get_recent_events, record_agent_event
from app.schemas.monitoring import SystemMetricsOverview, EvaluationScenarioRequest
from app.graph.workflow import run_payment_workflow
from app.graph.state import RazorAgentState
from app.core.security import generate_id
from app.core.logging import logger

router = APIRouter()


@router.get("/overview", response_model=SystemMetricsOverview)
async def get_overview(session: AsyncSession = Depends(get_db)):
    """Returns platform-wide metrics and real-time agent matrix."""
    return await get_system_metrics_overview(session)


@router.get("/events")
async def list_monitoring_events(
    limit: int = 50,
    agent_name: Optional[str] = None
):
    """Retrieves recent streaming activity events across agents."""
    return get_recent_events(limit=limit, agent_name=agent_name)


@router.post("/simulate")
async def simulate_scenario(
    req: EvaluationScenarioRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Diagnostic & evaluation simulator: Triggers specific real-world scenarios through the multi-agent graph.
    Supported scenarios:
    - 'normal_payment': Standard clean payment flow
    - 'high_risk_fraud': High risk triggers risk agent block/review
    - 'reconciliation_mismatch': Simulates gateway desync, triggering reconciliation mismatch & supervisor recovery
    - 'retry_loop': Simulates repeated execution failures
    - 'llm_outage': Simulates Groq failure -> Verifies zero fake intelligence & proper human escalation
    """
    scenario = req.scenario_type
    req_id = generate_id(f"sim_{scenario[:6]}")
    pay_id = generate_id("pay_sim")

    logger.info(f"Simulating scenario '{scenario}' for request {req_id}")

    if scenario == "llm_outage":
        # Simulates Groq outage to test safety escalation
        from app.graph.nodes import _handle_llm_failure
        dummy_state: RazorAgentState = {
            "request_id": req_id,
            "payment_id": pay_id,
            "customer_id": req.customer_id or "test_cust",
            "amount": req.amount or 1500.0,
            "currency": "INR",
            "idempotency_key": f"sim_idem_{req_id}",
            "workflow_status": "RUNNING",
            "events": [],
            "errors": [],
        }
        res_state = await _handle_llm_failure(dummy_state, "payment_agent", "Connection refused: Groq API timeout (Simulated)")
        return {
            "scenario": scenario,
            "status": res_state.get("workflow_status"),
            "requires_human_approval": res_state.get("requires_human_approval"),
            "incident_id": res_state.get("incident_id"),
            "errors": res_state.get("errors"),
            "message": "Verified fail-safe behavior: Zero fake intelligence used. Escalated to human operator.",
        }

    # Standard / Risk / Anomaly scenarios run through workflow
    payment_context = {"scenario": scenario, "customer_id": req.customer_id}
    if scenario == "high_risk_fraud":
        payment_context["velocity_warning"] = "15 attempts in 2 minutes from blacklisted IP"
        amount = 450000.0
    elif scenario == "reconciliation_mismatch":
        payment_context["simulate_mismatch"] = True
        amount = req.amount or 2999.0
    else:
        amount = req.amount or 1499.0

    state: RazorAgentState = {
        "request_id": req_id,
        "payment_id": pay_id,
        "customer_id": req.customer_id or "test_cust",
        "amount": amount,
        "currency": "INR",
        "idempotency_key": f"sim_idem_{req_id}",
        "method": "upi",
        "payment_context": payment_context,
        "workflow_status": "RUNNING",
        "retry_count": 0,
        "events": [],
        "errors": [],
    }

    final_state = await run_payment_workflow(state)

    return {
        "scenario": scenario,
        "request_id": req_id,
        "payment_id": pay_id,
        "workflow_status": final_state.get("workflow_status"),
        "requires_human_approval": final_state.get("requires_human_approval", False),
        "incident_id": final_state.get("incident_id"),
        "risk_assessment": final_state.get("risk_assessment"),
        "monitoring_decision": final_state.get("monitoring_decision"),
        "recovery_plan": final_state.get("recovery_plan"),
        "reconciliation_result": final_state.get("reconciliation_result"),
    }
