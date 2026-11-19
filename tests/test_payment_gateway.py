import unittest
from itertools import count
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import text

from database import Herbal, HerbalTransaction, Patient, Therapist, Visit
from helpers.owner_report_helper import build_owner_report_summary
from helpers.payment_gateway import (
    PROVIDER_UNAVAILABLE_MESSAGE,
    create_payment,
    get_payment_provider_registry,
)
from helpers.payment_providers import midtrans
from tests.api_test_utils import app_headers, client, db

_PHONE_COUNTER = count(1)


def _unique_phone():
    timestamp_digits = int(datetime.now().timestamp() * 1_000_000) % 1_000_000_000
    counter_digits = next(_PHONE_COUNTER) % 100
    return f"08{timestamp_digits:09d}{counter_digits:02d}"


class TestPaymentGatewayMock(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def _create_visit(self, price=150000, payment_method="qris", payment_provider="manual"):
        with db.Session() as session:
            patient = Patient(
                name=f"Gateway Pasien {datetime.now().timestamp()}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            therapist = Therapist(name="Gateway Terapis", gender="Laki-laki", specialization="Test")
            session.add_all([patient, therapist])
            session.flush()
            visit = Visit(
                patient_id=patient.id,
                therapist_id=therapist.id,
                date=datetime.now(),
                price=price,
                discount_applied=False,
                point_count=1,
                payment_status="unpaid",
                payment_method=payment_method,
                amount_paid=0,
                paid_at=None,
                payment_provider=payment_provider,
            )
            session.add(visit)
            session.commit()
            return visit.id

    def _create_gateway_visit(self, price=150000, payment_method="qris"):
        visit_id = self._create_visit(price=price, payment_method=payment_method)
        response = self.client.post(
            "/payments/gateway/create",
            data={
                "provider": "gateway_mock",
                "source_type": "visit",
                "source_id": str(visit_id),
                "amount": str(price),
                "payment_method": payment_method,
            },
            headers=app_headers(),
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["payment"]

    def test_gateway_columns_exist(self):
        with db.Session() as session:
            for table_name in ("visits", "herbal_transactions"):
                columns = {
                    row[1]
                    for row in session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                }
                self.assertTrue({
                    "payment_provider",
                    "payment_reference",
                    "payment_url",
                    "payment_channel",
                    "payment_expired_at",
                    "payment_gateway_status",
                }.issubset(columns))

    def test_old_empty_provider_is_returned_as_manual(self):
        visit_id = self._create_visit(payment_provider="")

        response = self.client.get("/invoices", headers=app_headers())

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.json() if item["id"] == f"v_{visit_id}")
        self.assertEqual(row["payment_provider"], "manual")

    def test_create_and_simulate_paid_visit_gateway_payment(self):
        payment = self._create_gateway_visit(price=175000, payment_method="qris")
        self.assertEqual(payment["payment_status"], "pending")
        self.assertEqual(payment["payment_provider"], "gateway_mock")
        self.assertTrue(payment["payment_reference"])
        self.assertTrue(payment["payment_url"])

        status_response = self.client.get(
            f"/payments/gateway/status/{payment['payment_reference']}?simulate=paid",
            headers=app_headers(),
        )

        self.assertEqual(status_response.status_code, 200)
        paid = status_response.json()["payment"]
        self.assertEqual(paid["payment_status"], "paid")
        self.assertEqual(paid["amount_paid"], 175000)
        self.assertTrue(paid["paid_at"])

    def test_simulate_expired_visit_gateway_payment(self):
        payment = self._create_gateway_visit(price=125000, payment_method="virtual_account")
        reference = payment["payment_reference"]

        response = self.client.get(
            f"/payments/gateway/status/{reference}?simulate=expired",
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        payment = response.json()["payment"]
        self.assertEqual(payment["payment_status"], "expired")
        self.assertEqual(payment["amount_paid"], 0)
        self.assertEqual(payment["payment_gateway_status"], "expired")

    def test_simulate_failed_visit_gateway_payment(self):
        payment = self._create_gateway_visit(price=115000, payment_method="ewallet")

        response = self.client.get(
            f"/payments/gateway/status/{payment['payment_reference']}?simulate=failed",
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        failed = response.json()["payment"]
        self.assertEqual(failed["payment_status"], "failed")
        self.assertEqual(failed["amount_paid"], 0)
        self.assertEqual(failed["payment_gateway_status"], "failed")

    def test_cash_manual_does_not_create_gateway_url(self):
        visit_id = self._create_visit(price=90000, payment_method="cash")

        response = self.client.post(
            "/payments/gateway/create",
            data={"provider": "gateway_mock", "source_type": "visit", "source_id": str(visit_id), "amount": "90000", "payment_method": "cash"},
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_provider or "manual", "manual")
            self.assertFalse(visit.payment_url)

    def test_coming_soon_gateway_provider_is_rejected_before_touching_manual_payment(self):
        visit_id = self._create_visit(price=90000, payment_method="qris")

        response = self.client.post(
            "/payments/gateway/create",
            data={
                "provider": "xendit",
                "source_type": "visit",
                "source_id": str(visit_id),
                "amount": "90000",
                "payment_method": "qris",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], PROVIDER_UNAVAILABLE_MESSAGE)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_provider or "manual", "manual")
            self.assertFalse(visit.payment_reference)
            self.assertFalse(visit.payment_url)

    def test_unknown_gateway_provider_is_rejected_before_touching_manual_payment(self):
        visit_id = self._create_visit(price=90000, payment_method="qris")

        response = self.client.post(
            "/payments/gateway/create",
            data={
                "provider": "unknownpay",
                "source_type": "visit",
                "source_id": str(visit_id),
                "amount": "90000",
                "payment_method": "qris",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Provider ini belum didukung. Gunakan Pembayaran Internal atau Midtrans.")
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_provider or "manual", "manual")
            self.assertFalse(visit.payment_reference)
            self.assertFalse(visit.payment_url)

    def test_midtrans_without_server_key_is_rejected_safely(self):
        visit_id = self._create_visit(price=100000, payment_method="qris")

        class FakeSettings:
            settings = {
                "midtrans_server_key": "",
                "payment_gateway_environment": "sandbox",
            }

        with patch.object(midtrans, "AppSettings", return_value=FakeSettings()):
            response = self.client.post(
                "/payments/gateway/create",
                data={
                    "provider": "midtrans",
                    "source_type": "visit",
                    "source_id": str(visit_id),
                    "amount": "100000",
                    "payment_method": "qris",
                },
                headers=app_headers(),
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Midtrans server key belum diisi.")

    def test_cash_does_not_create_midtrans_payment(self):
        visit_id = self._create_visit(price=100000, payment_method="cash")

        response = self.client.post(
            "/payments/gateway/create",
            data={
                "provider": "midtrans",
                "source_type": "visit",
                "source_id": str(visit_id),
                "amount": "100000",
                "payment_method": "cash",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Metode pembayaran ini memakai jalur manual.")

    def test_analytics_counts_paid_and_partial_only(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        with db.Session() as session:
            patient = Patient(
                name=f"Analytics Gateway {datetime.now().timestamp()}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            session.add(patient)
            session.flush()
            session.add_all([
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="paid", payment_method="cash"),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="partial", payment_method="transfer", amount_paid=40000),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="pending", payment_method="qris", amount_paid=0),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="expired", payment_method="qris", amount_paid=0),
            ])
            session.commit()

        stats = db.get_dashboard_stats()

        self.assertEqual(float(stats["total_income"]) - before_income, 140000)

    def test_invoice_response_contains_gateway_payment_fields(self):
        payment = self._create_gateway_visit(price=99000, payment_method="qris")

        response = self.client.get("/invoices", headers=app_headers())

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.json() if item["payment_reference"] == payment["payment_reference"])
        self.assertEqual(row["payment_status"], "pending")
        self.assertEqual(row["payment_method"], "qris")
        self.assertEqual(row["payment_provider"], "gateway_mock")
        self.assertEqual(row["payment_reference"], payment["payment_reference"])
        self.assertTrue(row["payment_url"])

    def test_invoice_gateway_external_url_uses_controlled_desktop_opener(self):
        source = Path("api/static/ts/invoices.ts").read_text(encoding="utf-8")

        self.assertNotIn("window.open(", source)
        self.assertIn("await openDesktopExternalUrl(paymentUrl, 'payment');", source)
        self.assertIn("function _absolutePaymentUrl", source)
        self.assertIn("gateway_mock: 'Pembayaran Internal'", source)
        self.assertIn("const isInternalPayment", source)
        self.assertIn("!isInternalGateway", source)

    def test_gateway_audit_log_records_create_and_status_changes(self):
        payment = self._create_gateway_visit(price=88000, payment_method="qris")
        reference = payment["payment_reference"]

        self.client.get(f"/payments/gateway/status/{reference}?simulate=paid", headers=app_headers())
        self.client.get(f"/payments/gateway/status/{reference}?simulate=expired", headers=app_headers())
        self.client.get(f"/payments/gateway/status/{reference}?simulate=failed", headers=app_headers())

        logs = db.get_audit_logs(limit=100)
        by_action = {}
        for row in logs:
            metadata = row.get("metadata") or {}
            if metadata.get("payment_reference") == reference or row.get("metadata", {}).get("payment_reference") == reference:
                by_action[row["action"]] = row
        self.assertIn("gateway_payment_created", by_action)
        self.assertIn("gateway_status_changed", by_action)
        self.assertIn("gateway_payment_paid", by_action)
        self.assertNotIn("gateway_payment_expired", by_action)
        self.assertNotIn("gateway_payment_failed", by_action)

    def test_gateway_final_state_duplicate_paid_is_ignored(self):
        payment = self._create_gateway_visit(price=76000, payment_method="qris")
        reference = payment["payment_reference"]

        first = self.client.get(f"/payments/gateway/status/{reference}?simulate=paid", headers=app_headers())
        second = self.client.get(f"/payments/gateway/status/{reference}?simulate=paid", headers=app_headers())

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json().get("ignored"))
        self.assertEqual(second.json().get("reason"), "payment_already_final")
        paid_logs = [
            row for row in db.get_audit_logs(action="gateway_payment_paid", limit=100)
            if (row.get("metadata") or {}).get("payment_reference") == reference
        ]
        self.assertEqual(len(paid_logs), 1)

    def test_manual_invoice_payment_marks_unpaid_visit_paid_qris(self):
        visit_id = self._create_visit(price=120000, payment_method="other")

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "qris",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_status, "paid")
            self.assertEqual(visit.payment_method, "qris")
            self.assertEqual(visit.amount_paid, 120000)
            self.assertEqual(visit.payment_provider, "gateway_mock")
            self.assertTrue(visit.paid_at)

    def test_manual_invoice_payment_marks_unpaid_visit_paid_cash(self):
        visit_id = self._create_visit(price=90000, payment_method="other")

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_status, "paid")
            self.assertEqual(visit.payment_method, "cash")
            self.assertEqual(visit.amount_paid, 90000)

    def test_manual_invoice_payment_records_partial_dp(self):
        visit_id = self._create_visit(price=100000, payment_method="other")

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "partial",
                "payment_method": "transfer",
                "amount_paid": "40000",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_status, "partial")
            self.assertEqual(visit.payment_method, "transfer")
            self.assertEqual(visit.amount_paid, 40000)
            self.assertEqual(visit.payment_provider, "gateway_mock")

    def test_manual_invoice_payment_marks_partial_visit_paid(self):
        visit_id = self._create_visit(price=110000, payment_method="transfer")
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            visit.payment_status = "partial"
            visit.amount_paid = 30000
            session.commit()

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_status, "paid")
            self.assertEqual(visit.amount_paid, 110000)

    def test_manual_invoice_payment_rejects_void_visit(self):
        visit_id = self._create_visit(price=100000, payment_method="other")
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            visit.invoice_status = "void"
            visit.payment_status = "void"
            session.commit()

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 400)

    def test_manual_invoice_payment_overrides_pending_gateway_without_midtrans(self):
        visit_id = self._create_visit(price=130000, payment_method="qris", payment_provider="midtrans")
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            visit.payment_status = "pending"
            visit.payment_reference = "MIDTRANS-123"
            visit.payment_url = "https://midtrans.example/pay"
            visit.payment_gateway_status = "pending"
            session.commit()

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            self.assertEqual(visit.payment_status, "paid")
            self.assertEqual(visit.payment_method, "cash")
            self.assertEqual(visit.payment_provider, "gateway_mock")
            self.assertEqual(visit.payment_reference, "")
            self.assertEqual(visit.payment_url, "")

    def test_manual_invoice_payment_allocates_visit_herbal_without_double_revenue(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        with db.Session() as session:
            patient = Patient(
                name=f"Manual Pay {datetime.now().timestamp()}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            herbal = Herbal(name=f"Manual Herbal {datetime.now().timestamp()}", stock=5, price=50000, cost_price=10000, unit="pcs")
            session.add_all([patient, herbal])
            session.flush()
            visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                discount_applied=False,
                payment_status="unpaid",
                payment_method="other",
                amount_paid=0,
            )
            session.add(visit)
            session.flush()
            session.add(HerbalTransaction(
                herbal_id=herbal.id,
                visit_id=visit.id,
                date=datetime.now(),
                quantity=1,
                total_price=50000,
                transaction_type="sale",
                payment_status="unpaid",
                payment_method="other",
                amount_paid=0,
            ))
            session.commit()
            visit_id = visit.id

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(db.get_dashboard_stats()["total_income"]) - before_income, 150000)
        with db.Session() as session:
            visit = session.get(Visit, visit_id)
            herbal_row = session.query(HerbalTransaction).filter(HerbalTransaction.visit_id == visit_id).one()
            self.assertEqual(visit.amount_paid, 100000)
            self.assertEqual(herbal_row.amount_paid, 50000)

    def test_manual_invoice_payment_records_audit_log(self):
        visit_id = self._create_visit(price=80000, payment_method="other")

        response = self.client.post(
            "/update_invoice_payment",
            data={
                "invoice_type": "visit",
                "visit_id": str(visit_id),
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(pin="1234"),
        )

        self.assertEqual(response.status_code, 200)
        logs = db.get_audit_logs(limit=50)
        self.assertTrue(any(row["action"] == "manual_payment_updated" for row in logs))


class TestHerbalGatewayMock(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def _create_herbal_transaction(self, total=100000, payment_method="ewallet"):
        with db.Session() as session:
            herbal = Herbal(name=f"Gateway Herbal {datetime.now().timestamp()}", stock=10, price=50000, cost_price=10000, unit="pcs")
            session.add(herbal)
            session.flush()
            transaction = HerbalTransaction(
                herbal_id=herbal.id,
                date=datetime.now(),
                quantity=2,
                total_price=total,
                transaction_type="sale",
                payment_status="unpaid",
                payment_method=payment_method,
                amount_paid=0,
            )
            session.add(transaction)
            session.commit()
            return transaction.id

    def _create_gateway_herbal_payment(self, total=100000, payment_method="ewallet"):
        transaction_id = self._create_herbal_transaction(total=total, payment_method=payment_method)
        response = self.client.post(
            "/payments/gateway/create",
            data={
                "provider": "gateway_mock",
                "source_type": "herbal",
                "source_id": str(transaction_id),
                "amount": str(total),
                "payment_method": payment_method,
            },
            headers=app_headers(),
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["payment"]

    def test_create_herbal_gateway_payment(self):
        payment = self._create_gateway_herbal_payment(total=100000, payment_method="ewallet")
        self.assertEqual(payment["payment_provider"], "gateway_mock")
        self.assertEqual(payment["payment_status"], "pending")

    def test_simulate_paid_expired_failed_herbal_gateway_payment(self):
        for simulate, expected_amount, expected_gateway_status in (
            ("paid", 100000, "paid"),
            ("expired", 0, "expired"),
            ("failed", 0, "failed"),
        ):
            payment = self._create_gateway_herbal_payment(total=100000, payment_method="ewallet")
            response = self.client.get(
                f"/payments/gateway/status/{payment['payment_reference']}?simulate={simulate}",
                headers=app_headers(),
            )

            self.assertEqual(response.status_code, 200)
            updated = response.json()["payment"]
            self.assertEqual(updated["payment_status"], simulate)
            self.assertEqual(updated["amount_paid"], expected_amount)
            self.assertEqual(updated["payment_gateway_status"], expected_gateway_status)
            if simulate == "paid":
                self.assertTrue(updated["paid_at"])

    def test_dashboard_and_owner_report_revenue_ignore_unpaid_gateway_statuses(self):
        before_dashboard = float(db.get_dashboard_stats()["total_income"])
        with db.Session() as session:
            before_owner = build_owner_report_summary(session, period="year")["summary"]["total_revenue"]
            patient = Patient(
                name=f"Owner Gateway {datetime.now().timestamp()}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            herbal = Herbal(name=f"Owner Herbal {datetime.now().timestamp()}", stock=20, price=50000, cost_price=10000, unit="pcs")
            session.add_all([patient, herbal])
            session.flush()
            session.add_all([
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="paid", payment_method="cash"),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="partial", payment_method="transfer", amount_paid=40000),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="pending", payment_method="qris", amount_paid=0),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="expired", payment_method="qris", amount_paid=0),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, payment_status="failed", payment_method="qris", amount_paid=0),
                Visit(patient_id=patient.id, date=datetime.now(), price=100000, discount_applied=False, invoice_status="void", payment_status="paid", payment_method="cash"),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", payment_status="paid", payment_method="cash"),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", payment_status="partial", payment_method="transfer", amount_paid=20000),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", payment_status="pending", payment_method="qris", amount_paid=0),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", payment_status="expired", payment_method="qris", amount_paid=0),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", payment_status="failed", payment_method="qris", amount_paid=0),
                HerbalTransaction(herbal_id=herbal.id, date=datetime.now(), quantity=1, total_price=50000, transaction_type="sale", invoice_status="void", payment_status="paid", payment_method="cash"),
            ])
            session.commit()
            after_owner = build_owner_report_summary(session, period="year")["summary"]["total_revenue"]

        after_dashboard = float(db.get_dashboard_stats()["total_income"])

        self.assertEqual(after_dashboard - before_dashboard, 210000)
        self.assertEqual(after_owner - before_owner, 210000)

    def test_revenue_reports_are_consistent_for_mixed_payment_states(self):
        before_dashboard = float(db.get_dashboard_stats()["total_income"])
        before_analytics_data = db.get_analytics_data(period="all")
        before_analytics = float(before_analytics_data["total_income"])
        unique = datetime.now().strftime("%H%M%S%f")
        report_start = datetime.now().isoformat()
        service_name = f"Revenue Mix Service {unique}"
        herbal_name = f"Revenue Mix Herbal {unique}"

        with db.Session() as session:
            before_owner_data = build_owner_report_summary(session, date_from=report_start, date_to=report_start)
            before_owner = before_owner_data["summary"]["total_revenue"]
            patient = Patient(
                name=f"Revenue Mix Patient {unique}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            herbal = Herbal(name=herbal_name, stock=20, price=50000, cost_price=10000, unit="pcs")
            session.add_all([patient, herbal])
            session.flush()
            paid_visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                payment_status="paid",
                payment_method="cash",
                amount_paid=100000,
            )
            partial_visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                payment_status="partial",
                payment_method="transfer",
                amount_paid=40000,
            )
            pending_visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                payment_status="pending",
                payment_method="qris",
                amount_paid=0,
            )
            void_visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                invoice_status="void",
                payment_status="paid",
                payment_method="cash",
                amount_paid=100000,
            )
            free_visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=0,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                is_free_visit=True,
                free_visit_reason="Promo",
                payment_status="paid",
                payment_method="free",
                amount_paid=0,
            )
            visit_with_herbal = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=100000,
                point_count=1,
                service_name=service_name,
                discount_applied=False,
                payment_status="paid",
                payment_method="cash",
                amount_paid=100000,
            )
            session.add_all([paid_visit, partial_visit, pending_visit, void_visit, free_visit, visit_with_herbal])
            session.flush()
            session.add_all([
                HerbalTransaction(
                    herbal_id=herbal.id,
                    visit_id=visit_with_herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    payment_status="paid",
                    payment_method="cash",
                    amount_paid=50000,
                ),
                HerbalTransaction(
                    herbal_id=herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    payment_status="paid",
                    payment_method="cash",
                    amount_paid=50000,
                ),
                HerbalTransaction(
                    herbal_id=herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    payment_status="partial",
                    payment_method="transfer",
                    amount_paid=20000,
                ),
                HerbalTransaction(
                    herbal_id=herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    payment_status="pending",
                    payment_method="qris",
                    amount_paid=0,
                ),
                HerbalTransaction(
                    herbal_id=herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    invoice_status="void",
                    payment_status="paid",
                    payment_method="cash",
                    amount_paid=50000,
                ),
                HerbalTransaction(
                    herbal_id=herbal.id,
                    date=datetime.now(),
                    quantity=1,
                    total_price=50000,
                    transaction_type="sale",
                    payment_status="paid",
                    payment_method="free",
                    amount_paid=0,
                ),
            ])
            session.commit()
            after_owner_data = build_owner_report_summary(session, date_from=report_start, date_to=datetime.now().isoformat())
            after_owner = after_owner_data["summary"]["total_revenue"]

        after_dashboard = float(db.get_dashboard_stats()["total_income"])
        after_analytics_data = db.get_analytics_data(period="all")
        after_analytics = float(after_analytics_data["total_income"])

        expected_revenue = 360000
        self.assertEqual(after_dashboard - before_dashboard, expected_revenue)
        self.assertEqual(after_owner - before_owner, expected_revenue)
        self.assertEqual(after_analytics - before_analytics, expected_revenue)
        self.assertEqual(
            after_owner_data["summary"]["visit_revenue"] - before_owner_data["summary"]["visit_revenue"],
            240000,
        )
        self.assertEqual(
            after_owner_data["summary"]["herbal_revenue"] - before_owner_data["summary"]["herbal_revenue"],
            120000,
        )

        service_row = next(row for row in after_owner_data["top_services"] if row["name"] == service_name)
        herbal_row = next(row for row in after_owner_data["top_herbals"] if row["name"] == herbal_name)
        self.assertEqual(service_row["revenue"], 240000)
        self.assertEqual(herbal_row["revenue"], 120000)
        current_month_label = datetime.now().strftime("%b %Y")
        before_monthly = dict(zip(before_analytics_data["monthly_labels"], before_analytics_data["monthly_income"]))
        after_monthly = dict(zip(after_analytics_data["monthly_labels"], after_analytics_data["monthly_income"]))
        self.assertEqual(round(after_monthly[current_month_label] - before_monthly.get(current_month_label, 0)), expected_revenue)


