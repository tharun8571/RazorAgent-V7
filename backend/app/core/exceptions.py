from typing import Optional, Dict, Any


class RazorAgentException(Exception):
    """Base exception for RazorAgent platform."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMUnavailableError(RazorAgentException):
    """Raised when Groq or LLM provider fails, times out, or returns 5xx/429."""
    pass


class LLMStructuredOutputError(RazorAgentException):
    """Raised when LLM output violates the required Pydantic schema."""
    pass


class SafetyPolicyViolation(RazorAgentException):
    """Raised when an operation violates deterministic safety boundaries."""
    pass


class IdempotencyViolationError(RazorAgentException):
    """Raised when a duplicate financial operation is detected."""
    pass


class RazorpayAPIError(RazorAgentException):
    """Raised when the payment provider returns an error."""
    pass


class WebhookSignatureError(RazorAgentException):
    """Raised when Razorpay webhook HMAC signature verification fails."""
    pass


class HumanApprovalRequired(RazorAgentException):
    """Raised when an action requires explicit human authorization."""
    pass
