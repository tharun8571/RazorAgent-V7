from typing import Dict, Any
from app.tools.razorpay.client import get_razorpay_client
from app.core.logging import logger
from app.core.exceptions import RazorpayAPIError


async def create_payment_order_tool(amount: float, currency: str = "INR", receipt: str = None, notes: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Creates an order on Razorpay.
    Amount is converted from currency units to subunits (e.g. paise: amount * 100).
    """
    client = get_razorpay_client()
    amount_subunits = int(round(amount * 100))
    data = {
        "amount": amount_subunits,
        "currency": currency,
        "receipt": receipt or "rcpt_default",
        "notes": notes or {}
    }
    try:
        order = client.order.create(data=data)
        logger.info(f"Created Razorpay order: {order.get('id')}", extra={"order_id": order.get("id"), "amount": amount})
        return order
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {str(e)}", exc_info=True)
        raise RazorpayAPIError(f"Razorpay order creation failed: {str(e)}")


async def fetch_order_tool(order_id: str) -> Dict[str, Any]:
    """Fetches details of an order from Razorpay."""
    client = get_razorpay_client()
    try:
        return client.order.fetch(order_id)
    except Exception as e:
        logger.error(f"Razorpay fetch order failed for {order_id}: {str(e)}")
        raise RazorpayAPIError(f"Razorpay fetch order failed: {str(e)}")
