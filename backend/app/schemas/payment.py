from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier", json_schema_extra={"example": "cust_98234"})
    amount: float = Field(..., gt=0, description="Amount in currency units (e.g. INR)", json_schema_extra={"example": 1499.00})
    currency: str = Field(default="INR", description="Currency code (e.g. INR, USD)", json_schema_extra={"example": "INR"})
    method: Optional[str] = Field(default="upi", description="Payment method: upi, card, netbanking, wallet")
    error_code: Optional[str] = Field(default=None, description="Simulated error code")
    dispute_count: int = Field(default=0, description="Number of past disputes")
    idempotency_key: str = Field(..., description="Unique request idempotency key", json_schema_extra={"example": "idem_txn_001"})
    description: Optional[str] = Field(default="Payment transaction", description="Order/Transaction description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom context or metadata")


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: Optional[str] = None
    customer_id: str
    amount: float
    currency: str
    status: str
    method: Optional[str] = None
    error_code: Optional[str] = None
    dispute_count: int = 0
    idempotency_key: str
    risk_score: float = 0.0
    risk_level: str = "low"
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WebhookPayload(BaseModel):
    event: str = Field(..., json_schema_extra={"example": "payment.captured"})
    payload: Dict[str, Any] = Field(..., description="Razorpay webhook entity payload")
    created_at: Optional[int] = None
