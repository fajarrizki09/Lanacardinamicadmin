import os
import io
import logging
import re
import tempfile
import time
import unittest
from datetime import datetime, timedelta

import openpyxl
from reportlab.lib.units import mm
from sqlalchemy import text

from database import CRMWhatsAppLog, Database, HerbalTransaction, InventoryTransaction, PatientContactPreference, Visit
from helpers.revenue_rules import calculate_revenue_amount
from helpers.backup_helper import BackupHelper
from helpers.crm_analysis_helper import build_crm_patients, create_crm_whatsapp_log, get_voucher_for_crm_message
from helpers.invoice_helper import InvoiceHelper
from helpers.owner_report_helper import build_owner_report_summary
from helpers.report_excel_helper import build_report_excel, safe_excel_filename
from helpers.support_helper import get_support_app_info, folder_path_for_kind
from api.routes.data import _build_operational_export
from api.routes.patients import _resolve_patient_update_phone
from db_models import AuditLog


class IsolatedDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test_data.db")
        self.db = Database(f"sqlite:///{self.db_path}")

    def tearDown(self):
        if hasattr(self, "db"):
            self.db.engine.dispose()
        for name, logger in logging.Logger.manager.loggerDict.items():
            if not (name.startswith("lancar.migration.") or name.startswith("lancar.audit.")) or not hasattr(logger, "handlers"):
                continue
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)
        self.tmp.cleanup()

    def app_meta_value(self, key):
        with self.db.Session() as session:
            return session.execute(
                text("SELECT value FROM app_meta WHERE key = :key"),
                {"key": key},
            ).scalar()


class TestDatabaseInitialization(IsolatedDatabaseTestCase):
    def test_app_meta_db_version_and_idempotent_migration(self):
        self.assertEqual(self.app_meta_value("db_version"), str(Database.DB_SCHEMA_VERSION))

        self.db._migrate_existing_data()
        self.assertEqual(self.app_meta_value("db_version"), str(Database.DB_SCHEMA_VERSION))

        self.db.engine.dispose()
        self.db = Database(f"sqlite:///{self.db_path}")
        self.assertEqual(self.app_meta_value("db_version"), str(Database.DB_SCHEMA_VERSION))

    def test_audit_logs_table_exists(self):
        with self.db.Session() as session:
            exists = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
            ).scalar()
        self.assertEqual(exists, "audit_logs")

    def test_voucher_usage_schema_exists(self):
        with self.db.Session() as session:
            table_exists = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='voucher_usages'")
            ).scalar()
            target_table_exists = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='voucher_patient_targets'")
            ).scalar()
            usage_limit_col = session.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('discount_rules') WHERE name = 'usage_limit'")
            ).scalar()
            per_patient_col = session.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('discount_rules') WHERE name = 'per_patient_limit'")
            ).scalar()

        self.assertEqual(table_exists, "voucher_usages")
        self.assertEqual(target_table_exists, "voucher_patient_targets")
        self.assertEqual(usage_limit_col, 1)
        self.assertEqual(per_patient_col, 1)

    def test_patients_created_at_column_exists_and_is_populated(self):
        patient_id = self.db.add_patient("Pasien Created At", "081211112222")

        with self.db.Session() as session:
            column_exists = session.execute(
                text("SELECT COUNT(*) FROM pragma_table_info('patients') WHERE name = 'created_at'")
            ).scalar()
            created_at = session.execute(
                text("SELECT created_at FROM patients WHERE id = :id"),
                {"id": patient_id},
            ).scalar()

        self.assertEqual(column_exists, 1)
        self.assertTrue(str(created_at or "").strip())


class TestAuditLogFlows(IsolatedDatabaseTestCase):
    def test_log_audit_creates_record(self):
        audit_id = self.db.log_audit(
            "test_action",
            "test_entity",
            "123",
            "Audit test",
            {"safe": "value"},
        )

        self.assertIsNotNone(audit_id)
        rows = self.db.get_audit_logs(action="test_action")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entity_type"], "test_entity")
        self.assertEqual(rows[0]["metadata"]["safe"], "value")

    def test_log_audit_failure_does_not_raise(self):
        original_session = self.db.Session

        def broken_session():
            raise RuntimeError("audit db unavailable")

        self.db.Session = broken_session
        try:
            self.assertIsNone(self.db.log_audit("broken", "audit"))
        finally:
            self.db.Session = original_session

    def test_add_patient_writes_audit_log(self):
        patient_id = self.db.add_patient("Pasien Audit", "081299999999")

        rows = self.db.get_audit_logs(action="patient_created", entity_type="patient")
        self.assertTrue(any(row["entity_id"] == str(patient_id) for row in rows))

    def test_required_audit_failure_raises(self):
        original_session = self.db.Session

        def broken_session():
            raise RuntimeError("audit db unavailable")

        self.db.Session = broken_session
        try:
            with self.assertRaises(RuntimeError):
                self.db.log_audit("broken", "audit", required=True)
        finally:
            self.db.Session = original_session


