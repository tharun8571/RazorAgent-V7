import hmac
import hashlib
import uuid
from typing import Dict, Any
from app.core.config import settings
from app.core.exceptions import WebhookSignatureError


def generate_id(prefix: str = "id") -> str:
    """Generate a clean, collision-resistant unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def verify_razorpay_webhook_signature(payload_body: bytes, signature: str, secret: str = None) -> bool:
    """
    Verify Razorpay webhook HMAC SHA256 signature.
    Deterministic security check.
    """
    webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET
    if not webhook_secret:
        raise WebhookSignatureError("Razorpay webhook secret is not configured")
    
    if not signature:
        raise WebhookSignatureError("Missing X-Razorpay-Signature header")

    computed_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        raise WebhookSignatureError("Invalid webhook signature")

    return True


def sanitize_for_llm(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strips raw secrets, auth headers, and full card numbers before
    passing context to Groq or LLMs.
    """
    sensitive_keys = {
        "key_secret", "secret", "password", "api_key", "token", "card_number",
        "cvv", "auth_token", "jwt", "private_key"
    }
    
    def _clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "[REDACTED_FOR_LLM]" if k.lower() in sensitive_keys else _clean(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [_clean(item) for item in obj]
        return obj

    return _clean(data)
