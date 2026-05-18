from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Index, Text, func
)
from sqlalchemy.orm import declarative_base, relationship, synonym

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False, index=True, unique=True)
    address = Column(String, default='', nullable=False)
    gender = Column(String, default='Laki-laki', nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan", order_by="desc(Visit.date)")

class Therapist(Base):
    __tablename__ = 'therapists'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=False)
    specialization = Column(String, default='', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    can_handle_any_gender = Column(Boolean, default=False, nullable=False)
    visits = relationship("Visit", back_populates="therapist")

class Visit(Base):
    __tablename__ = 'visits'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    service_name = Column(String, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    final_price = Column(Numeric(10, 2), default=0, nullable=False)
    discount_applied = Column(Boolean, default=False, nullable=False)
    point_count = Column(Integer, default=0, nullable=False)
    quantity = synonym("point_count")
    invoice_path = Column(String, nullable=True)
    pdf_generated_at = Column(DateTime, nullable=True)
    payment_updated_at = Column(DateTime, nullable=True)
    medical_notes = Column(Text, nullable=True)
    is_free_visit = Column(Boolean, default=False, nullable=False)
    free_visit_reason = Column(String, nullable=True)
    discount_rule_id = Column(Integer, ForeignKey("discount_rules.id"), nullable=True)
    discount_rule_name = Column(String, nullable=True)
    invoice_status = Column(String, default='active', nullable=False, index=True)
    void_reason = Column(Text, nullable=True)
    voided_at = Column(DateTime, nullable=True)
    payment_status = Column(String, default='paid', nullable=False, index=True)
    payment_method = Column(String, default='cash', nullable=False)
    amount_paid = Column(Integer, nullable=True)
    paid_at = Column(String, nullable=True)
    payment_provider = Column(String, default='manual', nullable=False)
    payment_reference = Column(String, default='', nullable=False, index=True)
    payment_url = Column(Text, default='', nullable=False)
    payment_channel = Column(String, default='', nullable=False)
    payment_expired_at = Column(String, nullable=True)
    payment_gateway_status = Column(String, default='', nullable=False)
    patient = relationship("Patient", back_populates="visits")
    therapist = relationship("Therapist", back_populates="visits")
    service = relationship("Service")
    __table_args__ = (Index('idx_patient_date', 'patient_id', 'date'),)

class Inventory(Base):
    __tablename__ = 'inventory'
    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False, unique=True)
    item_type = Column(String, default='consumable', nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    unit = Column(String, nullable=False)
    package_unit = Column(String, nullable=True)
    package_size = Column(Integer, default=1, nullable=False)
    min_stock = Column(Integer, default=10, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

class InventoryTransaction(Base):
    __tablename__ = 'inventory_transactions'
    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=False, index=True)
    date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    change = Column(Integer, nullable=False)
    transaction_type = Column(String, default='adjustment', nullable=False, index=True)
    note = Column(Text, nullable=True)
    visit_id = Column(Integer, ForeignKey('visits.id'), nullable=True, index=True)
    inventory = relationship("Inventory")
    visit = relationship("Visit")

class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    pricing_type = Column(String, default='per_unit', nullable=False, index=True)
    service_category = Column(String, default='general', nullable=False, index=True)
    fixed_price = Column(Numeric(10, 2), default=0, nullable=False)
    allow_manual_price = Column(Boolean, default=True, nullable=False)
    unit_label = Column(String, default='sesi', nullable=False)
    default_quantity = Column(Integer, default=1, nullable=False)
    price_per_unit = Column(Numeric(10, 2), default=0, nullable=False)
    notes_template = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

class ServiceInventoryUsage(Base):
    __tablename__ = 'service_inventory_usage'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False, index=True)
    inventory_id = Column(Integer, ForeignKey('inventory.id'), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    service = relationship("Service")
    inventory = relationship("Inventory")

class Herbal(Base):
    __tablename__ = 'herbals'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    stock = Column(Integer, default=0, nullable=False)
    cost_price = Column(Numeric(10, 2), default=0, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    unit = Column(String, nullable=False)
    package_unit = Column(String, nullable=True)
    package_size = Column(Integer, default=1, nullable=False)
    min_stock = Column(Integer, default=5, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

class HerbalTransaction(Base):
    __tablename__ = 'herbal_transactions'
    id = Column(Integer, primary_key=True)
    herbal_id = Column(Integer, ForeignKey('herbals.id'), nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey('visits.id'), nullable=True, index=True)
    sale_group_id = Column(String, nullable=True, index=True)
    date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String, default='sale', nullable=False, index=True)
    invoice_path = Column(String, nullable=True)
    pdf_generated_at = Column(DateTime, nullable=True)
    payment_updated_at = Column(DateTime, nullable=True)
    invoice_status = Column(String, default='active', nullable=False, index=True)
    void_reason = Column(Text, nullable=True)
    voided_at = Column(DateTime, nullable=True)
    payment_status = Column(String, default='paid', nullable=False, index=True)
    payment_method = Column(String, default='cash', nullable=False)
    amount_paid = Column(Integer, nullable=True)
    paid_at = Column(String, nullable=True)
    payment_provider = Column(String, default='manual', nullable=False)
    payment_reference = Column(String, default='', nullable=False, index=True)
    payment_url = Column(Text, default='', nullable=False)
    payment_channel = Column(String, default='', nullable=False)
    payment_expired_at = Column(String, nullable=True)
    payment_gateway_status = Column(String, default='', nullable=False)
    note = Column(Text, nullable=True)
    herbal = relationship("Herbal")
    visit = relationship("Visit")

class CorrectionLog(Base):
    __tablename__ = 'correction_logs'
    id = Column(Integer, primary_key=True)
    action_type = Column(String, nullable=False, index=True)
    herbal_id = Column(Integer, ForeignKey('herbals.id'), nullable=True, index=True)
    quantity_change = Column(Integer, nullable=True)
    stock_before = Column(Integer, nullable=True)
    stock_after = Column(Integer, nullable=True)
    reference_type = Column(String, nullable=True, index=True)
    reference_id = Column(String, nullable=True, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    created_by = Column(String, nullable=True)
    herbal = relationship("Herbal")

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    actor = Column(String, default='admin', nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

class DiscountRule(Base):
    __tablename__ = 'discount_rules'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, index=True)
    discount_type = Column(String, nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    condition_value = Column(Numeric(10, 2), nullable=True)
    voucher_code = Column(String, nullable=True, index=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=100, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    usage_limit = Column(Integer, nullable=True)
    per_patient_limit = Column(Integer, nullable=True)

class VoucherUsage(Base):
    __tablename__ = 'voucher_usages'
    id = Column(Integer, primary_key=True)
    discount_rule_id = Column(Integer, ForeignKey("discount_rules.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=True, index=True)
    voucher_code = Column(String, nullable=False, index=True)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    used_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    discount_rule = relationship("DiscountRule")
    patient = relationship("Patient")
    visit = relationship("Visit")
    __table_args__ = (Index('idx_voucher_usage_visit_unique', 'visit_id', unique=True),)

class VoucherPatientTarget(Base):
    __tablename__ = 'voucher_patient_targets'
    id = Column(Integer, primary_key=True)
    discount_rule_id = Column(Integer, ForeignKey("discount_rules.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    discount_rule = relationship("DiscountRule")
    patient = relationship("Patient")
    __table_args__ = (Index('idx_voucher_patient_target_unique', 'discount_rule_id', 'patient_id', unique=True),)

class PatientFollowup(Base):
    __tablename__ = 'patient_followups'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    status = Column(String, default='pending', nullable=False, index=True)
    outcome = Column(String, nullable=True, index=True)
    note = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True, index=True)
    last_contacted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    patient = relationship("Patient")

class PatientManualTag(Base):
    __tablename__ = 'patient_manual_tags'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    value = Column(String, nullable=False, index=True)
    label = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    patient = relationship("Patient")
    __table_args__ = (Index('idx_patient_manual_tag_unique', 'patient_id', 'value', unique=True),)

class PatientContactPreference(Base):
    __tablename__ = 'patient_contact_preferences'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, unique=True, index=True)
    boleh_reminder_kontrol = Column(Boolean, default=True, nullable=False)
    boleh_promo = Column(Boolean, default=True, nullable=False)
    jangan_dihubungi = Column(Boolean, default=False, nullable=False)
    catatan_kontak = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    patient = relationship("Patient")

class CRMWhatsAppLog(Base):
    __tablename__ = 'crm_whatsapp_logs'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    phone = Column(String, nullable=False)
    message_type = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    whatsapp_url = Column(Text, nullable=False)
    status = Column(String, default='drafted', nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    patient = relationship("Patient")
