from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Index, event, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload

Base = declarative_base()


class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False, index=True, unique=True)
    address = Column(String, default='', nullable=False)
    gender = Column(String, default='Laki-laki', nullable=False)

    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.name}', phone='{self.phone}', gender='{self.gender}')>"


class Therapist(Base):
    __tablename__ = 'therapists'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=False)
    specialization = Column(String, default='', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    visits = relationship("Visit", back_populates="therapist")

    def __repr__(self):
        return f"<Therapist(id={self.id}, name='{self.name}', gender='{self.gender}')>"


class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    discount_applied = Column(Boolean, default=False, nullable=False)
    point_count = Column(Integer, default=0, nullable=False)
    invoice_path = Column(String, nullable=True)
    medical_notes = Column(Text, nullable=True)  # Catatan perkembangan medis

    patient = relationship("Patient", back_populates="visits")
    therapist = relationship("Therapist", back_populates="visits")

    __table_args__ = (
        Index('idx_patient_date', 'patient_id', 'date'),
    )

    def __repr__(self):
        return f"<Visit(id={self.id}, date={self.date}, price={self.price}, points={self.point_count})>"


class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False, unique=True)
    quantity = Column(Integer, default=0, nullable=False)
    unit = Column(String, nullable=False)  # pcs, box, liter, dll
    min_stock = Column(Integer, default=10, nullable=False)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Inventory(item='{self.item_name}', qty={self.quantity} {self.unit})>"


@dataclass
class VisitData:
    id: Optional[int]
    date: datetime
    price: float
    discount_applied: bool
    point_count: int = 0
    therapist_id: Optional[int] = None
    invoice_path: Optional[str] = None
    medical_notes: Optional[str] = None


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


