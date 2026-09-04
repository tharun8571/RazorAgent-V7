from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), default="operator")  # operator, admin, system
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(64), primary_key=True, index=True)
    order_id = Column(String(64), index=True, nullable=True)
    customer_id = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="created", index=True)  # created, authorized, captured, failed, refunded, disputed
    method = Column(String(50), nullable=True)  # upi, card, netbanking, wallet
    error_code = Column(String(100), nullable=True) # network_error, card_expired, insufficient_funds
    dispute_count = Column(Integer, default=0)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    events = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    event_id = Column(String(64), primary_key=True, index=True)
    payment_id = Column(String(64), ForeignKey("payments.payment_id"), index=True, nullable=False)
    event_type = Column(String(100), nullable=False)  # payment.created, payment.captured, payment.failed, etc.
    source = Column(String(50), default="razorpay")   # razorpay, internal, webhook, agent
    payload_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    payment = relationship("Payment", back_populates="events")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    request_id = Column(String(64), index=True, nullable=False)
    payment_id = Column(String(64), index=True, nullable=True)
    status = Column(String(50), default="running")  # running, completed, paused_for_human, failed, recovered
    current_agent = Column(String(100), default="payment_agent")
    state_json = Column(Text, default="{}")
    langsmith_trace_id = Column(String(128), nullable=True, index=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    events = relationship("AgentEvent", back_populates="run", cascade="all, delete-orphan")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    event_id = Column(String(64), primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("agent_runs.run_id"), index=True, nullable=True)
    request_id = Column(String(64), index=True, nullable=False)
    agent_name = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), default="INFO")  # DEBUG, INFO, WARN, ERROR, CRITICAL
    payload_json = Column(Text, default="{}")
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)

    run = relationship("AgentRun", back_populates="events")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(20), default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="OPEN", index=True)      # OPEN, INVESTIGATING, AWAITING_APPROVAL, MITIGATING, RESOLVED, REJECTED
    detected_by = Column(String(100), default="monitor_agent")
    root_cause = Column(Text, nullable=True)
    evidence_json = Column(Text, default="{}")
    recovery_plan_json = Column(Text, default="{}")
    recovery_result_json = Column(Text, default="{}")
    human_review_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    recovery_actions = relationship("RecoveryAction", back_populates="incident", cascade="all, delete-orphan")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    action_id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.incident_id"), index=True, nullable=False)
    action_type = Column(String(100), nullable=False)  # pause_agent, retry_operation, switch_to_fallback, rollback, request_approval
    status = Column(String(50), default="PENDING")     # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    parameters_json = Column(Text, default="{}")
    result_json = Column(Text, default="{}")
    executed_by = Column(String(100), default="recovery_agent")
    executed_at = Column(DateTime(timezone=True), default=utcnow)

    incident = relationship("Incident", back_populates="recovery_actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(64), primary_key=True, index=True)
    actor = Column(String(100), nullable=False)  # system, monitor_agent, human_operator:alice, etc.
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)  # payment, incident, agent, policy
    resource_id = Column(String(64), nullable=False)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
