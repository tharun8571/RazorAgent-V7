import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.incident import RecoveryPlan, MonitoringDecision
from app.core.security import sanitize_for_llm


class RecoveryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="recovery_agent",
            role_description="Formulates autonomous recovery plans and mitigation strategies based on supervisor diagnoses."
        )

    async def plan_recovery(
        self,
        monitoring_decision: MonitoringDecision,
        incident_context: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> RecoveryPlan:
        """
        Synthesize diagnosis from Monitor Agent and determine the safest recovery plan.
        """
        system_prompt = (
            "You are the Recovery Agent in RazorAgent V7.\n"
            "Your role is to formulate an intelligent recovery plan based on the Monitor Agent's diagnosis and incident context.\n\n"
            "Available recovery capabilities:\n"
            "- 'pause_agent': Temporarily halt a malfunctioning agent to prevent cascading failures.\n"
            "- 'retry_operation': Safely re-attempt an idempotent operation (e.g. after a transient network blip).\n"
            "- 'switch_to_fallback': Route future traffic to secondary provider or degraded safe mode.\n"
            "- 'create_incident': Formally log a trackable incident for asynchronous resolution.\n"
            "- 'request_human_approval': Escalate critical or risky operations to a human operator for sign-off.\n"
            "- 'notify_operator': Send urgent notification without blocking execution.\n"
            "- 'rollback_safe_operation': Undo non-final operations (e.g. initiate refund if captured in error).\n"
            "- 'no_action': If no intervention is required.\n\n"
            "Rules:\n"
            "1. Output must be a valid structured RecoveryPlan schema.\n"
            "2. Reason over risk level and specify requires_human_approval=True if the recovery action involves financial movement, irreversible changes, or high risk.\n"
            "3. Specify a precise verification_plan detailing how success of this recovery action will be measured."
        )

        input_data = {
            "monitoring_decision": monitoring_decision.model_dump(),
            "incident_context": sanitize_for_llm(incident_context),
        }
        human_content = (
            f"Here is the monitor diagnosis and incident context:\n"
            f"```json\n{json.dumps(input_data, indent=2)}\n```\n"
            f"Please formulate the optimal recovery plan."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=RecoveryPlan,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"incident_context": input_data["incident_context"]}
        )