class TestFlowchartSyncRegressions(IsolatedDatabaseTestCase):
    def test_invoice_pdf_status_becomes_stale_after_payment_update(self):
        from api.routes.invoices import _pdf_status

        generated_at = datetime.now()
        updated_at = generated_at + timedelta(minutes=5)

        self.assertEqual(_pdf_status("active", "invoice.pdf", True, generated_at, None), "fresh")
        self.assertEqual(_pdf_status("active", "invoice.pdf", True, generated_at, updated_at), "stale")
        self.assertEqual(_pdf_status("active", "", False, None, None), "not_generated")
        self.assertEqual(_pdf_status("active", "invoice.pdf", False, generated_at, None), "missing")
        self.assertEqual(_pdf_status("void", "invoice.pdf", True, generated_at, updated_at), "void")

    def test_revenue_rule_statuses(self):
        self.assertEqual(calculate_revenue_amount(100000, 0, "paid", "active"), 100000)
        self.assertEqual(calculate_revenue_amount(100000, 40000, "partial", "active"), 40000)
        self.assertEqual(calculate_revenue_amount(100000, 0, "pending", "active"), 0)
        self.assertEqual(calculate_revenue_amount(100000, 0, "unpaid", "active"), 0)
        self.assertEqual(calculate_revenue_amount(100000, 100000, "paid", "void"), 0)

    def test_herbal_visit_link_not_counted_as_standalone_revenue(self):
        patient_id = self.db.add_patient("Pasien Revenue", f"08{time.time_ns() % 10_000_000_000:010d}")
        herbal_id = self.db.add_herbal("Herbal Revenue", "pcs", price=50000, stock=10)
        self.db.add_visit(
            patient_id,
            price=150000,
            point_count=1,
            service_name="Layanan + Herbal",
            herbal_items=[{"herbal_id": herbal_id, "quantity": 1}],
        )
        self.db.add_herbal_sale([{"herbal_id": herbal_id, "quantity": 1}], buyer_name="Umum")

        with self.db.Session() as session:
            report = build_owner_report_summary(session)

        self.assertEqual(report["summary"]["visit_revenue"], 200000)
        self.assertEqual(report["summary"]["herbal_revenue"], 50000)
        self.assertEqual(report["summary"]["total_revenue"], 250000)

    def test_inventory_transaction_records_visit_id_for_service_usage(self):
        inventory_id = self.db.add_inventory_item("Kasa Visit Link", "pcs", min_stock=1, initial_qty=10)
        service_id = self.db.add_service(
            "Layanan Inventory Link",
            price_per_unit=100000,
            inventory_usage=[{"inventory_id": inventory_id, "quantity": 2}],
        )
        patient_id = self.db.add_patient("Pasien Inventory Link", f"08{time.time_ns() % 10_000_000_000:010d}")
        self.db.add_visit(patient_id, price=100000, point_count=1, service_id=service_id)

        with self.db.Session() as session:
            tx = session.query(InventoryTransaction).filter(InventoryTransaction.inventory_id == inventory_id).order_by(InventoryTransaction.id.desc()).first()

        self.assertIsNotNone(tx)
        self.assertEqual(tx.transaction_type, "auto_usage")
        self.assertIsNotNone(tx.visit_id)

    def test_crm_preference_and_send_lock_skip_logs(self):
        patient_id = self.db.add_patient("Pasien Jangan Dihubungi", f"08{time.time_ns() % 10_000_000_000:010d}")
        with self.db.Session() as session:
            session.add(PatientContactPreference(patient_id=patient_id, jangan_dihubungi=True, updated_at=datetime.now()))
            session.commit()
            row = next(item for item in build_crm_patients(session) if item["id"] == patient_id)
            result = create_crm_whatsapp_log(session, row, template_type="routine")
            self.assertTrue(result["blocked"])
            self.assertEqual(result["status"], "skipped_preference")
            self.assertFalse(result["whatsapp_url"])

        patient_id_2 = self.db.add_patient("Pasien Lock", f"08{time.time_ns() % 10_000_000_000:010d}")
        with self.db.Session() as session:
            session.add(CRMWhatsAppLog(
                patient_id=patient_id_2,
                phone="628111111111",
                message_type="routine",
                message="halo",
                whatsapp_url="https://wa.me/628111111111",
                status="confirmed_sent",
                confirmed_at=datetime.now(),
            ))
            session.commit()
            row = next(item for item in build_crm_patients(session) if item["id"] == patient_id_2)
            result = create_crm_whatsapp_log(session, row, template_type="routine")
            self.assertTrue(result["blocked"])
            self.assertEqual(result["status"], "skipped_send_lock")
            self.assertFalse(result["whatsapp_url"])


class TestDemoDataFlows(IsolatedDatabaseTestCase):
    def test_seed_demo_data_creates_expected_records(self):
        result = self.db.seed_demo_data()

        self.assertTrue(result["created"])
        self.assertEqual(result["patients"], 5)
        self.assertGreaterEqual(result["services"], 1)
        self.assertGreaterEqual(result["herbals"], 1)
        self.assertGreaterEqual(result["inventory"], 1)
        self.assertGreaterEqual(result["visits"], 1)

        patients = self.db.get_all_patients()
        self.assertEqual(len([p for p in patients if str(p.phone).startswith("08990000000")]), 5)

        audit_rows = self.db.get_audit_logs(action="demo_data_seeded", entity_type="demo_data")
        self.assertEqual(len(audit_rows), 1)

    def test_seed_demo_data_is_guarded_on_second_run(self):
        first = self.db.seed_demo_data()
        patient_count = len(self.db.get_all_patients())

        second = self.db.seed_demo_data()

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(len(self.db.get_all_patients()), patient_count)


