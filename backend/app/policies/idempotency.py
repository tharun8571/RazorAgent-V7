from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.payments import PaymentRepository
from app.core.exceptions import IdempotencyViolationError
from app.core.logging import logger


async def enforce_idempotency(session: AsyncSession, idempotency_key: str) -> bool:
    """
    Deterministic check: Ensures the idempotency key has not been previously consumed.
    Raises IdempotencyViolationError if duplicate is detected.
    """
    if not idempotency_key:
        raise IdempotencyViolationError("Idempotency key is required for all financial payment operations.")

    repo = PaymentRepository(session)
    existing_payment = await repo.get_by_idempotency_key(idempotency_key)
    if existing_payment:
        logger.warning(
            f"Duplicate transaction attempted with idempotency key: {idempotency_key}",
            extra={"idempotency_key": idempotency_key, "existing_payment_id": existing_payment.payment_id}
        )
        raise IdempotencyViolationError(
            f"Duplicate transaction detected. Idempotency key '{idempotency_key}' is already bound to payment {existing_payment.payment_id}."
        )

    return True
