import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.agent import PaymentDecision
from app.core.security import sanitize_for_llm


class PaymentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="payment_agent",
            role_description="Analyzes incoming payment requests, validates intent, context, and operational readiness."
        )

    async def evaluate_payment(
        self,
        payment_context: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> PaymentDecision:
        """
        Reason over payment request intent, customer context, currency, and parameters.
        Returns structured PaymentDecision.
        """
        system_prompt = (
            "You are the Payment Agent in RazorAgent V7, an autonomous multi-agent payment operations system.\n"
            "Your role is to understand the payment request and determine the appropriate next operational step.\n"
            "You must reason thoroughly about:\n"
            "- Transaction context, customer profile, and purchase metadata\n"
            "- Payment status and operational intent\n"
            "- Sufficiency and validity of required parameters\n\n"
            "Rules:\n"
            "1. Output must be a valid structured PaymentDecision schema.\n"
            "2. Provide clear, logical reasoning in reasoning_summary explaining why the decision was reached.\n"
            "3. If details are sufficient for risk evaluation, decide 'PROCEED' and recommend 'risk_assessment'.\n"
            "4. If essential parameters are missing, decide 'REQUIRE_ADDITIONAL_INFO' or 'REJECT' with specific requirements."
        )

        sanitized_context = sanitize_for_llm(payment_context)
        human_content = (
            f"Please evaluate the following payment request context:\n"
            f"```json\n{json.dumps(sanitized_context, indent=2)}\n```"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=PaymentDecision,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"payment_context": sanitized_context}
        )
