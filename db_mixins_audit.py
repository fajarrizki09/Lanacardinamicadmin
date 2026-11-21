import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from sqlalchemy import desc
from db_models import AuditLog

class AuditMixin:
    def _get_audit_logger(self):
        # Match original implementation
        base_dir = os.path.dirname(os.path.abspath(self.db_path)) if hasattr(self, 'db_path') and self.db_path else os.getcwd()
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.abspath(os.path.join(log_dir, "audit_errors.log"))

        logger = logging.getLogger(f"lancar.audit.{id(self)}")
        logger.setLevel(logging.INFO)
        logger.propagate = True

        if not any(getattr(handler, "baseFilename", None) == log_path for handler in logger.handlers):
            handler = RotatingFileHandler(log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            logger.addHandler(handler)
        return logger

    def log_audit(self, action, entity_type, entity_id=None, description="", metadata=None, actor="admin", required=False):
        try:
            with self.Session() as session:
                row = self._add_audit_log_row(
                    session,
                    action,
                    entity_type,
                    entity_id=entity_id,
                    description=description,
                    metadata=metadata,
                    actor=actor,
                )
                session.commit()
                return row.id
        except Exception as exc:
            try:
                self._get_audit_logger().exception(
                    "Audit log failed: action=%s entity_type=%s entity_id=%s",
                    action,
                    entity_type,
                    entity_id,
                )
            except:
                pass
            if required:
                raise RuntimeError("Audit wajib gagal dicatat.") from exc
            return None

    def _add_audit_log_row(self, session, action, entity_type, entity_id=None, description="", metadata=None, actor="admin"):
        """Add an audit row to an existing transaction without committing it."""
        safe_metadata = metadata if isinstance(metadata, dict) else {}
        metadata_text = json.dumps(safe_metadata, ensure_ascii=False, default=str) if safe_metadata else None
        row = AuditLog(
            actor=str(actor or "admin")[:80],
            action=str(action or "").strip()[:80],
            entity_type=str(entity_type or "").strip()[:80],
            entity_id=str(entity_id)[:120] if entity_id is not None else None,
            description=str(description or "").strip()[:500],
            metadata_json=metadata_text,
        )
        session.add(row)
        return row

    def get_audit_logs(self, action="", entity_type="", date_from=None, date_to=None, limit=100):
        with self.Session() as session:
            query = session.query(AuditLog)
            if str(action or "").strip():
                query = query.filter(AuditLog.action == str(action).strip())
            if str(entity_type or "").strip():
                query = query.filter(AuditLog.entity_type == str(entity_type).strip())
            if date_from:
                query = query.filter(AuditLog.created_at >= date_from)
            if date_to:
                query = query.filter(AuditLog.created_at <= date_to)

            rows = query.order_by(AuditLog.created_at.desc()).limit(min(500, max(1, int(limit or 100)))).all()
            return [
                {
                    "id": row.id,
                    "created_at": row.created_at.isoformat(timespec="seconds") if row.created_at else None,
                    "actor": row.actor,
                    "action": row.action,
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "description": row.description or "",
                    "metadata": json.loads(row.metadata_json) if row.metadata_json else {},
                } for row in rows
            ]
