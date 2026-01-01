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

    def generate_invoice(self, patient_name, date, points, price, therapist_name="--"):
        filename = f"Invoice_{patient_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=A5)
        width, height = A5

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 50, "INVOICE LAYANAN BEKAM")
        
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 70, "Klinik Bekam Sunnah Pro")
        c.line(50, height - 80, width - 50, height - 80)

        # Info Pasien
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 110, f"Kepada: {patient_name}")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 125, f"Tanggal: {date}")

        # Detail Layanan
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, height - 160, "Deskripsi")
        c.drawString(width - 150, height - 160, "Jumlah")
        c.line(50, height - 165, width - 50, height - 165)

        c.setFont("Helvetica", 10)
        c.drawString(50, height - 185, "Layanan Bekam (Titik)")
        c.drawString(width - 150, height - 185, f"{points} Titik")
        
        c.drawString(50, height - 205, "Terapis")
        c.drawString(width - 150, height - 205, therapist_name)

        # Total
        c.line(50, height - 225, width - 50, height - 225)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 245, "TOTAL PEMBAYARAN")
        c.drawString(width - 150, height - 245, f"Rp {price:,.0f}")

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width/2, 50, "Terima kasih telah mempercayakan kesehatan Anda pada kami.")
        c.drawCentredString(width/2, 40, "Semoga menjadi wasilah kesembuhan yang berkah.")

        c.save()
        return filepath
