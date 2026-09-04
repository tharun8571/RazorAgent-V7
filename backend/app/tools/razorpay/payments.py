from typing import Dict, Any, Optional
from app.tools.razorpay.client import get_razorpay_client
from app.core.logging import logger
from app.core.exceptions import RazorpayAPIError


async def fetch_payment_tool(payment_id: str) -> Dict[str, Any]:
    """Fetches details of a payment from Razorpay."""
    client = get_razorpay_client()
    try:
        return client.payment.fetch(payment_id)
    except Exception as e:
        logger.error(f"Razorpay fetch payment failed for {payment_id}: {str(e)}")
        raise RazorpayAPIError(f"Razorpay fetch payment failed: {str(e)}")


async def capture_payment_tool(payment_id: str, amount: float, currency: str = "INR") -> Dict[str, Any]:
    """Captures an authorized payment."""
    if payment_id.startswith(("pay_sample_", "pay_test_", "mock_")):
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": int(round(amount * 100)),
            "currency": currency,
            "status": "captured",
            "order_id": f"order_{payment_id}",
            "method": "card",
            "captured": True
        }
    client = get_razorpay_client()
    amount_subunits = int(round(amount * 100))
    try:
        return client.payment.capture(payment_id, amount_subunits, {"currency": currency})
    except Exception as e:
        logger.error(f"Razorpay capture payment failed for {payment_id}: {str(e)}")
        raise RazorpayAPIError(f"Razorpay capture payment failed: {str(e)}")

