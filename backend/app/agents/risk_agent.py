import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.base import BaseAgent
from app.schemas.agent import RiskAssessment
from app.core.security import sanitize_for_llm


class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="risk_agent",
            role_description="Evaluates transaction risk signals, velocity patterns, device signals, and financial anomalies."
        )

    async def evaluate_risk(
        self,
        transaction_signals: Dict[str, Any],
        request_id: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Synthesizes transaction signals and assigns structured risk scoring.
        """
        system_prompt = (
            "You are the Risk Agent in RazorAgent V7.\n"
            "Your role is to assess transaction risk by reasoning over all available contextual and behavioral signals.\n"
            "Evaluate factors such as:\n"
            "- Amount magnitude and currency anomalies\n"
            "- Customer tenure, past velocity, transaction frequency\n"
            "- Payment method profile (UPI, International Card, NetBanking)\n"
            "- Metadata signals (IP location, device fingerprints, unexpected order patterns)\n\n"
            "Rules:\n"
            "1. Output a structured RiskAssessment schema.\n"
            "2. Assign a continuous risk_score from 0.0 (safest) to 1.0 (highest risk).\n"
            "3. Categorize into risk_level (LOW, MEDIUM, HIGH, CRITICAL).\n"
            "4. Specify risk_factors and provide a comprehensive reasoning_summary.\n"
            "5. CRITICAL RULE: If the amount is abnormally large (e.g., >= 1,000,000 INR), you MUST classify it as HIGH or CRITICAL risk with risk_score > 0.8. A transaction of 500 crore INR (5,000,000,000) MUST receive a risk score close to 1.0.\n"
            "6. CRITICAL RULE: If the customer has past disputes or high transaction frequency (dispute_count > 0), it indicates wash trading or fraud. You MUST classify it as HIGH or CRITICAL risk with risk_score > 0.7.\n"
            "7. If risk is normal/low, recommend 'APPROVE'. If moderately elevated, recommend 'FLAG_FOR_REVIEW' or 'STEP_UP_AUTH'. If high or fraud signals exist, recommend 'BLOCK'."
        )

        sanitized_signals = sanitize_for_llm(transaction_signals)
        human_content = (
            f"Please assess the risk for the following transaction signals:\n"
            f"```json\n{json.dumps(sanitized_signals, indent=2)}\n```"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]

        return await self.invoke_structured(
            schema=RiskAssessment,
            messages=messages,
            request_id=request_id,
            payment_id=payment_id,
            extra_metadata={"signals": sanitized_signals}
        )
