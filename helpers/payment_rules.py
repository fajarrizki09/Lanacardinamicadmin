from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from helpers.payment_gateway import get_available_gateway_providers


VALID_PAYMENT_STATUSES = {"paid", "unpaid", "partial", "pending", "failed", "expired", "void", "refunded"}
VALID_PAYMENT_METHODS = {
    "cash",
    "qris",
    "transfer",
    "debit",
    "ewallet",
    "virtual_account",
    "credit_card",
    "other",
    "free",
}
UNPAID_ALLOWED_METHODS = {"qris", "transfer", "ewallet", "virtual_account", "other"}
PENDING_ALLOWED_METHODS = {"qris", "ewallet", "virtual_account", "credit_card"}
GATEWAY_PROVIDERS = get_available_gateway_providers()


def allocate_payment_amounts(total_paid, component_totals):
    """Allocate payment amounts using Decimal for precision."""
    remaining = Decimal(str(total_paid or 0)).max(Decimal('0'))
    allocations = []
    for total in component_totals:
        component_total = Decimal(str(total or 0)).max(Decimal('0'))
        paid = min(component_total, remaining)
        remaining = (remaining - paid).max(Decimal('0'))
        allocations.append(int(paid.quantize(Decimal('1'), rounding=ROUND_HALF_UP)))
    return allocations


def normalize_visit_payment(
    total_amount,
    payment_status="paid",
    payment_method="",
    amount_paid=None,
    paid_at=None,
    is_free_visit=False,
    payment_provider="manual",
):
    status = str(payment_status or "").strip().lower() or "unpaid"
    method = str(payment_method or "").strip().lower()
    provider = str(payment_provider or "manual").strip().lower() or "manual"
    total = Decimal(str(total_amount or 0))

    if status not in VALID_PAYMENT_STATUSES:
        raise ValueError("Status pembayaran tidak valid.")
    if method and method not in VALID_PAYMENT_METHODS:
        raise ValueError("Metode pembayaran tidak valid.")

    if is_free_visit:
        return {
            "payment_status": "paid",
            "payment_method": "free",
            "amount_paid": 0,
            "paid_at": paid_at or datetime.now().isoformat(),
        }

    if method == "free":
        raise ValueError("Metode Gratis hanya boleh digunakan untuk kunjungan gratis.")

    if status == "refunded":
        method = method or "other"
        if method == "free":
            raise ValueError("Metode Gratis tidak boleh digunakan untuk refund.")
        return {
            "payment_status": status,
            "payment_method": method,
            "amount_paid": 0,
            "paid_at": None,
        }

    if status == "unpaid":
        method = method or "other"
        if method == "cash":
            raise ValueError("Metode Tunai hanya boleh digunakan jika pembayaran sudah lunas atau sebagian.")
        if method in {"debit", "credit_card"}:
            raise ValueError("Metode Debit/Kartu Kredit hanya boleh digunakan jika pembayaran sudah lunas atau sebagian.")
        if method not in UNPAID_ALLOWED_METHODS:
            raise ValueError("Metode pembayaran belum bayar tidak valid.")
        return {
            "payment_status": status,
            "payment_method": method,
            "amount_paid": 0,
            "paid_at": None,
        }

    if status == "pending":
        method = method or "qris"
        if provider not in GATEWAY_PROVIDERS:
            raise ValueError("Status pending hanya boleh digunakan untuk pembayaran gateway.")
        if method not in PENDING_ALLOWED_METHODS:
            raise ValueError("Metode pembayaran pending harus memakai kanal gateway.")
        return {
            "payment_status": status,
            "payment_method": method,
            "amount_paid": 0,
            "paid_at": None,
        }

    if status == "paid":
        if not method:
            raise ValueError("Metode pembayaran wajib diisi untuk status lunas.")
        return {
            "payment_status": status,
            "payment_method": method,
            "amount_paid": int(total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
            "paid_at": paid_at or datetime.now().isoformat(),
        }

    if status == "partial":
        if not method:
            raise ValueError("Metode pembayaran wajib diisi untuk pembayaran sebagian.")
        paid_amount = Decimal(str(amount_paid or 0))
        if paid_amount <= 0:
            raise ValueError("Jumlah bayar sebagian wajib lebih besar dari 0.")
        if paid_amount >= total:
            raise ValueError("Jumlah bayar sebagian harus lebih kecil dari total tagihan.")
        return {
            "payment_status": status,
            "payment_method": method,
            "amount_paid": int(paid_amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)),
            "paid_at": paid_at or datetime.now().isoformat(),
        }

    method = method or "other"
    return {
        "payment_status": status,
        "payment_method": method,
        "amount_paid": 0,
        "paid_at": None,
    }
