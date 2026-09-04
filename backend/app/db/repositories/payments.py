import json
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.db.models import Payment, PaymentEvent, AuditLog, utcnow


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(
        self,
        payment_id: str,
        customer_id: str,
        amount: float,
        currency: str,
        idempotency_key: str,
        order_id: Optional[str] = None,
        method: Optional[str] = None,
        error_code: Optional[str] = None,
        dispute_count: int = 0,
        risk_score: float = 0.0,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        initial_status = status or ("failed" if error_code else "created")
        payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            method=method,
            error_code=error_code,
            dispute_count=dispute_count,
            risk_score=risk_score,
            risk_level="low",
            status=initial_status,
            metadata_json=json.dumps(metadata or {}),
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).where(Payment.payment_id == payment_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
        return result.scalar_one_or_none()

    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        result = await self.session.execute(select(Payment).where(Payment.order_id == order_id))
        return result.scalar_one_or_none()

    async def update_status(self, payment_id: str, status: str, risk_score: Optional[float] = None, risk_level: Optional[str] = None, order_id: Optional[str] = None) -> Optional[Payment]:
        payment = await self.get_by_id(payment_id)
        if payment:
            payment.status = status
            if risk_score is not None:
                payment.risk_score = risk_score
            if risk_level is not None:
                payment.risk_level = risk_level
            if order_id is not None:
                payment.order_id = order_id
            payment.updated_at = utcnow()
            self.session.add(payment)
            await self.session.flush()
        return payment

    async def add_event(
        self,
        event_id: str,
        payment_id: str,
        event_type: str,
        source: str = "razorpay",
        payload: Optional[Dict[str, Any]] = None,
    ) -> PaymentEvent:
        event = PaymentEvent(
            event_id=event_id,
            payment_id=payment_id,
            event_type=event_type,
            source=source,
            payload_json=json.dumps(payload or {}),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_payments(self, limit: int = 50, offset: int = 0) -> List[Payment]:
        stmt = select(Payment).order_by(desc(Payment.created_at)).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def log_audit(
        self,
        log_id: str,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        audit = AuditLog(
            log_id=log_id,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details or {}),
        )
        self.session.add(audit)
        await self.session.flush()
        return audit
