from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QMessageBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from collections import defaultdict

class AnalyticsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Analitik Kunjungan & Pemasukan")
        self.resize(900, 700)
        self.db = db

        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self.date_start = QDateEdit(calendarPopup=True)
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setFixedWidth(120)

        self.date_end = QDateEdit(calendarPopup=True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setFixedWidth(120)

        self.btn_apply = QPushButton("Terapkan Filter")
        self.btn_apply.setFixedWidth(140)

        filter_layout.addWidget(QLabel("Dari:"))
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(QLabel("Sampai:"))
        filter_layout.addWidget(self.date_end)
        filter_layout.addWidget(self.btn_apply)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        stats_layout = QGridLayout()
        font_style = "font-size: 16px; font-weight: bold;"
        self.total_patients_label = QLabel()
        self.total_visits_label = QLabel()
        self.total_income_label = QLabel()
        for i, lbl in enumerate([self.total_patients_label, self.total_visits_label, self.total_income_label]):
            lbl.setStyleSheet(font_style)
            stats_layout.addWidget(lbl, i // 2, i % 2)
        layout.addLayout(stats_layout)

        layout.addWidget(QLabel("📈 Grafik Jumlah Kunjungan per Bulan"))
        self.canvas_visits = FigureCanvas(Figure(figsize=(8, 4)))
        layout.addWidget(self.canvas_visits)
        self.ax_visits = self.canvas_visits.figure.add_subplot(111)

        layout.addWidget(QLabel("💰 Grafik Total Pemasukan per Bulan"))
        self.canvas_income = FigureCanvas(Figure(figsize=(8, 4)))
        layout.addWidget(self.canvas_income)
        self.ax_income = self.canvas_income.figure.add_subplot(111)

        self.btn_apply.clicked.connect(self.refresh_data)
        self.refresh_data()

    def format_rupiah(self, amount):
        return f"Rp {amount:,.0f}".replace(",", ".")

    def refresh_data(self):
        start_date = self.date_start.date().toPython()
        end_date = self.date_end.date().toPython()
        if start_date > end_date:
            QMessageBox.warning(self, "Filter Salah", "Tanggal mulai harus sebelum tanggal selesai.")
            return

        visits = self.db.get_all_visits()
        patients = self.db.get_patients()

        filtered_visits = []
        for v in visits:
            dt = v["date"]
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except:
                    continue
            if not isinstance(dt, datetime):
                continue
            if start_date <= dt.date() <= end_date:
                filtered_visits.append({**v, "date": dt})

        total_patients = len(patients)
        total_visits = len(filtered_visits)
        total_income = sum(v["price"] for v in filtered_visits)

        self.total_patients_label.setText(f"👥 Total Pasien: {total_patients}")
        self.total_visits_label.setText(f"🩺 Total Kunjungan: {total_visits}")
        self.total_income_label.setText(f"💵 Total Pemasukan: {self.format_rupiah(total_income)}")

        visits_per_month = defaultdict(int)
        income_per_month = defaultdict(int)

        for v in filtered_visits:
            key = v["date"].strftime("%Y-%m")
            visits_per_month[key] += 1
            income_per_month[key] += v["price"]

        self.plot_visits(visits_per_month)
        self.plot_income(income_per_month)

    def plot_visits(self, visits_per_month):
        ax = self.ax_visits
        ax.clear()

        months = sorted(visits_per_month.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))
        values = [visits_per_month[m] for m in months]

        months_filtered = []
        values_filtered = []
        for m, v in zip(months, values):
            if v > 0:
                months_filtered.append(m)
                values_filtered.append(v)

        if months_filtered:
            ax.bar(range(len(months_filtered)), values_filtered, color="#3A86FF", width=0.6)
            ax.set_xlim(-0.5, len(months_filtered) - 0.5)

            ax.set_title("Jumlah Kunjungan per Bulan")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Jumlah")
            ax.set_xticks(range(len(months_filtered)))
            ax.set_xticklabels([datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months_filtered], rotation=45)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            ax.set_facecolor("#f9f9f9")

            max_val = max(values_filtered)
            for i, val in enumerate(values_filtered):
                ax.text(i, val + 0.05 * max_val, str(val), ha='center', va='bottom', fontsize=9)

        self.canvas_visits.figure.subplots_adjust(bottom=0.25, left=0.1, right=0.95)
        self.canvas_visits.draw()

    def plot_income(self, income_per_month):
        ax = self.ax_income
        ax.clear()

        months = sorted(income_per_month.keys(), key=lambda x: datetime.strptime(x, "%Y-%m"))
        values = [income_per_month[m] for m in months]

        months_filtered = []
        values_filtered = []
        for m, v in zip(months, values):
            if v > 0:
                months_filtered.append(m)
                values_filtered.append(v)

        if months_filtered:
            ax.bar(range(len(months_filtered)), values_filtered, color="#2ECC71", width=0.6)
            ax.set_xlim(-0.5, len(months_filtered) - 0.5)

            ax.set_title("Total Pemasukan per Bulan")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Rupiah")
            ax.set_xticks(range(len(months_filtered)))
            ax.set_xticklabels([datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months_filtered], rotation=45)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            ax.set_facecolor("#f9f9f9")

            def format_rupiah_singkat(amount):
                if amount >= 1_000_000_000:
                    return f"Rp {amount/1_000_000_000:.1f}M"
                elif amount >= 1_000_000:
                    return f"Rp {amount/1_000_000:.1f}Jt"
                elif amount >= 1_000:
                    return f"Rp {amount/1_000:.0f}Rb"
                else:
                    return f"Rp {amount}"

            max_val = max(values_filtered)
            for i, val in enumerate(values_filtered):
                ax.text(i, val + 0.05 * max_val, format_rupiah_singkat(val), ha='center', va='bottom', fontsize=8)

        self.canvas_income.figure.subplots_adjust(bottom=0.25, left=0.1, right=0.95)
        self.canvas_income.draw()
