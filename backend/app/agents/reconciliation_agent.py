import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.agent import ReconciliationResult
from app.core.security import sanitize_for_llm


class ReconciliationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="reconciliation_agent",
            role_description="Cross-references internal database records, Razorpay API states, and webhook events to detect discrepancies."
        )

    async def reconcile(
        self,
        reconciliation_data: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> ReconciliationResult:
        """
        Reason over internal DB records, gateway responses, and webhook records.
        """
        system_prompt = (
            "You are the Reconciliation Agent in RazorAgent V7.\n"
            "Your role is to compare state across three primary sources:\n"
            "1. Internal Database Record (our source of persistent truth)\n"
            "2. Razorpay Payment Gateway State (direct API fetch)\n"
            "3. Webhook Events received\n\n"
            "Rules:\n"
            "1. Output a structured ReconciliationResult schema.\n"
            "2. If all sources agree on amounts, currencies, and completion states, set status='MATCHED' and recommended_action='RESOLVE'.\n"
            "3. If there is a desync (e.g. gateway shows captured but internal is created, or webhook was dropped, or amount mismatch):\n"
            "   - Set status='MISMATCH_DETECTED'\n"
            "   - Identify mismatch_type (e.g. STATE_DESYNC, AMOUNT_MISMATCH, MISSING_WEBHOOK, GATEWAY_TIMEOUT)\n"
            "   - Provide concrete evidence in evidence dict\n"
            "   - Explain likely_cause\n"
            "   - Recommend action (e.g. 'CREATE_INCIDENT', 'RETRY_FETCH', 'ESCALATE_OPERATOR')"
        )

        sanitized_data = sanitize_for_llm(reconciliation_data)
        human_content = (
            f"Please perform reconciliation analysis on the following source data:\n"
            f"```json\n{json.dumps(sanitized_data, indent=2)}\n```"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=ReconciliationResult,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"reconciliation_sources": sanitized_data}
        )
