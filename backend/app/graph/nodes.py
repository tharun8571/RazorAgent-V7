import json
from typing import Dict, Any
from app.graph.state import RazorAgentState
from app.agents.payment_agent import PaymentAgent
from app.agents.risk_agent import RiskAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.reconciliation_agent import ReconciliationAgent
from app.agents.monitor_agent import MonitorAgent
from app.agents.recovery_agent import RecoveryAgent
from app.tools.razorpay.orders import create_payment_order_tool
from app.tools.razorpay.payments import fetch_payment_tool, capture_payment_tool
from app.tools.razorpay.refunds import create_refund_tool
from app.tools.database_tools import update_payment_db_tool
from app.policies.safety import validate_transaction_safety, check_retry_limit
from app.policies.authorization import check_human_approval_policy
from app.monitoring.events import record_agent_event
from app.monitoring.metrics import record_agent_activity
from app.monitoring.incident_manager import IncidentManager
from app.schemas.incident import MonitoringDecision, RecoveryPlan
from app.db.database import AsyncSessionLocal
from app.core.exceptions import LLMUnavailableError, SafetyPolicyViolation
from app.core.logging import logger

payment_agent = PaymentAgent()
risk_agent = RiskAgent()
executor_agent = ExecutorAgent()
reconciliation_agent = ReconciliationAgent()
monitor_agent = MonitorAgent()
recovery_agent = RecoveryAgent()


async def _handle_llm_failure(state: RazorAgentState, agent_name: str, error_msg: str) -> RazorAgentState:
    """
    CRITICAL SAFETY REQUIREMENT:
    When Groq/LLM is unavailable, NEVER simulate fake fallback intelligence.
    Record failure, create an incident, pause AI-dependent workflow, and escalate to human.
    """
    logger.critical(
        f"CRITICAL: LLM Provider failure in {agent_name}. Halting workflow and escalating to human operator. Error: {error_msg}",
        extra={"agent": agent_name, "request_id": state.get("request_id"), "error": error_msg}
    )

    req_id = state.get("request_id", "unknown_req")
    errors = state.get("errors", [])
    errors.append(f"[{agent_name}] LLM unavailable: {error_msg}")

    # Record agent event
    await record_agent_event(
        agent_name=agent_name,
        event_type=f"{agent_name}.llm_failure",
        request_id=req_id,
        severity="CRITICAL",
        payload={"error": error_msg, "reason": "Groq LLM service failure or invalid configuration"}
    )
    record_agent_activity(agent_name, status="ERROR", is_error=True, decision="LLM Failure — Halting for Human Escalation")

    # Create emergency incident in DB
    try:
        async with AsyncSessionLocal() as session:
            mgr = IncidentManager(session)
            monitoring_decision = MonitoringDecision(
                system_status="CRITICAL_ANOMALY",
                anomaly_detected=True,
                anomaly_type="LLM_PROVIDER_OUTAGE",
                severity="CRITICAL",
                root_cause=f"Groq LLM failure in {agent_name}: {error_msg}",
                evidence={"failed_agent": agent_name, "error": error_msg},
                recommended_recovery="Pause AI workflow and require human operator intervention.",
                confidence=1.0,
                human_intervention_required=True
            )
            recovery_plan = RecoveryPlan(
                action="request_human_approval",
                reason="LLM provider is unreachable; safety boundary forbids un-reasoned execution.",
                expected_effect="Prevents arbitrary unverified payment execution.",
                risk="HIGH",
                requires_human_approval=True,
                verification_plan="Human operator inspects LLM connectivity and approves manually.",
                action_parameters={"agent_name": agent_name, "request_id": req_id}
            )
            incident_id = await mgr.create_incident_from_monitoring(
                request_id=req_id,
                title=f"LLM Failure in {agent_name}: Human Review Required",
                monitoring_decision=monitoring_decision,
                recovery_plan=recovery_plan,
                detected_by="safety_infrastructure"
            )
            await session.commit()
            state["incident_id"] = incident_id
    except Exception as e:
        logger.error(f"Failed to record LLM emergency incident: {str(e)}")

    state["workflow_status"] = "PAUSED_FOR_HUMAN"
    state["requires_human_approval"] = True
    state["current_agent"] = agent_name
    state["errors"] = errors
    return state


