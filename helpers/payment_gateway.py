import re
import uuid
from datetime import datetime
from importlib import import_module

from helpers.payment_providers.base import (
    PROVIDER_STATUS_AVAILABLE,
    PROVIDER_STATUS_COMING_SOON,
    PROVIDER_UNAVAILABLE_MESSAGE,
)

PROVIDER_REGISTRY = {
    "gateway_mock": {
        "module": "helpers.payment_providers.mock",
        "display_name": "Pembayaran Internal",
        "status": PROVIDER_STATUS_AVAILABLE,
        "capabilities": {
            "supports_payment_link": False,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
    "midtrans": {
        "module": "helpers.payment_providers.midtrans",
        "display_name": "Midtrans",
        "status": PROVIDER_STATUS_AVAILABLE,
        "capabilities": {
            "supports_payment_link": True,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
    "xendit": {
        "module": "helpers.payment_providers.xendit",
        "display_name": "Xendit",
        "status": PROVIDER_STATUS_COMING_SOON,
        "capabilities": {
            "supports_payment_link": True,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
    "duitku": {
        "module": "helpers.payment_providers.duitku",
        "display_name": "Duitku",
        "status": PROVIDER_STATUS_COMING_SOON,
        "capabilities": {
            "supports_payment_link": True,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
    "doku": {
        "module": "helpers.payment_providers.doku",
        "display_name": "Doku",
        "status": PROVIDER_STATUS_COMING_SOON,
        "capabilities": {
            "supports_payment_link": True,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
    "tripay": {
        "module": "helpers.payment_providers.tripay",
        "display_name": "Tripay",
        "status": PROVIDER_STATUS_COMING_SOON,
        "capabilities": {
            "supports_payment_link": True,
            "supports_qris": True,
            "supports_va": True,
            "supports_webhook": False,
        },
    },
}

PAYMENT_GATEWAY_PROVIDERS = set(PROVIDER_REGISTRY)
AVAILABLE_GATEWAY_PROVIDERS = {
    provider_id
    for provider_id, info in PROVIDER_REGISTRY.items()
    if info["status"] == PROVIDER_STATUS_AVAILABLE
}
COMING_SOON_GATEWAY_PROVIDERS = {
    provider_id
    for provider_id, info in PROVIDER_REGISTRY.items()
    if info["status"] == PROVIDER_STATUS_COMING_SOON
}
ALLOWED_PAYMENT_PROVIDERS = {"manual", *PAYMENT_GATEWAY_PROVIDERS}
ACTIVE_GATEWAY_PROVIDERS = AVAILABLE_GATEWAY_PROVIDERS
GATEWAY_METHODS = {"qris", "ewallet", "virtual_account", "credit_card"}
VALID_PAYMENT_METHODS = {
    "cash",
    "qris",
    "transfer",
    "debit",
    "ewallet",
    "virtual_account",
    "credit_card",
    "other",
}


def _safe_token(value):
    token = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip()).strip("-")
    return token.upper() or "PAY"


def _normalize_provider(provider):
    normalized = str(provider or "").strip().lower()
    if normalized not in ALLOWED_PAYMENT_PROVIDERS:
        raise ValueError("Provider pembayaran belum didukung.")
    return normalized


def get_payment_provider_registry():
    return {
        provider_id: {
            "provider_id": provider_id,
            "display_name": info["display_name"],
            "status": info["status"],
            "capabilities": dict(info.get("capabilities") or {}),
        }
        for provider_id, info in PROVIDER_REGISTRY.items()
    }


def get_payment_provider_info(provider):
    normalized = _normalize_provider(provider)
    if normalized == "manual":
        return {
            "provider_id": "manual",
            "display_name": "Manual",
            "status": PROVIDER_STATUS_AVAILABLE,
            "capabilities": {
                "supports_payment_link": False,
                "supports_qris": False,
                "supports_va": False,
                "supports_webhook": False,
            },
        }
    return get_payment_provider_registry()[normalized]


def get_available_gateway_providers():
    return {
        provider_id
        for provider_id, info in PROVIDER_REGISTRY.items()
        if info["status"] == PROVIDER_STATUS_AVAILABLE
    }


def get_coming_soon_gateway_providers():
    return {
        provider_id
        for provider_id, info in PROVIDER_REGISTRY.items()
        if info["status"] == PROVIDER_STATUS_COMING_SOON
    }


def is_available_gateway_provider(provider):
    return _normalize_provider(provider) in get_available_gateway_providers()


def _ensure_available_gateway_provider(provider):
    normalized = _normalize_provider(provider)
    if normalized == "manual":
        raise ValueError("Provider pembayaran ini memakai jalur manual.")
    if normalized not in get_available_gateway_providers():
        raise ValueError(PROVIDER_UNAVAILABLE_MESSAGE)
    return normalized


def _provider_module(provider):
    normalized = _normalize_provider(provider)
    if normalized == "manual":
        raise ValueError("Provider pembayaran ini memakai jalur manual.")
    registry_item = PROVIDER_REGISTRY.get(normalized)
    if not registry_item:
        raise ValueError("Provider pembayaran belum didukung.")
    return import_module(registry_item["module"])


def generate_payment_reference(provider, source_type, source_id):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8].upper()
    parts = [
        _safe_token(provider),
        _safe_token(source_type),
        _safe_token(source_id),
        timestamp,
        suffix,
    ]
    return "-".join(parts)


def create_payment(provider, source_type, source_id, amount, method, customer=None):
    normalized_provider = _ensure_available_gateway_provider(provider)
    normalized_method = str(method or "").strip().lower()
    if normalized_method not in GATEWAY_METHODS:
        raise ValueError("Metode pembayaran ini belum mendukung link pembayaran otomatis.")
    provider_result = _provider_module(normalized_provider).create_payment(
        source_type=source_type,
        source_id=source_id,
        amount=amount,
        method=normalized_method,
        customer=customer,
    )
    return normalize_payment_result(provider_result)


def check_payment_status(provider, payment_reference):
    normalized_provider = _ensure_available_gateway_provider(provider)
    module = _provider_module(normalized_provider)
    status_checker = getattr(module, "check_status", None) or getattr(module, "check_payment_status")
    provider_result = status_checker(payment_reference)
    return normalize_payment_result(provider_result)


def map_gateway_status(provider, raw_status):
    normalized_provider = _normalize_provider(provider)
    normalized_status = str(raw_status or "").strip().lower()
    if normalized_provider == "gateway_mock":
        if normalized_status == "paid":
            return "paid"
        if normalized_status == "expired":
            return "expired"
        if normalized_status == "failed":
            return "failed"
        return "pending"
    if normalized_provider == "midtrans":
        return _provider_module("midtrans").map_status(normalized_status)
    return "pending"


def normalize_payment_result(provider_result):
    result = dict(provider_result or {})
    provider = _normalize_provider(result.get("payment_provider") or result.get("provider"))
    raw_status = str(
        result.get("payment_gateway_status")
        or result.get("gateway_status")
        or result.get("raw_status")
        or "pending"
    ).strip().lower()
    method = str(result.get("payment_method") or result.get("method") or "").strip().lower()
    return {
        "payment_provider": provider,
        "payment_reference": str(result.get("payment_reference") or result.get("reference") or "").strip(),
        "payment_url": str(result.get("payment_url") or result.get("url") or "").strip(),
        "payment_channel": str(result.get("payment_channel") or result.get("channel") or method or "").strip().lower(),
        "payment_expired_at": result.get("payment_expired_at") or result.get("expired_at"),
        "payment_gateway_status": raw_status,
        "payment_status": map_gateway_status(provider, raw_status),
        "payment_method": method,
        "amount_paid": int(float(result.get("amount_paid") or 0)),
        "paid_at": result.get("paid_at"),
        "amount": int(float(result.get("amount") or 0)),
    }


def create_mock_gateway_payment(source_type, source_id, amount, method):
    return create_payment("gateway_mock", source_type, source_id, amount, method)


def map_gateway_status_to_payment_status(gateway_status):
    return map_gateway_status("gateway_mock", gateway_status)
