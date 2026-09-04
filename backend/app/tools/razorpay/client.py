import razorpay
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import RazorpayAPIError


def get_razorpay_client():
    """
    Returns the official Razorpay client authenticated with credentials from environment.
    Requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to be set in .env
    """
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET

    if not key_id or not key_secret:
        raise RazorpayAPIError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env before making payment operations."
        )

    try:
        client = razorpay.Client(auth=(key_id, key_secret))
        logger.info("Razorpay client initialized", extra={"key_id": key_id[:12] + "..."})
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Razorpay client: {str(e)}")
        raise RazorpayAPIError(f"Razorpay client initialization failed: {str(e)}")