async def payment_node(state: RazorAgentState) -> RazorAgentState:
    state["current_agent"] = "payment_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    # Zero-latency deterministic safety pre-check (bypasses LLM network call for invalid amounts)
    try:
        validate_transaction_safety(state.get("amount", 0), state.get("currency", "INR"))
    except SafetyPolicyViolation as e:
        state["workflow_status"] = "REJECTED"
        state["errors"] = state.get("errors", []) + [f"Safety boundary pre-check: {str(e)}"]
        return state

    try:
        context = state.get("payment_context", {})
        context.update({
            "amount": state.get("amount"),
            "currency": state.get("currency"),
            "customer_id": state.get("customer_id"),
            "idempotency_key": state.get("idempotency_key"),
            "method": state.get("method"),
        })

        decision = await payment_agent.evaluate_payment(
            payment_context=context,
            request_id=req_id,
            payment_id=pay_id
        )
        state["payment_decision"] = decision.model_dump()

        await record_agent_event(
            agent_name="payment_agent",
            event_type="payment_agent.decision",
            request_id=req_id,
            severity="INFO",
            payload=decision.model_dump()
        )
        record_agent_activity("payment_agent", status="HEALTHY", decision=f"Decision: {decision.decision}")

        if decision.decision == "REJECT":
            state["workflow_status"] = "REJECTED"
        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "payment_agent", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in payment_node: {str(e)}", exc_info=True)
        return await _handle_llm_failure(state, "payment_agent", str(e))


async def risk_node(state: RazorAgentState) -> RazorAgentState:
    if state.get("workflow_status") in {"PAUSED_FOR_HUMAN", "REJECTED"}:
        return state

    state["current_agent"] = "risk_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    try:
        signals = {
            "amount": state.get("amount"),
            "currency": state.get("currency"),
            "customer_id": state.get("customer_id"),
            "method": state.get("method"),
            "payment_decision": state.get("payment_decision"),
            "payment_context": state.get("payment_context", {}),
        }

        assessment = await risk_agent.evaluate_risk(
            transaction_signals=signals,
            request_id=req_id,
            payment_id=pay_id
        )
        state["risk_assessment"] = assessment.model_dump()

        await record_agent_event(
            agent_name="risk_agent",
            event_type="risk_agent.assessment",
            request_id=req_id,
            severity="WARN" if assessment.risk_level in {"HIGH", "CRITICAL"} else "INFO",
            payload=assessment.model_dump()
        )
        record_agent_activity("risk_agent", status="HEALTHY", decision=f"Risk: {assessment.risk_level} ({assessment.risk_score})")

        # Deterministic Policy Check: High Risk Gate
        if assessment.risk_level in {"HIGH", "CRITICAL"} or assessment.recommended_action in {"BLOCK", "FLAG_FOR_REVIEW", "STEP_UP_AUTH"} or check_human_approval_policy(risk_assessment=assessment):
            state["workflow_status"] = "PAUSED_FOR_HUMAN"
            state["requires_human_approval"] = True
        elif assessment.risk_level == "CRITICAL" or assessment.recommended_action == "BLOCK":
            state["workflow_status"] = "BLOCKED_RISK"

        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "risk_agent", str(e))
    except Exception as e:
        logger.error(f"Unexpected error in risk_node: {str(e)}", exc_info=True)
        return await _handle_llm_failure(state, "risk_agent", str(e))


async def safety_boundary_node(state: RazorAgentState) -> RazorAgentState:
    """
    Deterministic safety policy: Enforces monetary bounds, retries limits, and schema validation.
    """
    req_id = state.get("request_id", "")
    try:
        validate_transaction_safety(state.get("amount", 0), state.get("currency", "INR"))
        check_retry_limit(state.get("retry_count", 0))
    except SafetyPolicyViolation as e:
        logger.warning(f"Safety policy violation: {str(e)}")
        state["workflow_status"] = "PAUSED_FOR_HUMAN"
        state["requires_human_approval"] = True
        state["errors"] = state.get("errors", []) + [f"Safety boundary: {str(e)}"]

        await record_agent_event(
            agent_name="safety_boundary",
            event_type="safety.violation",
            request_id=req_id,
            severity="HIGH",
            payload={"violation": str(e)}
        )
    return state