class TestOwnerReportFlows(IsolatedDatabaseTestCase):
    def test_owner_report_empty_data_does_not_error(self):
        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="month")

        self.assertIn("summary", report)
        self.assertEqual(report["summary"]["total_revenue"], 0)
        self.assertEqual(report["summary"]["total_visits"], 0)
        self.assertEqual(report["summary"]["new_patients"], 0)
        self.assertIsInstance(report["top_services"], list)
        self.assertIsInstance(report["top_herbals"], list)
        self.assertIsInstance(report["patients_need_followup"], list)

    def test_owner_report_demo_data_has_summary_fields(self):
        self.db.seed_demo_data()

        with self.db.Session() as session:
            report = build_owner_report_summary(session, period="month")

        summary = report["summary"]
        for key in (
            "total_revenue",
            "total_visits",
            "unique_patients",
            "new_patients",
            "active_patients",
            "patients_need_followup",
            "dormant_patients",
            "total_whatsapp_followups",
            "followup_booked",
        ):
            self.assertIn(key, summary)
            self.assertIsInstance(summary[key], (int, float))
        self.assertGreater(summary["total_visits"], 0)
        self.assertGreater(summary["total_revenue"], 0)
        self.assertGreater(len(report["top_services"]), 0)
        self.assertGreater(len(report["top_loyal_patients"]), 0)

    def test_owner_report_can_choose_new_patient_source(self):
        patient_id = self.db.add_patient("Pasien Source", "081277778888")
        self.db.add_visit(patient_id, 100000, point_count=1, service_name="Terapi Source")

        with self.db.Session() as session:
            session.execute(
                text("UPDATE patients SET created_at = '2000-01-01 12:00:00' WHERE id = :id"),
                {"id": patient_id},
            )
            session.commit()

            by_registration = build_owner_report_summary(
                session,
                date_from="2000-01-01",
                date_to="2000-01-01",
                new_patient_source="registration",
            )
            by_first_visit = build_owner_report_summary(
                session,
                date_from=datetime.now().strftime("%Y-%m-%d"),
                date_to=datetime.now().strftime("%Y-%m-%d"),
                new_patient_source="first_visit",
            )

        self.assertEqual(by_registration["summary"]["new_patients"], 1)
        self.assertEqual(by_registration["period"]["new_patient_source"], "registration")
        self.assertEqual(by_first_visit["summary"]["new_patients"], 1)
        self.assertEqual(by_first_visit["period"]["new_patient_source"], "first_visit")


class TestReportExcelExportFlows(IsolatedDatabaseTestCase):
    def test_export_owner_summary_creates_valid_xlsx(self):
        self.db.seed_demo_data()

        with self.db.Session() as session:
            filename, content = build_report_excel(session, report_type="owner_summary", period="month")

        self.assertTrue(filename.endswith(".xlsx"))
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = workbook.active
        self.assertEqual(sheet["A1"].value, "Laporan Owner")
        self.assertEqual(sheet["A5"].value, "Metrik")
        self.assertEqual(sheet["B5"].value, "Nilai")

    def test_export_empty_data_keeps_header_and_message(self):
        with self.db.Session() as session:
            filename, content = build_report_excel(session, report_type="visits", period="month")

        self.assertTrue(filename.endswith(".xlsx"))
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = workbook.active
        self.assertEqual(sheet["A5"].value, "Tanggal")
        self.assertEqual(sheet["A6"].value, "Tidak ada data untuk periode ini.")

    def test_safe_excel_filename_is_windows_friendly(self):
        filename = safe_excel_filename("owner_summary", "2026/05: klinik?*")

        self.assertEqual(filename, "laporan_owner_2026-05-klinik.xlsx")
        self.assertNotRegex(filename, r'[<>:"/\\|?*]')

    def test_operational_export_includes_herbal_and_inventory_sheets(self):
        self.db.seed_demo_data()
        original_db = __import__("api.routes.data", fromlist=["db"]).db
        data_route = __import__("api.routes.data", fromlist=["db"])
        data_route.db = self.db
        try:
            filename, content, _media_type = _build_operational_export("xlsx", "all")
        finally:
            data_route.db = original_db

        self.assertTrue(filename.startswith("export_semua_data_"))
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        self.assertIn("Herbal", workbook.sheetnames)
        self.assertIn("Transaksi Herbal", workbook.sheetnames)
        self.assertIn("Inventory", workbook.sheetnames)
        self.assertIn("Transaksi Inventory", workbook.sheetnames)


class TestSupportInfoFlows(IsolatedDatabaseTestCase):
    def test_support_app_info_contains_safe_paths_and_no_license_key(self):
        info = get_support_app_info(self.db)

        self.assertIn("app_version", info)
        self.assertTrue(info["database_path"].endswith("test_data.db"))
        self.assertIn("backup_dir", info)
        self.assertIn("logs_dir", info)
        self.assertIn("exports_dir", info)
        self.assertIn("support", info)
        self.assertNotIn("license_key", info.get("license", {}))

    def test_support_folder_kind_is_limited(self):
        backup_path = folder_path_for_kind("backups", self.db)
        self.assertTrue(backup_path)

        with self.assertRaises(ValueError):
            folder_path_for_kind("../../", self.db)