class Database:
    def __init__(self, db_url="sqlite:///data.db"):
        self.engine = create_engine(
            db_url, 
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )
        
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

    def _migrate_existing_data(self):
        with self.Session() as session:
            # Migration for point_count
            try:
                session.execute("SELECT point_count FROM visits LIMIT 1")
            except Exception:
                try:
                    session.execute("ALTER TABLE visits ADD COLUMN point_count INTEGER DEFAULT 0 NOT NULL")
                    session.commit()
                except Exception:
                    pass
            
            # Migration for invoice_path
            try:
                session.execute("SELECT invoice_path FROM visits LIMIT 1")
            except Exception:
                try:
                    session.execute("ALTER TABLE visits ADD COLUMN invoice_path TEXT")
                    session.commit()
                except Exception:
                    pass

            patients = session.query(Patient).all()
            for patient in patients:
                if not hasattr(patient, 'address') or patient.address is None:
                    patient.address = ''
                if not hasattr(patient, 'gender') or patient.gender is None:
                    patient.gender = 'Laki-laki'
            session.commit()

    def add_patient(self, name, phone, address='', gender='Laki-laki', visits=None):
        with self.Session() as session:
            patient = Patient(name=name, phone=phone, address=address, gender=gender)
            if visits:
                for visit in visits:
                    patient.visits.append(
                        Visit(
                            date=visit.date,
                            price=visit.price,
                            discount_applied=visit.discount_applied,
                            point_count=visit.point_count if hasattr(visit, 'point_count') else 0,
                            therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                        )
                    )
            session.add(patient)
            session.commit()
            return patient.id

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
                            price=float(visit.price),
                            discount_applied=visit.discount_applied,
                            point_count=visit.point_count if hasattr(visit, 'point_count') else 0,
                            therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                            invoice_path=visit.invoice_path if hasattr(visit, 'invoice_path') else None,
                        )
                        for visit in sorted(patient.visits, key=lambda v: v.date)
                    ]
                )
                for patient in patients
            ]

    def get_patients(self):
        with self.Session() as session:
            patients = session.query(Patient).options(joinedload(Patient.visits)).all()
            return [(p.id, p.name, p.phone, p.gender, p.address, len(p.visits)) for p in patients]

    def get_patient_with_visits(self, patient_id):
        with self.Session() as session:
            patient = session.query(Patient).options(joinedload(Patient.visits)).get(patient_id)
            if patient:
                return patient
            raise ValueError("Patient not found")

    def update_patient(self, patient_id, name, phone, address='', gender='Laki-laki'):
        with self.Session() as session:
            patient = session.get(Patient, patient_id)
            if not patient:
                raise ValueError("Patient not found")
            patient.name = name
            patient.phone = phone
            patient.address = address
            patient.gender = gender
            session.commit()

    def delete_patient(self, patient_id):
        with self.Session() as session:
            patient = session.get(Patient, patient_id)
            if patient:
                session.delete(patient)
                session.commit()

    def update_patient_visits(self, patient_id: int, new_visits: List[VisitData]):
        with self.Session() as session:
            patient = session.query(Patient).options(joinedload(Patient.visits)).get(patient_id)
            if not patient:
                raise ValueError("Patient not found")

            existing_visits = {v.id: v for v in patient.visits}
            new_visits_by_id = {v.id: v for v in new_visits if v.id is not None}

            for vid, data in new_visits_by_id.items():
                if vid in existing_visits:
                    v = existing_visits[vid]
                    v.date = data.date
                    v.price = data.price
                    v.discount_applied = data.discount_applied
                    if hasattr(data, 'point_count'):
                        v.point_count = data.point_count
                    if hasattr(data, 'therapist_id'):
                        v.therapist_id = data.therapist_id

            new_ids = set(new_visits_by_id.keys())
            for v in list(patient.visits):
                if v.id not in new_ids:
                    patient.visits.remove(v)

            for visit in new_visits:
                if visit.id is None:
                    new_visit = Visit(
                        date=visit.date,
                        price=visit.price,
                        discount_applied=visit.discount_applied,
                        point_count=visit.point_count if hasattr(visit, 'point_count') else 0,
                        therapist_id=visit.therapist_id if hasattr(visit, 'therapist_id') else None,
                    )
                    patient.visits.append(new_visit)

            session.commit()

    def add_visit(self, patient_id, price, point_count=0, therapist_id=None, 
                  discount_percentage=0, min_visits_for_discount=5, invoice_path=None,
                  medical_notes=None, inventory_config=None):
        with self.Session() as session:
            patient = session.query(Patient).options(joinedload(Patient.visits)).get(patient_id)
            if not patient:
                raise ValueError("Patient not found")

            visit_count = len(patient.visits)
            discount_applied = False
            final_price = float(price)

            if discount_percentage > 0 and visit_count >= min_visits_for_discount:
                final_price = final_price * (1 - discount_percentage / 100)
                discount_applied = True

            new_visit = Visit(
                patient_id=patient_id,
                therapist_id=therapist_id,
                date=datetime.now(),
                price=round(final_price, 2),
                discount_applied=discount_applied,
                point_count=point_count,
                invoice_path=invoice_path,
                medical_notes=medical_notes
            )
            session.add(new_visit)

            # --- Pengurangan Stok Otomatis (Dinamis) ---
            if inventory_config:
                for item_name, qty_reduction in inventory_config.items():
                    item = session.query(Inventory).filter(Inventory.item_name.like(f"%{item_name}%")).first()
                    if item:
                        item.quantity = max(0, item.quantity - qty_reduction)
            else:
                # Fallback ke default jika config tidak ada
                pisau = session.query(Inventory).filter(Inventory.item_name.like("%Pisau%")).first()
                if pisau:
                    pisau.quantity = max(0, pisau.quantity - 1)
                tisu = session.query(Inventory).filter(Inventory.item_name.like("%Tisu%")).first()
                if tisu:
                    tisu.quantity = max(0, tisu.quantity - 2)

            session.commit()

            return round(final_price, 2), discount_applied

    def get_visits(self, patient_id):
        with self.Session() as session:
            visits = session.query(Visit).filter(Visit.patient_id == patient_id).all()
            return [{
                'id': v.id,
                'date': v.date,
                'price': float(v.price),
                'discount_applied': v.discount_applied,
                'point_count': v.point_count if hasattr(v, 'point_count') else 0,
                'therapist_id': v.therapist_id if hasattr(v, 'therapist_id') else None,
                'invoice_path': v.invoice_path if hasattr(v, 'invoice_path') else None,
                'medical_notes': v.medical_notes if hasattr(v, 'medical_notes') else '-',
            } for v in visits]

    def get_all_visits(self):
        with self.Session() as session:
            visits = session.query(Visit).all()
            return [{
                'id': v.id,
                'date': v.date,
                'price': float(v.price),
                'discount_applied': v.discount_applied,
                'point_count': v.point_count if hasattr(v, 'point_count') else 0,
                'patient_id': v.patient_id,
                'therapist_id': v.therapist_id if hasattr(v, 'therapist_id') else None,
                'invoice_path': v.invoice_path if hasattr(v, 'invoice_path') else None,
                'medical_notes': v.medical_notes if hasattr(v, 'medical_notes') else '-',
            } for v in visits]

    def add_therapist(self, name, gender, specialization=''):
        with self.Session() as session:
            therapist = Therapist(name=name, gender=gender, specialization=specialization)
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
                    is_active=t.is_active
                )
                for t in therapists
            ]

    def get_therapists_by_gender(self, gender):
        with self.Session() as session:
            therapists = session.query(Therapist).filter(
                Therapist.gender == gender,
                Therapist.is_active == True
            ).all()
            return [
                TherapistData(
                    id=t.id,
                    name=t.name,
                    gender=t.gender,
                    specialization=t.specialization,
                    is_active=t.is_active
                )
                for t in therapists
            ]

    def update_therapist(self, therapist_id, name, gender, specialization='', is_active=True):
        with self.Session() as session:
            therapist = session.get(Therapist, therapist_id)
            if not therapist:
                raise ValueError("Therapist not found")
            therapist.name = name
            therapist.gender = gender
            therapist.specialization = specialization
            therapist.is_active = is_active
            session.commit()

    def delete_therapist(self, therapist_id):
        with self.Session() as session:
            therapist = session.get(Therapist, therapist_id)
            if therapist:
                therapist.is_active = False
                session.commit()

    def get_therapist(self, therapist_id):
        with self.Session() as session:
            therapist = session.get(Therapist, therapist_id)
            if therapist:
                return TherapistData(
                    id=therapist.id,
                    name=therapist.name,
                    gender=therapist.gender,
                    specialization=therapist.specialization,
                    is_active=therapist.is_active
                )
            return None

    # --- Inventory Methods ---
    def get_all_inventory(self):
        with self.Session() as session:
            items = session.query(Inventory).all()
            return [
                {
                    "id": item.id,
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "min_stock": item.min_stock,
                    "last_updated": item.last_updated
                } for item in items
            ]

    def update_stock(self, item_id, quantity_change):
        with self.Session() as session:
            item = session.get(Inventory, item_id)
            if item:
                item.quantity += quantity_change
                session.commit()
                return True
            return False

    def add_inventory_item(self, name, unit, min_stock, initial_qty=0):
        with self.Session() as session:
            item = Inventory(item_name=name, unit=unit, min_stock=min_stock, quantity=initial_qty)
            session.add(item)
            session.commit()
            return item.id

    def delete_inventory_item(self, item_id):
        with self.Session() as session:
            item = session.get(Inventory, item_id)
            if item:
                session.delete(item)
                session.commit()
