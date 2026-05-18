from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Index, event, text, Text, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload
from sqlalchemy.exc import SAWarning
import warnings
import uuid
import json
import re

warnings.filterwarnings('ignore', r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively.*", category=SAWarning)

from db_models import (
    Base, Patient, Therapist, Visit, Inventory, InventoryTransaction,
    Service, ServiceInventoryUsage, Herbal, HerbalTransaction,
    CorrectionLog, AuditLog, DiscountRule, VoucherUsage,
    VoucherPatientTarget, PatientFollowup, PatientManualTag,
    PatientContactPreference, CRMWhatsAppLog
)
from db_dataclasses import (
    VisitData, DiscountRuleData, PatientData, TherapistData, ServiceData
)
from db_mixins_audit import AuditMixin
from db_mixins_patient import PatientMixin
from db_mixins_staff import TherapistMixin, ServiceMixin
from db_mixins_inventory import HerbalMixin, InventoryMixin
from helpers.payment_rules import allocate_payment_amounts, normalize_visit_payment

class Database(AuditMixin, PatientMixin, TherapistMixin, ServiceMixin, HerbalMixin, InventoryMixin):
    DB_SCHEMA_VERSION = 11

    def __init__(self, db_url="sqlite:///data.db"):
        self.db_url = db_url
        self.db_path = db_url.replace("sqlite:///", "") if db_url.startswith("sqlite:///") else None
        self._migration_logger = None
        kwargs = {
            "pool_pre_ping": True,
        }
        if db_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 20

        self.engine = create_engine(db_url, **kwargs)

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._migrate_existing_data()

    def get_database_path(self):
        return self.db_path

    def _get_migration_logger(self):
        if self._migration_logger:
            return self._migration_logger

        import logging
        from logging.handlers import RotatingFileHandler
        import os

        base_dir = os.path.dirname(os.path.abspath(self.db_path)) if self.db_path else os.getcwd()
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.abspath(os.path.join(log_dir, "migration.log"))

        logger = logging.getLogger(f"lancar.migration.{id(self)}")
        logger.setLevel(logging.INFO)
        logger.propagate = True
        if not any(getattr(handler, "baseFilename", None) == log_path for handler in logger.handlers):
            handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        self._migration_logger = logger
        return logger

    def _log_migration(self, level, message, *args):
        logger = self._get_migration_logger()
        getattr(logger, level)(message, *args)

    def _backup_database(self, db_url):
        import os

        if not db_url.startswith("sqlite:///"):
            return

        db_path = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            return

        try:
            from helpers.backup_helper import BackupHelper

            base_dir = os.path.dirname(os.path.abspath(db_path))
            helper = BackupHelper(
                db_path=db_path,
                backup_dir=os.path.join(base_dir, "backups"),
                max_backups=14,
                log_dir=os.path.join(base_dir, "logs"),
            )
            backup_path = helper.create_backup(daily=False)
            if not backup_path:
                status = helper.get_status()
                raise RuntimeError(status.get("message") or "Backup sebelum migration gagal.")
            self._log_migration("info", "Pre-migration backup created: %s", backup_path)
        except Exception:
            self._log_migration("exception", "Pre-migration backup failed.")
            raise

    def _ensure_app_meta(self, session):
        session.execute(text(
            "CREATE TABLE IF NOT EXISTS app_meta ("
            "key TEXT PRIMARY KEY, "
            "value TEXT NOT NULL, "
            "updated_at DATETIME NOT NULL"
            ")"
        ))

    def _get_db_version(self, session):
        self._ensure_app_meta(session)
        row = session.execute(text("SELECT value FROM app_meta WHERE key = 'db_version'")).fetchone()
        try:
            return int(row[0]) if row else 0
        except (TypeError, ValueError):
            return 0

    def _set_db_version(self, session, version):
        self._ensure_app_meta(session)
        session.execute(
            text(
                "INSERT OR REPLACE INTO app_meta (key, value, updated_at) "
                "VALUES ('db_version', :value, :updated_at)"
            ),
            {"value": str(int(version)), "updated_at": datetime.now()},
        )

    def _run_migration(self, session, name, action):
        try:
            changed = bool(action())
            session.commit()
            self._log_migration("info", "%s: %s", name, "applied" if changed else "already ok")
            return changed
        except Exception:
            session.rollback()
            self._log_migration("exception", "%s: failed", name)
            raise

    def _column_exists(self, session, table_name, column_name):
        rows = session.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return column_name in {row[1] for row in rows}

    def _ensure_column(self, session, table_name, column_name, ddl):
        if self._column_exists(session, table_name, column_name):
            return False
        session.execute(text(ddl))
        return True

    def _table_exists(self, session, table_name):
        row = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table_name},
        ).fetchone()
        return row is not None

    def _ensure_table(self, session, table_name, statements):
        statements = list(statements)
        exists = self._table_exists(session, table_name)
        for statement in statements:
            session.execute(text(statement))
        return not exists

    def _backfill_visit_pricing_fields(self, session):
        if not all(
            self._column_exists(session, "visits", column)
            for column in ("original_price", "discount_amount", "final_price", "price")
        ):
            return False
        result = session.execute(text(
            "UPDATE visits "
            "SET "
            "original_price = CASE WHEN COALESCE(original_price, 0) = 0 THEN COALESCE(price, 0) ELSE original_price END, "
            "final_price = CASE WHEN COALESCE(final_price, 0) = 0 THEN COALESCE(price, 0) ELSE final_price END, "
            "discount_amount = CASE "
            "WHEN COALESCE(discount_amount, 0) < 0 THEN 0 "
            "WHEN COALESCE(discount_amount, 0) = 0 AND COALESCE(original_price, 0) > COALESCE(final_price, COALESCE(price, 0)) "
            "THEN COALESCE(original_price, 0) - COALESCE(final_price, COALESCE(price, 0)) "
            "ELSE COALESCE(discount_amount, 0) END "
            "WHERE COALESCE(original_price, 0) = 0 "
            "OR COALESCE(final_price, 0) = 0 "
            "OR COALESCE(discount_amount, 0) < 0"
        ))
        return bool(result.rowcount and result.rowcount > 0)

    def _migrate_existing_data(self):
        with self.Session() as session:
            previous_version = self._get_db_version(session)
            session.commit()
            self._log_migration("info", "Migration start. db_version=%s target=%s", previous_version, self.DB_SCHEMA_VERSION)
            if previous_version >= self.DB_SCHEMA_VERSION:
                self._log_migration("info", "Migration skipped. Database schema is up to date.")
                return

            self._backup_database(self.db_url)

            for table_name, column_name, ddl in [
                ("patients", "created_at", "ALTER TABLE patients ADD COLUMN created_at DATETIME"),
                ("therapists", "can_handle_any_gender", "ALTER TABLE therapists ADD COLUMN can_handle_any_gender BOOLEAN DEFAULT 0 NOT NULL"),
                ("visits", "point_count", "ALTER TABLE visits ADD COLUMN point_count INTEGER DEFAULT 0 NOT NULL"),
                ("visits", "invoice_path", "ALTER TABLE visits ADD COLUMN invoice_path TEXT"),
                ("visits", "pdf_generated_at", "ALTER TABLE visits ADD COLUMN pdf_generated_at DATETIME"),
                ("visits", "payment_updated_at", "ALTER TABLE visits ADD COLUMN payment_updated_at DATETIME"),
                ("inventory", "is_active", "ALTER TABLE inventory ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"),
                ("visits", "medical_notes", "ALTER TABLE visits ADD COLUMN medical_notes TEXT"),
                ("visits", "is_free_visit", "ALTER TABLE visits ADD COLUMN is_free_visit BOOLEAN DEFAULT 0 NOT NULL"),
                ("visits", "free_visit_reason", "ALTER TABLE visits ADD COLUMN free_visit_reason TEXT"),
                ("visits", "discount_rule_id", "ALTER TABLE visits ADD COLUMN discount_rule_id INTEGER"),
                ("visits", "discount_rule_name", "ALTER TABLE visits ADD COLUMN discount_rule_name TEXT"),
                ("visits", "service_id", "ALTER TABLE visits ADD COLUMN service_id INTEGER"),
                ("visits", "service_name", "ALTER TABLE visits ADD COLUMN service_name TEXT"),
                ("visits", "original_price", "ALTER TABLE visits ADD COLUMN original_price NUMERIC(10, 2) DEFAULT 0 NOT NULL"),
                ("visits", "discount_amount", "ALTER TABLE visits ADD COLUMN discount_amount NUMERIC(10, 2) DEFAULT 0 NOT NULL"),
                ("visits", "final_price", "ALTER TABLE visits ADD COLUMN final_price NUMERIC(10, 2) DEFAULT 0 NOT NULL"),
                ("services", "pricing_type", "ALTER TABLE services ADD COLUMN pricing_type TEXT DEFAULT 'per_unit' NOT NULL"),
                ("services", "service_category", "ALTER TABLE services ADD COLUMN service_category TEXT DEFAULT 'general' NOT NULL"),
                ("services", "fixed_price", "ALTER TABLE services ADD COLUMN fixed_price NUMERIC(10, 2) DEFAULT 0 NOT NULL"),
                ("services", "allow_manual_price", "ALTER TABLE services ADD COLUMN allow_manual_price BOOLEAN DEFAULT 1 NOT NULL"),
                ("visits", "invoice_status", "ALTER TABLE visits ADD COLUMN invoice_status TEXT DEFAULT 'active' NOT NULL"),
                ("visits", "void_reason", "ALTER TABLE visits ADD COLUMN void_reason TEXT"),
                ("visits", "voided_at", "ALTER TABLE visits ADD COLUMN voided_at DATETIME"),
                ("inventory", "item_type", "ALTER TABLE inventory ADD COLUMN item_type TEXT DEFAULT 'consumable' NOT NULL"),
                ("inventory", "package_unit", "ALTER TABLE inventory ADD COLUMN package_unit TEXT"),
                ("inventory", "package_size", "ALTER TABLE inventory ADD COLUMN package_size INTEGER DEFAULT 1 NOT NULL"),
                ("herbals", "cost_price", "ALTER TABLE herbals ADD COLUMN cost_price NUMERIC(10, 2) DEFAULT 0 NOT NULL"),
                ("herbals", "package_unit", "ALTER TABLE herbals ADD COLUMN package_unit TEXT"),
                ("herbals", "package_size", "ALTER TABLE herbals ADD COLUMN package_size INTEGER DEFAULT 1 NOT NULL"),
                ("herbals", "min_stock", "ALTER TABLE herbals ADD COLUMN min_stock INTEGER DEFAULT 5 NOT NULL"),
                ("herbal_transactions", "transaction_type", "ALTER TABLE herbal_transactions ADD COLUMN transaction_type TEXT DEFAULT 'sale' NOT NULL"),
                ("herbal_transactions", "note", "ALTER TABLE herbal_transactions ADD COLUMN note TEXT"),
                ("herbal_transactions", "visit_id", "ALTER TABLE herbal_transactions ADD COLUMN visit_id INTEGER"),
                ("herbal_transactions", "invoice_path", "ALTER TABLE herbal_transactions ADD COLUMN invoice_path TEXT"),
                ("herbal_transactions", "pdf_generated_at", "ALTER TABLE herbal_transactions ADD COLUMN pdf_generated_at DATETIME"),
                ("herbal_transactions", "payment_updated_at", "ALTER TABLE herbal_transactions ADD COLUMN payment_updated_at DATETIME"),
                ("herbal_transactions", "invoice_status", "ALTER TABLE herbal_transactions ADD COLUMN invoice_status TEXT DEFAULT 'active' NOT NULL"),
                ("herbal_transactions", "void_reason", "ALTER TABLE herbal_transactions ADD COLUMN void_reason TEXT"),
                ("herbal_transactions", "voided_at", "ALTER TABLE herbal_transactions ADD COLUMN voided_at DATETIME"),
                ("herbal_transactions", "sale_group_id", "ALTER TABLE herbal_transactions ADD COLUMN sale_group_id TEXT"),
                ("patient_followups", "outcome", "ALTER TABLE patient_followups ADD COLUMN outcome TEXT"),
                ("discount_rules", "usage_limit", "ALTER TABLE discount_rules ADD COLUMN usage_limit INTEGER"),
                ("discount_rules", "per_patient_limit", "ALTER TABLE discount_rules ADD COLUMN per_patient_limit INTEGER"),
                ("visits", "payment_status", "ALTER TABLE visits ADD COLUMN payment_status TEXT DEFAULT 'paid' "),
                ("visits", "payment_method", "ALTER TABLE visits ADD COLUMN payment_method TEXT DEFAULT 'cash' "),
                ("visits", "amount_paid", "ALTER TABLE visits ADD COLUMN amount_paid INTEGER"),
                ("visits", "paid_at", "ALTER TABLE visits ADD COLUMN paid_at TEXT"),
                ("herbal_transactions", "payment_status", "ALTER TABLE herbal_transactions ADD COLUMN payment_status TEXT DEFAULT 'paid' "),
                ("herbal_transactions", "payment_method", "ALTER TABLE herbal_transactions ADD COLUMN payment_method TEXT DEFAULT 'cash' "),
                ("herbal_transactions", "amount_paid", "ALTER TABLE herbal_transactions ADD COLUMN amount_paid INTEGER"),
                ("herbal_transactions", "paid_at", "ALTER TABLE herbal_transactions ADD COLUMN paid_at TEXT"),
                ("visits", "payment_provider", "ALTER TABLE visits ADD COLUMN payment_provider TEXT DEFAULT 'manual' "),
                ("visits", "payment_reference", "ALTER TABLE visits ADD COLUMN payment_reference TEXT DEFAULT '' "),
                ("visits", "payment_url", "ALTER TABLE visits ADD COLUMN payment_url TEXT DEFAULT '' "),
                ("visits", "payment_channel", "ALTER TABLE visits ADD COLUMN payment_channel TEXT DEFAULT '' "),
                ("visits", "payment_expired_at", "ALTER TABLE visits ADD COLUMN payment_expired_at TEXT DEFAULT NULL"),
                ("visits", "payment_gateway_status", "ALTER TABLE visits ADD COLUMN payment_gateway_status TEXT DEFAULT '' "),
                ("herbal_transactions", "payment_provider", "ALTER TABLE herbal_transactions ADD COLUMN payment_provider TEXT DEFAULT 'manual' "),
                ("herbal_transactions", "payment_reference", "ALTER TABLE herbal_transactions ADD COLUMN payment_reference TEXT DEFAULT '' "),
                ("herbal_transactions", "payment_url", "ALTER TABLE herbal_transactions ADD COLUMN payment_url TEXT DEFAULT '' "),
                ("herbal_transactions", "payment_channel", "ALTER TABLE herbal_transactions ADD COLUMN payment_channel TEXT DEFAULT '' "),
                ("herbal_transactions", "payment_expired_at", "ALTER TABLE herbal_transactions ADD COLUMN payment_expired_at TEXT DEFAULT NULL"),
                ("herbal_transactions", "payment_gateway_status", "ALTER TABLE herbal_transactions ADD COLUMN payment_gateway_status TEXT DEFAULT '' "),
                ("inventory_transactions", "visit_id", "ALTER TABLE inventory_transactions ADD COLUMN visit_id INTEGER"),
            ]:
                self._run_migration(
                    session,
                    f"ensure_column:{table_name}.{column_name}",
                    lambda table_name=table_name, column_name=column_name, ddl=ddl: self._ensure_column(session, table_name, column_name, ddl),
                )

            self._run_migration(
                session,
                "backfill:visits.pricing_fields",
                lambda: self._backfill_visit_pricing_fields(session),
            )

            self._run_migration(
                session,
                "ensure_table:inventory_transactions",
                lambda: self._ensure_table(session, "inventory_transactions", [
                    (
                        "CREATE TABLE IF NOT EXISTS inventory_transactions ("
                        "id INTEGER PRIMARY KEY, "
                        "inventory_id INTEGER NOT NULL, "
                        "date DATETIME NOT NULL, "
                        "change INTEGER NOT NULL, "
                        "transaction_type TEXT DEFAULT 'adjustment' NOT NULL, "
                        "note TEXT, "
                        "visit_id INTEGER, "
                        "FOREIGN KEY(inventory_id) REFERENCES inventory (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_inventory_transactions_inventory_id ON inventory_transactions (inventory_id)",
                    "CREATE INDEX IF NOT EXISTS ix_inventory_transactions_date ON inventory_transactions (date)",
                    "CREATE INDEX IF NOT EXISTS ix_inventory_transactions_transaction_type ON inventory_transactions (transaction_type)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:service_inventory_usage",
                lambda: self._ensure_table(session, "service_inventory_usage", [
                    (
                        "CREATE TABLE IF NOT EXISTS service_inventory_usage ("
                        "id INTEGER PRIMARY KEY, "
                        "service_id INTEGER NOT NULL, "
                        "inventory_id INTEGER NOT NULL, "
                        "quantity INTEGER DEFAULT 1 NOT NULL, "
                        "created_at DATETIME NOT NULL, "
                        "FOREIGN KEY(service_id) REFERENCES services (id), "
                        "FOREIGN KEY(inventory_id) REFERENCES inventory (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_service_inventory_usage_service_id ON service_inventory_usage (service_id)",
                    "CREATE INDEX IF NOT EXISTS ix_service_inventory_usage_inventory_id ON service_inventory_usage (inventory_id)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:crm_whatsapp_logs",
                lambda: self._ensure_table(session, "crm_whatsapp_logs", [
                    (
                        "CREATE TABLE IF NOT EXISTS crm_whatsapp_logs ("
                        "id INTEGER PRIMARY KEY, "
                        "patient_id INTEGER NOT NULL, "
                        "phone TEXT NOT NULL, "
                        "message_type TEXT NOT NULL, "
                        "message TEXT NOT NULL, "
                        "whatsapp_url TEXT NOT NULL, "
                        "status TEXT DEFAULT 'drafted' NOT NULL, "
                        "created_at DATETIME NOT NULL, "
                        "confirmed_at DATETIME, "
                        "note TEXT, "
                        "FOREIGN KEY(patient_id) REFERENCES patients (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_crm_whatsapp_logs_patient_id ON crm_whatsapp_logs (patient_id)",
                    "CREATE INDEX IF NOT EXISTS ix_crm_whatsapp_logs_message_type ON crm_whatsapp_logs (message_type)",
                    "CREATE INDEX IF NOT EXISTS ix_crm_whatsapp_logs_status ON crm_whatsapp_logs (status)",
                    "CREATE INDEX IF NOT EXISTS ix_crm_whatsapp_logs_created_at ON crm_whatsapp_logs (created_at)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:patient_manual_tags",
                lambda: self._ensure_table(session, "patient_manual_tags", [
                    (
                        "CREATE TABLE IF NOT EXISTS patient_manual_tags ("
                        "id INTEGER PRIMARY KEY, "
                        "patient_id INTEGER NOT NULL, "
                        "value TEXT NOT NULL, "
                        "label TEXT NOT NULL, "
                        "created_at DATETIME NOT NULL, "
                        "FOREIGN KEY(patient_id) REFERENCES patients (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_patient_manual_tags_patient_id ON patient_manual_tags (patient_id)",
                    "CREATE INDEX IF NOT EXISTS ix_patient_manual_tags_value ON patient_manual_tags (value)",
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_patient_manual_tag_unique ON patient_manual_tags (patient_id, value)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:patient_contact_preferences",
                lambda: self._ensure_table(session, "patient_contact_preferences", [
                    (
                        "CREATE TABLE IF NOT EXISTS patient_contact_preferences ("
                        "id INTEGER PRIMARY KEY, "
                        "patient_id INTEGER NOT NULL UNIQUE, "
                        "boleh_reminder_kontrol BOOLEAN DEFAULT 1 NOT NULL, "
                        "boleh_promo BOOLEAN DEFAULT 1 NOT NULL, "
                        "jangan_dihubungi BOOLEAN DEFAULT 0 NOT NULL, "
                        "catatan_kontak TEXT, "
                        "updated_at DATETIME NOT NULL, "
                        "FOREIGN KEY(patient_id) REFERENCES patients (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_patient_contact_preferences_patient_id ON patient_contact_preferences (patient_id)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:correction_logs",
                lambda: self._ensure_table(session, "correction_logs", [
                    (
                        "CREATE TABLE IF NOT EXISTS correction_logs ("
                        "id INTEGER PRIMARY KEY, "
                        "action_type TEXT NOT NULL, "
                        "herbal_id INTEGER, "
                        "quantity_change INTEGER, "
                        "stock_before INTEGER, "
                        "stock_after INTEGER, "
                        "reference_type TEXT, "
                        "reference_id TEXT, "
                        "reason TEXT NOT NULL, "
                        "created_at DATETIME NOT NULL, "
                        "created_by TEXT, "
                        "FOREIGN KEY(herbal_id) REFERENCES herbals (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_correction_logs_action_type ON correction_logs (action_type)",
                    "CREATE INDEX IF NOT EXISTS ix_correction_logs_herbal_id ON correction_logs (herbal_id)",
                    "CREATE INDEX IF NOT EXISTS ix_correction_logs_reference_type ON correction_logs (reference_type)",
                    "CREATE INDEX IF NOT EXISTS ix_correction_logs_reference_id ON correction_logs (reference_id)",
                    "CREATE INDEX IF NOT EXISTS ix_correction_logs_created_at ON correction_logs (created_at)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:audit_logs",
                lambda: self._ensure_table(session, "audit_logs", [
                    (
                        "CREATE TABLE IF NOT EXISTS audit_logs ("
                        "id INTEGER PRIMARY KEY, "
                        "created_at DATETIME NOT NULL, "
                        "actor TEXT DEFAULT 'admin' NOT NULL, "
                        "action TEXT NOT NULL, "
                        "entity_type TEXT NOT NULL, "
                        "entity_id TEXT, "
                        "description TEXT, "
                        "metadata_json TEXT"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at)",
                    "CREATE INDEX IF NOT EXISTS ix_audit_logs_actor ON audit_logs (actor)",
                    "CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action)",
                    "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type)",
                    "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs (entity_id)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:voucher_usages",
                lambda: self._ensure_table(session, "voucher_usages", [
                    (
                        "CREATE TABLE IF NOT EXISTS voucher_usages ("
                        "id INTEGER PRIMARY KEY, "
                        "discount_rule_id INTEGER NOT NULL, "
                        "patient_id INTEGER NOT NULL, "
                        "visit_id INTEGER, "
                        "voucher_code TEXT NOT NULL, "
                        "discount_amount NUMERIC(10, 2) DEFAULT 0 NOT NULL, "
                        "used_at DATETIME NOT NULL, "
                        "FOREIGN KEY(discount_rule_id) REFERENCES discount_rules (id), "
                        "FOREIGN KEY(patient_id) REFERENCES patients (id), "
                        "FOREIGN KEY(visit_id) REFERENCES visits (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_voucher_usages_discount_rule_id ON voucher_usages (discount_rule_id)",
                    "CREATE INDEX IF NOT EXISTS ix_voucher_usages_patient_id ON voucher_usages (patient_id)",
                    "CREATE INDEX IF NOT EXISTS ix_voucher_usages_visit_id ON voucher_usages (visit_id)",
                    "CREATE INDEX IF NOT EXISTS ix_voucher_usages_voucher_code ON voucher_usages (voucher_code)",
                    "CREATE INDEX IF NOT EXISTS ix_voucher_usages_used_at ON voucher_usages (used_at)",
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_voucher_usage_visit_unique ON voucher_usages (visit_id)",
                ]),
            )

            self._run_migration(
                session,
                "ensure_table:voucher_patient_targets",
                lambda: self._ensure_table(session, "voucher_patient_targets", [
                    (
                        "CREATE TABLE IF NOT EXISTS voucher_patient_targets ("
                        "id INTEGER PRIMARY KEY, "
                        "discount_rule_id INTEGER NOT NULL, "
                        "patient_id INTEGER NOT NULL, "
                        "created_at DATETIME NOT NULL, "
                        "FOREIGN KEY(discount_rule_id) REFERENCES discount_rules (id), "
                        "FOREIGN KEY(patient_id) REFERENCES patients (id)"
                        ")"
                    ),
                    "CREATE INDEX IF NOT EXISTS ix_voucher_patient_targets_discount_rule_id ON voucher_patient_targets (discount_rule_id)",
                    "CREATE INDEX IF NOT EXISTS ix_voucher_patient_targets_patient_id ON voucher_patient_targets (patient_id)",
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_voucher_patient_target_unique ON voucher_patient_targets (discount_rule_id, patient_id)",
                ]),
            )

            self._run_migration(session, "seed_default_services", lambda: self._seed_default_services(session))

            def normalize_existing_rows():
                session.execute(text("UPDATE patients SET address = '' WHERE address IS NULL"))
                session.execute(text("UPDATE patients SET gender = 'Laki-laki' WHERE gender IS NULL OR gender = ''"))
                session.execute(text(
                    "UPDATE patients SET created_at = COALESCE("
                    "(SELECT MIN(visits.date) FROM visits WHERE visits.patient_id = patients.id), "
                    "CURRENT_TIMESTAMP"
                    ") WHERE created_at IS NULL OR created_at = ''"
                ))
                session.execute(text("UPDATE visits SET service_name = 'Bekam' WHERE service_name IS NULL OR service_name = ''"))
                session.execute(text("UPDATE herbal_transactions SET transaction_type = 'sale' WHERE transaction_type IS NULL OR transaction_type = ''"))
                session.execute(text("UPDATE visits SET invoice_status = 'active' WHERE invoice_status IS NULL OR invoice_status = ''"))
                session.execute(text("UPDATE herbal_transactions SET invoice_status = 'active' WHERE invoice_status IS NULL OR invoice_status = ''"))
                return True

            self._run_migration(session, "normalize_existing_rows", normalize_existing_rows)
            self._run_migration(session, "ensure_performance_indexes", lambda: self._ensure_performance_indexes(session))
            self._run_migration(session, "set_db_version", lambda: self._set_db_version(session, self.DB_SCHEMA_VERSION) or True)
            self._log_migration("info", "Migration complete. db_version=%s", self.DB_SCHEMA_VERSION)

    def _ensure_performance_indexes(self, session):
        indexes = [
            ("ix_patients_name", "CREATE INDEX IF NOT EXISTS ix_patients_name ON patients (name)"),
            ("ix_patients_phone", "CREATE INDEX IF NOT EXISTS ix_patients_phone ON patients (phone)"),
            ("ix_patients_created_at", "CREATE INDEX IF NOT EXISTS ix_patients_created_at ON patients (created_at)"),
            ("ix_visits_patient_id", "CREATE INDEX IF NOT EXISTS ix_visits_patient_id ON visits (patient_id)"),
            ("ix_visits_date", "CREATE INDEX IF NOT EXISTS ix_visits_date ON visits (date)"),
            ("ix_visits_therapist_id", "CREATE INDEX IF NOT EXISTS ix_visits_therapist_id ON visits (therapist_id)"),
            ("ix_herbal_transactions_herbal_id", "CREATE INDEX IF NOT EXISTS ix_herbal_transactions_herbal_id ON herbal_transactions (herbal_id)"),
            ("ix_herbal_transactions_visit_id", "CREATE INDEX IF NOT EXISTS ix_herbal_transactions_visit_id ON herbal_transactions (visit_id)"),
            ("ix_herbal_transactions_sale_group_id", "CREATE INDEX IF NOT EXISTS ix_herbal_transactions_sale_group_id ON herbal_transactions (sale_group_id)"),
            ("ix_herbal_transactions_date", "CREATE INDEX IF NOT EXISTS ix_herbal_transactions_date ON herbal_transactions (date)"),
            ("ix_visits_invoice_status", "CREATE INDEX IF NOT EXISTS ix_visits_invoice_status ON visits (invoice_status)"),
            ("ix_herbal_transactions_invoice_status", "CREATE INDEX IF NOT EXISTS ix_herbal_transactions_invoice_status ON herbal_transactions (invoice_status)"),
            ("ix_inventory_transactions_visit_id", "CREATE INDEX IF NOT EXISTS ix_inventory_transactions_visit_id ON inventory_transactions (visit_id)"),
            ("ix_correction_logs_created_at", "CREATE INDEX IF NOT EXISTS ix_correction_logs_created_at ON correction_logs (created_at)"),
            ("ix_service_inventory_usage_service_id", "CREATE INDEX IF NOT EXISTS ix_service_inventory_usage_service_id ON service_inventory_usage (service_id)"),
            ("ix_service_inventory_usage_inventory_id", "CREATE INDEX IF NOT EXISTS ix_service_inventory_usage_inventory_id ON service_inventory_usage (inventory_id)"),
            ("ix_patient_followups_outcome", "CREATE INDEX IF NOT EXISTS ix_patient_followups_outcome ON patient_followups (outcome)"),
            ("ix_patient_manual_tags_patient_id", "CREATE INDEX IF NOT EXISTS ix_patient_manual_tags_patient_id ON patient_manual_tags (patient_id)"),
            ("ix_patient_manual_tags_value", "CREATE INDEX IF NOT EXISTS ix_patient_manual_tags_value ON patient_manual_tags (value)"),
            ("ix_patient_contact_preferences_patient_id", "CREATE INDEX IF NOT EXISTS ix_patient_contact_preferences_patient_id ON patient_contact_preferences (patient_id)"),
            ("ix_audit_logs_created_at", "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at)"),
            ("ix_audit_logs_action", "CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action)"),
            ("ix_audit_logs_entity_type", "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type)"),
            ("ix_audit_logs_entity_id", "CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id ON audit_logs (entity_id)"),
            ("ix_voucher_usages_discount_rule_id", "CREATE INDEX IF NOT EXISTS ix_voucher_usages_discount_rule_id ON voucher_usages (discount_rule_id)"),
            ("ix_voucher_usages_patient_id", "CREATE INDEX IF NOT EXISTS ix_voucher_usages_patient_id ON voucher_usages (patient_id)"),
            ("ix_voucher_usages_visit_id", "CREATE INDEX IF NOT EXISTS ix_voucher_usages_visit_id ON voucher_usages (visit_id)"),
            ("ix_voucher_usages_voucher_code", "CREATE INDEX IF NOT EXISTS ix_voucher_usages_voucher_code ON voucher_usages (voucher_code)"),
            ("ix_voucher_usages_used_at", "CREATE INDEX IF NOT EXISTS ix_voucher_usages_used_at ON voucher_usages (used_at)"),
            ("idx_voucher_usage_visit_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_voucher_usage_visit_unique ON voucher_usages (visit_id)"),
            ("ix_voucher_patient_targets_discount_rule_id", "CREATE INDEX IF NOT EXISTS ix_voucher_patient_targets_discount_rule_id ON voucher_patient_targets (discount_rule_id)"),
            ("ix_voucher_patient_targets_patient_id", "CREATE INDEX IF NOT EXISTS ix_voucher_patient_targets_patient_id ON voucher_patient_targets (patient_id)"),
            ("idx_voucher_patient_target_unique", "CREATE UNIQUE INDEX IF NOT EXISTS idx_voucher_patient_target_unique ON voucher_patient_targets (discount_rule_id, patient_id)"),
        ]
        changed = False
        for index_name, statement in indexes:
            exists = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
                {"name": index_name},
            ).fetchone()
            if exists:
                continue
            session.execute(text(statement))
            changed = True
        return changed

    def _low_stock_count(self, session):
        inventory_count = session.query(func.count(Inventory.id)).filter(
            Inventory.is_active == True,
            Inventory.quantity <= Inventory.min_stock,
        ).scalar() or 0
        herbal_count = session.query(func.count(Herbal.id)).filter(
            Herbal.is_active == True,
            Herbal.stock <= Herbal.min_stock,
        ).scalar() or 0
        return int(inventory_count or 0) + int(herbal_count or 0)

    def _seed_default_services(self, session):
        defaults = [
            ("Bekam", "titik", 13, 0, "Keluhan utama; titik bekam; kondisi darah; reaksi pasien; saran kontrol"),
            ("Pijat Refleksi", "sesi", 1, 75000, "Area pijat; keluhan; titik refleksi; tingkat nyeri sebelum/sesudah"),
            ("Akupuntur", "sesi", 1, 120000, "Keluhan utama; titik akupuntur; jumlah jarum; durasi; reaksi pasien"),
            ("Totok / Akupresur", "sesi", 1, 85000, "Area titik tekan; intensitas tekanan; respons pasien"),
            ("Pijat Tradisional", "sesi", 1, 90000, "Area tubuh; jenis keluhan; minyak/balm; kondisi otot"),
            ("Konsultasi Herbal", "sesi", 1, 50000, "Keluhan; riwayat penyakit; herbal disarankan; aturan konsumsi"),
        ]
        existing = {name.lower() for (name,) in session.query(Service.name).all()}
        changed = False
        for name, unit_label, default_quantity, price_per_unit, notes_template in defaults:
            if name.lower() in existing:
                continue
            session.add(Service(
                name=name,
                pricing_type="per_unit",
                service_category="therapy",
                fixed_price=price_per_unit * default_quantity,
                allow_manual_price=True,
                unit_label=unit_label,
                default_quantity=default_quantity,
                price_per_unit=price_per_unit,
                notes_template=notes_template,
                is_active=True,
            ))
            changed = True
        return changed

    def seed_demo_data(self):
        demo_phones = [f"08990000000{i}" for i in range(1, 6)]
        existing_demo = sum(1 for phone in demo_phones if self.patient_phone_exists(phone))
        if existing_demo >= 5:
            self.log_audit("demo_seed_skipped", "demo_data", None, "Data contoh sudah tersedia.")
            return {"created": False, "message": "Data contoh sudah tersedia.", "patients": existing_demo}

        created = {"patients": 0, "services": 0, "herbals": 0, "inventory": 0, "visits": 0}
        services_by_name = {service.name.lower(): service for service in self.get_all_services(active_only=False)}
        for name, unit, qty, price in [
            ("Demo Bekam Reguler", "titik", 13, 10000),
            ("Demo Pijat Terapi", "sesi", 1, 85000),
            ("Demo Konsultasi Herbal", "sesi", 1, 50000),
        ]:
            if name.lower() not in services_by_name:
                service_id = self.add_service(name, unit_label=unit, default_quantity=qty, price_per_unit=price)
                services_by_name[name.lower()] = self.get_service(service_id)
                created["services"] += 1

        inventory_names = {item["item_name"].lower() for item in self.get_all_inventory(active_only=False)}
        for name, unit, min_stock, qty in [
            ("Demo Kassa Steril", "pcs", 10, 80),
            ("Demo Minyak Terapi", "botol", 3, 12),
            ("Demo Sarung Tangan", "pcs", 20, 120),
        ]:
            if name.lower() not in inventory_names:
                self.add_inventory_item(name, unit, min_stock, qty)
                created["inventory"] += 1

        herbal_names = {item["name"].lower() for item in self.get_all_herbals(active_only=False)}
        for name, unit, price, stock in [
            ("Demo Madu Herbal", "botol", 65000, 18),
            ("Demo Habbatussauda", "pack", 45000, 22),
            ("Demo Minyak Zaitun", "botol", 55000, 14),
        ]:
            if name.lower() not in herbal_names:
                self.add_herbal(name, unit, price, stock)
                created["herbals"] += 1

        therapist_id = None
        therapists = self.get_all_therapists(active_only=True)
        if therapists:
            therapist_id = therapists[0].id
        else:
            therapist_id = self.add_therapist("Demo Terapis", "Laki-laki", "Terapis demo")

        service = services_by_name.get("demo bekam reguler") or next(iter(services_by_name.values()), None)
        service_id = service.id if service else None
        service_name = service.name if service else "Demo Bekam Reguler"

        demo_patients = [
            ("Demo Ahmad", demo_phones[0], "Laki-laki"),
            ("Demo Budi", demo_phones[1], "Laki-laki"),
            ("Demo Citra", demo_phones[2], "Perempuan"),
            ("Demo Dewi", demo_phones[3], "Perempuan"),
            ("Demo Eka", demo_phones[4], "Laki-laki"),
        ]
        for name, phone, gender in demo_patients:
            if self.patient_phone_exists(phone):
                continue
            patient_id = self.add_patient(name, phone, "Alamat demo", gender)
            created["patients"] += 1
            if gender == "Laki-laki":
                self.add_visit(patient_id, 130000, point_count=13, therapist_id=therapist_id, service_id=service_id, service_name=service_name, medical_notes="Data contoh kunjungan")
                created["visits"] += 1

        self.log_audit("demo_data_seeded", "demo_data", None, "Data contoh ditambahkan.", created)
        return {"created": True, "message": "Data contoh berhasil ditambahkan.", **created}

    def clear_demo_data(self):
        demo_phones = [f"08990000000{i}" for i in range(1, 6)]
        with self.Session() as session:
            patients = session.query(Patient).filter(Patient.phone.in_(demo_phones)).all()
            count = len(patients)
            for patient in patients:
                session.delete(patient)
            for model, names in [
                (Service, ["Demo Bekam Reguler", "Demo Pijat Terapi", "Demo Konsultasi Herbal"]),
                (Inventory, ["Demo Kassa Steril", "Demo Minyak Terapi", "Demo Sarung Tangan"]),
                (Herbal, ["Demo Madu Herbal", "Demo Habbatussauda", "Demo Minyak Zaitun"]),
            ]:
                for row in session.query(model).filter(model.name.in_(names) if model is Herbal else model.item_name.in_(names) if model is Inventory else model.name.in_(names)).all():
                    row.is_active = False
            session.commit()
        self.log_audit("demo_data_cleared", "demo_data", None, "Data contoh dihapus/dinonaktifkan.", {"patients": count})
        return {"status": "success", "message": "Data contoh dihapus/dinonaktifkan.", "patients": count}

    def _normalize_patient_phone(self, phone: str) -> str:
        return str(phone or "").strip()

    def add_patient(self, name, phone, address='', gender='Laki-laki', visits=None):
        if not str(name or "").strip():
            raise ValueError("Nama pasien wajib diisi")
        if gender not in ("Laki-laki", "Perempuan"):
            raise ValueError("Jenis kelamin pasien tidak valid")
        phone = self._normalize_patient_phone(phone)
        if phone and not phone.isdigit() and not phone.startswith("TEMP-"):
            raise ValueError("Nomor HP harus berupa angka")
        if self.patient_phone_exists(phone):
            raise ValueError(f"Nomor HP {phone} sudah terdaftar untuk pasien lain.")

        with self.Session() as session:
            patient = Patient(name=str(name).strip(), phone=phone, address=address, gender=gender)
            if visits:
                for visit in visits:
                    visit_price = float(visit.price or 0)
                    visit_points = int(visit.point_count if hasattr(visit, 'point_count') else 0)
                    visit_is_free = bool(visit.is_free_visit) if hasattr(visit, 'is_free_visit') else False
                    visit_free_reason = visit.free_visit_reason if hasattr(visit, 'free_visit_reason') else None
                    if visit_points < 1:
                        raise ValueError("Jumlah layanan minimal 1")
                    if visit_price < 0:
                        raise ValueError("Harga kunjungan tidak boleh kurang dari 0")
                    if visit_price == 0 and not visit_is_free:
                        raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis")
                    if visit_is_free and visit_price != 0:
                        raise ValueError("Kunjungan gratis harus memakai harga 0")
                    if visit_is_free and not str(visit_free_reason or "").strip():
                        raise ValueError("Alasan kunjungan gratis wajib diisi")
                    patient.visits.append(
                        Visit(
                            date=visit.date,
                            price=visit_price,
                            original_price=float(getattr(visit, 'original_price', None) or visit_price),
                            discount_amount=float(getattr(visit, 'discount_amount', None) or 0),
                            final_price=float(getattr(visit, 'final_price', None) or visit_price),
                            discount_applied=visit.discount_applied,
                            point_count=visit_points,
                            therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                            service_id=visit.service_id if hasattr(visit, 'service_id') else None,
                            service_name=(visit.service_name if hasattr(visit, 'service_name') else None) or 'Bekam',
                            medical_notes=visit.medical_notes if hasattr(visit, 'medical_notes') else None,
                            is_free_visit=visit_is_free,
                            free_visit_reason=str(visit_free_reason or "").strip() if visit_is_free else None,
                            discount_rule_id=visit.discount_rule_id if hasattr(visit, 'discount_rule_id') else None,
                            discount_rule_name=visit.discount_rule_name if hasattr(visit, 'discount_rule_name') else None,
                        )
                    )
            session.add(patient)
            session.commit()
            patient_id = patient.id
        self.log_audit("patient_created", "patient", patient_id, "Pasien baru ditambahkan.", {
            "name": str(name).strip(),
            "phone": str(phone or "").strip(),
            "gender": gender,
            "visit_count": len(visits or []),
        })
        return patient_id

    def patient_phone_exists(self, phone: str, exclude_patient_id: Optional[int] = None) -> bool:
        phone = self._normalize_patient_phone(phone)
        if not phone or phone.startswith("TEMP-"):
            return False
        with self.Session() as session:
            query = session.query(Patient.id).filter(Patient.phone == phone)
            if exclude_patient_id is not None:
                query = query.filter(Patient.id != exclude_patient_id)
            return session.query(query.exists()).scalar()

    def get_patient_detail(self, patient_id: int):
        with self.Session() as session:
            patient = session.query(Patient).options(joinedload(Patient.visits)).filter(Patient.id == patient_id).first()
            if not patient:
                return None
            visits = [
                {
                    "id": v.id,
                    "date": v.date.isoformat() if v.date else None,
                    "price": float(v.price or 0),
                    "original_price": float(getattr(v, "original_price", None) or v.price or 0),
                    "discount_amount": float(getattr(v, "discount_amount", None) or 0),
                    "final_price": float(getattr(v, "final_price", None) or v.price or 0),
                    "discount_applied": v.discount_applied,
                    "point_count": v.point_count if hasattr(v, 'point_count') else 0,
                    "quantity": v.point_count if hasattr(v, 'point_count') else 0,
                    "therapist_id": v.therapist_id if hasattr(v, 'therapist_id') else None,
                    "service_id": v.service_id if hasattr(v, 'service_id') else None,
                    "service_name": (v.service_name if hasattr(v, 'service_name') else None) or 'Bekam',
                    "invoice_path": v.invoice_path if hasattr(v, 'invoice_path') else None,
                    "medical_notes": v.medical_notes if hasattr(v, 'medical_notes') else None,
                    "is_free_visit": v.is_free_visit if hasattr(v, 'is_free_visit') else False,
                    "free_visit_reason": v.free_visit_reason if hasattr(v, 'free_visit_reason') else None,
                    "discount_rule_id": v.discount_rule_id if hasattr(v, 'discount_rule_id') else None,
                    "discount_rule_name": v.discount_rule_name if hasattr(v, 'discount_rule_name') else None,
                    "payment_status": getattr(v, "payment_status", None) or "paid",
                    "payment_method": getattr(v, "payment_method", None) or "cash",
                    "amount_paid": getattr(v, "amount_paid", None),
                    "paid_at": getattr(v, "paid_at", None),
                    "payment_provider": getattr(v, "payment_provider", None) or "manual",
                    "payment_reference": getattr(v, "payment_reference", None) or "",
                    "payment_url": getattr(v, "payment_url", None) or "",
                    "payment_channel": getattr(v, "payment_channel", None) or "",
                    "payment_expired_at": getattr(v, "payment_expired_at", None),
                    "payment_gateway_status": getattr(v, "payment_gateway_status", None) or "",
                }
                for v in patient.visits
            ]
            return {
                "id": patient.id,
                "name": patient.name,
                "phone": patient.phone,
                "gender": patient.gender,
                "address": patient.address,
                "visits_count": len(visits),
                "total_income": sum(float(v.get("final_price") or v.get("price") or 0) for v in visits),
                "visits": visits,
            }

    def get_all_patients(self):
        with self.Session() as session:
            patients = session.query(Patient).options(joinedload(Patient.visits)).all()
            return [
                PatientData(
                    id=patient.id,
                    name=patient.name,
                    phone=patient.phone,
                    address=patient.address if hasattr(patient, 'address') else '',
                    gender=patient.gender if hasattr(patient, 'gender') else 'Laki-laki',
                    visits=[
                        VisitData(
                            id=visit.id,
                            date=visit.date,
                            price=float(visit.price or 0),
                            original_price=float(getattr(visit, 'original_price', None) or visit.price or 0),
                            discount_amount=float(getattr(visit, 'discount_amount', None) or 0),
                            final_price=float(getattr(visit, 'final_price', None) or visit.price or 0),
                            discount_applied=visit.discount_applied,
                            point_count=visit.point_count if hasattr(visit, 'point_count') else 0,
                            quantity=visit.point_count if hasattr(visit, 'point_count') else 0,
                            therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                            service_id=visit.service_id if hasattr(visit, 'service_id') else None,
                            service_name=(visit.service_name if hasattr(visit, 'service_name') else None) or 'Bekam',
                            invoice_path=visit.invoice_path if hasattr(visit, 'invoice_path') else None,
                            medical_notes=visit.medical_notes if hasattr(visit, 'medical_notes') else None,
                            is_free_visit=visit.is_free_visit if hasattr(visit, 'is_free_visit') else False,
                            free_visit_reason=visit.free_visit_reason if hasattr(visit, 'free_visit_reason') else None,
                            discount_rule_id=visit.discount_rule_id if hasattr(visit, 'discount_rule_id') else None,
                            discount_rule_name=visit.discount_rule_name if hasattr(visit, 'discount_rule_name') else None,
                        )
                        for visit in patient.visits
                    ]
                )
                for patient in patients
            ]

    def get_patients_paginated(self, start=0, length=10, search_val="", order_col_idx=0, order_dir="asc"):
        from sqlalchemy import or_, func
        with self.Session() as session:
            visit_stats = (
                session.query(
                    Visit.patient_id.label("patient_id"),
                    func.count(Visit.id).label("visits_count"),
                    func.coalesce(func.sum(func.coalesce(Visit.final_price, Visit.price, 0)), 0).label("total_income"),
                )
                .group_by(Visit.patient_id)
                .subquery()
            )

            query = (
                session.query(
                    Patient,
                    func.coalesce(visit_stats.c.visits_count, 0).label("visits_count"),
                    func.coalesce(visit_stats.c.total_income, 0).label("total_income"),
                )
                .outerjoin(visit_stats, Patient.id == visit_stats.c.patient_id)
            )

            total_records = session.query(func.count(Patient.id)).scalar() or 0

            if search_val:
                search_term = f"%{search_val}%"
                query = query.filter(
                    or_(
                        Patient.name.ilike(search_term),
                        Patient.phone.ilike(search_term),
                        Patient.address.ilike(search_term)
                    )
                )

            filtered_records = query.order_by(None).count()

            if order_col_idx == 0:
                col = Patient.name
            elif order_col_idx == 1:
                col = Patient.gender
            elif order_col_idx == 2:
                col = Patient.phone
            elif order_col_idx == 3:
                col = visit_stats.c.visits_count
            else:
                col = Patient.id

            if order_dir == "desc":
                query = query.order_by(col.desc())
            else:
                query = query.order_by(col.asc())

            if length > 0:
                query = query.offset(start).limit(length)

            rows = query.all()
            data = []
            for p, visits_count, total_income in rows:
                data.append({
                    "id": p.id,
                    "name": p.name,
                    "phone": p.phone,
                    "gender": p.gender,
                    "address": p.address,
                    "visits_count": int(visits_count or 0),
                    "total_income": float(total_income or 0),
                    "visits": None,
                })

            return {
                "draw": 0,
                "recordsTotal": total_records,
                "recordsFiltered": filtered_records,
                "data": data
            }

    def _period_start_date(self, period):
        import datetime

        now = datetime.datetime.now()
        if period == "7d":
            return (now - datetime.timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "30d":
            return (now - datetime.timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "6m":
            return (now.replace(day=1) - datetime.timedelta(days=180)).replace(hour=0, minute=0, second=0, microsecond=0)
        if period == "1y":
            return (now.replace(day=1) - datetime.timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        return None

    def get_dashboard_stats(self):
        from sqlalchemy import func
        from helpers.dashboard_stats_helper import build_dashboard_stats
        with self.Session() as session:
            return build_dashboard_stats(session, {
                "func": func,
                "Patient": Patient,
                "Therapist": Therapist,
                "Visit": Visit,
                "Inventory": Inventory,
                "Herbal": Herbal,
                "HerbalTransaction": HerbalTransaction,
            })

    def get_analytics_data(self, period="6m"):
        from sqlalchemy import func
        from sqlalchemy import and_, or_
        from helpers.revenue_rules import active_invoice_filter, revenue_case
        from collections import defaultdict
        import datetime
        with self.Session() as session:
            now = datetime.datetime.now()
            active_visit_status = active_invoice_filter(Visit)
            void_visit_status = Visit.invoice_status == "void"
            active_herbal_status = active_invoice_filter(HerbalTransaction)
            void_herbal_status = HerbalTransaction.invoice_status == "void"
            herbal_sale_filter = HerbalTransaction.transaction_type == "sale"
            standalone_herbal_sale_filter = (
                HerbalTransaction.transaction_type == "sale",
                HerbalTransaction.visit_id.is_(None),
            )
            herbal_return_filter = HerbalTransaction.transaction_type.in_(["return", "retur"])

            linked_herbal_total_expr = (
                session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0))
                .filter(HerbalTransaction.visit_id == Visit.id, HerbalTransaction.transaction_type == "sale")
                .correlate(Visit)
                .scalar_subquery()
            )
            linked_herbal_paid_expr = (
                session.query(func.coalesce(func.sum(func.coalesce(HerbalTransaction.amount_paid, 0)), 0))
                .filter(HerbalTransaction.visit_id == Visit.id, HerbalTransaction.transaction_type == "sale")
                .correlate(Visit)
                .scalar_subquery()
            )
            visit_total_expr = func.coalesce(func.nullif(Visit.final_price, 0), Visit.price, 0) + linked_herbal_total_expr
            visit_paid_expr = func.coalesce(Visit.amount_paid, 0) + linked_herbal_paid_expr
            from sqlalchemy import case
            visit_revenue_expr = case(
                (Visit.payment_method == 'free', 0),
                (or_(Visit.payment_status == 'paid', Visit.payment_status.is_(None)), visit_total_expr),
                (Visit.payment_status == 'partial', visit_paid_expr),
                else_=0,
            )
            herbal_revenue_expr = revenue_case(HerbalTransaction, HerbalTransaction.total_price)

            # 1. Determine time ranges and init chart map
            chart_data = {}
            if period == "7d":
                start_date = self._period_start_date(period)
                for i in range(7):
                    d = start_date + datetime.timedelta(days=i)
                    chart_data[d.strftime("%d %b")] = {"visits": 0, "income": 0}
            elif period == "30d":
                start_date = self._period_start_date(period)
                for i in range(30):
                    d = start_date + datetime.timedelta(days=i)
                    chart_data[d.strftime("%d %b")] = {"visits": 0, "income": 0}
            elif period == "1y":
                start_date = self._period_start_date(period)
                curr = now
                m_list = []
                for _ in range(12):
                    m_list.append(curr.strftime("%b"))
                    curr = (curr.replace(day=1) - datetime.timedelta(days=1))
                for m in reversed(m_list):
                    chart_data[m] = {"visits": 0, "income": 0}
            elif period == "all":
                start_date = None
                first_visit = session.query(func.min(Visit.date)).scalar()
                first_herbal = session.query(func.min(HerbalTransaction.date)).scalar()
                candidates = [d for d in (first_visit, first_herbal) if d]
                first_date = min(candidates) if candidates else now
                curr = first_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                last = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                while curr <= last:
                    chart_data[curr.strftime("%b %Y")] = {"visits": 0, "income": 0}
                    year = curr.year + (1 if curr.month == 12 else 0)
                    month = 1 if curr.month == 12 else curr.month + 1
                    curr = curr.replace(year=year, month=month)
            else: # "6m"
                start_date = self._period_start_date("6m")
                curr = now
                m_list = []
                for _ in range(6):
                    m_list.append(curr.strftime("%b %Y"))
                    curr = (curr.replace(day=1) - datetime.timedelta(days=1))
                for m in reversed(m_list):
                    chart_data[m] = {"visits": 0, "income": 0}

            # 2. Main Queries
            # Core metrics that shouldn't be timeframe filtered
            total_patients_global = session.query(func.count(Patient.id)).scalar() or 0

            low_stock_count = self._low_stock_count(session)

            visits_query = session.query(
                func.count(Visit.id),
                func.coalesce(func.sum(visit_revenue_expr), 0),
            ).filter(active_visit_status)
            if start_date:
                visits_query = visits_query.filter(Visit.date >= start_date)
            total_visits, gross_visit_revenue = visits_query.one()
            total_visits = int(total_visits or 0)
            gross_visit_revenue = float(gross_visit_revenue or 0)

            void_visit_query = session.query(func.coalesce(func.sum(func.coalesce(Visit.final_price, Visit.price, 0)), 0)).filter(void_visit_status)
            if start_date:
                void_visit_query = void_visit_query.filter(Visit.date >= start_date)
            void_visit_revenue = float(void_visit_query.scalar() or 0)
            net_visit_revenue = gross_visit_revenue

            herbal_sales_query = session.query(
                func.count(HerbalTransaction.id),
                func.coalesce(func.sum(herbal_revenue_expr), 0),
            ).filter(*standalone_herbal_sale_filter, active_herbal_status)
            if start_date:
                herbal_sales_query = herbal_sales_query.filter(HerbalTransaction.date >= start_date)
            total_herbal_sales, gross_herbal_sales = herbal_sales_query.one()
            total_herbal_sales = int(total_herbal_sales or 0)
            gross_herbal_sales = float(gross_herbal_sales or 0)

            herbal_returns_query = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)).filter(herbal_return_filter, HerbalTransaction.visit_id.is_(None))
            if start_date:
                herbal_returns_query = herbal_returns_query.filter(HerbalTransaction.date >= start_date)
            herbal_returns = float(herbal_returns_query.scalar() or 0)
            net_herbal_sales = max(0, gross_herbal_sales - herbal_returns)

            herbal_cogs_query = (
                session.query(func.coalesce(func.sum(HerbalTransaction.quantity * Herbal.cost_price), 0))
                .join(Herbal, Herbal.id == HerbalTransaction.herbal_id)
                .filter(*standalone_herbal_sale_filter, active_herbal_status)
            )
            herbal_return_cogs_query = (
                session.query(func.coalesce(func.sum(HerbalTransaction.quantity * Herbal.cost_price), 0))
                .join(Herbal, Herbal.id == HerbalTransaction.herbal_id)
                .filter(herbal_return_filter, HerbalTransaction.visit_id.is_(None))
            )
            if start_date:
                herbal_cogs_query = herbal_cogs_query.filter(HerbalTransaction.date >= start_date)
                herbal_return_cogs_query = herbal_return_cogs_query.filter(HerbalTransaction.date >= start_date)
            herbal_cogs = max(0, float(herbal_cogs_query.scalar() or 0) - float(herbal_return_cogs_query.scalar() or 0))

            active_visit_invoice_query = session.query(func.coalesce(func.sum(visit_revenue_expr), 0)).filter(active_visit_status)
            if start_date:
                active_visit_invoice_query = active_visit_invoice_query.filter(Visit.date >= start_date)
            active_visit_invoice_total = float(active_visit_invoice_query.scalar() or 0)

            active_herbal_invoice_query = session.query(func.coalesce(func.sum(herbal_revenue_expr), 0)).filter(
                *standalone_herbal_sale_filter,
                active_herbal_status,
            )
            if start_date:
                active_herbal_invoice_query = active_herbal_invoice_query.filter(HerbalTransaction.date >= start_date)
            active_herbal_invoice_total = float(active_herbal_invoice_query.scalar() or 0)

            void_herbal_invoice_query = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)).filter(
                *standalone_herbal_sale_filter,
                void_herbal_status,
            )
            if start_date:
                void_herbal_invoice_query = void_herbal_invoice_query.filter(HerbalTransaction.date >= start_date)
            void_herbal_invoice_total = float(void_herbal_invoice_query.scalar() or 0)

            active_invoice_total = active_visit_invoice_total + active_herbal_invoice_total
            void_invoice_total = void_visit_revenue + void_herbal_invoice_total
            total_income = net_visit_revenue + net_herbal_sales
            gross_profit = total_income - herbal_cogs
            total_transactions = total_visits + total_herbal_sales

            def _visit_invoice_count(status_filter):
                query = session.query(func.count(Visit.id)).filter(status_filter)
                if start_date:
                    query = query.filter(Visit.date >= start_date)
                return int(query.scalar() or 0)

            def _herbal_only_invoice_count(status_filter):
                grouped_query = session.query(func.count(func.distinct(HerbalTransaction.sale_group_id))).filter(
                    herbal_sale_filter,
                    status_filter,
                    HerbalTransaction.visit_id.is_(None),
                    HerbalTransaction.sale_group_id.isnot(None),
                    HerbalTransaction.sale_group_id != "",
                )
                legacy_query = session.query(func.count(HerbalTransaction.id)).filter(
                    herbal_sale_filter,
                    status_filter,
                    HerbalTransaction.visit_id.is_(None),
                    or_(HerbalTransaction.sale_group_id.is_(None), HerbalTransaction.sale_group_id == ""),
                )
                if start_date:
                    grouped_query = grouped_query.filter(HerbalTransaction.date >= start_date)
                    legacy_query = legacy_query.filter(HerbalTransaction.date >= start_date)
                return int(grouped_query.scalar() or 0) + int(legacy_query.scalar() or 0)

            active_invoice_count = _visit_invoice_count(active_visit_status) + _herbal_only_invoice_count(active_herbal_status)
            void_invoice_count = _visit_invoice_count(void_visit_status) + _herbal_only_invoice_count(void_herbal_status)

            # Month-over-Month (MoM) Growth Calculation
            now = datetime.datetime.now()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if current_month_start.month == 1:
                prev_month_start = current_month_start.replace(year=current_month_start.year - 1, month=12)
            else:
                prev_month_start = current_month_start.replace(month=current_month_start.month - 1)

            current_month_visits, current_month_income = session.query(
                func.count(Visit.id),
                func.coalesce(func.sum(visit_revenue_expr), 0)
            ).filter(Visit.date >= current_month_start, active_visit_status).one()
            prev_month_visits, prev_month_income = session.query(
                func.count(Visit.id),
                func.coalesce(func.sum(visit_revenue_expr), 0)
            ).filter(and_(Visit.date >= prev_month_start, Visit.date < current_month_start), active_visit_status).one()

            current_month_herbal_sales, current_month_herbal_income = session.query(
                func.count(HerbalTransaction.id),
                func.coalesce(func.sum(herbal_revenue_expr), 0)
            ).filter(
                HerbalTransaction.date >= current_month_start,
                *standalone_herbal_sale_filter,
                active_herbal_status,
            ).one()
            current_month_herbal_returns = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)).filter(
                HerbalTransaction.date >= current_month_start,
                herbal_return_filter,
                HerbalTransaction.visit_id.is_(None),
            ).scalar() or 0
            prev_month_herbal_sales, prev_month_herbal_income = session.query(
                func.count(HerbalTransaction.id),
                func.coalesce(func.sum(herbal_revenue_expr), 0)
            ).filter(
                and_(HerbalTransaction.date >= prev_month_start, HerbalTransaction.date < current_month_start),
                *standalone_herbal_sale_filter,
                active_herbal_status,
            ).one()
            prev_month_herbal_returns = session.query(func.coalesce(func.sum(HerbalTransaction.total_price), 0)).filter(
                and_(HerbalTransaction.date >= prev_month_start, HerbalTransaction.date < current_month_start),
                herbal_return_filter,
                HerbalTransaction.visit_id.is_(None),
            ).scalar() or 0

            current_month_visits = int(current_month_visits or 0)
            current_month_herbal_sales = int(current_month_herbal_sales or 0)
            current_month_income = float(current_month_income or 0) + max(0, float(current_month_herbal_income or 0) - float(current_month_herbal_returns or 0))
            prev_month_visits = int(prev_month_visits or 0)
            prev_month_herbal_sales = int(prev_month_herbal_sales or 0)
            prev_month_income = float(prev_month_income or 0) + max(0, float(prev_month_herbal_income or 0) - float(prev_month_herbal_returns or 0))
            current_month_transactions = current_month_visits + current_month_herbal_sales
            prev_month_transactions = prev_month_visits + prev_month_herbal_sales

            visits_growth = 0
            if prev_month_transactions > 0:
                visits_growth = ((current_month_transactions - prev_month_transactions) / prev_month_transactions) * 100

            income_growth = 0
            if prev_month_income > 0:
                income_growth = ((current_month_income - prev_month_income) / prev_month_income) * 100

            # Asset valuation
            total_herbal_value = session.query(
                func.coalesce(func.sum(Herbal.price * Herbal.stock), 0)
            ).filter(Herbal.is_active == True).scalar() or 0
            total_herbal_value = float(total_herbal_value)

            # Genders with pure SQL Group By
            gender_query = session.query(
                Patient.gender, func.count(func.distinct(Visit.patient_id))
            ).select_from(Visit).join(Patient)
            if start_date:
                gender_query = gender_query.filter(Visit.date >= start_date)
            gender_data = gender_query.group_by(Patient.gender).all()

            male_count = 0
            female_count = 0
            for g, c in gender_data:
                if g == 'Laki-laki':
                    male_count += c
                else:
                    female_count += c

            # Chart Data - Aggregate by Month/Day in DB
            from sqlalchemy import extract

            if period in ("7d", "30d"):
                if start_date:
                    # Group by Day
                    chart_agg = session.query(
                        func.strftime('%d %m %Y', Visit.date).label('day'),
                        func.count(Visit.id),
                        func.sum(visit_revenue_expr)
                    ).filter(Visit.date >= start_date, active_visit_status).group_by('day').all()

                    for row in chart_agg:
                        if row[0]:
                            try:
                                d = datetime.datetime.strptime(row[0], '%d %m %Y')
                                key = d.strftime("%d %b")
                                if key in chart_data:
                                    chart_data[key]["visits"] += int(row[1] or 0)
                                    chart_data[key]["income"] += float(row[2] or 0)
                            except Exception:
                                pass
                    herbal_chart_agg = session.query(
                        func.strftime('%d %m %Y', HerbalTransaction.date).label('day'),
                        func.sum(herbal_revenue_expr)
                    ).filter(
                        HerbalTransaction.date >= start_date,
                        *standalone_herbal_sale_filter,
                        active_herbal_status,
                    ).group_by('day').all()

                    for row in herbal_chart_agg:
                        if row[0]:
                            try:
                                d = datetime.datetime.strptime(row[0], '%d %m %Y')
                                key = d.strftime("%d %b")
                                if key in chart_data:
                                    chart_data[key]["income"] += float(row[1] or 0)
                            except Exception:
                                pass
                    herbal_return_chart_agg = session.query(
                        func.strftime('%d %m %Y', HerbalTransaction.date).label('day'),
                        func.sum(HerbalTransaction.total_price)
                    ).filter(
                        HerbalTransaction.date >= start_date,
                        herbal_return_filter,
                        HerbalTransaction.visit_id.is_(None),
                    ).group_by('day').all()

                    for row in herbal_return_chart_agg:
                        if row[0]:
                            try:
                                d = datetime.datetime.strptime(row[0], '%d %m %Y')
                                key = d.strftime("%d %b")
                                if key in chart_data:
                                    chart_data[key]["income"] = max(0, chart_data[key]["income"] - float(row[1] or 0))
                            except Exception:
                                pass
            else:
                # Group by Month
                chart_agg = session.query(
                    func.strftime('%m %Y', Visit.date).label('month'),
                    func.count(Visit.id),
                    func.sum(visit_revenue_expr)
                )
                if start_date:
                    chart_agg = chart_agg.filter(Visit.date >= start_date)
                chart_agg = chart_agg.filter(active_visit_status)
                chart_agg = chart_agg.group_by('month').all()

                for row in chart_agg:
                    if row[0]:
                        try:
                            m, y = row[0].split(' ')
                            d = datetime.datetime(int(y), int(m), 1)
                            if period == "1y":
                                key = d.strftime("%b")
                            else:
                                key = d.strftime("%b %Y")

                            if key in chart_data:
                                chart_data[key]["visits"] += int(row[1] or 0)
                                chart_data[key]["income"] += float(row[2] or 0)
                        except Exception:
                            pass
                herbal_chart_agg = session.query(
                    func.strftime('%m %Y', HerbalTransaction.date).label('month'),
                    func.sum(herbal_revenue_expr)
                ).filter(*standalone_herbal_sale_filter, active_herbal_status)
                if start_date:
                    herbal_chart_agg = herbal_chart_agg.filter(HerbalTransaction.date >= start_date)
                herbal_chart_agg = herbal_chart_agg.group_by('month').all()

                for row in herbal_chart_agg:
                    if row[0]:
                        try:
                            m, y = row[0].split(' ')
                            d = datetime.datetime(int(y), int(m), 1)
                            if period == "1y":
                                key = d.strftime("%b")
                            else:
                                key = d.strftime("%b %Y")

                            if key in chart_data:
                                    chart_data[key]["income"] += float(row[1] or 0)
                        except Exception:
                            pass
                herbal_return_chart_agg = session.query(
                    func.strftime('%m %Y', HerbalTransaction.date).label('month'),
                    func.sum(HerbalTransaction.total_price)
                ).filter(herbal_return_filter, HerbalTransaction.visit_id.is_(None))
                if start_date:
                    herbal_return_chart_agg = herbal_return_chart_agg.filter(HerbalTransaction.date >= start_date)
                herbal_return_chart_agg = herbal_return_chart_agg.group_by('month').all()

                for row in herbal_return_chart_agg:
                    if row[0]:
                        try:
                            m, y = row[0].split(' ')
                            d = datetime.datetime(int(y), int(m), 1)
                            if period == "1y":
                                key = d.strftime("%b")
                            else:
                                key = d.strftime("%b %Y")

                            if key in chart_data:
                                chart_data[key]["income"] = max(0, chart_data[key]["income"] - float(row[1] or 0))
                        except Exception:
                            pass

            monthly_labels = list(chart_data.keys())
            monthly_visits = [chart_data[k]["visits"] for k in monthly_labels]
            monthly_income = [chart_data[k]["income"] for k in monthly_labels]

            # Top therapists
            top_t_query = session.query(
                Therapist.id, Therapist.name,
                func.count(Visit.id).label('v_count'),
                func.sum(visit_revenue_expr).label('t_income'),
                func.sum(Visit.point_count).label('t_points')
            ).select_from(Visit).join(Therapist).filter(Visit.date >= start_date if start_date else True)\
             .filter(active_visit_status)\
             .group_by(Therapist.id, Therapist.name).order_by(text('v_count DESC')).limit(5).all()

            top_therapists = [
                {"id": t.id, "name": t.name, "visits": t.v_count, "income": float(t.t_income or 0), "points": int(t.t_points or 0)}
                for t in top_t_query
            ]

            # Visit frequency per patient - relative to this timeframe!
            patient_v_counts = session.query(
                Visit.patient_id, func.count(Visit.id).label('v_count')
            ).filter(Visit.date >= start_date if start_date else True).filter(active_visit_status).group_by(Visit.patient_id).all()

            freq = {"1": 0, "2-4": 0, "5+": 0}
            for pid, count in patient_v_counts:
                if count == 1: freq["1"] += 1
                elif count <= 4: freq["2-4"] += 1
                else: freq["5+"] += 1

            # Recent transactions (last 10)
            recent_query = session.query(
                Visit.date, Visit.price, Visit.final_price, Visit.point_count,
                Patient.name.label('patient_name'), Therapist.name.label('therapist_name'),
                Visit.invoice_status,
                Visit.payment_status, Visit.payment_method,
            ).outerjoin(Patient, Patient.id == Visit.patient_id).outerjoin(Therapist, Therapist.id == Visit.therapist_id)\
             .order_by(Visit.date.desc()).limit(10).all()

            recent = []
            for v in recent_query:
                raw = v.date
                try:
                    d = raw if hasattr(raw, "strftime") else datetime.datetime.fromisoformat(str(raw))
                    date_str = d.strftime("%d %b %Y %H:%M")
                except Exception:
                    date_str = str(raw)

                recent.append({
                    "date": date_str,
                    "date_obj": d,
                    "type": "visit",
                    "patient": v.patient_name or "Unknown",
                    "therapist": v.therapist_name or "-",
                    "price": float(v.final_price or v.price or 0),
                    "point_count": v.point_count or 0,
                    "invoice_status": v.invoice_status or "active",
                    "payment_status": v.payment_status or "paid",
                    "payment_method": v.payment_method or "cash",
                })

            herbal_recent_query = session.query(
                HerbalTransaction.date,
                HerbalTransaction.quantity,
                HerbalTransaction.total_price,
                HerbalTransaction.transaction_type,
                HerbalTransaction.invoice_status,
                HerbalTransaction.payment_status, HerbalTransaction.payment_method,
                Herbal.name.label('herbal_name'),
            ).outerjoin(Herbal, Herbal.id == HerbalTransaction.herbal_id)\
             .filter(HerbalTransaction.transaction_type.in_(["sale", "return", "retur"]))\
             .order_by(HerbalTransaction.date.desc()).limit(10).all()

            for h in herbal_recent_query:
                raw = h.date
                try:
                    d = raw if hasattr(raw, "strftime") else datetime.datetime.fromisoformat(str(raw))
                    date_str = d.strftime("%d %b %Y %H:%M")
                except Exception:
                    d = datetime.datetime.min
                    date_str = str(raw)

                recent.append({
                    "date": date_str,
                    "date_obj": d,
                    "type": "herbal",
                    "patient": f"Herbal: {h.herbal_name or 'Unknown'}",
                    "therapist": "Retur herbal" if h.transaction_type in ("return", "retur") else "Penjualan herbal",
                    "price": float(h.total_price or 0),
                    "point_count": int(h.quantity or 0),
                    "transaction_type": h.transaction_type,
                    "invoice_status": h.invoice_status or "active",
                    "payment_status": h.payment_status or "paid",
                    "payment_method": h.payment_method or "cash",
                })

            recent.sort(key=lambda item: item["date_obj"], reverse=True)
            recent = recent[:10]
            for item in recent:
                item.pop("date_obj", None)

            avg_income = total_income / total_transactions if total_transactions > 0 else 0
            correction_query = session.query(CorrectionLog.action_type, func.count(CorrectionLog.id))
            if start_date:
                correction_query = correction_query.filter(CorrectionLog.created_at >= start_date)
            correction_counts = {
                action: int(count or 0)
                for action, count in correction_query.group_by(CorrectionLog.action_type).all()
            }

            return {
                "total_patients": total_patients_global,
                "total_visits": total_visits,
                "total_herbal_sales": total_herbal_sales,
                "total_transactions": total_transactions,
                "total_income": total_income,
                "gross_visit_revenue": gross_visit_revenue,
                "void_visit_revenue": void_visit_revenue,
                "net_visit_revenue": net_visit_revenue,
                "gross_herbal_sales": gross_herbal_sales,
                "herbal_returns": herbal_returns,
                "net_herbal_sales": net_herbal_sales,
                "herbal_cogs": herbal_cogs,
                "gross_profit": gross_profit,
                "active_invoice_total": active_invoice_total,
                "void_invoice_total": void_invoice_total,
                "active_invoice_count": active_invoice_count,
                "void_invoice_count": void_invoice_count,
                "correction_summary": {
                    "stock_corrections": correction_counts.get("stock_correction", 0),
                    "herbal_returns": correction_counts.get("return", 0) + correction_counts.get("retur", 0),
                    "void_invoices": correction_counts.get("void_invoice", 0),
                },
                "avg_income": avg_income,
                "current_month_visits": current_month_visits,
                "current_month_herbal_sales": current_month_herbal_sales,
                "current_month_transactions": current_month_transactions,
                "visits_growth_pct": round(visits_growth, 1),
                "current_month_income": current_month_income,
                "income_growth_pct": round(income_growth, 1),
                "total_herbal_value": total_herbal_value,
                "low_stock_count": low_stock_count,
                "male_count": male_count,
                "female_count": female_count,
                "monthly_labels": monthly_labels,
                "monthly_visits": monthly_visits,
                "monthly_income": monthly_income,
                "top_therapists": top_therapists,
                "visit_frequency": freq,
                "recent_visits": recent,
                "recent_transactions": recent
            }

    def get_patients(self):
        with self.Session() as session:
            patients = session.query(Patient).options(joinedload(Patient.visits)).all()
            return [(p.id, p.name, p.phone, p.gender, p.address, len(p.visits)) for p in patients]

    def get_patient_with_visits(self, patient_id):
        with self.Session() as session:
            patient = session.get(Patient, patient_id, options=[joinedload(Patient.visits)])
            if patient:
                return patient
            raise ValueError("Patient not found")

    def update_patient(self, patient_id, name, phone, address='', gender='Laki-laki'):
        with self.Session() as session:
            if not str(name or "").strip():
                raise ValueError("Nama pasien wajib diisi")
            if gender not in ("Laki-laki", "Perempuan"):
                raise ValueError("Jenis kelamin pasien tidak valid")
            phone = str(phone or "").strip()
            if phone and not phone.isdigit() and not phone.startswith("TEMP-"):
                raise ValueError("Nomor HP harus berupa angka")
            patient = session.get(Patient, patient_id)
            if not patient:
                raise ValueError("Patient not found")
            patient.name = str(name).strip()
            patient.phone = phone
            patient.address = address
            patient.gender = gender
            session.commit()

    def delete_patient(self, patient_id):
        with self.Session() as session:
            patient = session.get(Patient, patient_id)
            if patient:
                visit_count = session.query(func.count(Visit.id)).filter(Visit.patient_id == patient_id).scalar() or 0
                if int(visit_count or 0) > 0:
                    raise ValueError("Pasien sudah memiliki kunjungan/transaksi sehingga tidak boleh dihapus permanen.")
                session.delete(patient)
                session.commit()

    def _discount_rule_to_data(self, rule):
        usage_count = 0
        if hasattr(rule, "usage_count"):
            usage_count = int(rule.usage_count or 0)
        target_patient_ids = list(getattr(rule, "target_patient_ids", []) or [])
        target_patient_names = list(getattr(rule, "target_patient_names", []) or [])
        return DiscountRuleData(
            id=rule.id,
            name=rule.name,
            type=rule.type,
            discount_type=rule.discount_type,
            discount_value=float(rule.discount_value or 0),
            condition_value=float(rule.condition_value) if rule.condition_value is not None else None,
            voucher_code=rule.voucher_code,
            start_date=rule.start_date,
            end_date=rule.end_date,
            is_active=bool(rule.is_active),
            priority=int(rule.priority or 100),
            created_at=rule.created_at,
            usage_limit=int(rule.usage_limit) if rule.usage_limit is not None else None,
            per_patient_limit=int(rule.per_patient_limit) if rule.per_patient_limit is not None else None,
            usage_count=usage_count,
            target_patient_ids=target_patient_ids,
            target_patient_names=target_patient_names,
        )

    def get_discount_rules(self, active_only=False):
        with self.Session() as session:
            usage_counts = (
                session.query(VoucherUsage.discount_rule_id, func.count(VoucherUsage.id).label("usage_count"))
                .group_by(VoucherUsage.discount_rule_id)
                .subquery()
            )
            query = (
                session.query(DiscountRule, func.coalesce(usage_counts.c.usage_count, 0).label("usage_count"))
                .outerjoin(usage_counts, DiscountRule.id == usage_counts.c.discount_rule_id)
            )
            if active_only:
                query = query.filter(DiscountRule.is_active == True)
            rows = query.order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc()).all()
            result = []
            for rule, usage_count in rows:
                rule.usage_count = usage_count
                target_rows = (
                    session.query(VoucherPatientTarget.patient_id, Patient.name)
                    .join(Patient, Patient.id == VoucherPatientTarget.patient_id)
                    .filter(VoucherPatientTarget.discount_rule_id == rule.id)
                    .order_by(Patient.name.asc())
                    .all()
                )
                rule.target_patient_ids = [patient_id for patient_id, _name in target_rows]
                rule.target_patient_names = [name for _patient_id, name in target_rows]
                result.append(self._discount_rule_to_data(rule))
            return result

    def _normalize_target_patient_ids(self, session, patient_ids):
        normalized = []
        for raw_id in patient_ids or []:
            try:
                patient_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if patient_id > 0 and patient_id not in normalized:
                normalized.append(patient_id)
        if not normalized:
            return []
        existing_ids = {
            patient_id
            for (patient_id,) in session.query(Patient.id).filter(Patient.id.in_(normalized)).all()
        }
        return [patient_id for patient_id in normalized if patient_id in existing_ids]

    def _replace_voucher_patient_targets(self, session, rule_id, patient_ids):
        session.query(VoucherPatientTarget).filter(VoucherPatientTarget.discount_rule_id == rule_id).delete()
        for patient_id in self._normalize_target_patient_ids(session, patient_ids):
            session.add(VoucherPatientTarget(discount_rule_id=rule_id, patient_id=patient_id))

    def add_discount_rule(self, data):
        with self.Session() as session:
            rule = DiscountRule(
                name=data["name"],
                type=data["type"],
                discount_type=data["discount_type"],
                discount_value=float(data["discount_value"]),
                condition_value=data.get("condition_value"),
                voucher_code=data.get("voucher_code") or None,
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                is_active=bool(data.get("is_active", True)),
                priority=int(data.get("priority", 100)),
                usage_limit=data.get("usage_limit"),
                per_patient_limit=data.get("per_patient_limit"),
            )
            session.add(rule)
            session.flush()
            if rule.type == "voucher":
                self._replace_voucher_patient_targets(session, rule.id, data.get("target_patient_ids") or [])
            session.commit()
            return rule.id

    def update_discount_rule(self, rule_id, data):
        with self.Session() as session:
            rule = session.get(DiscountRule, rule_id)
            if not rule:
                return False
            rule.name = data["name"]
            rule.type = data["type"]
            rule.discount_type = data["discount_type"]
            rule.discount_value = float(data["discount_value"])
            rule.condition_value = data.get("condition_value")
            rule.voucher_code = data.get("voucher_code") or None
            rule.start_date = data.get("start_date")
            rule.end_date = data.get("end_date")
            rule.is_active = bool(data.get("is_active", True))
            rule.priority = int(data.get("priority", 100))
            rule.usage_limit = data.get("usage_limit")
            rule.per_patient_limit = data.get("per_patient_limit")
            if rule.type == "voucher":
                self._replace_voucher_patient_targets(session, rule.id, data.get("target_patient_ids") or [])
            else:
                self._replace_voucher_patient_targets(session, rule.id, [])
            session.commit()
            return True

    def set_discount_rule_active(self, rule_id, is_active):
        with self.Session() as session:
            rule = session.get(DiscountRule, rule_id)
            if not rule:
                return False
            rule.is_active = bool(is_active)
            session.commit()
            return True

    def delete_discount_rule(self, rule_id):
        with self.Session() as session:
            rule = session.get(DiscountRule, rule_id)
            if not rule:
                return False
            visit_count = session.query(func.count(Visit.id)).filter(Visit.discount_rule_id == rule_id).scalar() or 0
            usage_count = session.query(func.count(VoucherUsage.id)).filter(VoucherUsage.discount_rule_id == rule_id).scalar() or 0
            if int(visit_count or 0) > 0 or int(usage_count or 0) > 0:
                rule.is_active = False
                session.commit()
                return "deactivated"
            session.query(VoucherPatientTarget).filter(VoucherPatientTarget.discount_rule_id == rule_id).delete()
            session.delete(rule)
            session.commit()
            return "deleted"

    def _rule_date_matches(self, rule, current_dt):
        if rule.start_date and current_dt < rule.start_date:
            return False
        if rule.end_date:
            end_dt = rule.end_date
            if isinstance(end_dt, datetime) and end_dt.time() == time.min:
                end_dt = datetime.combine(end_dt.date(), time.max)
            if current_dt > end_dt:
                return False
        return True

    def _voucher_limit_matches(self, session, rule, patient_id=None):
        if rule.type != "voucher":
            return True

        target_count = (
            session.query(func.count(VoucherPatientTarget.id))
            .filter(VoucherPatientTarget.discount_rule_id == rule.id)
            .scalar()
            or 0
        )
        if target_count > 0:
            if not patient_id:
                return False
            is_targeted = (
                session.query(VoucherPatientTarget.id)
                .filter(
                    VoucherPatientTarget.discount_rule_id == rule.id,
                    VoucherPatientTarget.patient_id == patient_id,
                )
                .first()
                is not None
            )
            if not is_targeted:
                return False

        usage_limit = int(rule.usage_limit or 0)
        if usage_limit > 0:
            total_used = (
                session.query(func.count(VoucherUsage.id))
                .filter(VoucherUsage.discount_rule_id == rule.id)
                .scalar()
                or 0
            )
            if total_used >= usage_limit:
                return False

        per_patient_limit = int(rule.per_patient_limit or 0)
        if patient_id and per_patient_limit > 0:
            patient_used = (
                session.query(func.count(VoucherUsage.id))
                .filter(
                    VoucherUsage.discount_rule_id == rule.id,
                    VoucherUsage.patient_id == patient_id,
                )
                .scalar()
                or 0
            )
            if patient_used >= per_patient_limit:
                return False

        return True

    def _rule_matches(self, rule, visit_count, manual_price_used=False, voucher_code=None, current_dt=None, session=None, patient_id=None):
        current_dt = current_dt or datetime.now()
        if not self._rule_date_matches(rule, current_dt):
            return False
        if rule.type == "visit_count":
            threshold = int(rule.condition_value or 0)
            next_visit_number = visit_count + 1
            return threshold > 0 and next_visit_number >= threshold
        if rule.type == "voucher":
            code_matches = bool(voucher_code) and str(rule.voucher_code or "").strip().lower() == str(voucher_code).strip().lower()
            if not code_matches:
                return False
            if session is None:
                return True
            return self._voucher_limit_matches(session, rule, patient_id=patient_id)
        if rule.type == "manual":
            return bool(manual_price_used)
        if rule.type == "period":
            return True
        return False

    def _apply_discount_value(self, price, rule):
        if rule.discount_type == "percent":
            return max(0, price * (1 - float(rule.discount_value or 0) / 100))
        if rule.discount_type == "fixed":
            return max(0, price - float(rule.discount_value or 0))
        return price

    def find_matching_discount_rule(self, visit_count, price, manual_price_used=False, voucher_code=None, current_dt=None, patient_id=None):
        if float(price or 0) <= 0:
            return None
        with self.Session() as session:
            rules = (
                session.query(DiscountRule)
                .filter(DiscountRule.is_active == True)
                .order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc())
                .all()
            )
            for rule in rules:
                if self._rule_matches(
                    rule,
                    visit_count,
                    manual_price_used=manual_price_used,
                    voucher_code=voucher_code,
                    current_dt=current_dt,
                    session=session,
                    patient_id=patient_id,
                ):
                    return self._discount_rule_to_data(rule)
        return None

    def update_patient_visits(self, patient_id: int, new_visits: List[VisitData]):
        with self.Session() as session:
            patient = session.get(Patient, patient_id, options=[joinedload(Patient.visits)])
            if not patient:
                raise ValueError("Patient not found")

            existing_visits = {v.id: v for v in patient.visits}
            new_visits_by_id = {v.id: v for v in new_visits if v.id is not None}

            for vid, data in new_visits_by_id.items():
                if vid in existing_visits:
                    data_price = float(data.price or 0)
                    data_points = int(data.point_count if hasattr(data, 'point_count') else 0)
                    data_is_free = bool(data.is_free_visit) if hasattr(data, 'is_free_visit') else False
                    data_free_reason = data.free_visit_reason if hasattr(data, 'free_visit_reason') else None
                    if data_points < 1:
                        raise ValueError("Jumlah layanan minimal 1")
                    if data_price < 0:
                        raise ValueError("Harga kunjungan tidak boleh kurang dari 0")
                    if data_price == 0 and not data_is_free:
                        raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis")
                    if data_is_free and data_price != 0:
                        raise ValueError("Kunjungan gratis harus memakai harga 0")
                    if data_is_free and not str(data_free_reason or "").strip():
                        raise ValueError("Alasan kunjungan gratis wajib diisi")
                    v = existing_visits[vid]
                    v.date = data.date
                    v.price = data_price
                    v.original_price = float(getattr(data, 'original_price', None) or data_price)
                    v.discount_amount = float(getattr(data, 'discount_amount', None) or 0)
                    v.final_price = float(getattr(data, 'final_price', None) or data_price)
                    v.discount_applied = data.discount_applied
                    if hasattr(data, 'point_count'):
                        v.point_count = data_points
                    if hasattr(data, 'therapist_id'):
                        v.therapist_id = data.therapist_id
                    if hasattr(data, 'service_id'):
                        v.service_id = data.service_id
                    if hasattr(data, 'service_name'):
                        v.service_name = data.service_name or "Bekam"
                    if hasattr(data, 'medical_notes'):
                        v.medical_notes = data.medical_notes
                    v.is_free_visit = data_is_free
                    v.free_visit_reason = str(data_free_reason or "").strip() if data_is_free else None
                    if hasattr(data, 'discount_rule_id'):
                        v.discount_rule_id = data.discount_rule_id
                    if hasattr(data, 'discount_rule_name'):
                        v.discount_rule_name = data.discount_rule_name

            new_ids = set(new_visits_by_id.keys())
            for v in list(patient.visits):
                if v.id not in new_ids:
                    patient.visits.remove(v)

            for visit in new_visits:
                if visit.id is None:
                    visit_price = float(visit.price or 0)
                    visit_points = int(visit.point_count if hasattr(visit, 'point_count') else 0)
                    visit_is_free = bool(visit.is_free_visit) if hasattr(visit, 'is_free_visit') else False
                    visit_free_reason = visit.free_visit_reason if hasattr(visit, 'free_visit_reason') else None
                    if visit_points < 1:
                        raise ValueError("Jumlah layanan minimal 1")
                    if visit_price < 0:
                        raise ValueError("Harga kunjungan tidak boleh kurang dari 0")
                    if visit_price == 0 and not visit_is_free:
                        raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis")
                    if visit_is_free and visit_price != 0:
                        raise ValueError("Kunjungan gratis harus memakai harga 0")
                    if visit_is_free and not str(visit_free_reason or "").strip():
                        raise ValueError("Alasan kunjungan gratis wajib diisi")
                    new_visit = Visit(
                        date=visit.date,
                        price=visit_price,
                        original_price=float(getattr(visit, 'original_price', None) or visit_price),
                        discount_amount=float(getattr(visit, 'discount_amount', None) or 0),
                        final_price=float(getattr(visit, 'final_price', None) or visit_price),
                        discount_applied=visit.discount_applied,
                        point_count=visit_points,
                        therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                        service_id=visit.service_id if hasattr(visit, 'service_id') else None,
                        service_name=(visit.service_name if hasattr(visit, 'service_name') else None) or "Bekam",
                        medical_notes=visit.medical_notes if hasattr(visit, 'medical_notes') else None,
                        is_free_visit=visit_is_free,
                        free_visit_reason=str(visit_free_reason or "").strip() if visit_is_free else None,
                        discount_rule_id=visit.discount_rule_id if hasattr(visit, 'discount_rule_id') else None,
                        discount_rule_name=visit.discount_rule_name if hasattr(visit, 'discount_rule_name') else None,
                    )
                    patient.visits.append(new_visit)

            session.commit()

    def _is_active_visit_for_discount_count(self, visit) -> bool:
        status = str(getattr(visit, "invoice_status", None) or "active").strip().lower()
        return status not in {"void", "cancelled", "deleted"}

    def add_visit(self, patient_id, price, point_count=0, therapist_id=None,
                  service_id=None, service_name=None,
                  discount_percentage=0, min_visits_for_discount=5, invoice_path=None,
                  medical_notes=None, inventory_config=None, is_free_visit=False,
                  free_visit_reason=None, manual_price_used=False, voucher_code=None,
                  discount_rule_id=None, herbal_items=None, payment_status='paid',
                  payment_method='cash', amount_paid=None, paid_at=None, quantity=None):
        with self.Session() as session:
            if quantity is not None:
                point_count = quantity
            patient = session.get(Patient, patient_id, options=[joinedload(Patient.visits)])
            if not patient:
                raise ValueError("Patient not found")
            if int(point_count or 0) < 1:
                raise ValueError("Jumlah layanan minimal 1")

            normalized_herbal_items = self._validate_visit_herbal_items(session, herbal_items)
            herbal_summary_lines = [
                f"- {item['herbal'].name} x{item['quantity']} {item['herbal'].unit} = {self._format_rupiah(item['total_price'])}"
                for item in normalized_herbal_items
            ]
            normalized_notes = str(medical_notes).strip() if medical_notes else "-"
            if herbal_summary_lines:
                herbal_summary = "Pembelian herbal:\n" + "\n".join(herbal_summary_lines)
                normalized_notes = herbal_summary if normalized_notes == "-" else f"{normalized_notes}\n\n{herbal_summary}"

            visit_count = sum(
                1 for v in patient.visits
                if self._is_active_visit_for_discount_count(v)
            )
            discount_applied = False
            requested_discount_rule_id = discount_rule_id
            discount_rule_id = None
            discount_rule_name = None
            final_price = float(price)
            if final_price < 0:
                raise ValueError("Harga kunjungan tidak boleh kurang dari 0")
            if final_price == 0 and not is_free_visit:
                raise ValueError("Harga 0 hanya boleh untuk kunjungan gratis")
            if is_free_visit and final_price != 0:
                raise ValueError("Kunjungan gratis harus memakai harga 0")
            normalized_free_reason = str(free_visit_reason or "").strip() if is_free_visit else None
            if is_free_visit and not normalized_free_reason:
                raise ValueError("Alasan kunjungan gratis wajib diisi")

            normalized_service_name = str(service_name or "").strip()
            if service_id:
                service = session.get(Service, service_id)
                if not service:
                    raise ValueError("Layanan tidak ditemukan.")
                if not service.is_active:
                    raise ValueError("Layanan nonaktif tidak bisa dipakai untuk kunjungan baru.")
                normalized_service_name = service.name
            if not normalized_service_name:
                normalized_service_name = "Bekam"

            matched_rule = None
            if final_price > 0 and not is_free_visit:
                if requested_discount_rule_id:
                    matched_rule = session.get(DiscountRule, int(requested_discount_rule_id))
                    if not matched_rule:
                        raise ValueError("Rule diskon tidak ditemukan")
                    if not matched_rule.is_active:
                        raise ValueError("Rule diskon tidak aktif")
                    if not self._rule_date_matches(matched_rule, datetime.now()):
                        raise ValueError("Rule diskon tidak berlaku pada tanggal ini")
                    if not self._rule_matches(
                        matched_rule,
                        visit_count,
                        manual_price_used=manual_price_used,
                        voucher_code=voucher_code,
                        session=session,
                        patient_id=patient_id,
                    ):
                        if matched_rule.type == "voucher":
                            raise ValueError("Voucher tidak valid atau batas pemakaian sudah habis.")
                        raise ValueError("Rule diskon tidak cocok untuk kunjungan ini.")
                else:
                    rules = (
                        session.query(DiscountRule)
                        .filter(DiscountRule.is_active == True)
                        .order_by(DiscountRule.priority.asc(), DiscountRule.created_at.asc())
                        .all()
                    )
                    for rule in rules:
                        if self._rule_matches(
                            rule,
                            visit_count,
                            manual_price_used=manual_price_used,
                            voucher_code=voucher_code,
                            session=session,
                            patient_id=patient_id,
                        ):
                            matched_rule = rule
                            break

            original_price = float(final_price or 0)
            if matched_rule:
                final_price = max(0, self._apply_discount_value(final_price, matched_rule))
                discount_applied = True
                discount_rule_id = matched_rule.id
                discount_rule_name = matched_rule.name
            elif final_price > 0 and discount_percentage > 0 and visit_count >= min_visits_for_discount:
                final_price = max(0, final_price * (1 - discount_percentage / 100))
                discount_applied = True
                discount_rule_name = f"Diskon lama {discount_percentage}%"
            discount_amount = round(max(0, original_price - final_price), 2)

            herbal_total = sum(float(item["total_price"] or 0) for item in normalized_herbal_items)
            payment_total = final_price + herbal_total
            payment = normalize_visit_payment(
                payment_total,
                payment_status=payment_status,
                payment_method=payment_method,
                amount_paid=amount_paid,
                paid_at=paid_at,
                is_free_visit=is_free_visit,
            )
            component_payments = allocate_payment_amounts(
                payment["amount_paid"],
                [final_price] + [item["total_price"] for item in normalized_herbal_items],
            )
            visit_amount_paid = component_payments[0] if component_payments else 0
            herbal_amounts_paid = component_payments[1:]

            new_visit = Visit(
                patient_id=patient_id,
                therapist_id=therapist_id,
                service_id=service_id,
                service_name=normalized_service_name,
                date=datetime.now(),
                price=round(final_price, 2),
                original_price=round(original_price, 2),
                discount_amount=discount_amount,
                final_price=round(final_price, 2),
                discount_applied=discount_applied,
                point_count=int(point_count or 0),
                invoice_path=invoice_path,
                medical_notes=normalized_notes,
                is_free_visit=bool(is_free_visit),
                free_visit_reason=normalized_free_reason,
                discount_rule_id=discount_rule_id,
                discount_rule_name=discount_rule_name,
                payment_status=payment["payment_status"],
                payment_method=payment["payment_method"],
                amount_paid=visit_amount_paid,
                paid_at=payment["paid_at"]
            )
            session.add(new_visit)
            session.flush()

            if matched_rule and matched_rule.type == "voucher":
                session.add(
                    VoucherUsage(
                        discount_rule_id=matched_rule.id,
                        patient_id=patient_id,
                        visit_id=new_visit.id,
                        voucher_code=str(matched_rule.voucher_code or voucher_code or "").strip(),
                        discount_amount=discount_amount,
                    )
                )

            service_usage = []
            if service_id:
                service_usage = (
                    session.query(ServiceInventoryUsage)
                    .join(Inventory, ServiceInventoryUsage.inventory_id == Inventory.id)
                    .filter(
                        ServiceInventoryUsage.service_id == service_id,
                        Inventory.is_active == True,
                        Inventory.item_type == "consumable",
                    )
                    .all()
                )

            for usage in service_usage:
                item = usage.inventory
                qty_reduction = int(usage.quantity or 0)
                if not item or qty_reduction <= 0:
                    continue
                if item.quantity < qty_reduction:
                    raise ValueError(f"Stok {item.item_name} tidak cukup. Tersedia {item.quantity} {item.unit}, perlu {qty_reduction} {item.unit}.")
                item.quantity -= qty_reduction
                self._add_inventory_transaction(
                    session,
                    item.id,
                    -qty_reduction,
                    "auto_usage",
                    f"Pemakaian otomatis layanan {normalized_service_name} untuk kunjungan #{new_visit.id or ''}".strip(),
                    visit_id=new_visit.id,
                )

            for item, herbal_amount_paid in zip(normalized_herbal_items, herbal_amounts_paid):
                herbal = item["herbal"]
                quantity = item["quantity"]
                if int(herbal.stock or 0) < quantity:
                    raise ValueError("Stok herbal tidak cukup. Silakan cek ulang pembelian herbal.")
                herbal.stock = int(herbal.stock or 0) - quantity
                self._add_herbal_transaction(
                    session,
                    herbal.id,
                    quantity,
                    item["total_price"],
                    "sale",
                    f"Pembelian herbal pada kunjungan #{new_visit.id} - Pasien: {patient.name}",
                    visit_id=new_visit.id,
                    payment_status=payment["payment_status"],
                    payment_method=payment["payment_method"],
                    amount_paid=herbal_amount_paid,
                    paid_at=payment["paid_at"],
                )

            session.commit()

            return round(final_price, 2), discount_applied, discount_rule_name

    def get_visits(self, patient_id):
        with self.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).all()
            return [{
                'id': v.id,
                'date': v.date,
                'price': float(v.price or 0),
                'original_price': float(getattr(v, 'original_price', None) or v.price or 0),
                'discount_amount': float(getattr(v, 'discount_amount', None) or 0),
                'final_price': float(getattr(v, 'final_price', None) or v.price or 0),
                'discount_applied': v.discount_applied,
                'point_count': v.point_count if hasattr(v, 'point_count') else 0,
                'quantity': v.point_count if hasattr(v, 'point_count') else 0,
                'therapist_id': v.therapist_id if hasattr(v, 'therapist_id') else None,
                'service_id': v.service_id if hasattr(v, 'service_id') else None,
                'service_name': (v.service_name if hasattr(v, 'service_name') else None) or 'Bekam',
                'invoice_path': v.invoice_path if hasattr(v, 'invoice_path') else None,
                'medical_notes': v.medical_notes if v.medical_notes else '-',
                'is_free_visit': v.is_free_visit if hasattr(v, 'is_free_visit') else False,
                'free_visit_reason': v.free_visit_reason if hasattr(v, 'free_visit_reason') else None,
                'discount_rule_id': v.discount_rule_id if hasattr(v, 'discount_rule_id') else None,
                'discount_rule_name': v.discount_rule_name if hasattr(v, 'discount_rule_name') else None,
            } for v in visits]

    def get_all_visits(self):
        with self.Session() as session:
            visits = session.query(Visit).all()
            return [{
                'id': v.id,
                'date': v.date,
                'price': float(v.price or 0),
                'final_price': float(v.price or 0),
                'discount_applied': v.discount_applied,
                'point_count': v.point_count if hasattr(v, 'point_count') else 0,
                'quantity': v.point_count if hasattr(v, 'point_count') else 0,
                'patient_id': v.patient_id,
                'therapist_id': v.therapist_id if hasattr(v, 'therapist_id') else None,
                'service_id': v.service_id if hasattr(v, 'service_id') else None,
                'service_name': (v.service_name if hasattr(v, 'service_name') else None) or 'Bekam',
                'invoice_path': v.invoice_path if hasattr(v, 'invoice_path') else None,
                'is_free_visit': v.is_free_visit if hasattr(v, 'is_free_visit') else False,
                'free_visit_reason': v.free_visit_reason if hasattr(v, 'free_visit_reason') else None,
                'discount_rule_id': v.discount_rule_id if hasattr(v, 'discount_rule_id') else None,
                'discount_rule_name': v.discount_rule_name if hasattr(v, 'discount_rule_name') else None,
            } for v in visits]

    def get_invoices_only(self):
        with self.Session() as session:
            # Only fetch visits that have an invoice_path
            visits = session.query(Visit).join(Patient).filter(Visit.invoice_path.isnot(None), Visit.invoice_path != '').all()
            return [{
                'id': v.id,
                'date': v.date,
                'price': float(v.price or 0),
                'final_price': float(v.price or 0),
                'patient_id': v.patient_id,
                'patient_name': v.patient.name,
                'service_id': v.service_id if hasattr(v, 'service_id') else None,
                'service_name': (v.service_name if hasattr(v, 'service_name') else None) or 'Bekam',
                'invoice_path': v.invoice_path,
                'is_free_visit': v.is_free_visit if hasattr(v, 'is_free_visit') else False,
                'free_visit_reason': v.free_visit_reason if hasattr(v, 'free_visit_reason') else None,
                'discount_rule_id': v.discount_rule_id if hasattr(v, 'discount_rule_id') else None,
                'discount_rule_name': v.discount_rule_name if hasattr(v, 'discount_rule_name') else None,
            } for v in visits]

    def add_therapist(self, name, gender, specialization='', can_handle_any_gender=False):
        with self.Session() as session:
            if not str(name or "").strip():
                raise ValueError("Nama terapis wajib diisi")
            if gender not in ("Laki-laki", "Perempuan"):
                raise ValueError("Jenis kelamin terapis tidak valid")
            therapist = Therapist(
                name=name,
                gender=gender,
                specialization=specialization,
                can_handle_any_gender=bool(can_handle_any_gender),
            )
            session.add(therapist)
            session.commit()
            return therapist.id

    def get_all_therapists(self, active_only=True):
        with self.Session() as session:
            query = session.query(Therapist)
            if active_only:
                query = query.filter(Therapist.is_active == True)
            therapists = query.all()
            return [
                TherapistData(
                    id=t.id,
                    name=t.name,
                    gender=t.gender,
                    specialization=t.specialization,
                    is_active=t.is_active,
                    can_handle_any_gender=bool(getattr(t, "can_handle_any_gender", False)),
                )
                for t in therapists
            ]

    def get_therapists_by_gender(self, gender):
        with self.Session() as session:
            therapists = session.query(Therapist).filter(
                (Therapist.gender == gender) | (Therapist.can_handle_any_gender == True),
                Therapist.is_active == True
            ).all()
            return [
                TherapistData(
                    id=t.id,
                    name=t.name,
                    gender=t.gender,
                    specialization=t.specialization,
                    is_active=t.is_active,
                    can_handle_any_gender=bool(getattr(t, "can_handle_any_gender", False)),
                )
                for t in therapists
            ]

    def update_therapist(self, therapist_id, name, gender, specialization='', is_active=True, can_handle_any_gender=False):
        with self.Session() as session:
            if not str(name or "").strip():
                raise ValueError("Nama terapis wajib diisi")
            if gender not in ("Laki-laki", "Perempuan"):
                raise ValueError("Jenis kelamin terapis tidak valid")
            therapist = session.get(Therapist, therapist_id)
            if not therapist:
                raise ValueError("Therapist not found")
            therapist.name = name
            therapist.gender = gender
            therapist.specialization = specialization
            therapist.is_active = is_active
            therapist.can_handle_any_gender = bool(can_handle_any_gender)
            session.commit()

    def delete_therapist(self, therapist_id):
        with self.Session() as session:
            therapist = session.get(Therapist, therapist_id)
            if not therapist:
                return False
            visit_count = session.query(func.count(Visit.id)).filter(Visit.therapist_id == therapist_id).scalar() or 0
            if visit_count > 0:
                raise ValueError("Data sudah memiliki riwayat kunjungan. Gunakan Nonaktifkan agar riwayat tetap aman.")
            session.delete(therapist)
            session.commit()
            return True

    def get_therapist(self, therapist_id):
        with self.Session() as session:
            therapist = session.get(Therapist, therapist_id)
            if therapist:
                return TherapistData(
                    id=therapist.id,
                    name=therapist.name,
                    gender=therapist.gender,
                    specialization=therapist.specialization,
                    is_active=therapist.is_active,
                    can_handle_any_gender=bool(getattr(therapist, "can_handle_any_gender", False)),
                )
            return None

    # --- Service Methods ---
    def _normalize_service_inventory_usage(self, session, usage_items):
        normalized = []
        seen = set()
        for raw in usage_items or []:
            if not isinstance(raw, dict):
                continue
            inventory_id = int(raw.get("inventory_id") or 0)
            quantity = int(raw.get("quantity") or 0)
            if inventory_id <= 0 or quantity <= 0:
                continue
            if inventory_id in seen:
                raise ValueError("Item inventaris pada pemakaian layanan tidak boleh dobel.")
            item = session.get(Inventory, inventory_id)
            if not item or not item.is_active:
                raise ValueError("Inventaris pada pemakaian layanan tidak ditemukan atau tidak aktif.")
            normalized.append({"inventory": item, "quantity": quantity})
            seen.add(inventory_id)
        return normalized

    def _replace_service_inventory_usage(self, session, service_id, usage_items):
        session.query(ServiceInventoryUsage).filter(ServiceInventoryUsage.service_id == service_id).delete()
        for usage in self._normalize_service_inventory_usage(session, usage_items):
            session.add(ServiceInventoryUsage(
                service_id=service_id,
                inventory_id=usage["inventory"].id,
                quantity=usage["quantity"],
            ))

    def _service_inventory_usage_payload(self, session, service_id):
        rows = (
            session.query(ServiceInventoryUsage)
            .join(Inventory, ServiceInventoryUsage.inventory_id == Inventory.id)
            .filter(ServiceInventoryUsage.service_id == service_id)
            .order_by(ServiceInventoryUsage.id.asc())
            .all()
        )
        return [
            {
                "id": row.id,
                "inventory_id": row.inventory_id,
                "item_name": row.inventory.item_name if row.inventory else "",
                "unit": row.inventory.unit if row.inventory else "",
                "quantity": int(row.quantity or 0),
            }
            for row in rows
        ]

    def add_service(self, name, unit_label='sesi', default_quantity=1, price_per_unit=0, notes_template='', inventory_usage=None,
                    pricing_type='per_unit', service_category='general', fixed_price=0, allow_manual_price=True):
        with self.Session() as session:
            if not str(name or "").strip():
                raise ValueError("Nama layanan wajib diisi")
            normalized_pricing_type = self._normalize_service_pricing_type(pricing_type)
            normalized_service_category = self._normalize_service_category(service_category)
            if int(default_quantity or 0) < 1:
                raise ValueError("Jumlah default layanan minimal 1")
            if float(price_per_unit or 0) < 0:
                raise ValueError("Harga layanan tidak boleh negatif")
            if float(fixed_price or 0) < 0:
                raise ValueError("Harga tetap layanan tidak boleh negatif")
            resolved_fixed_price = float(fixed_price or 0)
            if normalized_pricing_type == "fixed" and resolved_fixed_price <= 0:
                resolved_fixed_price = float(price_per_unit or 0) * int(default_quantity or 1)
            service = Service(
                name=str(name).strip(),
                pricing_type=normalized_pricing_type,
                service_category=normalized_service_category,
                fixed_price=resolved_fixed_price,
                allow_manual_price=bool(allow_manual_price),
                unit_label=unit_label or 'sesi',
                default_quantity=int(default_quantity or 1),
                price_per_unit=float(price_per_unit or 0),
                notes_template=notes_template or '',
                is_active=True,
            )
            session.add(service)
            session.flush()
            self._replace_service_inventory_usage(session, service.id, inventory_usage)
            session.commit()
            return service.id

    def update_service(self, service_id, name, unit_label='sesi', default_quantity=1,
                       price_per_unit=0, notes_template='', is_active=True, inventory_usage=None,
                       pricing_type='per_unit', service_category='general', fixed_price=0, allow_manual_price=True):
        with self.Session() as session:
            if not str(name or "").strip():
                raise ValueError("Nama layanan wajib diisi")
            normalized_pricing_type = self._normalize_service_pricing_type(pricing_type)
            normalized_service_category = self._normalize_service_category(service_category)
            if int(default_quantity or 0) < 1:
                raise ValueError("Jumlah default layanan minimal 1")
            if float(price_per_unit or 0) < 0:
                raise ValueError("Harga layanan tidak boleh negatif")
            if float(fixed_price or 0) < 0:
                raise ValueError("Harga tetap layanan tidak boleh negatif")
            resolved_fixed_price = float(fixed_price or 0)
            if normalized_pricing_type == "fixed" and resolved_fixed_price <= 0:
                resolved_fixed_price = float(price_per_unit or 0) * int(default_quantity or 1)
            service = session.get(Service, service_id)
            if not service:
                raise ValueError("Service not found")
            service.name = str(name).strip()
            service.pricing_type = normalized_pricing_type
            service.service_category = normalized_service_category
            service.fixed_price = resolved_fixed_price
            service.allow_manual_price = bool(allow_manual_price)
            service.unit_label = unit_label or 'sesi'
            service.default_quantity = int(default_quantity or 1)
            service.price_per_unit = float(price_per_unit or 0)
            service.notes_template = notes_template or ''
            service.is_active = bool(is_active)
            self._replace_service_inventory_usage(session, service.id, inventory_usage)
            session.commit()

    def delete_service(self, service_id):
        with self.Session() as session:
            service = session.get(Service, service_id)
            if not service:
                return False
            visit_count = session.query(func.count(Visit.id)).filter(Visit.service_id == service_id).scalar() or 0
            if visit_count > 0:
                raise ValueError("Data sudah memiliki riwayat kunjungan. Gunakan Nonaktifkan agar riwayat tetap aman.")
            session.query(ServiceInventoryUsage).filter(ServiceInventoryUsage.service_id == service_id).delete()
            session.delete(service)
            session.commit()
            return True

    def get_service(self, service_id):
        with self.Session() as session:
            service = session.get(Service, service_id)
            if not service:
                return None
            return ServiceData(
                id=service.id,
                name=service.name,
                pricing_type=getattr(service, "pricing_type", None) or "per_unit",
                service_category=getattr(service, "service_category", None) or "general",
                fixed_price=float(getattr(service, "fixed_price", None) or 0),
                allow_manual_price=bool(getattr(service, "allow_manual_price", True)),
                unit_label=service.unit_label,
                default_quantity=service.default_quantity,
                price_per_unit=float(service.price_per_unit or 0),
                notes_template=service.notes_template or '',
                is_active=service.is_active,
                inventory_usage=self._service_inventory_usage_payload(session, service.id),
            )

    def get_all_services(self, active_only=True):
        with self.Session() as session:
            query = session.query(Service).order_by(Service.id.asc())
            if active_only:
                query = query.filter(Service.is_active == True)
            services = query.all()
            return [
                ServiceData(
                    id=s.id,
                    name=s.name,
                    pricing_type=getattr(s, "pricing_type", None) or "per_unit",
                    service_category=getattr(s, "service_category", None) or "general",
                    fixed_price=float(getattr(s, "fixed_price", None) or 0),
                    allow_manual_price=bool(getattr(s, "allow_manual_price", True)),
                    unit_label=s.unit_label,
                    default_quantity=s.default_quantity,
                    price_per_unit=float(s.price_per_unit or 0),
                    notes_template=s.notes_template or '',
                    is_active=s.is_active,
                    inventory_usage=self._service_inventory_usage_payload(session, s.id),
                )
                for s in services
            ]

    # --- Herbal Methods ---
    def _normalize_unit(self, unit):
        return str(unit or "pcs").strip().lower() or "pcs"

    def _normalize_package_size(self, package_size):
        return max(1, int(package_size or 1))

    def _stock_label(self, quantity, unit, package_unit=None, package_size=1):
        quantity = int(quantity or 0)
        unit = self._normalize_unit(unit)
        package_unit = self._normalize_unit(package_unit) if package_unit else ""
        package_size = self._normalize_package_size(package_size)
        if not package_unit or package_unit == unit or package_size <= 1:
            return f"{quantity} {unit}"
        packages, remainder = divmod(quantity, package_size)
        if packages and remainder:
            return f"{packages} {package_unit} + {remainder} {unit}"
        if packages:
            return f"{packages} {package_unit}"
        return f"{remainder} {unit}"

    def _normalize_inventory_item_type(self, item_type):
        normalized = str(item_type or "consumable").strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"nonconsumable", "non_consumable", "asset", "reusable"}:
            return "non_consumable"
        return "consumable"

    def _normalize_service_pricing_type(self, pricing_type):
        normalized = str(pricing_type or "per_unit").strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"fixed", "fixed_price", "flat", "package", "paket"}:
            return "fixed"
        return "per_unit"

    def _normalize_service_category(self, service_category):
        normalized = str(service_category or "general").strip().lower()
        normalized = re.sub(r"[^a-z0-9_\-]+", "_", normalized).strip("_")
        return normalized or "general"

    def _add_inventory_transaction(self, session, inventory_id, change, transaction_type="adjustment", note=None, visit_id=None):
        if int(change or 0) == 0:
            return
        session.add(InventoryTransaction(
            inventory_id=inventory_id,
            change=int(change),
            transaction_type=transaction_type,
            note=note,
            visit_id=visit_id,
        ))

    @staticmethod
    def _format_rupiah(value):
        amount = int(round(float(value or 0)))
        return "Rp" + f"{amount:,}".replace(",", ".")

    def _validate_visit_herbal_items(self, session, herbal_items):
        if not herbal_items:
            return []
        merged = {}
        for raw in herbal_items:
            try:
                herbal_id = int(raw.get("herbal_id"))
                quantity = int(raw.get("quantity"))
            except (TypeError, ValueError, AttributeError):
                raise ValueError("Data pembelian herbal tidak valid.")
            if quantity <= 0:
                raise ValueError("Jumlah pembelian herbal harus lebih dari 0.")
            merged[herbal_id] = merged.get(herbal_id, 0) + quantity

        result = []
        for herbal_id, quantity in merged.items():
            herbal = session.get(Herbal, herbal_id)
            if not herbal or not herbal.is_active:
                raise ValueError("Herbal tidak ditemukan atau tidak aktif.")
            if int(herbal.stock or 0) < quantity:
                raise ValueError("Stok herbal tidak cukup. Silakan cek ulang pembelian herbal.")
            unit_price = float(herbal.price or 0)
            result.append({
                "herbal": herbal,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": unit_price * quantity,
            })
        return result

    def add_herbal_sale(self, items, buyer_name=None, patient_id=None,
                        payment_status='paid', payment_method='cash', amount_paid=None, paid_at=None,
                        payment_provider='manual'):
        with self.Session() as session:
            if not items:
                raise ValueError("Minimal pilih satu herbal untuk dijual.")
            patient = None
            if patient_id:
                patient = session.get(Patient, int(patient_id))
                if not patient:
                    raise ValueError("Pasien tidak ditemukan.")

            normalized_items = self._validate_visit_herbal_items(session, items)
            if not normalized_items:
                raise ValueError("Minimal pilih satu herbal untuk dijual.")

            buyer = str(buyer_name or "").strip()
            if patient:
                buyer = patient.name
            buyer_note = buyer or "Umum"
            note = f"Penjualan herbal tanpa kunjungan - Pembeli: {buyer_note}"
            sale_group_id = f"HS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

            saved_items = []
            total = 0
            for item in normalized_items:
                total += float(item["total_price"] or 0)

            payment_provider = str(payment_provider or "manual").strip().lower() or "manual"
            if payment_provider != "manual":
                from helpers.payment_gateway import get_available_gateway_providers
                if payment_provider not in get_available_gateway_providers():
                    raise ValueError("Provider pembayaran ini belum tersedia.")
            payment = normalize_visit_payment(
                total,
                payment_status=payment_status,
                payment_method=payment_method,
                amount_paid=amount_paid,
                paid_at=paid_at,
                payment_provider=payment_provider,
            )
            herbal_payment_allocations = allocate_payment_amounts(
                payment["amount_paid"],
                [item["total_price"] for item in normalized_items],
            )

            # Session already has an implicit transaction after validation queries.
            # Keep all stock checks and writes before a single commit so exceptions rollback atomically.
            for item in normalized_items:
                herbal = item["herbal"]
                quantity = item["quantity"]
                if not herbal.is_active:
                    raise ValueError("Herbal tidak ditemukan atau tidak aktif.")
                if int(herbal.stock or 0) < quantity:
                    raise ValueError("Stok herbal tidak cukup. Silakan cek ulang penjualan herbal.")
            for item, item_amount_paid in zip(normalized_items, herbal_payment_allocations):
                herbal = item["herbal"]
                quantity = item["quantity"]
                herbal.stock = int(herbal.stock or 0) - quantity
                self._add_herbal_transaction(
                    session,
                    herbal.id,
                    quantity,
                    item["total_price"],
                    "sale",
                    note,
                    visit_id=None,
                    sale_group_id=sale_group_id,
                    payment_status=payment["payment_status"],
                    payment_method=payment["payment_method"],
                    amount_paid=item_amount_paid,
                    paid_at=payment["paid_at"],
                    payment_provider=payment_provider,
                )
                saved_items.append({
                    "herbal_id": herbal.id,
                    "name": herbal.name,
                    "quantity": quantity,
                    "unit": herbal.unit,
                    "unit_price": item["unit_price"],
                    "total_price": item["total_price"],
                })
            session.commit()

            return {
                "buyer_name": buyer_note,
                "patient_id": patient.id if patient else None,
                "sale_group_id": sale_group_id,
                "total": round(float(total), 2),
                "items": saved_items,
            }

    def _add_herbal_transaction(
        self,
        session,
        herbal_id,
        quantity,
        total_price=0,
        transaction_type="adjustment",
        note=None,
        visit_id=None,
        sale_group_id=None,
        payment_status="paid",
        payment_method="cash",
        amount_paid=None,
        paid_at=None,
        payment_provider="manual",
    ):
        if int(quantity or 0) == 0:
            return
        session.add(HerbalTransaction(
            herbal_id=herbal_id,
            visit_id=visit_id,
            sale_group_id=sale_group_id,
            quantity=abs(int(quantity)),
            total_price=max(0, float(total_price or 0)),
            transaction_type=transaction_type,
            note=note,
            payment_status=payment_status,
            payment_method=payment_method,
            amount_paid=amount_paid,
            paid_at=paid_at,
            payment_provider=payment_provider,
        ))

    @staticmethod
    def _normalize_correction_reason(reason):
        text_value = str(reason or "").strip()
        if len(text_value) < 5:
            raise ValueError("Alasan wajib diisi minimal 5 karakter.")
        return text_value

    def _add_correction_log(
        self,
        session,
        action_type,
        reason,
        herbal_id=None,
        quantity_change=None,
        stock_before=None,
        stock_after=None,
        reference_type=None,
        reference_id=None,
        created_by=None,
    ):
        session.add(CorrectionLog(
            action_type=str(action_type or "").strip(),
            herbal_id=herbal_id,
            quantity_change=quantity_change,
            stock_before=stock_before,
            stock_after=stock_after,
            reference_type=reference_type,
            reference_id=str(reference_id) if reference_id is not None else None,
            reason=self._normalize_correction_reason(reason),
            created_by=created_by,
        ))

    def get_correction_logs(self, limit=100, action_type=None):
        with self.Session() as session:
            query = session.query(CorrectionLog).options(joinedload(CorrectionLog.herbal))
            action = str(action_type or "").strip()
            if action:
                query = query.filter(CorrectionLog.action_type == action)
            rows = query.order_by(CorrectionLog.created_at.desc()).limit(min(250, max(10, int(limit or 100)))).all()
            return [
                {
                    "id": row.id,
                    "action_type": row.action_type,
                    "herbal_id": row.herbal_id,
                    "herbal_name": row.herbal.name if row.herbal else None,
                    "quantity_change": row.quantity_change,
                    "stock_before": row.stock_before,
                    "stock_after": row.stock_after,
                    "reference_type": row.reference_type,
                    "reference_id": row.reference_id,
                    "reason": row.reason,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "created_by": row.created_by,
                }
                for row in rows
            ]

    def get_all_herbals(self, active_only=True):
        with self.Session() as session:
            query = session.query(Herbal)
            if active_only:
                query = query.filter(Herbal.is_active == True)
            items = query.all()
            return [
                {
                    "id": item.id,
                    "name": item.name,
                    "stock": item.stock,
                    "stock_display": self._stock_label(item.stock, item.unit, item.package_unit, item.package_size),
                    "cost_price": float(item.cost_price or 0),
                    "price": float(item.price),
                    "unit": item.unit,
                    "package_unit": item.package_unit or "",
                    "package_size": int(item.package_size or 1),
                    "min_stock": int(item.min_stock or 5),
                    "margin": float(item.price or 0) - float(item.cost_price or 0),
                } for item in items
            ]

    def add_herbal(self, name, unit, price, stock=0, cost_price=0, package_unit=None, package_size=1, min_stock=5):
        with self.Session() as session:
            normalized_name = str(name or "").strip()
            normalized_unit = self._normalize_unit(unit)
            normalized_package_unit = self._normalize_unit(package_unit) if package_unit else None
            normalized_package_size = self._normalize_package_size(package_size)
            initial_stock = int(stock or 0)
            if not normalized_name:
                raise ValueError("Nama herbal wajib diisi")
            if float(price or 0) < 0:
                raise ValueError("Harga herbal tidak boleh negatif")
            if float(cost_price or 0) < 0:
                raise ValueError("Harga modal herbal tidak boleh negatif")
            if initial_stock < 0:
                raise ValueError("Stok herbal tidak boleh negatif")
            existing = session.query(Herbal).filter(Herbal.name == normalized_name).first()
            if existing:
                if existing.is_active:
                    raise ValueError("Nama herbal sudah terdaftar")
                old_stock = int(existing.stock or 0)
                existing.unit = normalized_unit
                existing.package_unit = normalized_package_unit
                existing.package_size = normalized_package_size
                existing.cost_price = float(cost_price or 0)
                existing.price = float(price or 0)
                existing.stock = initial_stock
                existing.min_stock = int(min_stock or 5)
                existing.is_active = True
                diff = initial_stock - old_stock
                self._add_herbal_transaction(session, existing.id, abs(diff), 0, "adjustment", "Reaktivasi herbal nonaktif")
                session.commit()
                return existing.id
            item = Herbal(
                name=normalized_name,
                unit=normalized_unit,
                package_unit=normalized_package_unit,
                package_size=normalized_package_size,
                cost_price=float(cost_price or 0),
                price=float(price or 0),
                stock=initial_stock,
                min_stock=int(min_stock or 5),
            )
            session.add(item)
            session.flush()
            if initial_stock > 0:
                self._add_herbal_transaction(session, item.id, initial_stock, 0, "stock_in", "Stok awal herbal")
            session.commit()
            return item.id

    def update_herbal(self, herbal_id, name, unit, price, stock, cost_price=0, package_unit=None, package_size=1, min_stock=5, correction_reason=None):
        with self.Session() as session:
            normalized_name = str(name or "").strip()
            normalized_unit = self._normalize_unit(unit)
            normalized_package_unit = self._normalize_unit(package_unit) if package_unit else None
            normalized_package_size = self._normalize_package_size(package_size)
            new_stock = int(stock or 0)
            if not normalized_name:
                raise ValueError("Nama herbal wajib diisi")
            if float(price or 0) < 0:
                raise ValueError("Harga herbal tidak boleh negatif")
            if float(cost_price or 0) < 0:
                raise ValueError("Harga modal herbal tidak boleh negatif")
            if new_stock < 0:
                raise ValueError("Stok herbal tidak boleh negatif")
            duplicate = session.query(Herbal).filter(Herbal.name == normalized_name, Herbal.id != herbal_id).first()
            if duplicate:
                raise ValueError("Nama herbal sudah terdaftar")
            item = session.get(Herbal, herbal_id)
            if item:
                old_stock = int(item.stock or 0)
                item.name = normalized_name
                item.unit = normalized_unit
                item.package_unit = normalized_package_unit
                item.package_size = normalized_package_size
                item.cost_price = float(cost_price or 0)
                item.price = float(price or 0)
                item.stock = new_stock
                item.min_stock = int(min_stock or 5)
                diff = new_stock - old_stock
                self._add_herbal_transaction(session, item.id, abs(diff), 0, "adjustment", "Koreksi stok herbal manual")
                if diff:
                    self._add_correction_log(
                        session,
                        "stock_correction",
                        correction_reason or "Koreksi stok herbal manual",
                        herbal_id=item.id,
                        quantity_change=diff,
                        stock_before=old_stock,
                        stock_after=new_stock,
                        reference_type="herbal",
                        reference_id=item.id,
                    )
                session.commit()
                return True
            return False

    def delete_herbal(self, herbal_id):
        with self.Session() as session:
            item = session.get(Herbal, herbal_id)
            if item:
                item.is_active = False
                session.commit()
                return True
            return False

    def update_herbal_stock(self, herbal_id, change, transaction_type=None, note=None, correction_reason=None):
        with self.Session() as session:
            item = session.get(Herbal, herbal_id)
            if item:
                change = int(change or 0)
                old_stock = int(item.stock or 0)
                new_stock = old_stock + change
                if new_stock < 0:
                    raise ValueError(f"Stok {item.name} tidak cukup. Tersedia {item.stock}, perlu {abs(change)}.")
                item.stock = new_stock
                if change:
                    tx_type = transaction_type or ("stock_in" if change > 0 else "sale")
                    total_price = float(item.price or 0) * abs(change) if tx_type == "sale" else 0
                    self._add_herbal_transaction(
                        session,
                        herbal_id,
                        abs(change),
                        total_price,
                        tx_type,
                        note or ("Herbal masuk" if change > 0 else "Penjualan herbal"),
                    )
                    self._add_correction_log(
                        session,
                        "stock_correction",
                        correction_reason or note or ("Herbal masuk" if change > 0 else "Herbal keluar"),
                        herbal_id=herbal_id,
                        quantity_change=change,
                        stock_before=old_stock,
                        stock_after=new_stock,
                        reference_type="herbal",
                        reference_id=herbal_id,
                    )

                session.commit()
                return True
            return False

    def return_herbal_sale(self, transaction_id, quantity, reason):
        with self.Session() as session:
            reason = self._normalize_correction_reason(reason)
            quantity = int(quantity or 0)
            if quantity <= 0:
                raise ValueError("Jumlah retur harus lebih dari 0.")
            tx = (
                session.query(HerbalTransaction)
                .options(joinedload(HerbalTransaction.herbal))
                .filter(
                    HerbalTransaction.id == int(transaction_id),
                    HerbalTransaction.transaction_type == "sale",
                )
                .first()
            )
            if not tx or not tx.herbal:
                raise ValueError("Transaksi penjualan herbal tidak ditemukan.")
            returned_qty = (
                session.query(func.coalesce(func.sum(CorrectionLog.quantity_change), 0))
                .filter(
                    CorrectionLog.action_type == "return",
                    CorrectionLog.reference_type == "herbal_transaction",
                    CorrectionLog.reference_id == str(tx.id),
                )
                .scalar()
                or 0
            )
            sold_qty = int(tx.quantity or 0)
            if int(returned_qty or 0) + quantity > sold_qty:
                remaining = max(0, sold_qty - int(returned_qty or 0))
                raise ValueError(f"Jumlah retur melebihi sisa transaksi. Sisa bisa diretur: {remaining}.")

            herbal = tx.herbal
            stock_before = int(herbal.stock or 0)
            stock_after = stock_before + quantity
            unit_price = float(tx.total_price or 0) / sold_qty if sold_qty else 0
            herbal.stock = stock_after
            self._add_herbal_transaction(
                session,
                herbal.id,
                quantity,
                unit_price * quantity,
                "return",
                f"Retur penjualan #{tx.id}: {reason}",
                visit_id=tx.visit_id,
                sale_group_id=tx.sale_group_id,
            )
            self._add_correction_log(
                session,
                "return",
                reason,
                herbal_id=herbal.id,
                quantity_change=quantity,
                stock_before=stock_before,
                stock_after=stock_after,
                reference_type="herbal_transaction",
                reference_id=tx.id,
            )
            session.commit()
            return {
                "transaction_id": tx.id,
                "herbal_id": herbal.id,
                "herbal_name": herbal.name,
                "quantity": quantity,
                "stock_before": stock_before,
                "stock_after": stock_after,
            }

    def get_all_inventory(self, active_only=True):
        with self.Session() as session:
            query = session.query(Inventory)
            if active_only:
                query = query.filter(Inventory.is_active == True)
            items = query.all()
            return [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "item_type": getattr(item, "item_type", None) or "consumable",
                    "quantity": item.quantity,
                    "stock_display": self._stock_label(item.quantity, item.unit, item.package_unit, item.package_size),
                    "unit": item.unit,
                    "package_unit": item.package_unit or "",
                    "package_size": int(item.package_size or 1),
                    "min_stock": item.min_stock,
                    "last_updated": item.last_updated
                } for item in items
            ]

    def update_stock(self, item_id, quantity_change, transaction_type=None, note=None):
        with self.Session() as session:
            item = session.get(Inventory, item_id)
            if item:
                quantity_change = int(quantity_change or 0)
                new_quantity = item.quantity + quantity_change
                if new_quantity < 0:
                    raise ValueError(f"Stok {item.item_name} tidak cukup. Tersedia {item.quantity}, perlu {abs(quantity_change)}.")
                item.quantity = new_quantity
                tx_type = transaction_type or ("stock_in" if quantity_change > 0 else "stock_out")
                self._add_inventory_transaction(
                    session,
                    item_id,
                    quantity_change,
                    tx_type,
                    note or ("Stok inventory masuk" if quantity_change > 0 else "Stok inventory keluar"),
                )
                session.commit()
                return True
            return False

    def add_inventory_item(self, name, unit, min_stock, initial_qty=0, package_unit=None, package_size=1, item_type="consumable"):
        with self.Session() as session:
            normalized_name = str(name or "").strip()
            normalized_item_type = self._normalize_inventory_item_type(item_type)
            normalized_unit = self._normalize_unit(unit)
            normalized_package_unit = self._normalize_unit(package_unit) if package_unit else None
            normalized_package_size = self._normalize_package_size(package_size)
            initial_qty = int(initial_qty or 0)
            if not normalized_name:
                raise ValueError("Nama inventory wajib diisi")
            if initial_qty < 0:
                raise ValueError("Stok awal tidak boleh negatif")
            if int(min_stock or 0) < 0:
                raise ValueError("Stok minimum tidak boleh negatif")
            item = session.query(Inventory).filter(Inventory.item_name == normalized_name).first()
            if item:
                if item.is_active:
                    raise ValueError("Nama inventory sudah terdaftar")
                old_quantity = int(item.quantity or 0)
                item.item_type = normalized_item_type
                item.unit = normalized_unit
                item.package_unit = normalized_package_unit
                item.package_size = normalized_package_size
                item.min_stock = int(min_stock or 0)
                item.quantity = initial_qty
                item.is_active = True
                diff = initial_qty - old_quantity
                self._add_inventory_transaction(session, item.id, diff, "adjustment", "Reaktivasi inventory nonaktif")
                session.commit()
                return item.id
            item = Inventory(
                item_name=normalized_name,
                item_type=normalized_item_type,
                unit=normalized_unit,
                package_unit=normalized_package_unit,
                package_size=normalized_package_size,
                min_stock=int(min_stock or 0),
                quantity=initial_qty,
            )
            session.add(item)
            session.flush()
            if initial_qty > 0:
                self._add_inventory_transaction(session, item.id, initial_qty, "stock_in", "Stok awal inventory")
            session.commit()
            return item.id

    def update_inventory_item(self, item_id, name, quantity, unit, min_stock, package_unit=None, package_size=1, item_type="consumable"):
        with self.Session() as session:
            normalized_name = str(name or "").strip()
            normalized_item_type = self._normalize_inventory_item_type(item_type)
            normalized_unit = self._normalize_unit(unit)
            normalized_package_unit = self._normalize_unit(package_unit) if package_unit else None
            normalized_package_size = self._normalize_package_size(package_size)
            new_quantity = int(quantity or 0)
            if not normalized_name:
                raise ValueError("Nama inventory wajib diisi")
            if new_quantity < 0:
                raise ValueError("Stok inventory tidak boleh negatif")
            if int(min_stock or 0) < 0:
                raise ValueError("Stok minimum tidak boleh negatif")
            duplicate = session.query(Inventory).filter(Inventory.item_name == normalized_name, Inventory.id != item_id).first()
            if duplicate:
                raise ValueError("Nama inventory sudah terdaftar")
            item = session.get(Inventory, item_id)
            if item:
                old_quantity = int(item.quantity or 0)
                item.item_name = normalized_name
                item.item_type = normalized_item_type
                item.quantity = new_quantity
                item.unit = normalized_unit
                item.package_unit = normalized_package_unit
                item.package_size = normalized_package_size
                item.min_stock = int(min_stock or 0)
                diff = new_quantity - old_quantity
                self._add_inventory_transaction(session, item.id, diff, "adjustment", "Koreksi stok inventory manual")
                session.commit()
                return True
            return False

    def delete_inventory_item(self, item_id):
        with self.Session() as session:
            item = session.get(Inventory, item_id)
            if item:
                item.is_active = False
                session.commit()
                return True
            return False

    # ── Invoice helpers ────────────────────────────────────────────────────────

    def get_visit_for_invoice(self, visit_id):
        """Return (VisitData, patient_name, therapist_name) tuple for invoice generation."""
        from sqlalchemy.orm import joinedload
        with self.Session() as session:
            visit = (
                session.query(Visit)
                .options(joinedload(Visit.patient), joinedload(Visit.therapist))
                .filter(Visit.id == visit_id)
                .first()
            )
            if not visit:
                return None, None, None
            # Baca semua data SEBELUM session ditutup untuk hindari DetachedInstanceError
            visit_data     = VisitData(
                id=visit.id,
                date=visit.date,
                price=float(visit.price or 0),
                original_price=float(getattr(visit, "original_price", None) or visit.price or 0),
                discount_amount=float(getattr(visit, "discount_amount", None) or 0),
                final_price=float(getattr(visit, "final_price", None) or visit.price or 0),
                discount_applied=visit.discount_applied,
                point_count=visit.point_count,
                quantity=visit.point_count,
                therapist_id=visit.therapist_id,
                service_id=visit.service_id if hasattr(visit, 'service_id') else None,
                service_name=(visit.service_name if hasattr(visit, 'service_name') else None) or "Bekam",
                invoice_path=visit.invoice_path,
                medical_notes=visit.medical_notes,
                is_free_visit=visit.is_free_visit if hasattr(visit, 'is_free_visit') else False,
                free_visit_reason=visit.free_visit_reason if hasattr(visit, 'free_visit_reason') else None,
                discount_rule_id=visit.discount_rule_id if hasattr(visit, 'discount_rule_id') else None,
                discount_rule_name=visit.discount_rule_name if hasattr(visit, 'discount_rule_name') else None,
                invoice_status=visit.invoice_status if hasattr(visit, 'invoice_status') else "active",
                void_reason=visit.void_reason if hasattr(visit, 'void_reason') else None,
                voided_at=visit.voided_at if hasattr(visit, 'voided_at') else None,
                payment_status=getattr(visit, "payment_status", None) or "paid",
                payment_method=getattr(visit, "payment_method", None) or "cash",
                amount_paid=getattr(visit, "amount_paid", None),
                paid_at=getattr(visit, "paid_at", None),
                payment_provider=getattr(visit, "payment_provider", None) or "manual",
                payment_reference=getattr(visit, "payment_reference", None) or "",
                payment_url=getattr(visit, "payment_url", None) or "",
                payment_channel=getattr(visit, "payment_channel", None) or "",
                payment_expired_at=getattr(visit, "payment_expired_at", None),
                payment_gateway_status=getattr(visit, "payment_gateway_status", None) or "",
            )
            patient_name   = visit.patient.name   if visit.patient   else "Pasien"
            therapist_name = visit.therapist.name if visit.therapist else "--"
            return visit_data, patient_name, therapist_name

    def get_herbal_transactions_for_visit(self, visit_id):
        with self.Session() as session:
            rows = (
                session.query(HerbalTransaction)
                .options(joinedload(HerbalTransaction.herbal))
                .filter(
                    HerbalTransaction.visit_id == visit_id,
                    HerbalTransaction.transaction_type == "sale",
                )
                .order_by(HerbalTransaction.id.asc())
                .all()
            )
            return [
                {
                    "id": row.id,
                    "herbal_id": row.herbal_id,
                    "name": row.herbal.name if row.herbal else "Herbal",
                    "quantity": int(row.quantity or 0),
                    "unit": row.herbal.unit if row.herbal else "",
                    "total_price": float(row.total_price or 0),
                    "unit_price": (float(row.total_price or 0) / int(row.quantity or 1)) if int(row.quantity or 0) else 0,
                }
                for row in rows
            ]

    def _herbal_invoice_payload_from_rows(self, rows):
        rows = list(rows or [])
        if not rows:
            return None
        first = rows[0]
        return {
            "id": first.id,
            "sale_group_id": first.sale_group_id,
            "date": first.date,
            "buyer_name": self._buyer_name_from_herbal_note(first.note),
            "note": first.note or "",
            "invoice_path": first.invoice_path if hasattr(first, "invoice_path") else None,
            "invoice_status": first.invoice_status if hasattr(first, "invoice_status") else "active",
            "void_reason": first.void_reason if hasattr(first, "void_reason") else None,
            "payment_status": getattr(first, "payment_status", None) or "paid",
            "payment_method": getattr(first, "payment_method", None) or "cash",
            "amount_paid": getattr(first, "amount_paid", None),
            "paid_at": getattr(first, "paid_at", None),
            "payment_provider": getattr(first, "payment_provider", None) or "manual",
            "payment_reference": getattr(first, "payment_reference", None) or "",
            "payment_url": getattr(first, "payment_url", None) or "",
            "payment_channel": getattr(first, "payment_channel", None) or "",
            "payment_expired_at": getattr(first, "payment_expired_at", None),
            "payment_gateway_status": getattr(first, "payment_gateway_status", None) or "",
            "items": [
                {
                    "id": row.id,
                    "herbal_id": row.herbal_id,
                    "name": row.herbal.name if row.herbal else "Herbal",
                    "quantity": int(row.quantity or 0),
                    "unit": row.herbal.unit if row.herbal else "",
                    "total_price": float(row.total_price or 0),
                    "unit_price": (float(row.total_price or 0) / int(row.quantity or 1)) if int(row.quantity or 0) else 0,
                }
                for row in rows
            ],
            "total": sum(float(row.total_price or 0) for row in rows),
        }

    def get_herbal_transaction_for_invoice(self, transaction_id):
        with self.Session() as session:
            row = (
                session.query(HerbalTransaction)
                .options(joinedload(HerbalTransaction.herbal))
                .filter(
                    HerbalTransaction.id == transaction_id,
                    HerbalTransaction.transaction_type == "sale",
                    HerbalTransaction.visit_id.is_(None),
                )
                .first()
            )
            if not row:
                return None
            if row.sale_group_id:
                grouped_rows = (
                    session.query(HerbalTransaction)
                    .options(joinedload(HerbalTransaction.herbal))
                    .filter(
                        HerbalTransaction.sale_group_id == row.sale_group_id,
                        HerbalTransaction.transaction_type == "sale",
                        HerbalTransaction.visit_id.is_(None),
                    )
                    .order_by(HerbalTransaction.id.asc())
                    .all()
                )
                return self._herbal_invoice_payload_from_rows(grouped_rows)
            return self._herbal_invoice_payload_from_rows([row])

    def get_herbal_sale_group_for_invoice(self, sale_group_id):
        with self.Session() as session:
            rows = (
                session.query(HerbalTransaction)
                .options(joinedload(HerbalTransaction.herbal))
                .filter(
                    HerbalTransaction.sale_group_id == sale_group_id,
                    HerbalTransaction.transaction_type == "sale",
                    HerbalTransaction.visit_id.is_(None),
                )
                .order_by(HerbalTransaction.id.asc())
                .all()
            )
            return self._herbal_invoice_payload_from_rows(rows)

    @staticmethod
    def _buyer_name_from_herbal_note(note):
        text = str(note or "")
        marker = "Pembeli:"
        if marker in text:
            return text.split(marker, 1)[1].strip() or "Umum"
        return "Umum"

    def update_herbal_invoice_path(self, transaction_id, invoice_path):
        with self.Session() as session:
            row = session.get(HerbalTransaction, transaction_id)
            if row:
                row.invoice_path = invoice_path
                row.pdf_generated_at = datetime.now()
                session.commit()
                return True
            return False

    def update_herbal_group_invoice_path(self, sale_group_id, invoice_path):
        with self.Session() as session:
            rows = (
                session.query(HerbalTransaction)
                .filter(
                    HerbalTransaction.sale_group_id == sale_group_id,
                    HerbalTransaction.transaction_type == "sale",
                    HerbalTransaction.visit_id.is_(None),
                )
                .all()
            )
            if not rows:
                return False
            now = datetime.now()
            for row in rows:
                row.invoice_path = invoice_path
                row.pdf_generated_at = now
            session.commit()
            return True

    def void_visit_invoice(self, visit_id, reason):
        with self.Session() as session:
            reason = self._normalize_correction_reason(reason)
            visit = session.get(Visit, int(visit_id))
            if not visit:
                raise ValueError("Kunjungan tidak ditemukan.")
            if (visit.invoice_status or "active") == "void":
                raise ValueError("Invoice kunjungan sudah dibatalkan.")
            visit.invoice_status = "void"
            visit.void_reason = reason
            visit.voided_at = datetime.now()
            visit.payment_status = "void"
            self._add_correction_log(
                session,
                "void_invoice",
                reason,
                reference_type="visit_invoice",
                reference_id=visit.id,
            )
            self._add_audit_log_row(session, "invoice_voided", "invoice", visit.id, "Invoice dibatalkan.", {
                "invoice_type": "visit",
                "reason": reason,
            })
            session.commit()
            return True

    def void_herbal_invoice(self, transaction_id=None, sale_group_id=None, reason=""):
        with self.Session() as session:
            reason = self._normalize_correction_reason(reason)
            group = str(sale_group_id or "").strip()
            if group:
                rows = (
                    session.query(HerbalTransaction)
                    .filter(
                        HerbalTransaction.sale_group_id == group,
                        HerbalTransaction.transaction_type == "sale",
                        HerbalTransaction.visit_id.is_(None),
                    )
                    .all()
                )
                reference_id = group
            else:
                row = session.get(HerbalTransaction, int(transaction_id or 0))
                rows = [row] if row and row.transaction_type == "sale" and row.visit_id is None else []
                reference_id = transaction_id
            if not rows:
                raise ValueError("Invoice herbal tidak ditemukan.")
            if all((row.invoice_status or "active") == "void" for row in rows):
                raise ValueError("Invoice herbal sudah dibatalkan.")
            now = datetime.now()
            for row in rows:
                row.invoice_status = "void"
                row.void_reason = reason
                row.voided_at = now
                row.payment_status = "void"
            self._add_correction_log(
                session,
                "void_invoice",
                reason,
                reference_type="herbal_invoice_group" if group else "herbal_invoice",
                reference_id=reference_id,
            )
            self._add_audit_log_row(session, "invoice_voided", "invoice", reference_id, "Invoice dibatalkan.", {
                "invoice_type": "herbal",
                "reason": reason,
            })
            session.commit()
            return True

    def update_invoice_manual_payment(
        self,
        invoice_type,
        visit_id=None,
        transaction_id=None,
        sale_group_id=None,
        payment_status="paid",
        payment_method="cash",
        amount_paid=None,
    ):
        normalized_type = str(invoice_type or "").strip().lower()
        normalized_status = str(payment_status or "").strip().lower()
        normalized_method = str(payment_method or "").strip().lower()
        if normalized_status not in {"paid", "partial"}:
            raise ValueError("Status pembayaran manual harus lunas atau sebagian.")
        if normalized_method not in {"cash", "qris", "transfer", "ewallet"}:
            raise ValueError("Metode pembayaran manual tidak valid.")

        with self.Session() as session:
            if normalized_type == "visit":
                visit = session.get(Visit, int(visit_id or 0))
                if not visit:
                    raise ValueError("Kunjungan tidak ditemukan.")
                if (visit.invoice_status or "active") == "void":
                    raise ValueError("Invoice void tidak boleh ditandai lunas/DP.")
                linked_herbals = (
                    session.query(HerbalTransaction)
                    .filter(
                        HerbalTransaction.visit_id == visit.id,
                        HerbalTransaction.transaction_type == "sale",
                    )
                    .order_by(HerbalTransaction.id.asc())
                    .all()
                )
                visit_total = float(getattr(visit, "final_price", None) or visit.price or 0)
                total_amount = visit_total + sum(float(row.total_price or 0) for row in linked_herbals)
                payment = normalize_visit_payment(
                    total_amount,
                    payment_status=normalized_status,
                    payment_method=normalized_method,
                    amount_paid=amount_paid,
                    paid_at=datetime.now().isoformat(),
                    payment_provider="gateway_mock",
                )
                allocations = allocate_payment_amounts(
                    payment["amount_paid"],
                    [visit_total] + [row.total_price for row in linked_herbals],
                )
                visit.payment_status = payment["payment_status"]
                visit.payment_method = payment["payment_method"]
                visit.amount_paid = allocations[0] if allocations else 0
                visit.paid_at = payment["paid_at"]
                visit.payment_updated_at = datetime.now()
                visit.payment_provider = "gateway_mock"
                visit.payment_reference = ""
                visit.payment_url = ""
                visit.payment_channel = normalized_method
                visit.payment_expired_at = None
                visit.payment_gateway_status = ""
                for row, paid_amount in zip(linked_herbals, allocations[1:]):
                    row.payment_status = payment["payment_status"]
                    row.payment_method = payment["payment_method"]
                    row.amount_paid = paid_amount
                    row.paid_at = payment["paid_at"]
                    row.payment_updated_at = datetime.now()
                    row.payment_provider = "gateway_mock"
                    row.payment_reference = ""
                    row.payment_url = ""
                    row.payment_channel = normalized_method
                    row.payment_expired_at = None
                    row.payment_gateway_status = ""
                self._add_audit_log_row(
                    session,
                    "manual_payment_updated",
                    "invoice",
                    visit.id,
                    "Status pembayaran invoice diperbarui manual.",
                    {
                        "invoice_type": "visit",
                        "payment_status": payment.get("payment_status"),
                        "payment_method": payment.get("payment_method"),
                        "amount_paid": payment.get("amount_paid"),
                        "payment_provider": "gateway_mock",
                    },
                )
                session.commit()
                return {
                    "invoice_type": "visit",
                    "entity_id": visit.id,
                    "total_amount": total_amount,
                    **payment,
                    "payment_provider": "gateway_mock",
                }

            if normalized_type == "herbal":
                group = str(sale_group_id or "").strip()
                if group:
                    rows = (
                        session.query(HerbalTransaction)
                        .filter(
                            HerbalTransaction.sale_group_id == group,
                            HerbalTransaction.transaction_type == "sale",
                            HerbalTransaction.visit_id.is_(None),
                        )
                        .order_by(HerbalTransaction.id.asc())
                        .all()
                    )
                    reference_id = group
                else:
                    row = session.get(HerbalTransaction, int(transaction_id or 0))
                    rows = [row] if row and row.transaction_type == "sale" and row.visit_id is None else []
                    reference_id = transaction_id
                if not rows:
                    raise ValueError("Invoice herbal tidak ditemukan.")
                if any((row.invoice_status or "active") == "void" for row in rows):
                    raise ValueError("Invoice void tidak boleh ditandai lunas/DP.")
                total_amount = sum(float(row.total_price or 0) for row in rows)
                payment = normalize_visit_payment(
                    total_amount,
                    payment_status=normalized_status,
                    payment_method=normalized_method,
                    amount_paid=amount_paid,
                    paid_at=datetime.now().isoformat(),
                    payment_provider="gateway_mock",
                )
                allocations = allocate_payment_amounts(payment["amount_paid"], [row.total_price for row in rows])
                now = datetime.now()
                for row, paid_amount in zip(rows, allocations):
                    row.payment_status = payment["payment_status"]
                    row.payment_method = payment["payment_method"]
                    row.amount_paid = paid_amount
                    row.paid_at = payment["paid_at"]
                    row.payment_updated_at = now
                    row.payment_provider = "gateway_mock"
                    row.payment_reference = ""
                    row.payment_url = ""
                    row.payment_channel = normalized_method
                    row.payment_expired_at = None
                    row.payment_gateway_status = ""
                self._add_audit_log_row(
                    session,
                    "manual_payment_updated",
                    "invoice",
                    reference_id,
                    "Status pembayaran invoice diperbarui manual.",
                    {
                        "invoice_type": "herbal",
                        "payment_status": payment.get("payment_status"),
                        "payment_method": payment.get("payment_method"),
                        "amount_paid": payment.get("amount_paid"),
                        "payment_provider": "gateway_mock",
                    },
                )
                session.commit()
                return {
                    "invoice_type": "herbal",
                    "entity_id": reference_id,
                    "total_amount": total_amount,
                    **payment,
                    "payment_provider": "gateway_mock",
                }

        raise ValueError("Tipe invoice tidak valid.")


    def update_visit_invoice_path(self, visit_id, invoice_path):
        """Store the generated invoice file path in the database."""
        with self.Session() as session:
            visit = session.get(Visit, visit_id)
            if visit:
                visit.invoice_path = invoice_path
                visit.pdf_generated_at = datetime.now()
                session.commit()
                return True
            return False