class TestMidtransAdapter(unittest.TestCase):
    def test_midtrans_status_mapping(self):
        self.assertEqual(midtrans.map_status("settlement"), "paid")
        self.assertEqual(midtrans.map_status("capture"), "paid")
        self.assertEqual(midtrans.map_status("pending"), "pending")
        self.assertEqual(midtrans.map_status("expire"), "expired")
        self.assertEqual(midtrans.map_status("cancel"), "failed")
        self.assertEqual(midtrans.map_status("deny"), "failed")
        self.assertEqual(midtrans.map_status("failure"), "failed")

    def test_midtrans_create_payment_builds_sandbox_snap_payload(self):
        captured = {}

        class FakeSettings:
            settings = {
                "midtrans_server_key": "SB-MID-SERVER-KEY",
                "payment_gateway_environment": "sandbox",
            }

        def fake_json_request(url, method, payload=None):
            captured["url"] = url
            captured["method"] = method
            captured["payload"] = payload
            return {"token": "snap-token", "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/snap-token"}

        with patch.object(midtrans, "AppSettings", return_value=FakeSettings()), patch.object(midtrans, "_json_request", side_effect=fake_json_request):
            result = midtrans.create_payment(
                source_type="visit",
                source_id="123",
                amount=150000,
                method="qris",
                customer={"name": "Pasien Test", "phone": "081234567890"},
            )

        self.assertEqual(captured["url"], midtrans.SNAP_SANDBOX_URL)
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["payload"]["transaction_details"]["gross_amount"], 150000)
        self.assertTrue(captured["payload"]["transaction_details"]["order_id"].startswith("MIDTRANS-VISIT-123-"))
        self.assertEqual(captured["payload"]["enabled_payments"], ["qris"])
        self.assertEqual(captured["payload"]["customer_details"]["first_name"], "Pasien")
        self.assertEqual(result["payment_provider"], "midtrans")
        self.assertEqual(result["payment_gateway_status"], "pending")
        self.assertTrue(result["payment_url"])


