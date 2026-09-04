from typing import Dict, Any
from app.core.config import settings
from app.core.exceptions import SafetyPolicyViolation
from app.core.logging import logger


def validate_transaction_safety(amount: float, currency: str = "INR") -> bool:
    """
    Deterministic safety policy: Rejects invalid amounts or amounts exceeding absolute hard safety ceiling.
    """
    if amount <= 0:
        raise SafetyPolicyViolation(f"Transaction amount must be strictly greater than 0. Received: {amount}")

    if currency.upper() == "INR" and amount > settings.MAX_TRANSACTION_AMOUNT_INR:
        raise SafetyPolicyViolation(
            f"Transaction amount {amount} INR exceeds maximum deterministic safety ceiling ({settings.MAX_TRANSACTION_AMOUNT_INR} INR)."
        )

    return True


def check_retry_limit(retry_count: int) -> bool:
    """
    Deterministic safety boundary: Prevents infinite agent retry loops.
    """
    if retry_count >= settings.MAX_AUTO_RETRIES:
        raise SafetyPolicyViolation(
            f"Execution exceeded maximum permitted retry attempts ({settings.MAX_AUTO_RETRIES}). Halting for incident escalation."
        )
    return True
