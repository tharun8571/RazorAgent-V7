from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.incidents import IncidentRepository
from app.db.repositories.payments import PaymentRepository
from app.schemas.incident import MonitoringDecision, RecoveryPlan
from app.core.security import generate_id
from app.core.logging import logger
from app.monitoring.events import record_agent_event
from app.tools.razorpay.refunds import create_refund_tool


class IncidentManager:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.incident_repo = IncidentRepository(session)
        self.payment_repo = PaymentRepository(session)

    async def create_incident_from_monitoring(
        self,
        request_id: str,
        title: str,
        monitoring_decision: MonitoringDecision,
        recovery_plan: Optional[RecoveryPlan] = None,
        detected_by: str = "monitor_agent",
    ) -> str:
        """
        Creates an incident in the database based on LLM Monitor diagnosis.
        """
        incident_id = generate_id("inc")
        status = "AWAITING_APPROVAL" if (recovery_plan and recovery_plan.requires_human_approval) else "OPEN"

        await self.incident_repo.create_incident(
            incident_id=incident_id,
            title=title,
            severity=monitoring_decision.severity,
            detected_by=detected_by,
            root_cause=monitoring_decision.root_cause,
            evidence=monitoring_decision.evidence,
            recovery_plan=recovery_plan.model_dump() if recovery_plan else {},
            human_review_required=recovery_plan.requires_human_approval if recovery_plan else False,
            status=status,
        )

        await record_agent_event(
            agent_name=detected_by,
            event_type="incident.created",
            request_id=request_id,
            severity=monitoring_decision.severity,
            payload={"incident_id": incident_id, "title": title, "root_cause": monitoring_decision.root_cause}
        )

        await self.payment_repo.log_audit(
            log_id=generate_id("aud"),
            actor=detected_by,
            action="create_incident",
            resource_type="incident",
            resource_id=incident_id,
            details={"title": title, "severity": monitoring_decision.severity}
        )

        return incident_id

    async def approve_incident_recovery(self, incident_id: str, operator_name: str, reason: str) -> Dict[str, Any]:
        """
        Human-in-the-loop: Operator approves a pending recovery action.
        Executes the approved recovery plan deterministically.
        """
        incident = await self.incident_repo.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        logger.info(f"Operator {operator_name} approved recovery for incident {incident_id}: {reason}")

        # Update incident status
        await self.incident_repo.update_incident(
            incident_id=incident_id,
            status="MITIGATING"
        )

        # Parse recovery plan
        import json
        plan_dict = json.loads(incident.recovery_plan_json or "{}")
        action_type = plan_dict.get("action", "no_action")
        action_params = plan_dict.get("action_parameters", {})

        action_id = generate_id("act")
        result: Dict[str, Any] = {"status": "EXECUTED", "executed_by": operator_name}

        try:
            if action_type == "rollback_safe_operation":
                payment_id = action_params.get("payment_id")
                if payment_id:
                    refund_res = await create_refund_tool(payment_id=payment_id)
                    result["refund_response"] = refund_res
            elif action_type == "pause_agent":
                agent_to_pause = action_params.get("agent_name", "executor_agent")
                result["paused_agent"] = agent_to_pause
            elif action_type == "retry_operation":
                result["retry_scheduled"] = True
            
            await self.incident_repo.add_recovery_action(
                action_id=action_id,
                incident_id=incident_id,
                action_type=action_type,
                status="EXECUTED",
                parameters=action_params,
                result=result,
                executed_by=operator_name
            )

            await self.incident_repo.update_incident(
                incident_id=incident_id,
                status="RESOLVED",
                recovery_result=result,
                resolved=True
            )

            await self.payment_repo.log_audit(
                log_id=generate_id("aud"),
                actor=operator_name,
                action="approve_recovery",
                resource_type="incident",
                resource_id=incident_id,
                details={"reason": reason, "recovery_result": result}
            )

            return {"status": "success", "incident_id": incident_id, "action_result": result}
        except Exception as e:
            logger.error(f"Failed to execute approved recovery action: {str(e)}", exc_info=True)
            await self.incident_repo.update_incident(
                incident_id=incident_id,
                status="OPEN",
                recovery_result={"error": str(e)}
            )
            raise

    async def reject_incident_recovery(self, incident_id: str, operator_name: str, reason: str) -> Dict[str, Any]:
        """
        Human-in-the-loop: Operator rejects a proposed recovery action.
        """
        incident = await self.incident_repo.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        await self.incident_repo.update_incident(
            incident_id=incident_id,
            status="REJECTED",
            recovery_result={"rejection_reason": reason, "rejected_by": operator_name}
        )

        await self.payment_repo.log_audit(
            log_id=generate_id("aud"),
            actor=operator_name,
            action="reject_recovery",
            resource_type="incident",
            resource_id=incident_id,
            details={"reason": reason}
        )

        return {"status": "rejected", "incident_id": incident_id, "reason": reason}
