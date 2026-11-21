from __future__ import annotations

from sqlalchemy import case, func, or_

NON_REVENUE_PAYMENT_STATUSES = {"unpaid", "pending", "failed", "expired", "void"}
REVENUE_PAYMENT_STATUSES = {"paid", "partial"}


def normalize_status(value, default=""):
    return str(value or default or "").strip().lower()


def is_void_invoice(invoice_status):
    return normalize_status(invoice_status, "active") == "void"


def is_revenue_payment_status(payment_status):
    return normalize_status(payment_status, "paid") in REVENUE_PAYMENT_STATUSES


def calculate_revenue_amount(total, amount_paid=0, payment_status="paid", invoice_status="active"):
    if is_void_invoice(invoice_status):
        return 0.0
    status = normalize_status(payment_status, "paid")
    if status == "paid":
        return float(total or 0)
    if status == "partial":
        return float(amount_paid or 0)
    return 0.0


def active_invoice_filter(model):
    return or_(model.invoice_status.is_(None), model.invoice_status != "void")


def revenue_case(model, total_expr, *, free_method=True):
    clauses = []
    if free_method and hasattr(model, "payment_method"):
        clauses.append((model.payment_method == "free", 0))
    clauses.extend([
        (or_(model.payment_status == "paid", model.payment_status.is_(None)), total_expr),
        (model.payment_status == "partial", func.coalesce(model.amount_paid, 0)),
    ])
    return case(*clauses, else_=0)
