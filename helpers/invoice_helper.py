from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os

class InvoiceHelper:
    def __init__(self, output_dir="invoices"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_invoice(self, patient_name, date, points, price, therapist_name="--", custom_settings=None):
        filename = f"Invoice_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        if not custom_settings:
            custom_settings = {
                "clinic_name": "Klinik Bekam Sunnah Pro",
                "clinic_tagline": "Professional Cupping Therapy",
                "invoice_footer": "Semoga menjadi wasilah kesembuhan yang berkah.",
                "admin_label": "Admin Klinik,"
            }

        try:
            from reportlab.lib.pagesizes import A5
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            from reportlab.lib.units import mm
            
            c = canvas.Canvas(filepath, pagesize=A5)
            width, height = A5

            # --- Background Decoration ---
            c.setStrokeColor(colors.hexColor("#27ae60"))
            c.setLineWidth(2)
            c.rect(5*mm, 5*mm, width-10*mm, height-10*mm) # Border luar
            
            # --- Header ---
            c.setFillColor(colors.hexColor("#27ae60"))
            c.rect(10*mm, height-35*mm, width-20*mm, 20*mm, fill=1, stroke=0)
            
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width/2, height-25*mm, custom_settings.get("clinic_name", "INVOICE LAYANAN BEKAM").upper())
            
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, height-31*mm, custom_settings.get("clinic_tagline", ""))

            # --- Info Section ---
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(15*mm, height-50*mm, "INFORMASI PASIEN")
            c.setLineWidth(0.5)
            c.line(15*mm, height-52*mm, 60*mm, height-52*mm)
            
            c.setFont("Helvetica", 10)
            c.drawString(15*mm, height-60*mm, f"Nama Pasien  : {patient_name}")
            c.drawString(15*mm, height-66*mm, f"Tanggal       : {date}")
            c.drawString(15*mm, height-72*mm, f"Terapis       : {therapist_name}")

            # --- Table Header ---
            table_top = height - 85*mm
            c.setFillColor(colors.hexColor("#f1f1f1"))
            c.rect(15*mm, table_top, width-30*mm, 10*mm, fill=1, stroke=0)
            
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(20*mm, table_top + 3.5*mm, "DESKRIPSI LAYANAN")
            c.drawRightString(width-20*mm, table_top + 3.5*mm, "SUBTOTAL")

            # --- Table Content ---
            c.setFont("Helvetica", 10)
            row_y = table_top - 10*mm
            c.drawString(20*mm, row_y, f"Terapi Bekam ({points} Titik)")
            c.drawRightString(width-20*mm, row_y, f"Rp {price:,.0f}")
            
            # Garis pemisah table
            c.setStrokeColor(colors.hexColor("#dddddd"))
            c.line(15*mm, row_y - 5*mm, width-15*mm, row_y - 5*mm)

            # --- Total Section ---
            c.setFillColor(colors.hexColor("#27ae60"))
            c.rect(width-70*mm, row_y - 25*mm, 55*mm, 12*mm, fill=1, stroke=0)
            
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(width-65*mm, row_y - 18*mm, "TOTAL")
            c.drawRightString(width-20*mm, row_y - 18*mm, f"Rp {price:,.0f}")

            # --- Signature / Stamp Area ---
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 9)
            c.drawCentredString(width-40*mm, 35*mm, custom_settings.get("admin_label", "Admin Klinik,"))
            c.line(width-60*mm, 15*mm, width-20*mm, 15*mm)

            # --- Footer / Doa ---
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.hexColor("#7f8c8d"))
            footer_text = custom_settings.get("invoice_footer", "")
            c.drawCentredString(width/2, 25*mm, footer_text)
            c.setFont("Helvetica", 8)
            c.drawCentredString(width/2, 20*mm, "Terima kasih atas kunjungan Anda.")

            c.save()
            return filepath
        except ImportError:
            # Fallback if reportlab is not available
            with open(filepath.replace(".pdf", ".txt"), "w") as f:
                f.write(f"INVOICE\n\nPasien: {patient_name}\nTanggal: {date}\nTitik: {points}\nHarga: {price}\nTerapis: {therapist_name}")
            return filepath.replace(".pdf", ".txt")