class TestPatientAndVisitFlows(IsolatedDatabaseTestCase):
    def test_add_patient_success_and_duplicate_phone_rejected(self):
        patient_id = self.db.add_patient(
            "Pasien Test",
            "081234567890",
            address="Alamat Test",
            gender="Laki-laki",
        )

        patients = self.db.get_all_patients()
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].id, patient_id)

        with self.assertRaises(Exception):
            self.db.add_patient("Pasien Duplikat", "081234567890")

    def test_add_visit_links_patient_and_service(self):
        patient_id = self.db.add_patient("Pasien Kunjungan", "081200000001")
        service_id = self.db.add_service(
            "Terapi Test",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=100000,
        )

        final_price, discount_applied, discount_name = self.db.add_visit(
            patient_id,
            price=100000,
            point_count=1,
            service_id=service_id,
            service_name="Terapi Test",
        )

        visits = self.db.get_visits(patient_id)
        self.assertEqual(final_price, 100000)
        self.assertFalse(discount_applied)
        self.assertIsNone(discount_name)
        self.assertEqual(len(visits), 1)
        self.assertEqual(visits[0]["service_id"], service_id)
        self.assertEqual(visits[0]["service_name"], "Terapi Test")

    def test_free_visit_is_always_marked_paid(self):
        patient_id = self.db.add_patient("Pasien Gratis Lunas", "081200000011")

        self.db.add_visit(
            patient_id,
            price=0,
            point_count=1,
            service_name="Bekam",
            is_free_visit=True,
            free_visit_reason="Bonus kontrol",
            payment_status="unpaid",
        )

        with self.db.Session() as session:
            visit = session.query(Visit).filter(Visit.patient_id == patient_id).one()
        self.assertTrue(visit.is_free_visit)
        self.assertEqual(visit.payment_status, "paid")
        self.assertEqual(visit.payment_method, "free")
        self.assertEqual(visit.amount_paid, 0)
        self.assertTrue(visit.paid_at)

    def test_database_add_visit_rejects_unpaid_cash(self):
        patient_id = self.db.add_patient("Pasien DB Unpaid Cash", "081200000012")

        with self.assertRaisesRegex(ValueError, "Metode Tunai hanya boleh digunakan"):
            self.db.add_visit(
                patient_id,
                price=100000,
                point_count=1,
                service_name="Bekam",
                payment_status="unpaid",
                payment_method="cash",
            )

    def test_full_patient_update_keeps_existing_temp_phone_when_blank(self):
        self.assertEqual(
            _resolve_patient_update_phone("", "TEMP-OLD-QA"),
            "TEMP-OLD-QA",
        )

    def test_full_patient_update_validates_new_phone_when_provided(self):
        self.assertEqual(
            _resolve_patient_update_phone("081234567890", "TEMP-OLD-QA"),
            "081234567890",
        )
        with self.assertRaises(ValueError):
            _resolve_patient_update_phone("6281234567890", "TEMP-OLD-QA")

    def test_full_patient_update_still_rejects_blank_non_temp_phone(self):
        with self.assertRaises(ValueError):
            _resolve_patient_update_phone("", "081234567890")

    # ── Bug fix: duplicate phone ──────────────────────────────────────────────

    def test_add_patient_new_unique_phone_succeeds(self):
        """Pasien baru dengan HP unik harus berhasil disimpan."""
        pid = self.db.add_patient("Pasien Baru HP Unik", "081299991111", gender="Laki-laki")
        self.assertIsNotNone(pid)
        patients = self.db.get_all_patients()
        self.assertEqual(len([p for p in patients if p.phone == "081299991111"]), 1)

    def test_add_patient_duplicate_phone_raises_value_error(self):
        """HP yang sudah ada harus tolak dengan ValueError yang jelas."""
        self.db.add_patient("Pasien Asli", "081299992222", gender="Laki-laki")
        self.assertTrue(self.db.patient_phone_exists(" 081299992222 "))
        with self.assertRaises(ValueError) as ctx:
            self.db.add_patient("Pasien Duplikat HP", " 081299992222 ", gender="Perempuan")
        self.assertIn("sudah terdaftar", str(ctx.exception))

    def test_temp_phone_does_not_trigger_duplicate_check(self):
        """HP bertipe TEMP tidak boleh dicek duplikat karena unik per-auto-generate."""
        pid1 = self.db.add_patient("Pasien Temp 1", "TEMP-AAA-001", gender="Laki-laki")
        pid2 = self.db.add_patient("Pasien Temp 2", "TEMP-BBB-002", gender="Perempuan")
        self.assertNotEqual(pid1, pid2)

    # ── Bug fix: visit_count excludes void ────────────────────────────────────

    def test_visit_count_excludes_void_for_discount(self):
        """Kunjungan void tidak boleh masuk hitungan visit_count untuk diskon."""
        self.db.add_discount_rule({
            "name": "Diskon Kunjungan Ke-2",
            "type": "visit_count",
            "condition_value": 2,       # berlaku mulai kunjungan ke-2
            "discount_type": "percent",
            "discount_value": 10,
            "is_active": True,
            "priority": 1,
        })
        patient_id = self.db.add_patient("Pasien Count Void", "081299993333", gender="Laki-laki")

        # Kunjungan pertama — aktif
        self.db.add_visit(patient_id, price=100000, point_count=1, service_name="Bekam")

        # Void kunjungan pertama
        with self.db.Session() as session:
            v = session.query(Visit).filter(Visit.patient_id == patient_id).first()
            v.invoice_status = "void"
            session.commit()

        # Kunjungan kedua — setelah void; visit_count aktif = 0, diskon TIDAK boleh aktif
        _price2, discount2, _name2 = self.db.add_visit(
            patient_id, price=100000, point_count=1, service_name="Bekam"
        )
        self.assertFalse(discount2, "Diskon tidak boleh aktif karena kunjungan aktif baru 1")
        self.assertEqual(_price2, 100000)

    def test_visit_count_counts_active_visits_for_discount(self):
        """Kunjungan aktif harus tetap dihitung sehingga diskon bisa triggered."""
        self.db.add_discount_rule({
            "name": "Diskon Kunjungan Ke-2 Aktif",
            "type": "visit_count",
            "condition_value": 2,
            "discount_type": "percent",
            "discount_value": 10,
            "is_active": True,
            "priority": 1,
        })
        patient_id = self.db.add_patient("Pasien Count Aktif", "081299994444", gender="Laki-laki")

        # Kunjungan pertama — aktif, tidak di-void
        self.db.add_visit(patient_id, price=100000, point_count=1, service_name="Bekam")

        # Kunjungan kedua — visit_count aktif = 1, next = 2 → cocok threshold 2 → diskon aktif
        _price2, discount2, _name2 = self.db.add_visit(
            patient_id, price=100000, point_count=1, service_name="Bekam"
        )
        self.assertTrue(discount2, "Diskon harus aktif karena kunjungan aktif sudah 1 (ke-2)")
        self.assertEqual(_price2, 90000)


