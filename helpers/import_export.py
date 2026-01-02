import json
import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

class ImportExportHelper:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

    def export_data(self):
        options = ["Excel (XLSX)", "JSON"]
        format_choice, ok = QInputDialog.getItem(
            self.parent, "Export Data", "Pilih format ekspor:", options, 0, False
        )
        if not ok:
            return

        if format_choice == "Excel (XLSX)":
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Simpan file Excel", "", "Excel Files (*.xlsx)"
            )
            if file_path:
                if not file_path.endswith(".xlsx"):
                    file_path += ".xlsx"
                try:
                    patients = self.db.get_all_patients()
                    data = []
                    for p in patients:
                        data.append({
                            "Nama": p.name,
                            "Telepon": p.phone,
                            "Alamat": p.address,
                            "Gender": p.gender,
                            "Total Kunjungan": len(p.visits)
                        })
                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
                    QMessageBox.information(self.parent, "Sukses", f"Data berhasil diekspor ke {file_path}")
                except Exception as e:
                    QMessageBox.critical(self.parent, "Error", f"Gagal ekspor data:\n{e}")

        elif format_choice == "JSON":
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
            self.parent, "Pilih File untuk Impor", "", "Excel Files (*.xlsx);;JSON Files (*.json)"
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
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
                # Map column names to expected fields
                column_mapping = {
                    'nama': 'name', 'name': 'name',
                    'telepon': 'phone', 'phone': 'phone', 'no hp': 'phone',
                    'alamat': 'address', 'address': 'address',
                    'gender': 'gender', 'jenis kelamin': 'gender'
                }
                df.columns = [column_mapping.get(c.lower(), c) for c in df.columns]
                
                for _, row in df.iterrows():
                    name = row.get('name')
                    phone = row.get('phone')
                    address = row.get('address') or ''
                    gender = row.get('gender') or 'Laki-laki'
                    
                    if name:
                        if not phone:
                            phone = "TEMP-" + datetime.now().strftime("%H%M%S%f")[:10]
                        self.db.add_patient(name, str(phone), address, gender)
                
                QMessageBox.information(self.parent, "Sukses", "Data Excel berhasil diimpor!")
                return True

            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # ... existing JSON import logic ...
                # (Keep existing JSON logic here for full compatibility)
                therapists = self.db.get_all_therapists(active_only=False)
                therapist_name_map = {t.name.lower(): t.id for t in therapists}
                therapist_id_map = {}

                if "therapists" in data:
                    for t_data in data["therapists"]:
                        t_name_lower = t_data["name"].lower()
                        if t_name_lower in therapist_name_map:
                            therapist_id_map[t_data["id"]] = therapist_name_map[t_name_lower]
                        else:
                            new_id = self.db.add_therapist(t_data["name"], t_data["gender"], t_data.get("specialization", ""))
                            therapist_id_map[t_data["id"]] = new_id

                if "patients" in data:
                    from database import VisitData
                    existing_patients = {p.phone: p.id for p in self.db.get_all_patients()}
                    for p_data in data["patients"]:
                        phone = p_data["phone"]
                        p_id = existing_patients.get(phone)
                        visits = []
                        for v_data in p_data.get("visits", []):
                            v_date = v_data["date"]
                            if isinstance(v_date, str):
                                v_date = datetime.fromisoformat(v_date)
                            old_t_id = v_data.get("therapist_id")
                            new_t_id = therapist_id_map.get(old_t_id) if old_t_id is not None else None
                            visits.append(VisitData(id=None, date=v_date, price=v_data["price"], discount_applied=v_data["discount_applied"], point_count=v_data.get("point_count", 0), therapist_id=new_t_id))
                        
                        if p_id:
                            self.db.update_patient_visits(p_id, visits)
                        else:
                            self.db.add_patient(p_data["name"], phone, p_data.get("address", ""), p_data.get("gender", "Laki-laki"), visits=visits)
                
                QMessageBox.information(self.parent, "Sukses", "Data JSON berhasil diimpor.")
                return True
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Gagal impor data:\n{e}")
            return False
