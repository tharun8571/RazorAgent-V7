from typing import Dict, Any
from app.core.config import settings
from app.schemas.agent import RiskAssessment
from app.schemas.incident import RecoveryPlan


def check_human_approval_policy(
    risk_assessment: RiskAssessment = None,
    recovery_plan: RecoveryPlan = None,
    action_type: str = None
) -> bool:
    """
    Deterministic policy engine to decide if human-in-the-loop approval is mandatory.
    """
    # 1. High risk threshold check
    if risk_assessment and risk_assessment.risk_score >= settings.HIGH_RISK_THRESHOLD:
        return True

    if risk_assessment and risk_assessment.risk_level in {"HIGH", "CRITICAL"}:
        return True

    # 2. Critical recovery actions
    if recovery_plan:
        if recovery_plan.requires_human_approval:
            return True
        if recovery_plan.action in {"rollback_safe_operation", "pause_agent", "request_human_approval"}:
            return True

    if action_type in {"refund_all", "pause_agent", "manual_override"}:
        return True

    return False