class TestPaymentProviderRegistry(unittest.TestCase):
    def test_registry_marks_available_and_coming_soon_providers(self):
        registry = get_payment_provider_registry()

        self.assertEqual(registry["gateway_mock"]["status"], "available")
        self.assertEqual(registry["gateway_mock"]["display_name"], "Pembayaran Internal")
        self.assertFalse(registry["gateway_mock"]["capabilities"]["supports_payment_link"])
        self.assertEqual(registry["midtrans"]["status"], "available")
        self.assertEqual(registry["midtrans"]["display_name"], "Midtrans")
        self.assertTrue(registry["midtrans"]["capabilities"]["supports_payment_link"])
        for provider in ("xendit", "duitku", "doku", "tripay"):
            with self.subTest(provider=provider):
                self.assertEqual(registry[provider]["status"], "coming_soon")

    def test_gateway_mock_create_payment_remains_available(self):
        payment = create_payment("gateway_mock", "visit", "registry", 50000, "qris")

        self.assertEqual(payment["payment_provider"], "gateway_mock")
        self.assertEqual(payment["payment_status"], "pending")
        self.assertTrue(payment["payment_reference"])

    def test_coming_soon_providers_reject_create_payment(self):
        for provider in ("xendit", "duitku", "doku", "tripay"):
            with self.subTest(provider=provider):
                with self.assertRaisesRegex(ValueError, PROVIDER_UNAVAILABLE_MESSAGE):
                    create_payment(provider, "visit", "registry", 50000, "qris")

    def test_coming_soon_provider_files_do_not_contain_real_secrets(self):
        for provider in ("xendit", "duitku", "doku", "tripay"):
            with self.subTest(provider=provider):
                source = Path(f"helpers/payment_providers/{provider}.py").read_text(encoding="utf-8").lower()
                self.assertNotIn("secret_key", source)
                self.assertNotIn("api_key", source)
                self.assertNotIn("sk_live", source)


class TestMidtransGatewayEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def _create_visit(self, price=150000, payment_method="qris"):
        with db.Session() as session:
            patient = Patient(
                name=f"Midtrans Pasien {datetime.now().timestamp()}",
                phone=_unique_phone(),
                address="Test",
                gender="Laki-laki",
            )
            session.add(patient)
            session.flush()
            visit = Visit(
                patient_id=patient.id,
                date=datetime.now(),
                price=price,
                discount_applied=False,
                point_count=1,
                payment_status="unpaid",
                payment_method=payment_method,
                amount_paid=0,
                paid_at=None,
            )
            session.add(visit)
            session.commit()
            return visit.id

    def _fake_settings(self):
        class FakeSettings:
            settings = {
                "midtrans_server_key": "SB-MID-SERVER-KEY",
                "payment_gateway_environment": "sandbox",
            }

        return FakeSettings()

    def _create_midtrans_payment(self, price=150000, status_response=None):
        visit_id = self._create_visit(price=price, payment_method="qris")
        captured = {}

        def fake_json_request(url, method, payload=None):
            if method == "POST":
                captured["create_url"] = url
                captured["create_payload"] = payload
                return {
                    "token": "snap-token",
                    "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/snap-token",
                }
            captured["status_url"] = url
            return status_response or {"transaction_status": "pending"}

        patcher_settings = patch.object(midtrans, "AppSettings", return_value=self._fake_settings())
        patcher_request = patch.object(midtrans, "_json_request", side_effect=fake_json_request)
        with patcher_settings, patcher_request:
            response = self.client.post(
                "/payments/gateway/create",
                data={
                    "provider": "midtrans",
                    "source_type": "visit",
                    "source_id": str(visit_id),
                    "amount": str(price),
                    "payment_method": "qris",
                },
                headers=app_headers(),
            )
        self.assertEqual(response.status_code, 200)
        return response.json()["payment"], captured

    def test_midtrans_endpoint_create_qris_pending_payment(self):
        payment, captured = self._create_midtrans_payment(price=150000)

        self.assertEqual(payment["payment_provider"], "midtrans")
        self.assertEqual(payment["payment_method"], "qris")
        self.assertEqual(payment["payment_channel"], "qris")
        self.assertEqual(payment["payment_status"], "pending")
        self.assertEqual(payment["amount_paid"], 0)
        self.assertTrue(payment["payment_reference"].startswith("MIDTRANS-VISIT-"))
        self.assertEqual(payment["payment_url"], "https://app.sandbox.midtrans.com/snap/v2/vtweb/snap-token")
        self.assertEqual(captured["create_url"], midtrans.SNAP_SANDBOX_URL)
        self.assertEqual(captured["create_payload"]["enabled_payments"], ["qris"])
        self.assertEqual(captured["create_payload"]["transaction_details"]["gross_amount"], 150000)

    def test_midtrans_endpoint_status_pending_stays_pending(self):
        payment, _ = self._create_midtrans_payment(price=120000)

        with patch.object(midtrans, "AppSettings", return_value=self._fake_settings()), patch.object(
            midtrans,
            "_json_request",
            return_value={"transaction_status": "pending"},
        ):
            response = self.client.get(
                f"/payments/gateway/status/{payment['payment_reference']}",
                headers=app_headers(),
            )

        self.assertEqual(response.status_code, 200)
        updated = response.json()["payment"]
        self.assertEqual(updated["payment_status"], "pending")
        self.assertEqual(updated["payment_gateway_status"], "pending")
        self.assertEqual(updated["amount_paid"], 0)
        self.assertFalse(updated["paid_at"])

    def test_midtrans_endpoint_status_paid_variants_set_paid_fields(self):
        for raw_status in ("settlement", "capture"):
            payment, _ = self._create_midtrans_payment(price=130000)

            with patch.object(midtrans, "AppSettings", return_value=self._fake_settings()), patch.object(
                midtrans,
                "_json_request",
                return_value={"transaction_status": raw_status},
            ):
                response = self.client.get(
                    f"/payments/gateway/status/{payment['payment_reference']}",
                    headers=app_headers(),
                )

            self.assertEqual(response.status_code, 200)
            updated = response.json()["payment"]
            self.assertEqual(updated["payment_status"], "paid")
            self.assertEqual(updated["payment_gateway_status"], raw_status)
            self.assertEqual(updated["amount_paid"], 130000)
            self.assertTrue(updated["paid_at"])

    def test_midtrans_endpoint_status_expire_sets_expired(self):
        payment, _ = self._create_midtrans_payment(price=140000)

        with patch.object(midtrans, "AppSettings", return_value=self._fake_settings()), patch.object(
            midtrans,
            "_json_request",
            return_value={"transaction_status": "expire"},
        ):
            response = self.client.get(
                f"/payments/gateway/status/{payment['payment_reference']}",
                headers=app_headers(),
            )

        self.assertEqual(response.status_code, 200)
        updated = response.json()["payment"]
        self.assertEqual(updated["payment_status"], "expired")
        self.assertEqual(updated["payment_gateway_status"], "expire")
        self.assertEqual(updated["amount_paid"], 0)

    def test_midtrans_endpoint_status_failed_variants_set_failed(self):
        for raw_status in ("cancel", "deny", "failure"):
            payment, _ = self._create_midtrans_payment(price=150000)

            with patch.object(midtrans, "AppSettings", return_value=self._fake_settings()), patch.object(
                midtrans,
                "_json_request",
                return_value={"transaction_status": raw_status},
            ):
                response = self.client.get(
                    f"/payments/gateway/status/{payment['payment_reference']}",
                    headers=app_headers(),
                )

            self.assertEqual(response.status_code, 200)
            updated = response.json()["payment"]
            self.assertEqual(updated["payment_status"], "failed")
            self.assertEqual(updated["payment_gateway_status"], raw_status)
            self.assertEqual(updated["amount_paid"], 0)
