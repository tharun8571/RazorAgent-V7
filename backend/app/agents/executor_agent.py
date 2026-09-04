import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.agent import ExecutorDecision
from app.core.security import sanitize_for_llm


class ExecutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="executor_agent",
            role_description="Selects and prepares execution payloads for payment provider tools based on state."
        )

    async def decide_execution(
        self,
        execution_context: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> ExecutorDecision:
        """
        LLM reasons over the current transaction lifecycle state and determines which tool and parameters to invoke.
        """
        system_prompt = (
            "You are the Executor Agent in RazorAgent V7.\n"
            "Your role is to analyze the transaction lifecycle state and select the appropriate registered payment tool to execute.\n"
            "Available tools:\n"
            "- create_payment_order: Create an initial order on Razorpay for a new payment.\n"
            "- fetch_payment: Retrieve payment details and verification from Razorpay.\n"
            "- fetch_order: Retrieve order details from Razorpay.\n"
            "- capture_payment: Manually capture an authorized payment if required.\n"
            "- create_refund: Initiate a full or partial refund for a captured payment.\n"
            "- fetch_refund: Inspect refund status.\n"
            "- none: If no immediate tool call is warranted.\n\n"
            "Rules:\n"
            "1. Output must be a valid ExecutorDecision schema.\n"
            "2. Fill in tool_arguments precisely with necessary fields (e.g. amount, currency, receipt/order_id).\n"
            "3. State your reasoning clearly in reasoning_summary.\n"
            "4. CRITICAL: If order_id is null, empty, or missing in the transaction state, NO order has been created on Razorpay yet. You MUST choose 'create_payment_order' as tool_to_execute so an order is created on Razorpay."
        )

        sanitized_context = sanitize_for_llm(execution_context)
        human_content = (
            f"Given the current transaction state:\n"
            f"```json\n{json.dumps(sanitized_context, indent=2)}\n```\n"
            f"Determine the tool and payload to execute."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=ExecutorDecision,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"context": sanitized_context}
        )
