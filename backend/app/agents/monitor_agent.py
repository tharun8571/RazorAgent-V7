import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.incident import MonitoringDecision
from app.core.security import sanitize_for_llm


class MonitorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="monitor_agent",
            role_description="Supervises overall system execution, detects anomalies across agent outputs and logs, identifies root causes, and assigns severity."
        )

    async def monitor_system(
        self,
        system_context: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> MonitoringDecision:
        """
        Synthesize multi-agent outputs, error logs, latencies, retry counts, and traces.
        """
        system_prompt = (
            "You are the Monitor Agent in RazorAgent V7, the LLM-driven supervisor of the payment platform.\n"
            "You are NOT a fixed rule script. You reason deeply over runtime observations to answer:\n"
            "1. 'What is happening across the agents?'\n"
            "2. 'Is the system behaving normally or is there an anomaly?'\n"
            "3. 'What is the likely root cause of any degradation or failure?'\n"
            "4. 'How severe is it (LOW, MEDIUM, HIGH, CRITICAL)?'\n"
            "5. 'What recovery strategy should be initiated?'\n"
            "6. 'Is human intervention immediately required?'\n\n"
            "Rules:\n"
            "- Return a valid structured MonitoringDecision schema.\n"
            "- If all agents succeeded with normal parameters, set system_status='HEALTHY', anomaly_detected=False, severity='LOW'.\n"
            "- If workflow_status is 'PAUSED_FOR_HUMAN' or 'BLOCKED_RISK', or risk_level is 'HIGH' or 'CRITICAL', or repeated failures occur:\n"
            "  * Set anomaly_detected=True\n"
            "  * Set human_intervention_required=True\n"
            "  * Categorize anomaly_type (e.g. HIGH_RISK_SUSPICION, RETRY_LOOP, LATENCY_SPIKE, RECONCILIATION_DESYNC, PROVIDER_ERROR)\n"
            "  * Extract concrete evidence in the evidence dict\n"
            "  * State the root_cause clearly\n"
            "  * Recommend the next recovery path."
        )

        sanitized_context = sanitize_for_llm(system_context)
        human_content = (
            f"Here is the real-time operational context across agents and infrastructure:\n"
            f"```json\n{json.dumps(sanitized_context, indent=2)}\n```\n"
            f"Please conduct an autonomous supervisory diagnosis."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=MonitoringDecision,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"system_context": sanitized_context}
        )
