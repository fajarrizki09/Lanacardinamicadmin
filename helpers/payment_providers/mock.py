from datetime import datetime, timedelta

from helpers.payment_gateway import generate_payment_reference
from helpers.payment_providers.base import PROVIDER_STATUS_AVAILABLE


provider_id = "gateway_mock"
display_name = "Pembayaran Internal"
status = PROVIDER_STATUS_AVAILABLE
capabilities = {
    "supports_payment_link": False,
    "supports_qris": True,
    "supports_va": True,
    "supports_webhook": False,
}


def validate_config(*_args, **_kwargs):
    return True


def build_payment_url(payment_reference):
    return f"/payments/gateway/pay/{payment_reference}"


def create_payment(source_type, source_id, amount, method, customer=None):
    payment_reference = generate_payment_reference("gateway_mock", source_type, source_id)
    return {
        "payment_provider": "gateway_mock",
        "payment_reference": payment_reference,
        "payment_url": build_payment_url(payment_reference),
        "payment_channel": method,
        "payment_expired_at": (datetime.now() + timedelta(hours=24)).isoformat(),
        "payment_gateway_status": "pending",
        "payment_method": method,
        "amount": int(float(amount or 0)),
    }


def check_payment_status(payment_reference):
    return {
        "payment_provider": "gateway_mock",
        "payment_reference": str(payment_reference or "").strip(),
        "payment_url": build_payment_url(payment_reference),
        "payment_gateway_status": "pending",
    }


get_payment_status = check_payment_status
