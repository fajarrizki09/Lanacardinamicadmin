from datetime import datetime
import os
import re
import textwrap

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


GREEN = colors.HexColor("#178060")
DARK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5b6670")
LINE = colors.HexColor("#cbd5df")
SOFT_BG = colors.HexColor("#f8fafc")
SOFT_GREEN = colors.HexColor("#ecfdf5")


class InvoiceHelper:
    def __init__(self, output_dir="invoices"):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def _safe_output_path(self, filename):
        safe_name = self.safe_filename(os.path.basename(str(filename or "")), fallback="Invoice")
        if not safe_name.lower().endswith(".pdf"):
            safe_name = f"{safe_name}.pdf"
        output_path = os.path.abspath(os.path.join(self.output_dir, safe_name))
        common = os.path.commonpath([self.output_dir, output_path])
        if common != self.output_dir:
            raise ValueError("Path invoice tidak valid.")
        return output_path

    @staticmethod
    def safe_filename(value, fallback="Pasien"):
        text = str(value or "").strip()
        text = re.sub(r'[\\/:\*\?"<>\|]+', "", text)
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"_+", "_", text).strip("._ ")
        return text or fallback

    @staticmethod
    def format_rupiah(value):
        amount = int(round(float(value or 0)))
        return "Rp " + f"{amount:,}".replace(",", ".")

    @staticmethod
    def parse_date(value):
        if isinstance(value, datetime):
            return value
        text = str(value or "").strip()
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def format_date(value):
        months = {
            1: "Januari",
            2: "Februari",
            3: "Maret",
            4: "April",
            5: "Mei",
            6: "Juni",
            7: "Juli",
            8: "Agustus",
            9: "September",
            10: "Oktober",
            11: "November",
            12: "Desember",
        }
        dt = InvoiceHelper.parse_date(value)
        return f"{dt.day:02d} {months[dt.month]} {dt.year}"

    @staticmethod
    def wrap_text(text, max_chars=44, max_lines=2):
        clean = " ".join(str(text or "").split())
        if not clean:
            return [""]
        lines = textwrap.wrap(clean, width=max(8, int(max_chars))) or [clean]
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            if len(lines[-1]) > 3:
                lines[-1] = lines[-1][:-3].rstrip() + "..."
        return lines

    @staticmethod
    def truncate(text, max_chars=60):
        clean = " ".join(str(text or "").split())
        if len(clean) <= max_chars:
            return clean
        return clean[: max(0, max_chars - 3)].rstrip() + "..."

    @staticmethod
    def _pdf_payment_link(url):
        text = str(url or "").strip()
        if text.startswith("/"):
            return "http://127.0.0.1:8000" + text
        return text

    @staticmethod
    def _payment_provider_label(provider):
        normalized = str(provider or "manual").strip().lower()
        labels = {
            "gateway_mock": "Pembayaran Internal",
            "midtrans": "Midtrans",
            "manual": "Manual",
        }
        return labels.get(normalized, "Provider Tidak Didukung")

    @staticmethod
    def _payment_status_label(status):
        normalized = str(status or "").strip().lower()
        labels = {
            "paid": "Lunas",
            "unpaid": "Belum Bayar",
            "partial": "Sebagian",
            "pending": "Menunggu",
            "expired": "Kedaluwarsa",
            "failed": "Gagal",
        }
        return labels.get(normalized, str(status or "-"))

    @staticmethod
    def _payment_method_label(method):
        normalized = str(method or "").strip().lower()
        labels = {
            "cash": "Tunai",
            "qris": "QRIS",
            "transfer": "Transfer",
            "debit": "Debit",
            "ewallet": "E-Wallet",
            "virtual_account": "Virtual Account",
            "credit_card": "Kartu Kredit",
            "other": "Lainnya",
            "free": "Gratis",
        }
        return labels.get(normalized, str(method or "-"))

    def _draw_wrapped(self, c, text, x, y, max_chars, max_lines, font="Helvetica", size=8, leading=4.2 * mm):
        c.setFont(font, max(8, size))
        lines = self.wrap_text(text, max_chars=max_chars, max_lines=max_lines)
        for line in lines:
            c.drawString(x, y, line)
            y -= leading
        return y

    def _draw_label_value(self, c, label, value, x, y, label_width=27 * mm, max_chars=44):
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(x, y, label)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8)
        value_lines = self.wrap_text(value, max_chars=max_chars, max_lines=2)
        for idx, line in enumerate(value_lines):
            c.drawString(x + label_width, y - (idx * 4 * mm), line)
        return y - max(1, len(value_lines)) * 4.2 * mm

    def _draw_logo(self, c, logo_path, x, y_top, max_h=20 * mm):
        if not logo_path or not os.path.exists(logo_path):
            return 0
        try:
            c.drawImage(
                logo_path,
                x,
                y_top - max_h,
                width=max_h,
                height=max_h,
                preserveAspectRatio=True,
                anchor="nw",
                mask="auto",
            )
            return max_h + 4 * mm
        except Exception:
            return 0

    @staticmethod
    def draw_right_text(c, x, y, text):
        c.drawRightString(x, y, str(text or ""))

    def _new_page(self, c, invoice_number, clinic_name, top, left, right):
        c.showPage()
        c.setTitle(invoice_number)
        c.setAuthor(clinic_name)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(left, top, f"{invoice_number} - lanjutan")
        c.setStrokeColor(LINE)
        c.line(left, top - 5 * mm, right, top - 5 * mm)
        return top - 11 * mm

    def _draw_service_table_header(self, c, y, left, right, col_desc, col_qty, price_right_x, subtotal_right_x):
        header_h = 7 * mm
        c.setFillColor(SOFT_BG)
        c.setStrokeColor(colors.HexColor("#d8e1ea"))
        c.setLineWidth(0.35)
        c.roundRect(left, y - header_h, right - left, header_h, 1.5 * mm, stroke=1, fill=1)
        y -= 4.7 * mm
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 7.8)
        c.drawString(col_desc + 2 * mm, y, "Deskripsi")
        c.drawCentredString(col_qty, y, "Qty")
        self.draw_right_text(c, price_right_x, y, "Harga Satuan")
        self.draw_right_text(c, subtotal_right_x, y, "Subtotal")
        return y - 6 * mm

    def _draw_herbal_table_header(self, c, y, left, right, col_no, col_desc, col_qty, price_right_x, subtotal_right_x):
        header_h = 7 * mm
        c.setFillColor(SOFT_BG)
        c.setStrokeColor(colors.HexColor("#d8e1ea"))
        c.setLineWidth(0.35)
        c.roundRect(left, y - header_h, right - left, header_h, 1.5 * mm, stroke=1, fill=1)
        y -= 4.7 * mm
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 7.8)
        c.drawString(col_no, y, "No")
        c.drawString(col_desc, y, "Nama Produk / Herbal")
        c.drawCentredString(col_qty, y, "Qty")
        self.draw_right_text(c, price_right_x, y, "Harga Satuan")
        self.draw_right_text(c, subtotal_right_x, y, "Subtotal")
        return y - 6 * mm

    def _draw_item_row(self, c, y, left, right, col_desc, col_qty, price_right_x, subtotal_right_x, desc_lines, qty_text, unit_text, unit_price, subtotal, kind=None):
        qty_lines = self.wrap_text(qty_text, max_chars=8, max_lines=1)
        unit_lines = self.wrap_text(f"Unit: {unit_text}", max_chars=34, max_lines=2) if unit_text else []
        row_h = self._item_row_height(len(desc_lines), len(unit_lines), has_kind=bool(kind))
        content_top = y
        if kind:
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Bold", 6.4)
            c.drawString(col_desc + 2 * mm, content_top, str(kind).upper())
            desc_y = content_top - 4.2 * mm
        else:
            desc_y = content_top

        c.setFillColor(DARK)
        c.setFont("Helvetica", 8.2)
        for line_idx, line in enumerate(desc_lines):
            c.setFont("Helvetica-Bold" if line_idx == 0 else "Helvetica", 8.2)
            c.drawString(col_desc + 2 * mm, desc_y, line)
            desc_y -= 3.6 * mm

        if unit_lines:
            desc_y -= 0.5 * mm
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 7)
            for line in unit_lines:
                c.drawString(col_desc + 2 * mm, desc_y, line)
                desc_y -= 3 * mm

        c.setFillColor(DARK)
        c.setFont("Helvetica", 8.2)
        qty_y = y
        for line in qty_lines:
            c.drawCentredString(col_qty, qty_y, line)
            qty_y -= 3.4 * mm
        self.draw_right_text(c, price_right_x, y, self.format_rupiah(unit_price))
        c.setFont("Helvetica-Bold", 8.2)
        self.draw_right_text(c, subtotal_right_x, y, self.format_rupiah(subtotal))

        next_y = y - row_h + 6
        c.setStrokeColor(LINE)
        c.setLineWidth(0.3)
        c.line(left, next_y - 2, right, next_y - 2)
        return next_y

    def _split_qty_unit(self, qty_text):
        parts = str(qty_text or "").split(maxsplit=1)
        if not parts:
            return "", ""
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    @staticmethod
    def _item_row_height(desc_line_count, unit_line_count=0, has_kind=False):
        height = 7 + (max(1, desc_line_count) * 3.6 * mm)
        if has_kind:
            height += 4.2 * mm
        if unit_line_count:
            height += 1.5 * mm + (unit_line_count * 3 * mm)
        return max(18.5 * mm if has_kind else 15.5 * mm, height)

    def _summary_block_height(self, rows):
        note_line_counts = [
            len(self.wrap_text(note, max_chars=34, max_lines=2)) if note else 0
            for _label, _value, note in rows
        ]
        return (len(rows) * 5.2 * mm) + (sum(note_line_counts) * 3.2 * mm) + 12 * mm

    def _draw_summary_block(self, c, y, left, right, rows, total_label, total_value):
        summary_w = min(72 * mm, right - left)
        x = right - summary_w
        content_h = self._summary_block_height(rows)
        c.setFillColor(SOFT_BG)
        c.setStrokeColor(colors.HexColor("#d8e1ea"))
        c.setLineWidth(0.35)
        c.roundRect(x, y - content_h, summary_w, content_h, 2 * mm, stroke=1, fill=1)

        row_y = y - 5.2 * mm
        value_right = right - 4 * mm
        value_left = x + 33 * mm
        value_max_chars = 25
        for label, value, note in rows:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 7.8)
            c.drawString(x + 4 * mm, row_y, label)
            c.setFillColor(DARK)
            c.setFont("Helvetica-Bold", 8)
            display_value = self.truncate(value, value_max_chars)
            self.draw_right_text(c, value_right, row_y, display_value)
            if str(label).lower().startswith("link pembayaran") and note:
                c.linkURL(str(note), (value_left, row_y - 1.2 * mm, value_right, row_y + 3.2 * mm), relative=0)
            row_y -= 4.4 * mm
            if note:
                c.setFillColor(MUTED)
                c.setFont("Helvetica", 6.8)
                note_lines = self.wrap_text(note, max_chars=34, max_lines=2)
                for line in note_lines:
                    note_text = self.truncate(line, 34)
                    c.drawString(x + 4 * mm, row_y, note_text)
                    if str(label).lower().startswith("link pembayaran"):
                        c.linkURL(str(note), (x + 4 * mm, row_y - 1.2 * mm, right - 4 * mm, row_y + 2.8 * mm), relative=0)
                    row_y -= 3.2 * mm

        total_h = 9 * mm
        c.setFillColor(GREEN)
        c.roundRect(x, y - content_h, summary_w, total_h, 2 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 4 * mm, y - content_h + 3.3 * mm, total_label)
        c.setFont("Helvetica-Bold", 11.5)
        self.draw_right_text(c, right - 4 * mm, y - content_h + 3.2 * mm, self.format_rupiah(total_value))
        return y - content_h

    def _ensure_page_space(self, c, y, needed_height, bottom_limit, invoice_number, clinic_name, top, left, right, header_callback):
        if y - needed_height >= bottom_limit:
            return y
        y = self._new_page(c, invoice_number, clinic_name, top, left, right)
        return header_callback(c, y)

    @staticmethod
    def _row_height(line_count):
        return max(22, 10 + (max(1, line_count) * 11) + 12)

    @staticmethod
    def _setting_value(settings, key, fallback=""):
        value = (settings or {}).get(key)
        if value is None:
            return fallback
        text = str(value).strip()
        return text or fallback

    @staticmethod
    def _clinic_name(settings):
        clinic_name = InvoiceHelper._setting_value(settings, "clinic_name", "Lancar Dynamic Admin")
        legacy_typo = "Lancar " + "Dina" + "mic Admin"
        if clinic_name == legacy_typo:
            return "Lancar Dynamic Admin"
        return clinic_name

    @staticmethod
    def _invoice_title(has_service=True, has_herbal=False):
        return "INVOICE / NOTA"

    @staticmethod
    def _invoice_category(has_service=True, has_herbal=False):
        if has_service and has_herbal:
            return "Layanan & Produk"
        if has_herbal:
            return "Produk / Herbal"
        return "Layanan"

    def _draw_invoice_badge(self, c, right, top, title, category="", width=40 * mm):
        title = str(title or "INVOICE / NOTA").strip()
        category = str(category or "").strip()
        badge_w = width
        badge_h = 12 * mm
        x = right - badge_w
        y = top - badge_h
        c.setFillColor(SOFT_GREEN)
        c.setStrokeColor(GREEN)
        c.setLineWidth(0.8)
        c.roundRect(x, y, badge_w, badge_h, 2 * mm, stroke=1, fill=1)
        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 8.8)
        c.drawCentredString(x + badge_w / 2, top - 5 * mm, title)
        if category:
            c.setFont("Helvetica", 6.8)
            c.drawCentredString(x + badge_w / 2, top - 8.8 * mm, category)

    def _draw_header(
        self,
        c,
        left,
        right,
        top,
        clinic_name,
        clinic_tagline,
        clinic_address,
        clinic_phone,
        clinic_email,
        clinic_website,
        clinic_logo_path,
        invoice_title,
        invoice_category,
    ):
        badge_w = 40 * mm
        self._draw_invoice_badge(c, right, top, invoice_title, invoice_category, width=badge_w)
        header_text_right = right - badge_w - 7 * mm

        y = top
        logo_offset = self._draw_logo(c, clinic_logo_path, left, y, max_h=16 * mm)
        header_x = left + logo_offset
        max_text_w = max(35 * mm, header_text_right - header_x)
        max_chars = max(24, int(max_text_w / (2.1 * mm)))

        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 12.8)
        for line in self.wrap_text(clinic_name, max_chars=max_chars, max_lines=2):
            c.drawString(header_x, y, line)
            y -= 4.8 * mm

        if clinic_tagline:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 7.2)
            c.drawString(header_x, y, self.truncate(clinic_tagline, max_chars + 6))
            y -= 3.6 * mm

        contact_lines = []
        if clinic_address:
            contact_lines.extend(self.wrap_text(clinic_address, max_chars=max_chars + 8, max_lines=2))
        contact_joined = " | ".join([value for value in [clinic_phone, clinic_email, clinic_website] if value])
        if contact_joined:
            contact_lines.extend(self.wrap_text(contact_joined, max_chars=max_chars + 8, max_lines=2))

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        for line in contact_lines[:4]:
            c.drawString(header_x, y, line)
            y -= 3.2 * mm

        header_bottom = min(y, top - 23 * mm)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.4)
        c.line(left, header_bottom, right, header_bottom)
        return header_bottom - 5 * mm

    def _draw_info_panel(self, c, y, left, right, items):
        item_lines = [
            self.wrap_text(value, max_chars=29 if idx % 2 == 0 else 27, max_lines=3)
            for idx, (_label, value) in enumerate(items[:4])
        ]
        top_row_lines = max(len(item_lines[0]), len(item_lines[1])) if len(item_lines) >= 2 else 1
        bottom_row_lines = max(len(item_lines[2]), len(item_lines[3])) if len(item_lines) >= 4 else 1
        top_row_h = 7.8 * mm + ((top_row_lines - 1) * 3.4 * mm)
        bottom_row_h = 7.8 * mm + ((bottom_row_lines - 1) * 3.4 * mm)
        panel_h = top_row_h + bottom_row_h + 5.5 * mm
        c.setFillColor(SOFT_BG)
        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.setLineWidth(0.35)
        c.roundRect(left, y - panel_h, right - left, panel_h, 2 * mm, stroke=1, fill=1)

        col_w = (right - left) / 2
        row_y = [y - 6.4 * mm, y - top_row_h - 5.8 * mm]
        for idx, (label, value) in enumerate(items[:4]):
            col = idx % 2
            row = idx // 2
            x = left + 4 * mm + (col * col_w)
            value_max_chars = 29 if col == 0 else 27
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 6.8)
            c.drawString(x, row_y[row] + 3 * mm, str(label))
            c.setFillColor(DARK)
            c.setFont("Helvetica-Bold", 8)
            for line_idx, line in enumerate(item_lines[idx]):
                c.drawString(x, row_y[row] - (line_idx * 3.4 * mm), line)

        c.setStrokeColor(colors.HexColor("#e2e8f0"))
        c.line(left + col_w, y - 3.5 * mm, left + col_w, y - panel_h + 3.5 * mm)
        c.line(left + 3 * mm, y - top_row_h - 0.9 * mm, right - 3 * mm, y - top_row_h - 0.9 * mm)
        return y - panel_h - 5 * mm

    @staticmethod
    def _signature_y(y, bottom):
        target = bottom + 38 * mm
        upper_limit = y - 14 * mm
        if upper_limit > target:
            return target
        return max(bottom + 32 * mm, upper_limit)

    def _draw_signature(self, c, center_x, line_y, line_width=34 * mm):
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        c.drawCentredString(center_x, line_y + 11 * mm, "Admin Klinik")
        c.setStrokeColor(LINE)
        half_width = line_width / 2
        c.line(center_x - half_width, line_y, center_x + half_width, line_y)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(center_x, line_y - 3.6 * mm, "Admin/Kasir")

    def _draw_signature_near_summary(self, c, center_x, summary_bottom, bottom):
        line_y = max(bottom + 42 * mm, summary_bottom + 18 * mm)
        self._draw_signature(c, center_x, line_y, line_width=32 * mm)

    def _draw_footer(self, c, left, right, bottom, footer_text=None):
        footer_y = bottom + 10 * mm
        c.setStrokeColor(LINE)
        c.line(left, footer_y + 9 * mm, right, footer_y + 9 * mm)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        lines = self.wrap_text(footer_text or "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah.", max_chars=76, max_lines=2)
        y = footer_y
        for line in lines:
            c.drawString(left, y, line)
            y -= 3.8 * mm
        c.drawString(left, y, "Invoice ini dibuat otomatis oleh sistem.")

    def generate_invoice(
        self,
        patient_name,
        date,
        points,
        price,
        therapist_name="--",
        custom_settings=None,
        discount_rule_name=None,
        service_name="Layanan Terapi",
        invoice_number=None,
        is_free_visit=False,
        free_visit_reason=None,
        unit_label=None,
        original_price=None,
        discount_amount=None,
        herbal_items=None,
        payment_method=None,
        payment_status=None,
        payment_provider=None,
        payment_reference=None,
        payment_url=None,
    ):
        custom_settings = custom_settings or {}
        clinic_name = self._clinic_name(custom_settings)
        clinic_tagline = self._setting_value(custom_settings, "clinic_tagline")
        clinic_address = self._setting_value(custom_settings, "clinic_address", "Kota Wisata")
        clinic_phone = self._setting_value(custom_settings, "clinic_phone")
        clinic_email = self._setting_value(custom_settings, "clinic_email")
        clinic_website = self._setting_value(custom_settings, "clinic_website")
        clinic_logo_path = self._setting_value(custom_settings, "clinic_logo_path")
        invoice_footer = self._setting_value(custom_settings, "invoice_footer", "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah.")
        raw_payment_provider = self._setting_value({"value": payment_provider}, "value", "manual")
        payment_method = self._payment_method_label(self._setting_value({"value": payment_method}, "value", "-"))
        payment_status = self._payment_status_label(self._setting_value({"value": payment_status}, "value", "Lunas"))
        payment_provider = self._payment_provider_label(raw_payment_provider)
        payment_reference = self._setting_value({"value": payment_reference}, "value", "")
        payment_url = self._pdf_payment_link(self._setting_value({"value": payment_url}, "value", ""))
        if str(raw_payment_provider).strip().lower() == "gateway_mock":
            payment_reference = ""
            payment_url = ""

        service_name = service_name or "Layanan Terapi"
        qty = max(1, int(points or 1))
        final_price = 0 if is_free_visit else max(0, float(price or 0))
        base_price = max(final_price, float(original_price if original_price is not None else final_price))
        discount_value = 0 if is_free_visit else max(0, float(discount_amount if discount_amount is not None else base_price - final_price))
        unit = unit_label or "layanan"
        unit_price = 0 if qty <= 0 else base_price / qty
        invoice_number = invoice_number or f"INV-{self.parse_date(date).strftime('%Y%m%d')}-00000"
        herbal_items = herbal_items or []
        herbal_total = sum(float(item.get("total_price") or 0) for item in herbal_items)
        grand_total = final_price + herbal_total
        invoice_title = self._invoice_title(has_service=True, has_herbal=bool(herbal_items))
        invoice_category = self._invoice_category(has_service=True, has_herbal=bool(herbal_items))

        safe_patient = self.safe_filename(patient_name)
        safe_invoice = self.safe_filename(invoice_number, fallback="Invoice")
        filename = f"{safe_invoice}_{safe_patient}.pdf"
        filepath = self._safe_output_path(filename)

        c = canvas.Canvas(filepath, pagesize=A5)
        width, height = A5
        left = 14 * mm
        right = width - 14 * mm
        top = height - 8 * mm
        bottom = 8 * mm
        item_bottom_limit = bottom + 24 * mm

        c.setTitle(invoice_number)
        c.setAuthor(clinic_name)

        y = self._draw_header(
            c,
            left,
            right,
            top,
            clinic_name,
            clinic_tagline,
            clinic_address,
            clinic_phone,
            clinic_email,
            clinic_website,
            clinic_logo_path,
            invoice_title,
            invoice_category,
        )

        y = self._draw_info_panel(
            c,
            y,
            left,
            right,
            [
                ("No Invoice", invoice_number),
                ("Nama Pasien", patient_name or "Pasien"),
                ("Tanggal", self.format_date(date)),
                ("Terapis", therapist_name or "--"),
            ],
        )

        if is_free_visit:
            c.setStrokeColor(GREEN)
            c.setLineWidth(0.6)
            c.roundRect(left, y - 9 * mm, right - left, 8 * mm, 1.8 * mm, stroke=1, fill=0)
            c.setFillColor(GREEN)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(left + 3 * mm, y - 6.2 * mm, "KUNJUNGAN GRATIS")
            if free_visit_reason:
                c.setFillColor(DARK)
                c.setFont("Helvetica", 8)
                c.drawRightString(right - 3 * mm, y - 6.2 * mm, "Alasan: " + self.truncate(free_visit_reason, 52))
            y -= 13 * mm

        # Detail table
        table_x = left
        col_desc = table_x
        col_qty = left + 64 * mm
        price_right_x = right - 28 * mm
        subtotal_right_x = right

        service_header = lambda page_canvas, page_y: self._draw_service_table_header(
            page_canvas, page_y, table_x, right, col_desc, col_qty, price_right_x, subtotal_right_x
        )
        y = service_header(c, y)

        desc_lines = self.wrap_text(service_name, max_chars=35, max_lines=4)
        y = self._ensure_page_space(
            c,
            y,
            self._item_row_height(len(desc_lines), len(self.wrap_text(f"Unit: {unit}", max_chars=34, max_lines=2)), has_kind=True),
            item_bottom_limit,
            invoice_number,
            clinic_name,
            top,
            left,
            right,
            service_header,
        )
        y = self._draw_item_row(
            c,
            y,
            table_x,
            right,
            col_desc,
            col_qty,
            price_right_x,
            subtotal_right_x,
            desc_lines,
            str(qty),
            unit,
            unit_price,
            final_price,
            kind="Layanan",
        )

        for item in herbal_items:
            item_name = item.get("name") or "Produk / Herbal"
            desc_lines = self.wrap_text(item_name, max_chars=35, max_lines=3)
            y = self._ensure_page_space(
                c,
                y,
                self._item_row_height(
                    len(desc_lines),
                    len(self.wrap_text(f"Unit: {item.get('unit') or ''}", max_chars=34, max_lines=2)) if item.get("unit") else 0,
                    has_kind=True,
                ),
                item_bottom_limit,
                invoice_number,
                clinic_name,
                top,
                left,
                right,
                service_header,
            )
            item_qty = max(1, int(item.get("quantity") or 1))
            item_unit = item.get("unit") or ""
            item_total = float(item.get("total_price") or 0)
            item_unit_price = float(item.get("unit_price") or (item_total / item_qty if item_qty else 0))
            y = self._draw_item_row(
                c,
                y,
                table_x,
                right,
                col_desc,
                col_qty,
                price_right_x,
                subtotal_right_x,
                desc_lines,
                str(item_qty),
                item_unit,
                item_unit_price,
                item_total,
                kind="Produk / Herbal",
            )

        y -= 7

        # Payment summary
        discount_display = "-" if is_free_visit or not discount_value else f"- {self.format_rupiah(discount_value)}"
        summary_rows_data = [
            ("Status Pembayaran", payment_status, None),
            ("Metode Pembayaran", payment_method, None),
            ("Provider Pembayaran", payment_provider, None),
        ]
        if payment_reference:
            summary_rows_data.append(("Referensi Pembayaran", self.truncate(payment_reference, 28), None))
        if payment_url:
            summary_rows_data.append(("Link Pembayaran", "Buka link", payment_url))
        summary_rows_data.extend([
            ("Subtotal Layanan", self.format_rupiah(base_price), None),
            ("Diskon", discount_display, discount_rule_name if discount_value and discount_rule_name and not is_free_visit else None),
        ])
        if herbal_total:
            summary_rows_data.append(("Subtotal Produk/Herbal", self.format_rupiah(herbal_total), None))
        summary_height = self._summary_block_height(summary_rows_data)
        if y - summary_height < bottom + 18 * mm:
            y = self._new_page(c, invoice_number, clinic_name, top, left, right)
        y = self._draw_summary_block(c, y, left, right, summary_rows_data, "Grand Total", grand_total)

        # Footer and signature
        self._draw_signature_near_summary(c, left + 30 * mm, y, bottom)

        self._draw_footer(c, left, right, bottom, invoice_footer)

        c.save()
        return filepath

    def generate_herbal_invoice(
        self,
        buyer_name,
        date,
        items,
        total,
        custom_settings=None,
        invoice_number=None,
        note=None,
        payment_method=None,
        payment_status=None,
        payment_provider=None,
        payment_reference=None,
        payment_url=None,
    ):
        custom_settings = custom_settings or {}
        clinic_name = self._clinic_name(custom_settings)
        clinic_tagline = self._setting_value(custom_settings, "clinic_tagline")
        clinic_address = self._setting_value(custom_settings, "clinic_address", "Kota Wisata")
        clinic_phone = self._setting_value(custom_settings, "clinic_phone")
        clinic_email = self._setting_value(custom_settings, "clinic_email")
        clinic_website = self._setting_value(custom_settings, "clinic_website")
        clinic_logo_path = self._setting_value(custom_settings, "clinic_logo_path")
        invoice_footer = self._setting_value(custom_settings, "invoice_footer", "Semoga menjadi wasilah ikhtiar kesembuhan yang berkah.")
        raw_payment_provider = self._setting_value({"value": payment_provider}, "value", "manual")
        payment_method = self._payment_method_label(self._setting_value({"value": payment_method}, "value", "-"))
        payment_status = self._payment_status_label(self._setting_value({"value": payment_status}, "value", "Lunas"))
        payment_provider = self._payment_provider_label(raw_payment_provider)
        payment_reference = self._setting_value({"value": payment_reference}, "value", "")
        payment_url = self._pdf_payment_link(self._setting_value({"value": payment_url}, "value", ""))
        if str(raw_payment_provider).strip().lower() == "gateway_mock":
            payment_reference = ""
            payment_url = ""

        buyer_name = buyer_name or "Umum"
        dt = self.parse_date(date)
        invoice_number = invoice_number or f"HBL-{dt.strftime('%Y%m%d')}-00000"
        total = float(total or 0)
        items = items or []
        invoice_title = self._invoice_title(has_service=False, has_herbal=True)
        invoice_category = self._invoice_category(has_service=False, has_herbal=True)

        safe_buyer = self.safe_filename(buyer_name, fallback="Pembeli")
        safe_invoice = self.safe_filename(invoice_number, fallback="Invoice_Herbal")
        filepath = self._safe_output_path(f"{safe_invoice}_{safe_buyer}.pdf")

        c = canvas.Canvas(filepath, pagesize=A5, pageCompression=0)
        width, height = A5
        left = 14 * mm
        right = width - 14 * mm
        top = height - 8 * mm
        bottom = 8 * mm
        item_bottom_limit = bottom + 24 * mm

        c.setTitle(invoice_number)
        c.setAuthor(clinic_name)

        y = self._draw_header(
            c,
            left,
            right,
            top,
            clinic_name,
            clinic_tagline,
            clinic_address,
            clinic_phone,
            clinic_email,
            clinic_website,
            clinic_logo_path,
            invoice_title,
            invoice_category,
        )

        y = self._draw_info_panel(
            c,
            y,
            left,
            right,
            [
                ("No Invoice", invoice_number),
                ("Pembeli", buyer_name),
                ("Tanggal", self.format_date(dt)),
                ("Jenis", "Penjualan Produk / Herbal"),
            ],
        )

        table_x = left
        col_no = table_x + 1 * mm
        col_desc = left + 9 * mm
        col_qty = left + 64 * mm
        price_right_x = right - 28 * mm
        subtotal_right_x = right

        herbal_header = lambda page_canvas, page_y: self._draw_herbal_table_header(
            page_canvas, page_y, table_x, right, col_no, col_desc, col_qty, price_right_x, subtotal_right_x
        )
        y = herbal_header(c, y)

        for idx, item in enumerate(items, start=1):
            item_qty = max(1, int(item.get("quantity") or 1))
            item_unit = item.get("unit") or ""
            item_total = float(item.get("total_price") or 0)
            item_unit_price = float(item.get("unit_price") or (item_total / item_qty if item_qty else 0))
            desc_lines = self.wrap_text(item.get("name") or "Produk / Herbal", max_chars=32, max_lines=4)
            y = self._ensure_page_space(
                c,
                y,
                self._item_row_height(
                    len(desc_lines),
                    len(self.wrap_text(f"Unit: {item.get('unit') or ''}", max_chars=34, max_lines=2)) if item.get("unit") else 0,
                    has_kind=False,
                ),
                item_bottom_limit,
                invoice_number,
                clinic_name,
                top,
                left,
                right,
                herbal_header,
            )
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 8)
            c.drawString(col_no, y, str(idx))
            y = self._draw_item_row(
                c,
                y,
                table_x,
                right,
                col_desc - 2 * mm,
                col_qty,
                price_right_x,
                subtotal_right_x,
                desc_lines,
                str(item_qty),
                item_unit,
                item_unit_price,
                item_total,
            )

        if note:
            if y - 18 * mm < item_bottom_limit:
                y = self._new_page(c, invoice_number, clinic_name, top, left, right)
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 8)
            for line in self.wrap_text(note, max_chars=72, max_lines=2):
                c.drawString(left, y, line)
                y -= 4 * mm
            y -= 2 * mm

        summary_rows_data = [
            ("Status Pembayaran", payment_status, None),
            ("Metode Pembayaran", payment_method, None),
            ("Provider Pembayaran", payment_provider, None),
        ]
        if payment_reference:
            summary_rows_data.append(("Referensi Pembayaran", self.truncate(payment_reference, 28), None))
        if payment_url:
            summary_rows_data.append(("Link Pembayaran", "Buka link", payment_url))
        summary_rows_data.append(("Subtotal Produk/Herbal", self.format_rupiah(total), None))
        summary_height = self._summary_block_height(summary_rows_data)
        if y - summary_height < bottom + 18 * mm:
            y = self._new_page(c, invoice_number, clinic_name, top, left, right)
        y = self._draw_summary_block(
            c,
            y,
            left,
            right,
            summary_rows_data,
            "Grand Total",
            total,
        )

        self._draw_signature_near_summary(c, left + 30 * mm, y, bottom)

        self._draw_footer(c, left, right, bottom, invoice_footer)

        c.save()
        return filepath
