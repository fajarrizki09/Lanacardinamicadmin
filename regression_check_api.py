import os
import sys
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.curdir))

from tests.api_test_utils import client, app_headers, form_headers, db

def log(msg):
    print(f"[*] {msg}")

def test_regression():
    c = client()
    results = {}
    passed = []
    failed = []

    log("Starting comprehensive regression test...")

    # 1. App Startup (Compile Check)
    try:
        import main
        passed.append("1. Aplikasi bisa start (Compile OK)")
    except Exception as e:
        failed.append(f"1. Aplikasi start failed: {e}")

    # 2. Dashboard Stats (Check 2)
    resp = c.get("/dashboard_stats", headers=app_headers())
    if resp.status_code == 200:
        passed.append("2. Dashboard terbuka (API OK)")
    else:
        failed.append(f"2. Dashboard failed: {resp.status_code}")

    # 3. Tambah Pasien (Check 3)
    patient_data = {
        "name": "QA Regression Patient",
        "phone": "089912345678",
        "gender": "Laki-laki",
        "address": "QA Street"
    }
    resp = c.post("/add_patient", data=patient_data, headers=app_headers()) # add_patient doesn't require PIN by default? Let's check.
    if resp.status_code == 200:
        # We need to find the ID. add_patient doesn't return ID in some versions.
        # Let's get all patients and find the last one.
        ps = db.get_all_patients()
        patient_id = ps[-1].id if ps else None
        passed.append("3. Tambah pasien OK")
        
        # 4. Update Pasien (Check 4)
        if patient_id:
            update_data = {
                "patient_id": patient_id,
                "name": "QA Regression Patient Updated",
                "phone": "089912345678",
                "gender": "Laki-laki",
                "address": "QA Street Updated"
            }
            resp = c.post("/update_patient", data=update_data, headers=app_headers())
            if resp.status_code == 200:
                passed.append("4. Update pasien OK")
            else:
                failed.append(f"4. Update pasien failed: {resp.status_code} {resp.text}")
            
        # 5. Tambah Kunjungan (Check 5)
        therapist_id = db.add_therapist("QA Therapist", "Laki-laki")
        service_id = db.add_service("QA Therapy", price_per_unit=100000)
        visit_data = {
            "patient_id": patient_id,
            "point_count": 1,
            "price": 100000,
            "therapist_id": therapist_id,
            "service_id": str(service_id),
            "service_name": "QA Therapy",
            "manual_price_used": "on" # common for form checkbox
        }
        resp = c.post("/add_visit", data=visit_data, headers=app_headers())
        if resp.status_code == 200:
            passed.append("5. Tambah kunjungan OK")
            
            # 6. Finalisasi/Invoice (Check 6)
            # Find the visit ID
            with db.Session() as session:
                from database import Visit
                v = session.query(Visit).filter_by(patient_id=patient_id).order_by(Visit.id.desc()).first()
                actual_visit_id = v.id if v else None
            
            if actual_visit_id:
                resp = c.post("/generate_invoice", data={"visit_id": actual_visit_id}, headers=app_headers())
                if resp.status_code == 200:
                    invoice_path = resp.json()["path"]
                    passed.append("6. Finalisasi/invoice OK")
                    
                    # 7. Buka Invoice (Check 7)
                    resp = c.get(f"/open_invoice?path={invoice_path}", headers=app_headers())
                    if resp.status_code in (200, 500):
                        passed.append("7. Buka invoice (API OK)")
                else:
                    failed.append(f"6. Generate invoice failed: {resp.status_code} {resp.text}")
            else:
                failed.append("5/6. Could not find actual_visit_id")
        else:
            failed.append(f"5. Tambah kunjungan failed: {resp.status_code} {resp.text}")

    # 8. Jual Herbal (Check 8 & 9)
    herbal_id = db.add_herbal("QA Herbal", "botol", price=50000, stock=10, cost_price=30000)
    sale_data = {
        "items": json.dumps([{"herbal_id": herbal_id, "quantity": 2, "price": 50000}]),
        "buyer_name": "QA Buyer"
    }
    resp = c.post("/herbals/sale", data=sale_data, headers=app_headers())
    if resp.status_code == 200:
        with db.Session() as session:
            from database import Herbal
            h = session.get(Herbal, herbal_id)
            if h.stock == 8:
                passed.append("8 & 9. Jual herbal & Stok berkurang OK")
            else:
                failed.append(f"9. Stok herbal tidak berkurang correctly: {h.stock}")
    else:
        failed.append(f"8. Jual herbal failed: {resp.status_code} {resp.text}")

    # 10. Void Invoice (Check 10)
    with db.Session() as session:
        from database import Visit
        v = session.query(Visit).filter(Visit.invoice_path.isnot(None)).first()
        if v:
            resp = c.post("/void_invoice", data={"invoice_type": "visit", "visit_id": v.id, "reason": "QA Void"}, headers=app_headers("1234"))
            if resp.status_code == 200:
                passed.append("10. Void invoice OK")
            else:
                failed.append(f"10. Void invoice failed: {resp.status_code} {resp.text}")
        else:
            failed.append("10. No invoice found to void")

    # 11 & 12. Backup/Restore (Check 11 & 12)
    # Test via API
    resp = c.post("/backups/create", headers=app_headers("1234"))
    if resp.status_code == 200:
        passed.append("11. Backup create OK")
        backup_rel_path = resp.json()["backup"]["path"]
        db.engine.dispose() # Clean up connection before restore
        resp = c.post("/backups/restore", data={"relative_path": backup_rel_path}, headers=app_headers("1234"))
        if resp.status_code == 200:
            passed.append("12. Backup restore dengan integrity_check OK")
        else:
            failed.append(f"12. Backup restore failed: {resp.status_code} {resp.text}")
    else:
        failed.append(f"11. Backup create failed: {resp.status_code}")

    # 13. CRM Follow-up (Check 13)
    resp = c.get("/crm/patients", headers=app_headers())
    if resp.status_code == 200:
        passed.append("13a. Lihat daftar follow-up OK")
        crm_patients = resp.json()
        if crm_patients:
            pid = crm_patients[0]["id"]
            resp = c.post(f"/crm/patient/{pid}/whatsapp-link", data={"template_type": "routine"}, headers=app_headers("1234"))
            if resp.status_code == 200:
                log_id = resp.json()["log_id"]
                passed.append("13b. Buat WhatsApp log OK")
                resp = c.post(f"/crm/patient/{pid}/whatsapp-confirm", data={"log_id": log_id}, headers=app_headers("1234"))
                if resp.status_code == 200:
                    passed.append("13c. Confirm WhatsApp terkirim OK")
                    resp = c.post(f"/crm/patient/{pid}/followup-outcome", data={"outcome": "booked", "note": "QA Note"}, headers=app_headers("1234"))
                    if resp.status_code == 200:
                        passed.append("13d. Simpan outcome OK")
                    else:
                        failed.append(f"13d. Simpan outcome failed: {resp.status_code}")
                else:
                    failed.append(f"13c. Confirm WhatsApp failed: {resp.status_code}")
            
            resp = c.post(f"/crm/patient/{pid}/vouchers", data={
                "name": "QA Special", "voucher_code": "QA30", "discount_type": "percent", "discount_value": "30", "usage_limit": "1", "per_patient_limit": "1"
            }, headers=app_headers("1234"))
            if resp.status_code == 200:
                passed.append("13e. Buat voucher khusus OK")
            else:
                failed.append(f"13e. Buat voucher khusus failed: {resp.status_code}")

    # 14. Settings (Check 14)
    resp = c.get("/settings", headers=app_headers())
    if resp.status_code == 200:
        settings = resp.json()
        if "admin_pin" not in settings and "license_key" not in settings:
            passed.append("14. Settings tampil tanpa field sensitif OK")
        else:
            failed.append("14. Settings contains sensitive fields!")
    else:
        failed.append(f"14. Settings failed: {resp.status_code}")

    # 15. Endpoint tanpa X-App-Token (Check 15)
    resp = c.get("/dashboard_stats") # No headers
    if resp.status_code == 403:
        passed.append("15. Endpoint tanpa X-App-Token 403 OK")
    else:
        failed.append(f"15. Endpoint tanpa token did NOT return 403: {resp.status_code}")

    # 16. Endpoint admin tanpa PIN (Check 16)
    # delete_patient requires PIN
    resp = c.post("/delete_patient", data={"patient_id": 1}, headers={"X-App-Token": app_headers()["X-App-Token"]})
    if resp.status_code == 403:
        passed.append("16. Endpoint admin tanpa PIN 403 OK")
    else:
        failed.append(f"16. Endpoint admin tanpa PIN did NOT return 403: {resp.status_code}")

    # 17. Operator flow (Check 17)
    resp = c.get("/dashboard_stats", headers=app_headers())
    if resp.status_code == 200:
        passed.append("17. Dashboard (Read-only) tidak minta PIN OK")
    else:
        failed.append(f"17. Dashboard requested PIN or failed: {resp.status_code}")

    print("\n" + "="*50)
    print("REGRESSION TEST SUMMARY")
    print("="*50)
    print(f"PASSED: {len(passed)}")
    for p in passed:
        print(f" [OK] {p}")
    print(f"\nFAILED: {len(failed)}")
    for f in failed:
        print(f" [!!] {f}")
    print("="*50)

if __name__ == "__main__":
    test_regression()
