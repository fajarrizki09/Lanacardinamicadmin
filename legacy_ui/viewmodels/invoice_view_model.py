import os


class InvoiceViewModel:
    """Jalur data invoice agar widget daftar invoice tidak query database langsung."""

    def __init__(self, db):
        self.db = db

    def get_invoice_rows(self, search_text=""):
        search = (search_text or "").lower()
        visits = self.db.get_all_visits() or []
        patients = {p.id: p.name for p in self.db.get_all_patients()}
        rows = []

        for visit in visits:
            invoice_path = visit.get("invoice_path")
            if not invoice_path or not os.path.exists(invoice_path):
                continue

            patient_name = patients.get(visit.get("patient_id"), "Unknown")
            date_value = visit.get("date")
            date_str = date_value.strftime("%d/%m/%Y %H:%M") if hasattr(date_value, "strftime") else str(date_value)
            if search and search not in patient_name.lower() and search not in date_str.lower():
                continue

            rows.append({
                "date": date_str,
                "name": patient_name,
                "service": visit.get("service_name") or "Bekam",
                "price": float(visit.get("price", 0) or 0),
                "path": invoice_path,
            })

        rows.sort(key=lambda item: item["date"], reverse=True)
        return rows
