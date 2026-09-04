import pytest
import hmac
import hashlib
from app.core.security import verify_razorpay_webhook_signature
from app.tools.razorpay.orders import create_payment_order_tool
from app.tools.razorpay.payments import capture_payment_tool
from app.core.exceptions import WebhookSignatureError


@pytest.mark.asyncio
async def test_razorpay_tools_execution():
    """Verify tool execution via test sandbox."""
    order = await create_payment_order_tool(amount=1999.0, currency="INR", receipt="rcpt_unit_01")
    assert order["id"].startswith("order_")
    assert order["amount"] == 199900

    captured = await capture_payment_tool(payment_id="pay_sample_123", amount=1999.0)
    assert captured["id"] == "pay_sample_123"
    assert captured["status"] == "captured"


def test_webhook_signature_verification():
    secret = "test_webhook_secret_key"
    payload = b'{"event":"payment.captured","entity":"payment"}'
    valid_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    # Valid signature
    assert verify_razorpay_webhook_signature(payload, valid_sig, secret=secret) is True

    # Invalid signature
    with pytest.raises(WebhookSignatureError):
        verify_razorpay_webhook_signature(payload, "invalid_signature_hex", secret=secret)
