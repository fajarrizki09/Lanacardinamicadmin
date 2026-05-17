from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class VisitData:
    id: Optional[int]
    date: datetime
    price: float
    discount_applied: bool
    point_count: int = 0
    therapist_id: Optional[int] = None
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    invoice_path: Optional[str] = None
    medical_notes: Optional[str] = None
    is_free_visit: bool = False
    free_visit_reason: Optional[str] = None
    discount_rule_id: Optional[int] = None
    discount_rule_name: Optional[str] = None
    invoice_status: str = "active"
    void_reason: Optional[str] = None
    voided_at: Optional[datetime] = None
    payment_status: str = "paid"
    payment_method: str = "cash"
    amount_paid: Optional[int] = None
    paid_at: Optional[str] = None
    payment_provider: str = "manual"
    payment_reference: str = ""
    payment_url: str = ""
    payment_channel: str = ""
    payment_expired_at: Optional[str] = None
    payment_gateway_status: str = ""

@dataclass
class DiscountRuleData:
    id: Optional[int]
    name: str
    type: str
    discount_type: str
    discount_value: float
    condition_value: Optional[float] = None
    voucher_code: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    priority: int = 100
    created_at: Optional[datetime] = None
    usage_limit: Optional[int] = None
    per_patient_limit: Optional[int] = None
    usage_count: int = 0
    target_patient_ids: list = field(default_factory=list)
    target_patient_names: list = field(default_factory=list)

@dataclass
class PatientData:
    id: int
    name: str
    phone: str
    address: str
    gender: str
    visits: List[VisitData]

@dataclass
class TherapistData:
    id: int
    name: str
    gender: str
    specialization: str
    is_active: bool
    can_handle_any_gender: bool = False

@dataclass
class ServiceData:
    id: int
    name: str
    unit_label: str
    default_quantity: int
    price_per_unit: float
    notes_template: str
    is_active: bool
    inventory_usage: list = field(default_factory=list)
