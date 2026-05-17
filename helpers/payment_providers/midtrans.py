import base64
import json
from urllib import error, parse, request

from helpers.payment_gateway import generate_payment_reference
from helpers.payment_providers.base import PROVIDER_STATUS_AVAILABLE
from settings import AppSettings


SNAP_SANDBOX_URL = "https://app.sandbox.midtrans.com/snap/v1/transactions"
API_SANDBOX_BASE_URL = "https://api.sandbox.midtrans.com"
MIDTRANS_GATEWAY_METHODS = {"qris", "ewallet", "virtual_account", "credit_card"}
SAFE_MIDTRANS_ERROR = "Midtrans sandbox gagal memproses pembayaran. Periksa konfigurasi gateway dan coba lagi."
provider_id = "midtrans"
display_name = "Midtrans"
status = PROVIDER_STATUS_AVAILABLE
capabilities = {
    "supports_payment_link": True,
    "supports_qris": True,
    "supports_va": True,
    "supports_webhook": False,
}


class MidtransPaymentError(ValueError):
    pass


def _settings():
    return AppSettings().settings


def _server_key():
    key = str(_settings().get("midtrans_server_key") or "").strip()
    if not key:
        raise MidtransPaymentError("Midtrans server key belum diisi.")
    return key


def validate_config(*_args, **_kwargs):
    _ensure_sandbox()
    _server_key()
    return True


def _ensure_sandbox():
    environment = str(_settings().get("payment_gateway_environment") or "sandbox").strip().lower()
    if environment != "sandbox":
        raise MidtransPaymentError("Midtrans production belum diaktifkan. Gunakan sandbox terlebih dahulu.")


def _auth_header(server_key):
    auth_value = base64.b64encode(f"{server_key}:".encode("utf-8")).decode("ascii")
    return f"Basic {auth_value}"


def _enabled_payments(method):
    if method == "qris":
        return ["qris"]
    if method == "ewallet":
        return ["gopay", "shopeepay"]
    if method == "virtual_account":
        return ["bank_transfer", "bca_va", "bni_va", "bri_va", "permata_va"]
    if method == "credit_card":
        return ["credit_card"]
    return []


def _safe_customer_details(customer):
    customer = customer or {}
    details = {}
    name = str(customer.get("name") or "").strip()
    email = str(customer.get("email") or "").strip()
    phone = str(customer.get("phone") or "").strip()
    if name:
        parts = name.split(None, 1)
        details["first_name"] = parts[0]
        if len(parts) > 1:
            details["last_name"] = parts[1]
    if email:
        details["email"] = email
    if phone:
        details["phone"] = phone
    return details


def _snap_payload(order_id, source_type, source_id, amount, method, customer=None, items=None):
    payload = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": int(float(amount or 0)),
        },
        "enabled_payments": _enabled_payments(method),
        "custom_field1": str(source_type or ""),
        "custom_field2": str(source_id or ""),
    }
    if method == "credit_card":
        payload["credit_card"] = {"secure": True}
    customer_details = _safe_customer_details(customer)
    if customer_details:
        payload["customer_details"] = customer_details
    if items:
        payload["item_details"] = items
    return payload


def _json_request(url, method, payload=None):
    server_key = _server_key()
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": _auth_header(server_key),
        },
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body or "{}")
    except error.HTTPError as exc:
        try:
            response_body = exc.read().decode("utf-8")
            response_data = json.loads(response_body or "{}")
            message = str(response_data.get("status_message") or "").strip()
        except Exception:
            message = ""
        raise MidtransPaymentError(message or SAFE_MIDTRANS_ERROR) from exc
    except Exception as exc:
        raise MidtransPaymentError(SAFE_MIDTRANS_ERROR) from exc


def create_payment(source_type, source_id, amount, method, customer=None, items=None):
    _ensure_sandbox()
    normalized_method = str(method or "").strip().lower()
    if normalized_method not in MIDTRANS_GATEWAY_METHODS:
        raise MidtransPaymentError("Metode pembayaran ini tidak didukung Midtrans sandbox.")
    order_id = generate_payment_reference("midtrans", source_type, source_id)
    payload = _snap_payload(order_id, source_type, source_id, amount, normalized_method, customer=customer, items=items)
    response = _json_request(SNAP_SANDBOX_URL, "POST", payload)
    redirect_url = str(response.get("redirect_url") or "").strip()
    token = str(response.get("token") or "").strip()
    if not redirect_url:
        raise MidtransPaymentError(SAFE_MIDTRANS_ERROR)
    return {
        "payment_provider": "midtrans",
        "payment_reference": order_id,
        "payment_url": redirect_url,
        "payment_channel": normalized_method,
        "payment_gateway_status": "pending",
        "payment_method": normalized_method,
        "amount": int(float(amount or 0)),
        "midtrans_token": token,
    }


def check_status(payment_reference):
    _ensure_sandbox()
    encoded_reference = parse.quote(str(payment_reference or "").strip(), safe="")
    response = _json_request(f"{API_SANDBOX_BASE_URL}/v2/{encoded_reference}/status", "GET")
    raw_status = str(response.get("transaction_status") or response.get("status_code") or "pending").strip().lower()
    return {
        "payment_provider": "midtrans",
        "payment_reference": str(payment_reference or "").strip(),
        "payment_gateway_status": raw_status,
    }


get_payment_status = check_status


def map_status(raw_status):
    normalized = str(raw_status or "").strip().lower()
    if normalized in {"settlement", "capture"}:
        return "paid"
    if normalized == "pending":
        return "pending"
    if normalized == "expire":
        return "expired"
    if normalized in {"cancel", "deny", "failure"}:
        return "failed"
    return "pending"