class TestStockFlows(IsolatedDatabaseTestCase):
    def test_service_inventory_stock_decreases_and_cannot_go_minus(self):
        patient_id = self.db.add_patient("Pasien Stok Layanan", "081200000002")
        inventory_id = self.db.add_inventory_item("Kassa Test", "pcs", min_stock=0, initial_qty=3)
        service_id = self.db.add_service(
            "Layanan Pakai Kassa",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=75000,
            inventory_usage=[{"inventory_id": inventory_id, "quantity": 2}],
        )

        self.db.add_visit(
            patient_id,
            price=75000,
            point_count=1,
            service_id=service_id,
            service_name="Layanan Pakai Kassa",
        )

        inventory = self.db.get_all_inventory()[0]
        self.assertEqual(inventory["quantity"], 1)

        with self.assertRaises(ValueError):
            self.db.add_visit(
                patient_id,
                price=75000,
                point_count=1,
                service_id=service_id,
                service_name="Layanan Pakai Kassa",
            )

        inventory_after = self.db.get_all_inventory()[0]
        self.assertEqual(inventory_after["quantity"], 1)

    def test_herbal_stock_decreases_and_cannot_go_minus(self):
        herbal_id = self.db.add_herbal("Herbal Test", "botol", price=25000, stock=2)

        sale = self.db.add_herbal_sale(
            [{"herbal_id": herbal_id, "quantity": 1}],
            buyer_name="Pembeli Test",
        )

        self.assertEqual(sale["total"], 25000)
        herbal = self.db.get_all_herbals()[0]
        self.assertEqual(herbal["stock"], 1)

        with self.assertRaises(ValueError):
            self.db.add_herbal_sale(
                [{"herbal_id": herbal_id, "quantity": 99}],
                buyer_name="Pembeli Test",
            )

        herbal_after = self.db.get_all_herbals()[0]
        self.assertEqual(herbal_after["stock"], 1)


