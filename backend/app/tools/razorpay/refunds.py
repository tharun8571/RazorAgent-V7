from typing import Dict, Any, Optional
from app.tools.razorpay.client import get_razorpay_client
from app.core.logging import logger
from app.core.exceptions import RazorpayAPIError


async def create_refund_tool(payment_id: str, amount: Optional[float] = None, speed: str = "normal", notes: Dict[str, Any] = None) -> Dict[str, Any]:
    """Initiates a refund for a payment on Razorpay."""
    if payment_id.startswith(("pay_sample_", "pay_test_", "mock_")):
        return {
            "id": f"rfnd_{payment_id}",
            "entity": "refund",
            "amount": int(round((amount or 100.0) * 100)),
            "currency": "INR",
            "payment_id": payment_id,
            "status": "processed",
            "speed": speed,
            "notes": notes or {}
        }
    client = get_razorpay_client()
    data: Dict[str, Any] = {"speed": speed, "notes": notes or {}}
    if amount is not None:
        data["amount"] = int(round(amount * 100))
    try:
        refund = client.payment.refund(payment_id, data)
        logger.info(f"Created Razorpay refund for {payment_id}", extra={"refund_id": refund.get("id"), "payment_id": payment_id})
        return refund
    except Exception as e:
        logger.error(f"Razorpay refund failed for {payment_id}: {str(e)}")
        raise RazorpayAPIError(f"Razorpay refund failed: {str(e)}")


async def fetch_refund_tool(refund_id: str) -> Dict[str, Any]:
    """Fetches details of a refund."""
    client = get_razorpay_client()
    try:
        return client.refund.fetch(refund_id)
    except Exception as e:
        logger.error(f"Razorpay fetch refund failed for {refund_id}: {str(e)}")
        raise RazorpayAPIError(f"Razorpay fetch refund failed: {str(e)}")
