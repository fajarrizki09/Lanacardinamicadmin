import json
import os
import sys
import unittest
from pathlib import Path


sys.path.insert(0, os.path.dirname(__file__))
from api_test_utils import app_headers, client, db
from database import Herbal, HerbalTransaction, Visit


class TestPatientApi(unittest.TestCase):
    def setUp(self):
        self.client = client()

    def test_add_patient_with_valid_phone_succeeds_without_admin_pin(self):
        response = self.client.post(
            "/add_patient",
            data={
                "name": "Pasien API Test",
                "phone": "081234567801",
                "address": "Jl. Test",
                "gender": "Laki-laki",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_add_patient_rejects_invalid_phone(self):
        response = self.client.post(
            "/add_patient",
            data={
                "name": "Pasien Invalid Phone",
                "phone": "12345",
                "gender": "Perempuan",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Nomor HP", response.json()["detail"])

    def test_add_visit_without_payment_status_defaults_unpaid(self):
        patient_id = db.add_patient("Pasien Visit Default Unpaid", "081234567811", gender="Laki-laki")
        db.add_therapist("Terapis Visit Default", "Laki-laki", can_handle_any_gender=True)

        response = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertEqual(visit.payment_status, "unpaid")
        self.assertEqual(visit.payment_method, "other")
        self.assertEqual(visit.amount_paid, 0)
        self.assertIsNone(visit.paid_at)

    def _post_visit(self, patient_name, phone, gender="Laki-laki", **overrides):
        patient_id = db.add_patient(patient_name, phone, gender=gender)
        db.add_therapist(f"Terapis {patient_name}", gender, can_handle_any_gender=True)
        data = {
            "patient_id": patient_id,
            "point_count": 1,
            "price": 100000,
            "service_name": "Bekam",
            "manual_price_used": "true",
        }
        data.update(overrides)
        response = self.client.post(
            "/add_visit",
            data=data,
            headers=app_headers(),
        )
        return patient_id, response

    def test_add_visit_with_active_service_id_succeeds(self):
        service_id = db.add_service(
            "Layanan Aktif API Visit",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=75000,
        )
        patient_id, response = self._post_visit(
            "Pasien Service Aktif",
            "081234567821",
            service_id=str(service_id),
            service_name="Nama request harus diganti service",
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertEqual(visit.service_id, service_id)
        self.assertEqual(visit.service_name, "Layanan Aktif API Visit")

    def test_add_visit_with_inactive_service_id_is_rejected(self):
        service_id = db.add_service(
            "Layanan Nonaktif API Visit",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=75000,
        )
        db.update_service(
            service_id,
            "Layanan Nonaktif API Visit",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=75000,
            is_active=False,
        )
        patient_id, response = self._post_visit(
            "Pasien Service Nonaktif",
            "081234567822",
            service_id=str(service_id),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Layanan nonaktif tidak bisa dipakai untuk kunjungan baru.")
        with db.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).count()
        self.assertEqual(visits, 0)

    def test_add_visit_with_missing_service_id_is_rejected(self):
        patient_id, response = self._post_visit(
            "Pasien Service Hilang",
            "081234567823",
            service_id="99999999",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Layanan tidak ditemukan.")
        with db.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).count()
        self.assertEqual(visits, 0)

    def test_existing_visit_history_keeps_inactive_service_name(self):
        patient_id = db.add_patient("Pasien Riwayat Service Nonaktif", "081234567824", gender="Laki-laki")
        service_id = db.add_service(
            "Layanan Riwayat Aman",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=90000,
        )
        db.add_visit(patient_id, price=90000, point_count=1, service_id=service_id)
        db.update_service(
            service_id,
            "Layanan Riwayat Aman",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=90000,
            is_active=False,
        )

        visits = db.get_visits(patient_id)

        self.assertEqual(len(visits), 1)
        self.assertEqual(visits[0]["service_id"], service_id)
        self.assertEqual(visits[0]["service_name"], "Layanan Riwayat Aman")

    def test_add_visit_unpaid_allows_gateway_or_transfer_plan_methods(self):
        cases = [
            ("qris", "081234567813"),
            ("transfer", "081234567814"),
        ]
        for method, phone in cases:
            with self.subTest(method=method):
                patient_id, response = self._post_visit(
                    f"Pasien Unpaid {method}",
                    phone,
                    payment_status="unpaid",
                    payment_method=method,
                )

                self.assertEqual(response.status_code, 200)
                with db.Session() as session:
                    visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
                self.assertEqual(visit.payment_status, "unpaid")
                self.assertEqual(visit.payment_method, method)
                self.assertEqual(visit.amount_paid, 0)
                self.assertIsNone(visit.paid_at)

    def test_add_visit_unpaid_cash_is_rejected(self):
        _, response = self._post_visit(
            "Pasien Unpaid Cash Reject",
            "081234567815",
            payment_status="unpaid",
            payment_method="cash",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "Metode Tunai hanya boleh digunakan jika pembayaran sudah lunas atau sebagian.",
        )

    def test_add_visit_paid_cash_sets_full_payment(self):
        patient_id, response = self._post_visit(
            "Pasien Paid Cash",
            "081234567816",
            payment_status="paid",
            payment_method="cash",
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertEqual(visit.payment_status, "paid")
        self.assertEqual(visit.payment_method, "cash")
        self.assertEqual(visit.amount_paid, 100000)
        self.assertTrue(visit.paid_at)

    def test_add_visit_partial_allows_cash_and_qris_when_amount_valid(self):
        cases = [
            ("cash", "081234567817"),
            ("qris", "081234567818"),
        ]
        for method, phone in cases:
            with self.subTest(method=method):
                patient_id, response = self._post_visit(
                    f"Pasien Partial {method}",
                    phone,
                    payment_status="partial",
                    payment_method=method,
                    amount_paid="50000",
                )

                self.assertEqual(response.status_code, 200)
                with db.Session() as session:
                    visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
                self.assertEqual(visit.payment_status, "partial")
                self.assertEqual(visit.payment_method, method)
                self.assertEqual(visit.amount_paid, 50000)
                self.assertTrue(visit.paid_at)

    def test_add_visit_paid_voucher_counts_discounted_revenue(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        patient_id = db.add_patient("Pasien Paid Voucher Manual", "081234567825", gender="Laki-laki")
        db.add_therapist("Terapis Paid Voucher Manual", "Laki-laki", can_handle_any_gender=True)
        db.add_discount_rule({
            "name": "Voucher Paid Manual API",
            "type": "voucher",
            "condition_value": None,
            "discount_type": "fixed",
            "discount_value": 10000,
            "voucher_code": "PAIDMANUAL10",
            "is_active": True,
            "priority": -900,
        })

        response = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
                "voucher_code": "PAIDMANUAL10",
                "payment_status": "paid",
                "payment_method": "cash",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertEqual(visit.payment_status, "paid")
        self.assertEqual(visit.payment_method, "cash")
        self.assertEqual(visit.price, 90000)
        self.assertEqual(visit.amount_paid, 90000)
        self.assertEqual(float(db.get_dashboard_stats()["total_income"]) - before_income, 90000)

    def test_add_visit_unpaid_with_herbal_does_not_count_herbal_revenue(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        herbal_id = db.add_herbal("Herbal Visit Unpaid Manual", "botol", 25000, stock=5, cost_price=10000)
        patient_id, response = self._post_visit(
            "Pasien Visit Herbal Unpaid",
            "081234567826",
            payment_status="unpaid",
            payment_method="transfer",
            herbal_items=json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
            tx = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.visit_id == visit.id, HerbalTransaction.transaction_type == "sale")
                .one()
            )
        self.assertEqual(visit.payment_status, "unpaid")
        self.assertEqual(visit.amount_paid, 0)
        self.assertEqual(tx.payment_status, "unpaid")
        self.assertEqual(tx.payment_method, "transfer")
        self.assertEqual(tx.amount_paid, 0)
        self.assertEqual(float(db.get_dashboard_stats()["total_income"]) - before_income, 0)

    def test_add_visit_partial_with_herbal_allocates_paid_amount_once(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        herbal_id = db.add_herbal("Herbal Visit Partial Manual", "botol", 25000, stock=5, cost_price=10000)
        patient_id, response = self._post_visit(
            "Pasien Visit Herbal Partial",
            "081234567827",
            payment_status="partial",
            payment_method="cash",
            amount_paid="120000",
            herbal_items=json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
            tx = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.visit_id == visit.id, HerbalTransaction.transaction_type == "sale")
                .one()
            )
        self.assertEqual(visit.payment_status, "partial")
        self.assertEqual(visit.amount_paid, 100000)
        self.assertEqual(tx.payment_status, "partial")
        self.assertEqual(tx.amount_paid, 20000)
        self.assertEqual(float(db.get_dashboard_stats()["total_income"]) - before_income, 120000)

    def test_add_free_visit_forces_paid_even_if_unpaid_submitted(self):
        patient_id, response = self._post_visit(
            "Pasien Visit Gratis Paid",
            "081234567812",
            gender="Perempuan",
            price=0,
            is_free_visit="true",
            free_visit_reason="Bonus kontrol",
            payment_status="unpaid",
            payment_method="cash",
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertTrue(visit.is_free_visit)
        self.assertEqual(visit.payment_status, "paid")
        self.assertEqual(visit.payment_method, "free")
        self.assertEqual(visit.amount_paid, 0)
        self.assertTrue(visit.paid_at)

    def test_add_free_visit_with_herbal_keeps_all_manual_revenue_zero(self):
        before_income = float(db.get_dashboard_stats()["total_income"])
        herbal_id = db.add_herbal("Herbal Visit Free Manual", "botol", 25000, stock=5, cost_price=10000)
        patient_id, response = self._post_visit(
            "Pasien Visit Herbal Free",
            "081234567828",
            gender="Perempuan",
            price=0,
            is_free_visit="true",
            free_visit_reason="Bonus kontrol",
            payment_status="paid",
            payment_method="free",
            herbal_items=json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
        )

        self.assertEqual(response.status_code, 200)
        with db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
            tx = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.visit_id == visit.id, HerbalTransaction.transaction_type == "sale")
                .one()
            )
        self.assertTrue(visit.is_free_visit)
        self.assertEqual(visit.payment_status, "paid")
        self.assertEqual(visit.payment_method, "free")
        self.assertEqual(visit.amount_paid, 0)
        self.assertEqual(tx.payment_status, "paid")
        self.assertEqual(tx.payment_method, "free")
        self.assertEqual(tx.amount_paid, 0)
        self.assertEqual(float(db.get_dashboard_stats()["total_income"]) - before_income, 0)

    def test_add_visit_double_click_modal_key_replays_without_duplicate_visit(self):
        patient_id, response = self._post_visit(
            "Pasien Visit Idempotent",
            "081234567829",
            payment_status="paid",
            payment_method="cash",
            idempotency_key="visit-idempotent-regression",
        )

        replay = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
                "payment_status": "paid",
                "payment_method": "cash",
                "idempotency_key": "visit-idempotent-regression",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["idempotent_replay"])
        with db.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).all()
        self.assertEqual(len(visits), 1)
        self.assertFalse(visits[0].invoice_path)

    def test_add_visit_replay_key_with_herbal_does_not_reduce_stock_twice(self):
        herbal_id = db.add_herbal("Herbal Visit Replay Guard", "botol", 25000, stock=5, cost_price=10000)
        patient_id, response = self._post_visit(
            "Pasien Visit Herbal Replay",
            "081234567833",
            payment_status="paid",
            payment_method="cash",
            herbal_items=json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
            idempotency_key="visit-herbal-replay-regression",
        )
        replay = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
                "payment_status": "paid",
                "payment_method": "cash",
                "herbal_items": json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
                "idempotency_key": "visit-herbal-replay-regression",
            },
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(replay.status_code, 200)
        self.assertTrue(replay.json()["idempotent_replay"])
        with db.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).all()
            transactions = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                .all()
            )
            herbal = session.get(Herbal, herbal_id)
        self.assertEqual(len(visits), 1)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(herbal.stock, 3)

    def test_add_visit_pending_idempotency_key_is_rejected(self):
        from api.routes import patients as patients_route

        key = "visit-pending-regression"
        patients_route._reserve_visit_idempotency_key(key)
        try:
            patient_id = db.add_patient("Pasien Visit Pending Key", "081234567834", gender="Laki-laki")
            db.add_therapist("Terapis Visit Pending Key", "Laki-laki", can_handle_any_gender=True)
            response = self.client.post(
                "/add_visit",
                data={
                    "patient_id": patient_id,
                    "point_count": 1,
                    "price": 100000,
                    "service_name": "Bekam",
                    "manual_price_used": "true",
                    "payment_status": "paid",
                    "payment_method": "cash",
                    "idempotency_key": key,
                },
                headers=app_headers(),
            )
        finally:
            patients_route._release_visit_idempotency_key(key)

        self.assertEqual(response.status_code, 409)
        self.assertIn("sedang diproses", response.json()["detail"])
        with db.Session() as session:
            visit_count = session.query(Visit).filter(Visit.patient_id == patient_id).count()
        self.assertEqual(visit_count, 0)

    def test_add_visit_without_idempotency_key_allows_similar_visits(self):
        herbal_id = db.add_herbal("Herbal Visit Duplicate Guard", "botol", 25000, stock=5, cost_price=10000)
        patient_id = db.add_patient("Pasien Visit Duplicate Guard", "081234567830", gender="Laki-laki")
        db.add_therapist("Terapis Visit Duplicate Guard", "Laki-laki", can_handle_any_gender=True)
        data = {
            "patient_id": patient_id,
            "point_count": 1,
            "price": 100000,
            "service_name": "Bekam",
            "manual_price_used": "true",
            "payment_status": "paid",
            "payment_method": "cash",
            "herbal_items": json.dumps([{"herbal_id": herbal_id, "quantity": 2}]),
        }

        first = self.client.post("/add_visit", data=data, headers=app_headers())
        duplicate = self.client.post("/add_visit", data=data, headers=app_headers())

        self.assertEqual(first.status_code, 200)
        self.assertEqual(duplicate.status_code, 200)
        with db.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).all()
            transactions = (
                session.query(HerbalTransaction)
                .filter(HerbalTransaction.herbal_id == herbal_id, HerbalTransaction.transaction_type == "sale")
                .all()
            )
            herbal = session.get(Herbal, herbal_id)
        self.assertEqual(len(visits), 2)
        self.assertEqual(len(transactions), 2)
        self.assertEqual(herbal.stock, 1)

    def test_add_visit_recent_but_different_request_is_allowed(self):
        patient_id = db.add_patient("Pasien Visit Berbeda", "081234567831", gender="Laki-laki")
        db.add_therapist("Terapis Visit Berbeda", "Laki-laki", can_handle_any_gender=True)
        base_data = {
            "patient_id": patient_id,
            "point_count": 1,
            "price": 100000,
            "service_name": "Bekam",
            "manual_price_used": "true",
            "payment_status": "paid",
            "payment_method": "cash",
        }

        first = self.client.post(
            "/add_visit",
            data={**base_data, "medical_notes": "Sesi pertama"},
            headers=app_headers(),
        )
        second = self.client.post(
            "/add_visit",
            data={**base_data, "medical_notes": "Sesi lanjutan"},
            headers=app_headers(),
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        with db.Session() as session:
            visit_count = session.query(Visit).filter(Visit.patient_id == patient_id).count()
        self.assertEqual(visit_count, 2)

    def test_add_visit_validation_error_releases_idempotency_key(self):
        patient_id = db.add_patient("Pasien Visit Key Retry", "081234567832", gender="Laki-laki")
        db.add_therapist("Terapis Visit Key Retry", "Laki-laki", can_handle_any_gender=True)
        invalid = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
                "payment_status": "unpaid",
                "payment_method": "cash",
                "idempotency_key": "visit-idempotent-validation-retry",
            },
            headers=app_headers(),
        )
        valid = self.client.post(
            "/add_visit",
            data={
                "patient_id": patient_id,
                "point_count": 1,
                "price": 100000,
                "service_name": "Bekam",
                "manual_price_used": "true",
                "payment_status": "paid",
                "payment_method": "cash",
                "idempotency_key": "visit-idempotent-validation-retry",
            },
            headers=app_headers(),
        )

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(valid.status_code, 200)
        with db.Session() as session:
            visit_count = session.query(Visit).filter(Visit.patient_id == patient_id).count()
        self.assertEqual(visit_count, 1)

    def test_visit_form_has_double_submit_guard_and_unlock_path(self):
        source = Path("api/static/modules/patients.js").read_text(encoding="utf-8")
        app_source = Path("api/static/app.js").read_text(encoding="utf-8")

        self.assertIn("window._visitSubmitInProgress", source)
        self.assertIn("window._visitConfirmInProgress", source)
        self.assertIn("window._visitConfirmInProgress = true;", source)
        self.assertIn("setVisitSubmitLoading(true);", source)
        self.assertIn("resetVisitSubmitLoading();", source)
        self.assertIn("formData.set('idempotency_key', getVisitIdempotencyKey(form));", source)
        self.assertIn("typeof resetVisitSubmitLoading === 'function'", app_source)

    def test_visit_form_initial_payment_state_is_unpaid_and_not_cash(self):
        source = Path("api/static/modules/patients.js").read_text(encoding="utf-8")

        self.assertIn('<option value="unpaid" selected>Belum Dibayar</option>', source)
        self.assertIn('<option value="other" selected>Lainnya / Belum Ditentukan</option>', source)
        self.assertNotIn('<option value="cash" selected>', source)
        self.assertIn("const directMethods = new Set(['cash', 'debit', 'credit_card']);", source)
        self.assertIn("paymentHint.textContent = 'Belum ada pembayaran. Tagihan belum masuk pendapatan.';", source)

    def test_visit_form_free_toggle_disables_voucher_and_sets_free_method(self):
        source = Path("api/static/modules/patients.js").read_text(encoding="utf-8")

        self.assertIn("methodSelect.value = 'free';", source)
        self.assertIn("voucherInput.disabled = true;", source)
        self.assertIn("formData.set('voucher_code', '');", source)


    def test_visit_confirmation_previews_automatic_discount_rule(self):
        source = Path("api/static/modules/patients.js").read_text(encoding="utf-8")

        self.assertIn("async function getVisitDiscountPreview", source)
        self.assertIn("/discount_rules/simulate?", source)
        self.assertIn("patient_id: String(patient.id || formData.get('patient_id') || '')", source)
        self.assertIn("Voucher / Diskon Otomatis", source)
        self.assertIn("Aturan aktif", source)
        self.assertIn("Biaya setelah diskon", source)
        self.assertIn("const total = discountedVisitPrice + herbalSubtotal;", source)

    def test_discount_simulation_uses_patient_visit_history(self):
        rule_name = "Preview Riwayat Pasien API"
        db.add_discount_rule({
            "name": rule_name,
            "type": "visit_count",
            "condition_value": 2,
            "discount_type": "percent",
            "discount_value": 15,
            "is_active": True,
            "priority": -500,
        })
        patient_id = db.add_patient("Pasien Preview Diskon", "081234567899", gender="Laki-laki")
        db.add_visit(patient_id, price=100000, point_count=1, service_name="Bekam")

        response = self.client.get(
            f"/discount_rules/simulate?price=250000&visit_count=0&patient_id={patient_id}",
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        selected = response.json()["selected"]
        self.assertIsNotNone(selected)
        self.assertEqual(selected["name"], rule_name)
        self.assertEqual(selected["final_price"], 212500)

    def test_discount_simulation_includes_voucher_usage_count_safely(self):
        patient_id = db.add_patient("Pasien Preview Voucher Usage", "081234567898", gender="Laki-laki")
        rule_id = db.add_discount_rule({
            "name": "Preview Voucher Usage API",
            "type": "voucher",
            "condition_value": None,
            "discount_type": "fixed",
            "discount_value": 10000,
            "voucher_code": "PREVIEWUSAGE",
            "usage_limit": 5,
            "per_patient_limit": 2,
            "target_patient_ids": [patient_id],
            "is_active": True,
            "priority": -600,
        })
        db.add_visit(
            patient_id,
            price=100000,
            point_count=1,
            service_name="Bekam",
            voucher_code="PREVIEWUSAGE",
            discount_rule_id=rule_id,
        )

        response = self.client.get(
            f"/discount_rules/simulate?price=100000&visit_count=0&patient_id={patient_id}&voucher_code=PREVIEWUSAGE",
            headers=app_headers(),
        )

        self.assertEqual(response.status_code, 200)
        selected = response.json()["selected"]
        self.assertIsNotNone(selected)
        self.assertEqual(selected["name"], "Preview Voucher Usage API")
        self.assertEqual(selected["usage_count"], 1)
        self.assertEqual(selected["target_patient_ids"], [patient_id])
        self.assertEqual(selected["final_price"], 90000)

    def test_add_patient_rejects_duplicate_phone_via_api(self):
        """Nomor HP yang sudah terdaftar harus ditolak oleh endpoint /add_patient."""
        phone = "081234560001"
        self.client.post(
            "/add_patient",
            data={"name": "Pasien Pertama Dup", "phone": phone, "gender": "Laki-laki"},
            headers=app_headers(),
        )
        response = self.client.post(
            "/add_patient",
            data={"name": "Pasien Duplikat HP", "phone": phone, "gender": "Perempuan"},
            headers=app_headers(),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("sudah terdaftar", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