class TestInvoiceAndDiscountFlows(IsolatedDatabaseTestCase):
    @staticmethod
    def invoice_number(visit_id, visit_date):
        date_part = visit_date.strftime("%Y%m%d")
        return f"INV-{date_part}-{int(visit_id):05d}"

    def create_visit_for_invoice(self, patient_name="Pasien Invoice", price=125000, **visit_kwargs):
        patient_id = self.db.add_patient(patient_name, f"08{abs(hash(patient_name)) % 10_000_000_000:010d}")
        service_id = self.db.add_service(
            f"Layanan {patient_name}",
            unit_label="sesi",
            default_quantity=1,
            price_per_unit=max(1, int(price or 1)),
        )
        self.db.add_visit(
            patient_id,
            price=price,
            point_count=1,
            service_id=service_id,
            service_name=f"Layanan {patient_name}",
            **visit_kwargs,
        )
        return self.db.get_visits(patient_id)[0]

    def test_generate_invoice_pdf_creates_file_and_invoice_number(self):
        visit = self.create_visit_for_invoice()
        visit_data, patient_name, therapist_name = self.db.get_visit_for_invoice(visit["id"])
        invoice_number = self.invoice_number(visit["id"], visit_data.date)

        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "invoices"))
        pdf_path = helper.generate_invoice(
            patient_name=patient_name,
            date=visit_data.date,
            points=visit_data.point_count,
            price=visit_data.price,
            therapist_name=therapist_name or "--",
            custom_settings={"clinic_name": "Klinik Test", "clinic_address": "Alamat Test"},
            service_name=visit_data.service_name,
            invoice_number=invoice_number,
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 100)
        self.assertIn(invoice_number, os.path.basename(pdf_path))
        with open(pdf_path, "rb") as pdf_file:
            self.assertEqual(pdf_file.read(4), b"%PDF")

    def test_invoice_payment_link_is_pdf_safe_and_summary_allows_notes(self):
        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "invoices"))
        rows = [
            ("Status Pembayaran", "pending", None),
            ("Referensi Pembayaran", "GATEWAY-MOCK-VISIT-48-20260514100600-BA3CBC7D", None),
            ("Link Pembayaran", "Buka link", "http://127.0.0.1:8000/payments/gateway/pay/GATEWAY-MOCK-VISIT-48-20260514100600-BA3CBC7D"),
        ]

        self.assertEqual(
            helper._pdf_payment_link("/payments/gateway/pay/ABC"),
            "http://127.0.0.1:8000/payments/gateway/pay/ABC",
        )
        self.assertGreater(helper._summary_block_height(rows), (len(rows) * 5.2 * mm) + 12 * mm)

    def test_invoice_labels_internal_gateway_without_customer_link(self):
        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "invoices"))

        self.assertEqual(helper._payment_provider_label("gateway_mock"), "Pembayaran Internal")
        self.assertEqual(helper._payment_status_label("pending"), "Menunggu")
        self.assertEqual(helper._payment_method_label("qris"), "QRIS")

    def test_void_invoice_rolls_back_when_required_audit_fails(self):
        visit = self.create_visit_for_invoice(patient_name="Pasien Audit Void", price=100000)
        original_add_audit = self.db._add_audit_log_row

        def broken_add_audit(session, *args, **kwargs):
            raise RuntimeError("audit unavailable")

        self.db._add_audit_log_row = broken_add_audit
        try:
            with self.assertRaises(RuntimeError):
                self.db.void_visit_invoice(visit["id"], "Alasan audit gagal")
        finally:
            self.db._add_audit_log_row = original_add_audit

        with self.db.Session() as session:
            refreshed = session.get(Visit, visit["id"])
            audit_count = session.query(AuditLog).filter(AuditLog.action == "invoice_voided").count()

        self.assertEqual(refreshed.invoice_status, "active")
        self.assertEqual(refreshed.payment_status, "paid")
        self.assertEqual(audit_count, 0)

    def test_manual_payment_rolls_back_when_required_audit_fails(self):
        visit = self.create_visit_for_invoice(patient_name="Pasien Audit Payment", price=100000, payment_status="unpaid", payment_method="qris", amount_paid=0)
        original_add_audit = self.db._add_audit_log_row

        def broken_add_audit(session, *args, **kwargs):
            raise RuntimeError("audit unavailable")

        self.db._add_audit_log_row = broken_add_audit
        try:
            with self.assertRaises(RuntimeError):
                self.db.update_invoice_manual_payment(
                    "visit",
                    visit_id=visit["id"],
                    payment_status="paid",
                    payment_method="transfer",
                    amount_paid=100000,
                )
        finally:
            self.db._add_audit_log_row = original_add_audit

        with self.db.Session() as session:
            refreshed = session.get(Visit, visit["id"])
            audit_count = session.query(AuditLog).filter(AuditLog.action == "manual_payment_updated").count()

        self.assertEqual(refreshed.payment_status, "unpaid")
        self.assertEqual(refreshed.amount_paid or 0, 0)
        self.assertEqual(audit_count, 0)

    def test_discount_does_not_make_total_negative(self):
        rule_id = self.db.add_discount_rule({
            "name": "Diskon Besar Test",
            "type": "manual",
            "discount_type": "fixed",
            "discount_value": 999999,
            "is_active": True,
            "priority": 1,
        })

        visit = self.create_visit_for_invoice(
            patient_name="Pasien Diskon",
            price=100000,
            manual_price_used=True,
            discount_rule_id=rule_id,
        )

        self.assertEqual(visit["price"], 0)
        self.assertTrue(visit["discount_applied"])
        self.assertEqual(visit["discount_rule_name"], "Diskon Besar Test")

    def test_negative_price_creates_validation_error(self):
        patient_id = self.db.add_patient("Harga Minus", "081122334455")
        
        with self.assertRaises(ValueError) as context:
            self.db.add_visit(patient_id, -50000, point_count=1)
        self.assertIn("Harga kunjungan tidak boleh kurang dari 0", str(context.exception))
        
        rule_id = self.db.add_discount_rule({
            "name": "Diskon Valid",
            "type": "period",
            "discount_type": "fixed",
            "discount_value": 0,
            "is_active": True
        })
        with self.assertRaises(ValueError) as context:
            self.db.add_visit(patient_id, -100, point_count=1, discount_rule_id=rule_id)
        self.assertIn("Harga kunjungan tidak boleh kurang dari 0", str(context.exception))

    def test_free_visit_requires_reason(self):
        patient_id = self.db.add_patient("Pasien Gratis Tanpa Alasan", "081122334466")
        
        with self.assertRaises(ValueError) as context:
            self.db.add_visit(patient_id, 0, point_count=1, is_free_visit=True, free_visit_reason="")
        self.assertIn("Alasan kunjungan gratis wajib diisi", str(context.exception))

        with self.assertRaises(ValueError) as context:
            self.db.add_visit(patient_id, 0, point_count=1, is_free_visit=True, free_visit_reason="   ")
        self.assertIn("Alasan kunjungan gratis wajib diisi", str(context.exception))

    def test_free_visit_with_reason_allowed(self):
        patient_id = self.db.add_patient("Pasien Gratis Valid", "081122334477")
        
        price, _, _ = self.db.add_visit(patient_id, 0, point_count=1, is_free_visit=True, free_visit_reason="Bonus tahun baru")
        self.assertEqual(price, 0)
        
        visits = self.db.get_visits(patient_id)
        self.assertTrue(visits[0]["is_free_visit"])
        self.assertEqual(visits[0]["free_visit_reason"], "Bonus tahun baru")

    def test_voucher_total_usage_limit_is_enforced(self):
        self.db.add_discount_rule({
            "name": "Voucher Terbatas",
            "type": "voucher",
            "discount_type": "fixed",
            "discount_value": 25000,
            "voucher_code": "HEMAT25",
            "usage_limit": 1,
            "per_patient_limit": 1,
            "is_active": True,
            "priority": 1,
        })
        first_patient_id = self.db.add_patient("Pasien Voucher Satu", "081255550001")
        second_patient_id = self.db.add_patient("Pasien Voucher Dua", "081255550002")

        first_price, first_discount, first_name = self.db.add_visit(
            first_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="HEMAT25",
        )
        second_price, second_discount, second_name = self.db.add_visit(
            second_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="HEMAT25",
        )

        self.assertEqual(first_price, 75000)
        self.assertTrue(first_discount)
        self.assertEqual(first_name, "Voucher Terbatas")
        self.assertEqual(second_price, 100000)
        self.assertFalse(second_discount)
        self.assertIsNone(second_name)
        with self.db.Session() as session:
            usage_count = session.execute(text("SELECT COUNT(*) FROM voucher_usages")).scalar()
        self.assertEqual(usage_count, 1)
        rule = next(rule for rule in self.db.get_discount_rules() if rule.name == "Voucher Terbatas")
        self.assertEqual(rule.usage_count, 1)

    def test_voucher_per_patient_limit_is_enforced(self):
        self.db.add_discount_rule({
            "name": "Voucher Sekali Pasien",
            "type": "voucher",
            "discount_type": "percent",
            "discount_value": 10,
            "voucher_code": "PASIEN10",
            "per_patient_limit": 1,
            "is_active": True,
            "priority": 1,
        })
        patient_id = self.db.add_patient("Pasien Voucher Repeat", "081255550003")

        first_price, first_discount, _first_name = self.db.add_visit(
            patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="PASIEN10",
        )
        second_price, second_discount, second_name = self.db.add_visit(
            patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="PASIEN10",
        )

        self.assertEqual(first_price, 90000)
        self.assertTrue(first_discount)
        self.assertEqual(second_price, 100000)
        self.assertFalse(second_discount)
        self.assertIsNone(second_name)
        with self.db.Session() as session:
            usage_count = session.execute(text("SELECT COUNT(*) FROM voucher_usages WHERE patient_id = :patient_id"), {"patient_id": patient_id}).scalar()
        self.assertEqual(usage_count, 1)

    def test_voucher_can_be_limited_to_specific_patients(self):
        allowed_patient_id = self.db.add_patient("Pasien Voucher Khusus", "081255550004")
        other_patient_id = self.db.add_patient("Pasien Tanpa Voucher Khusus", "081255550005")
        self.db.add_discount_rule({
            "name": "Voucher Pasien Khusus",
            "type": "voucher",
            "discount_type": "fixed",
            "discount_value": 30000,
            "voucher_code": "KHUSUS30",
            "target_patient_ids": [allowed_patient_id],
            "is_active": True,
            "priority": 1,
        })

        allowed_price, allowed_discount, allowed_name = self.db.add_visit(
            allowed_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="KHUSUS30",
        )
        other_price, other_discount, other_name = self.db.add_visit(
            other_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="KHUSUS30",
        )

        self.assertEqual(allowed_price, 70000)
        self.assertTrue(allowed_discount)
        self.assertEqual(allowed_name, "Voucher Pasien Khusus")
        self.assertEqual(other_price, 100000)
        self.assertFalse(other_discount)
        self.assertIsNone(other_name)
        rule = next(rule for rule in self.db.get_discount_rules() if rule.name == "Voucher Pasien Khusus")
        self.assertEqual(rule.target_patient_ids, [allowed_patient_id])
        self.assertEqual(rule.target_patient_names, ["Pasien Voucher Khusus"])

    def test_general_voucher_still_applies_to_all_patients(self):
        self.db.add_discount_rule({
            "name": "Voucher Umum",
            "type": "voucher",
            "discount_type": "fixed",
            "discount_value": 15000,
            "voucher_code": "UMUM15",
            "is_active": True,
            "priority": 1,
        })
        first_patient_id = self.db.add_patient("Pasien Umum Satu", "081255550006")
        second_patient_id = self.db.add_patient("Pasien Umum Dua", "081255550007")

        first_price, first_discount, _first_name = self.db.add_visit(
            first_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="UMUM15",
        )
        second_price, second_discount, _second_name = self.db.add_visit(
            second_patient_id,
            price=100000,
            point_count=1,
            service_name="Terapi Voucher",
            voucher_code="UMUM15",
        )

        self.assertEqual(first_price, 85000)
        self.assertTrue(first_discount)
        self.assertEqual(second_price, 85000)
        self.assertTrue(second_discount)

    def test_crm_voucher_badge_and_whatsapp_message_include_special_voucher(self):
        patient_id = self.db.add_patient("Pasien CRM Voucher", "081255550008")
        rule_id = self.db.add_discount_rule({
            "name": "Voucher CRM Personal",
            "type": "voucher",
            "discount_type": "percent",
            "discount_value": 20,
            "voucher_code": "CRM20",
            "target_patient_ids": [patient_id],
            "is_active": True,
            "priority": 1,
        })

        with self.db.Session() as session:
            rows = build_crm_patients(session)
            row = next(item for item in rows if item["id"] == patient_id)
            voucher = get_voucher_for_crm_message(session, patient_id, rule_id)
            message_data = create_crm_whatsapp_log(session, row, template_type="promo", voucher=voucher)

        self.assertTrue(row["has_special_voucher"])
        self.assertIn("Voucher CRM Personal", message_data["message"])
        self.assertIn("CRM20", message_data["message"])
        self.assertIn("20%", message_data["message"])

    def test_free_visit_invoice_does_not_break_total(self):
        visit = self.create_visit_for_invoice(
            patient_name="Pasien Free Visit",
            price=0,
            is_free_visit=True,
            free_visit_reason="Bonus kontrol test",
        )
        visit_data, patient_name, therapist_name = self.db.get_visit_for_invoice(visit["id"])
        invoice_number = self.invoice_number(visit["id"], visit_data.date)

        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "free_visit_invoices"))
        pdf_path = helper.generate_invoice(
            patient_name=patient_name,
            date=visit_data.date,
            points=visit_data.point_count,
            price=visit_data.price,
            therapist_name=therapist_name or "--",
            custom_settings={"clinic_name": "Klinik Test"},
            service_name=visit_data.service_name,
            invoice_number=invoice_number,
            is_free_visit=visit_data.is_free_visit,
            free_visit_reason=visit_data.free_visit_reason,
            original_price=100000,
            discount_amount=100000,
        )

        self.assertEqual(visit["price"], 0)
        self.assertTrue(visit["is_free_visit"])
        self.assertTrue(os.path.exists(pdf_path))

    def test_invoice_pdf_handles_long_text_and_many_herbal_items(self):
        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "long_invoice"))
        herbal_items = [
            {
                "name": f"Herbal Racikan Premium Nama Sangat Panjang Nomor {idx} untuk Uji Wrap Kolom",
                "quantity": idx,
                "unit": "botol besar ukuran terapi keluarga",
                "unit_price": 17500 + idx,
                "total_price": (17500 + idx) * idx,
            }
            for idx in range(1, 24)
        ]

        pdf_path = helper.generate_invoice(
            patient_name="Pasien Dengan Nama Sangat Panjang Untuk Menguji Layout Invoice A5 Supaya Tidak Keluar Kolom",
            date=datetime.now(),
            points=12,
            price=1250000,
            therapist_name="Terapis Dengan Nama Panjang",
            custom_settings={
                "clinic_name": "Klinik Terapi Herbal dan Bekam Nama Panjang Sekali",
                "clinic_tagline": "Pusat layanan terapi keluarga",
                "clinic_address": (
                    "Jl. Contoh Alamat Klinik Yang Sangat Panjang Nomor 123, "
                    "Komplek Ruko Sehat Sentosa, Kecamatan Panjang, Kota Uji Cetak"
                ),
                "clinic_phone": "081234567890",
                "clinic_email": "admin@klinikcontoh.test",
                "invoice_footer": (
                    "Catatan footer invoice yang sengaja dibuat panjang untuk memastikan "
                    "area bawah halaman tetap aman saat dicetak di kertas A5."
                ),
            },
            discount_rule_name="Diskon Member Nama Panjang",
            service_name="Layanan Terapi Kombinasi Bekam Herbal Akupresur Dengan Nama Sangat Panjang",
            invoice_number="INV-20260507-99999",
            unit_label="layanan panjang terapi premium",
            original_price=1500000,
            discount_amount=250000,
            herbal_items=herbal_items,
            payment_method="Transfer Bank",
            payment_status="Lunas",
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 100)
        with open(pdf_path, "rb") as pdf_file:
            self.assertEqual(pdf_file.read(4), b"%PDF")

    def test_short_service_and_herbal_invoice_stays_on_one_page(self):
        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "short_invoice"))
        pdf_path = helper.generate_invoice(
            patient_name="Pasien RC",
            date=datetime.now(),
            points=1,
            price=75000,
            therapist_name="Demo Terapis",
            custom_settings={
                "clinic_name": "Klinik RC",
                "clinic_tagline": "Clinic Management System",
                "clinic_address": "Alamat RC",
                "clinic_phone": "081234567000",
            },
            service_name="Terapi RC",
            invoice_number="INV-20260508-00005",
            unit_label="sesi",
            original_price=75000,
            herbal_items=[{
                "name": "Herbal RC",
                "quantity": 2,
                "unit": "botol",
                "unit_price": 25000,
                "total_price": 50000,
            }],
            payment_method="Tunai",
            payment_status="Lunas",
        )

        with open(pdf_path, "rb") as pdf_file:
            page_count = len(re.findall(rb"/Type\s*/Page\b(?!s)", pdf_file.read()))
        self.assertEqual(page_count, 1)

    def test_herbal_invoice_pdf_handles_many_items_and_long_buyer_name(self):
        helper = InvoiceHelper(output_dir=os.path.join(self.tmp.name, "long_herbal_invoice"))
        herbal_items = [
            {
                "name": f"Produk Herbal Terapi Nama Panjang untuk Cetak A5 Nomor {idx}",
                "quantity": idx,
                "unit": "botol",
                "unit_price": 22000,
                "total_price": 22000 * idx,
            }
            for idx in range(1, 28)
        ]

        pdf_path = helper.generate_herbal_invoice(
            buyer_name="Pembeli Klinik Dengan Nama Panjang Untuk Menguji Panel Identitas",
            date=datetime.now(),
            items=herbal_items,
            total=sum(item["total_price"] for item in herbal_items),
            custom_settings={
                "clinic_name": "Klinik Terapi Herbal Profesional",
                "clinic_tagline": "Terapi keluarga dan produk herbal",
                "clinic_address": "Alamat klinik panjang untuk memastikan header tetap rapi di A5",
                "clinic_phone": "081234567890",
                "invoice_footer": "Footer panjang tetap aman dan tidak mengubah logic pembayaran.",
            },
            invoice_number="HBL-20260508-LONG-001",
            note="Catatan transaksi herbal panjang yang tetap harus aman saat invoice multipage.",
            payment_method="Transfer Bank",
            payment_status="Lunas",
        )

        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 100)
        with open(pdf_path, "rb") as pdf_file:
            self.assertEqual(pdf_file.read(4), b"%PDF")
        with open(pdf_path, "rb") as pdf_file:
            self.assertEqual(pdf_file.read(4), b"%PDF")