async def executor_node(state: RazorAgentState) -> RazorAgentState:
    if state.get("workflow_status") in {"PAUSED_FOR_HUMAN", "REJECTED", "BLOCKED_RISK"}:
        return state

    state["current_agent"] = "executor_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    try:
        exec_context = {
            "amount": state.get("amount"),
            "currency": state.get("currency"),
            "payment_id": pay_id,
            "order_id": state.get("order_id"),
            "risk_assessment": state.get("risk_assessment"),
            "status": state.get("workflow_status"),
        }

        decision = await executor_agent.decide_execution(
            execution_context=exec_context,
            request_id=req_id,
            payment_id=pay_id
        )
        state["executor_decision"] = decision.model_dump()

        # Tool execution boundary
        tool_name = decision.tool_to_execute
        tool_args = decision.tool_arguments or {}
        exec_result: Dict[str, Any] = {}

        if tool_name == "create_payment_order":
            order = await create_payment_order_tool(
                amount=state.get("amount", 0),
                currency=state.get("currency", "INR"),
                receipt=f"rcpt_{req_id[:8]}"
            )
            state["order_id"] = order.get("id")
            exec_result = order
        elif tool_name == "fetch_payment":
            exec_result = await fetch_payment_tool(pay_id or tool_args.get("payment_id", ""))
        elif tool_name == "capture_payment":
            exec_result = await capture_payment_tool(
                payment_id=pay_id or tool_args.get("payment_id", ""),
                amount=state.get("amount", 0),
                currency=state.get("currency", "INR")
            )
        elif tool_name == "create_refund":
            exec_result = await create_refund_tool(
                payment_id=pay_id or tool_args.get("payment_id", ""),
                amount=state.get("amount", 0)
            )
        else:
            exec_result = {"status": "NOOP", "message": "No tool requested"}

        state["execution_result"] = exec_result

        # Update DB
        if pay_id:
            await update_payment_db_tool(
                payment_id=pay_id,
                status="captured" if tool_name == "capture_payment" else "created",
                risk_score=state.get("risk_assessment", {}).get("risk_score"),
                risk_level=state.get("risk_assessment", {}).get("risk_level"),
                order_id=state.get("order_id")
            )

        await record_agent_event(
            agent_name="executor_agent",
            event_type="executor.tool_executed",
            request_id=req_id,
            severity="INFO",
            payload={"tool": tool_name, "result": exec_result}
        )
        record_agent_activity("executor_agent", status="HEALTHY", decision=f"Tool: {tool_name}")
        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "executor_agent", str(e))
    except Exception as e:
        logger.error(f"Execution error in executor_node: {str(e)}", exc_info=True)
        state["errors"] = state.get("errors", []) + [f"Executor error: {str(e)}"]
        state["workflow_status"] = "EXECUTION_ERROR"
        return state


async def reconciliation_node(state: RazorAgentState) -> RazorAgentState:
    if state.get("workflow_status") in {"PAUSED_FOR_HUMAN", "REJECTED", "BLOCKED_RISK"}:
        return state

    state["current_agent"] = "reconciliation_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    try:
        recon_data = {
            "internal_db_state": {
                "amount": state.get("amount"),
                "currency": state.get("currency"),
                "payment_id": pay_id,
                "order_id": state.get("order_id"),
            },
            "gateway_execution_result": state.get("execution_result"),
            "events_count": len(state.get("events", [])),
        }

        result = await reconciliation_agent.reconcile(
            reconciliation_data=recon_data,
            request_id=req_id,
            payment_id=pay_id
        )
        state["reconciliation_result"] = result.model_dump()

        await record_agent_event(
            agent_name="reconciliation_agent",
            event_type="reconciliation.completed",
            request_id=req_id,
            severity="WARN" if result.status == "MISMATCH_DETECTED" else "INFO",
            payload=result.model_dump()
        )
        record_agent_activity("reconciliation_agent", status="HEALTHY", decision=f"Status: {result.status}")
        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "reconciliation_agent", str(e))
    except Exception as e:
        logger.error(f"Reconciliation error: {str(e)}", exc_info=True)
        return state


