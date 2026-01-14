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
        options = ["Excel (XLSX) - Semua Data", "Excel (XLSX) - Per Bulan", "JSON (Semua Data)"]
        format_choice, ok = QInputDialog.getItem(
            self.parent, "Export Data", "Pilih format ekspor:", options, 0, False
        )
        if not ok:
            return

        target_month = None
        if "Per Bulan" in format_choice:
            now = datetime.now()
            month_options = []
            for i in range(12):
                m = (now.month - i - 1) % 12 + 1
                y = now.year if now.month - i > 0 else now.year - 1
                month_options.append(f"{y}-{m:02d}")
            
            month_str, ok = QInputDialog.getItem(
                self.parent, "Pilih Bulan", "Pilih bulan untuk diekspor:", month_options, 0, False
            )
            if not ok: return
            target_month = month_str

        if "Excel" in format_choice:
            default_name = f"data_pasien_{target_month}.xlsx" if target_month else "data_pasien_lengkap.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Simpan file Excel", default_name, "Excel Files (*.xlsx)"
            )
            if file_path:
                if not file_path.endswith(".xlsx"):
                    file_path += ".xlsx"
                try:
                    patients = self.db.get_all_patients()
                    therapists = self.db.get_all_therapists(active_only=False)
                    t_dict = {t.id: t.name for t in therapists}
                    
                    data = []
                    for p in patients:
                        filtered_visits = p.visits
                        if target_month:
                            filtered_visits = [v for v in p.visits if v.date.strftime("%Y-%m") == target_month]
                        
                        if not filtered_visits:
                            if not target_month:
                                data.append({
                                    "Nama Pasien": p.name,
                                    "Telepon": p.phone,
                                    "Alamat": p.address,
                                    "Gender": p.gender,
                                    "Tanggal Kunjungan": "-",
                                    "Terapis": "-",
                                    "Jumlah Titik": 0,
                                    "Harga": 0,
                                    "Diskon": "-"
                                })
                            continue

                        for v in filtered_visits:
                            data.append({
                                "Nama Pasien": p.name,
                                "Telepon": p.phone,
                                "Alamat": p.address,
                                "Gender": p.gender,
                                "Tanggal Kunjungan": v.date.strftime("%Y-%m-%d %H:%M"),
                                "Terapis": t_dict.get(v.therapist_id, "-"),
                                "Jumlah Titik": v.point_count,
                                "Harga": v.price,
                                "Diskon": "Ya" if v.discount_applied else "Tidak"
                            })
                    
                    if not data:
                        QMessageBox.warning(self.parent, "Peringatan", "Tidak ada data untuk periode tersebut.")
                        return

                    df = pd.DataFrame(data)
                    df.to_excel(file_path, index=False)
                    QMessageBox.information(self.parent, "Sukses", f"Data berhasil diekspor ke {file_path}")
                except Exception as e:
                    QMessageBox.critical(self.parent, "Error", f"Gagal ekspor data:\n{e}")

        elif format_choice == "JSON (Semua Data)":
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
                    'nama pasien': 'name', 'nama': 'name', 'name': 'name',
                    'telepon': 'phone', 'phone': 'phone', 'no hp': 'phone',
                    'alamat': 'address', 'address': 'address',
                    'gender': 'gender', 'jenis kelamin': 'gender',
                    'tanggal kunjungan': 'v_date', 'tanggal': 'v_date',
                    'terapis': 'v_therapist',
                    'jumlah titik': 'v_points', 'titik': 'v_points',
                    'harga terapi': 'v_price_therapy',
                    'harga herbal': 'v_price_herbal',
                    'harga': 'v_price',
                    'diskon': 'v_discount',
                    'keterangan': 'v_notes'
                }
                df.columns = [column_mapping.get(c.lower(), c) for c in df.columns]
                
                # Group by patient to handle multiple visits in one import
                from database import VisitData
                therapists = self.db.get_all_therapists(active_only=False)
                t_name_map = {t.name.lower(): t.id for t in therapists}
                
                patient_groups = df.groupby(['name', 'phone'])
                
                for (name, phone), group in patient_groups:
                    address = group['address'].iloc[0] if 'address' in group.columns else ''
                    gender = group['gender'].iloc[0] if 'gender' in group.columns else 'Laki-laki'
                    
                    visits = []
                    if 'v_date' in group.columns:
                        for _, row in group.iterrows():
                            v_date_raw = row.get('v_date')
                            if pd.isna(v_date_raw) or v_date_raw == "-": continue
                            
                            try:
                                v_date = pd.to_datetime(v_date_raw).to_pydatetime()
                                
                                v_notes_raw = str(row.get('v_notes', '')) if not pd.isna(row.get('v_notes')) else ""
                                
                                # Skip data that is purely sales (no name/phone/visit indicators)
                                # If name is empty or it looks like a standalone herbal sale
                                if not name or (not v_notes_raw and not row.get('v_points') and total_price > 0):
                                    # Very basic heuristic: if it has herbal name but no visit codes, 
                                    # and we are in a row that might be standalone
                                    if any(keyword in v_notes_raw.lower() for keyword in ['pl 13', 'pl dhuafa', 'pb konsul', 'titik']):
                                        pass # Keep it
                                    elif total_price > 0 and not row.get('v_price_therapy'):
                                        continue # Skip standalone herbal sales

                                # Combined price logic (Therapy + Herbal)
                                v_price_therapy = row.get('v_price_therapy', 0) if not pd.isna(row.get('v_price_therapy')) else 0
                                v_price_herbal = row.get('v_price_herbal', 0) if not pd.isna(row.get('v_price_herbal')) else 0
                                v_price_base = row.get('v_price', 0) if not pd.isna(row.get('v_price')) else 0
                                
                                total_price = int(v_price_therapy) + int(v_price_herbal)
                                if total_price == 0:
                                    total_price = int(v_price_base)
                                
                                v_points_raw = row.get('v_points', 0)
                                
                                # Smart point extraction
                                v_points = 0
                                if isinstance(v_points_raw, (int, float)):
                                    v_points = int(v_points_raw)
                                elif isinstance(v_points_raw, str):
                                    import re
                                    match = re.search(r'(\d+)', v_points_raw)
                                    if match:
                                        v_points = int(match.group(1))
                                
                                v_notes_raw = str(row.get('v_notes', '')) if not pd.isna(row.get('v_notes')) else ""
                                
                                # Smart point extraction and note processing
                                v_points = 0
                                # Check for specific codes in notes first
                                notes_lower = v_notes_raw.lower()
                                if 'pl 13' in notes_lower:
                                    v_points = 13
                                elif 'pl dhuafa' in notes_lower:
                                    # Assuming a default for Dhuafa, or just keep notes
                                    pass
                                elif 'pb konsul' in notes_lower:
                                    # Consultation usually 0 points unless specified
                                    v_points = 0
                                
                                # Try extracting points from v_points column if still 0
                                if v_points == 0:
                                    if isinstance(v_points_raw, (int, float)):
                                        v_points = int(v_points_raw)
                                    elif isinstance(v_points_raw, str):
                                        import re
                                        match = re.search(r'(\d+)', v_points_raw)
                                        if match:
                                            v_points = int(match.group(1))
                                
                                # If points still 0, try finding "XX titik" in notes
                                if v_points == 0 and v_notes_raw:
                                    import re
                                    match = re.search(r'(\d+)\s*titik', notes_lower)
                                    if match:
                                        v_points = int(match.group(1))
                                
                                v_discount = str(row.get('v_discount', '')).lower() in ['ya', 'yes', 'true', '1']
                                t_name = str(row.get('v_therapist', '')).lower()
                                t_id = t_name_map.get(t_name)
                                
                                visits.append(VisitData(
                                    id=None, date=v_date, price=total_price,
                                    discount_applied=v_discount, point_count=v_points,
                                    therapist_id=t_id, medical_notes=v_notes_raw if v_notes_raw else None
                                ))
                            except: continue

                    if name:
                        if not phone or pd.isna(phone):
                            phone = "TEMP-" + datetime.now().strftime("%H%M%S%f")[:10]
                        
                        # Check if patient exists
                        existing = self.db.get_patient_by_phone(str(phone))
                        if existing:
                            self.db.update_patient_visits(existing.id, visits)
                        else:
                            self.db.add_patient(name, str(phone), address, gender, visits=visits)
                
                QMessageBox.information(self.parent, "Sukses", "Data detail kunjungan berhasil diimpor!")
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
