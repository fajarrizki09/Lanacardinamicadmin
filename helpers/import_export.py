import json
import os
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

class ImportExportHelper:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

    def export_data(self):
        options = ["JSON"]
        format_choice, ok = QInputDialog.getItem(
            self.parent, "Export Data", "Pilih format ekspor:", options, 0, False
        )
        if not ok:
            return

        if format_choice == "JSON":
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Simpan file JSON", "", "JSON Files (*.json)"
            )
            if file_path:
                if not file_path.endswith(".json"):
                    file_path += ".json"
                
                try:
                    patients = self.db.get_all_patients()
                    therapists = self.db.get_all_therapists(active_only=False)
                    
                    data = {
                        "metadata": {
                            "version": "1.0",
                            "export_date": datetime.now().isoformat(),
                            "app": "Aplikasi Pasien Bekam"
                        },
                        "therapists": [
                            {
                                "id": t.id,
                                "name": t.name,
                                "gender": t.gender,
                                "specialization": t.specialization,
                                "is_active": t.is_active
                            } for t in therapists
                        ],
                        "patients": [
                            {
                                "name": p.name,
                                "phone": p.phone,
                                "address": p.address,
                                "gender": p.gender,
                                "visits": [
                                    {
                                        "date": v.date.isoformat() if hasattr(v.date, 'isoformat') else v.date,
                                        "price": v.price,
                                        "discount_applied": v.discount_applied,
                                        "point_count": v.point_count,
                                        "therapist_id": v.therapist_id
                                    } for v in p.visits
                                ]
                            } for p in patients
                        ]
                    }
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    
                    QMessageBox.information(self.parent, "Sukses", f"Data berhasil diekspor ke {file_path}")
                except Exception as e:
                    QMessageBox.critical(self.parent, "Error", f"Gagal ekspor data:\n{e}")

    def import_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent, "Pilih File JSON untuk Impor", "", "JSON Files (*.json)"
        )
        if not file_path:
            return False

        confirm = QMessageBox.question(
            self.parent, "Konfirmasi Impor",
            "Impor data akan menggabungkan data baru ke database. Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. Import Therapists first to maintain relationships
            therapist_map = {} # Old ID -> New ID
            if "therapists" in data:
                existing_therapists = {t.name: t.id for t in self.db.get_all_therapists(active_only=False)}
                for t_data in data["therapists"]:
                    if t_data["name"] in existing_therapists:
                        therapist_map[t_data["id"]] = existing_therapists[t_data["name"]]
                    else:
                        new_id = self.db.add_therapist(
                            t_data["name"], 
                            t_data["gender"], 
                            t_data.get("specialization", "")
                        )
                        therapist_map[t_data["id"]] = new_id

            # 2. Import Patients and Visits
            if "patients" in data:
                from database import VisitData
                for p_data in data["patients"]:
                    # Handle visits and map therapists
                    visits = []
                    for v_data in p_data.get("visits", []):
                        v_date = v_data["date"]
                        if isinstance(v_date, str):
                            v_date = datetime.fromisoformat(v_date)
                        
                        # Map old therapist ID to new one, or None if empty
                        old_t_id = v_data.get("therapist_id")
                        new_t_id = therapist_map.get(old_t_id) if old_t_id is not None else None
                        
                        visits.append(VisitData(
                            id=None,
                            date=v_date,
                            price=v_data["price"],
                            discount_applied=v_data["discount_applied"],
                            point_count=v_data.get("point_count", 0),
                            therapist_id=new_t_id
                        ))
                    
                    # Add patient (handle duplicate phone check implicitly in add_patient or here)
                    self.db.add_patient(
                        p_data["name"],
                        p_data["phone"],
                        p_data.get("address", ""),
                        p_data.get("gender", "Laki-laki"),
                        visits=visits
                    )
            
            QMessageBox.information(self.parent, "Sukses", "Data berhasil diimpor.")
            return True
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Gagal impor data:\n{e}")
            return False