async def monitor_node(state: RazorAgentState) -> RazorAgentState:
    state["current_agent"] = "monitor_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    try:
        system_context = {
            "request_id": req_id,
            "payment_id": pay_id,
            "workflow_status": state.get("workflow_status"),
            "payment_decision": state.get("payment_decision"),
            "risk_assessment": state.get("risk_assessment"),
            "execution_result": state.get("execution_result"),
            "reconciliation_result": state.get("reconciliation_result"),
            "retry_count": state.get("retry_count", 0),
            "errors": state.get("errors", []),
        }

        mon_decision = await monitor_agent.monitor_system(
            system_context=system_context,
            request_id=req_id,
            payment_id=pay_id
        )
        state["monitoring_decision"] = mon_decision.model_dump()

        await record_agent_event(
            agent_name="monitor_agent",
            event_type="monitor.supervision",
            request_id=req_id,
            severity=mon_decision.severity,
            payload=mon_decision.model_dump()
        )
        record_agent_activity("monitor_agent", status="HEALTHY", decision=f"Diagnosis: {mon_decision.root_cause[:60]}")

        if mon_decision.human_intervention_required:
            state["requires_human_approval"] = True
            state["workflow_status"] = "PAUSED_FOR_HUMAN"

        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "monitor_agent", str(e))
    except Exception as e:
        logger.error(f"Monitor error: {str(e)}", exc_info=True)
        return state


async def recovery_node(state: RazorAgentState) -> RazorAgentState:
    mon_decision_data = state.get("monitoring_decision")
    if not mon_decision_data or not mon_decision_data.get("anomaly_detected"):
        return state

    state["current_agent"] = "recovery_agent"
    req_id = state.get("request_id", "")
    pay_id = state.get("payment_id", "")

    try:
        mon_decision = MonitoringDecision.model_validate(mon_decision_data)
        plan = await recovery_agent.plan_recovery(
            monitoring_decision=mon_decision,
            incident_context={
                "request_id": req_id,
                "payment_id": pay_id,
                "workflow_status": state.get("workflow_status"),
                "errors": state.get("errors", []),
            },
            request_id=req_id,
            payment_id=pay_id
        )
        state["recovery_plan"] = plan.model_dump()

        # Enforce human approval policy
        requires_approval = (
            state.get("requires_human_approval", False)
            or (plan and plan.requires_human_approval)
            or check_human_approval_policy(recovery_plan=plan)
            or state.get("workflow_status") == "PAUSED_FOR_HUMAN"
        )
        state["requires_human_approval"] = requires_approval

        # Create Incident in DB
        async with AsyncSessionLocal() as session:
            mgr = IncidentManager(session)
            inc_id = await mgr.create_incident_from_monitoring(
                request_id=req_id,
                title=f"Anomaly: {mon_decision.anomaly_type or 'Payment Incident'}",
                monitoring_decision=mon_decision,
                recovery_plan=plan,
                detected_by="monitor_agent"
            )
            await session.commit()
            state["incident_id"] = inc_id

        await record_agent_event(
            agent_name="recovery_agent",
            event_type="recovery.plan_created",
            request_id=req_id,
            severity="WARN" if requires_approval else "INFO",
            payload=plan.model_dump()
        )
        record_agent_activity("recovery_agent", status="HEALTHY", decision=f"Plan: {plan.action}")

        if requires_approval:
            state["workflow_status"] = "PAUSED_FOR_HUMAN"
        else:
            state["workflow_status"] = "RECOVERED"

        return state

    except LLMUnavailableError as e:
        return await _handle_llm_failure(state, "recovery_agent", str(e))
    except Exception as e:
        logger.error(f"Recovery agent error: {str(e)}", exc_info=True)
        return state


async def verification_node(state: RazorAgentState) -> RazorAgentState:
    """Final verification node in the closed self-healing loop."""
    wf_status = state.get("workflow_status")
    if state.get("requires_human_approval"):
        state["workflow_status"] = "PAUSED_FOR_HUMAN"
        wf_status = "PAUSED_FOR_HUMAN"
    elif wf_status not in {"PAUSED_FOR_HUMAN", "BLOCKED_RISK", "REJECTED"}:
        state["workflow_status"] = "COMPLETED"
        wf_status = "COMPLETED"

    pay_id = state.get("payment_id")
    if pay_id:
        risk_assessment = state.get("risk_assessment", {})
        db_status = "failed" if wf_status in {"REJECTED", "BLOCKED_RISK"} else ("captured" if state.get("order_id") else "created")
        await update_payment_db_tool(
            payment_id=pay_id,
            status=db_status,
            risk_score=risk_assessment.get("risk_score"),
            risk_level=risk_assessment.get("risk_level", "low"),
            order_id=state.get("order_id")
        )

    req_id = state.get("request_id", "")
    await record_agent_event(
        agent_name="system_supervisor",
        event_type="workflow.completed",
        request_id=req_id,
        severity="INFO",
        payload={"final_status": state.get("workflow_status"), "incident_id": state.get("incident_id")}
    )
    return state
