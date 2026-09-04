from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class PaymentDecision(BaseModel):
    """Structured decision output from Payment Agent."""
    decision: Literal["PROCEED", "REVISE", "REJECT", "REQUIRE_ADDITIONAL_INFO"] = Field(
        default="PROCEED",
        description="The operational decision for the payment request"
    )
    reasoning_summary: Optional[str] = Field(
        default="Valid transaction parameters.",
        description="Detailed LLM reasoning explaining why this decision was reached"
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score in the decision between 0.0 and 1.0"
    )
    required_information: List[str] = Field(
        default_factory=list,
        description="Missing parameters or fields if additional information is required"
    )
    recommended_next_step: Optional[str] = Field(
        default="risk_assessment",
        description="Suggested next pipeline step (e.g., 'risk_assessment', 'reject_with_reason')"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorical tags characterizing the payment"
    )


class RiskAssessment(BaseModel):
    """Structured assessment output from Risk Agent."""
    risk_score: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Quantitative risk score determined by LLM reasoning over contextual signals"
    )
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        default="LOW",
        description="Categorical risk classification"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Identified risk triggers or anomalies"
    )
    reasoning_summary: Optional[str] = Field(
        default="Low risk signals.",
        description="Comprehensive justification for the risk score and classification"
    )
    recommended_action: Literal["APPROVE", "FLAG_FOR_REVIEW", "BLOCK", "STEP_UP_AUTH"] = Field(
        default="APPROVE",
        description="Recommended action based on risk assessment"
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="LLM confidence in the risk evaluation"
    )


class ExecutorDecision(BaseModel):
    """Structured decision output from Executor Agent."""
    tool_to_execute: Literal[
        "create_payment_order",
        "fetch_payment",
        "fetch_order",
        "capture_payment",
        "create_refund",
        "fetch_refund",
        "none"
    ] = Field(
        default="create_payment_order",
        description="Selected registered tool to execute"
    )
    tool_arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the chosen tool"
    )
    reasoning_summary: Optional[str] = Field(
        default="Executing target tool.",
        description="Reasoning explaining why this tool and arguments were selected"
    )
    requires_safety_override: bool = Field(
        default=False,
        description="Whether this execution requests special safety bypass (subject to policy rejection)"
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score for tool selection"
    )


class ReconciliationResult(BaseModel):
    """Structured reconciliation output comparing internal DB, Razorpay, and Webhooks."""
    status: Literal["MATCHED", "MISMATCH_DETECTED", "PENDING_CONFIRMATION", "RECONCILED"] = Field(
        default="MATCHED",
        description="Reconciliation status across records"
    )
    mismatch_type: Optional[str] = Field(
        default=None,
        description="Type of mismatch (e.g. AMOUNT_MISMATCH, STATE_DESYNC, MISSING_WEBHOOK, GATEWAY_TIMEOUT)"
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evidence and delta facts extracted from sources"
    )
    likely_cause: Optional[str] = Field(
        default="State alignment confirmed.",
        description="LLM reasoning diagnosing the probable root cause of the discrepancy"
    )
    recommended_action: Literal["RESOLVE", "CREATE_INCIDENT", "RETRY_FETCH", "ESCALATE_OPERATOR"] = Field(
        default="RESOLVE",
        description="Recommended follow-up action"
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence score for reconciliation diagnosis"
    )