class TestBackupRestoreFlow(IsolatedDatabaseTestCase):
    def test_backup_restore_after_dispose_removes_later_rows(self):
        helper = BackupHelper(
            db_path=self.db_path,
            backup_dir=os.path.join(self.tmp.name, "backups"),
            log_dir=os.path.join(self.tmp.name, "logs"),
        )
        self.db.add_patient("Pasien Sebelum Restore", "081200000101")
        backup_path = helper.create_backup(daily=False)
        self.assertTrue(backup_path)

        self.db.add_patient("Pasien Setelah Backup", "081200000102")
        self.db.engine.dispose()
        status = helper.restore_backup(backup_path)
        self.db.engine.dispose()

        self.assertTrue(status["success"], status["message"])
        self.db = Database(f"sqlite:///{self.db_path}")
        patients = self.db.get_all_patients()
        self.assertEqual([p.name for p in patients], ["Pasien Sebelum Restore"])

    def test_backup_restore_keeps_database_readable(self):
        original_patient_id = self.db.add_patient("Pasien Backup", "081200000003")
        helper = BackupHelper(
            db_path=self.db_path,
            backup_dir=os.path.join(self.tmp.name, "backups"),
            log_dir=os.path.join(self.tmp.name, "logs"),
        )

        backup_path = helper.create_backup(daily=False)
        self.assertTrue(backup_path)
        self.assertTrue(os.path.exists(backup_path))

        self.db.add_patient("Pasien Setelah Backup", "081200000004")
        self.assertEqual(len(self.db.get_all_patients()), 2)

        self.db.engine.dispose()
        time.sleep(1.1)
        status = helper.restore_backup(backup_path)
        self.assertTrue(status["success"], status["message"])

        self.db = Database(f"sqlite:///{self.db_path}")
        patients = self.db.get_all_patients()
        self.assertEqual(len(patients), 1)
        self.assertEqual(patients[0].id, original_patient_id)
        self.assertEqual(patients[0].name, "Pasien Backup")


if __name__ == "__main__":
    unittest.main()
