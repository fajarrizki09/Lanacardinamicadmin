from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Visit:
    id: Optional[int]
    date: datetime
    price: int
    discount_applied: bool
    therapist_id: Optional[int] = None

@dataclass
class Patient:
    id: int
    name: str
    phone: str
    address: str
    gender: str
    visits: List[Visit]

@dataclass
class Therapist:
    id: int
    name: str
    gender: str
    specialization: str
    is_active: bool = True
