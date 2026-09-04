from typing import Dict, Any, Optional
from app.db.database import AsyncSessionLocal
from app.db.repositories.payments import PaymentRepository
from app.core.logging import logger


async def get_payment_from_db_tool(payment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves payment record from database."""
    async with AsyncSessionLocal() as session:
        repo = PaymentRepository(session)
        payment = await repo.get_by_id(payment_id)
        if not payment:
            return None
        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "customer_id": payment.customer_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "risk_score": payment.risk_score,
            "risk_level": payment.risk_level,
            "idempotency_key": payment.idempotency_key,
        }


async def update_payment_db_tool(payment_id: str, status: str, risk_score: Optional[float] = None, risk_level: Optional[str] = None, order_id: Optional[str] = None) -> bool:
    """Updates payment record in database."""
    async with AsyncSessionLocal() as session:
        repo = PaymentRepository(session)
        payment = await repo.update_status(payment_id=payment_id, status=status, risk_score=risk_score, risk_level=risk_level, order_id=order_id)
        await session.commit()
        return payment is not None
