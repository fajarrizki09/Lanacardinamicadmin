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
        self.resize(1000, 800)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ---- HEADER / FILTER ----
        filter_card = QGroupBox("Filter Periode")
        filter_card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)

        self.date_start = QDateEdit(calendarPopup=True)
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setFixedWidth(130)
        self.date_start.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")

        self.date_end = QDateEdit(calendarPopup=True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setFixedWidth(130)
        self.date_end.setStyleSheet("padding: 5px; border: 1px solid #ced4da; border-radius: 4px;")

        self.btn_apply = QPushButton("🔍 Terapkan Filter")
        self.btn_apply.setFixedWidth(150)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)

        filter_layout.addWidget(QLabel("📅 Dari:"))
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(QLabel("📅 Sampai:"))
        filter_layout.addWidget(self.date_end)
        filter_layout.addSpacing(10)
        filter_layout.addWidget(self.btn_apply)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # ---- SUMMARY CARDS ----
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        def create_stat_card(title, color):
            card = QGroupBox()
            card.setStyleSheet(f"""
                QGroupBox {{
                    background-color: {color};
                    border-radius: 10px;
                    border: none;
                }}
            """)
            c_layout = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
            v_lbl = QLabel("0")
            v_lbl.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
            c_layout.addWidget(t_lbl)
            c_layout.addWidget(v_lbl)
            return card, v_lbl

        self.card_patients, self.val_patients = create_stat_card("TOTAL PASIEN", "#34495e")
        self.card_visits, self.val_visits = create_stat_card("TOTAL KUNJUNGAN", "#3498db")
        self.card_income, self.val_income = create_stat_card("TOTAL PEMASUKAN", "#2ecc71")

        stats_layout.addWidget(self.card_patients)
        stats_layout.addWidget(self.card_visits)
        stats_layout.addWidget(self.card_income)
        layout.addLayout(stats_layout)

        # ---- CHARTS ----
        charts_container = QHBoxLayout()
        
        # Left Chart
        left_box = QGroupBox("📈 Tren Kunjungan")
        left_box.setStyleSheet("font-weight: bold; background-color: white; border: 1px solid #dcdde1; border-radius: 8px;")
        left_layout = QVBoxLayout(left_box)
        self.canvas_visits = FigureCanvas(Figure(figsize=(5, 4), dpi=100))
        left_layout.addWidget(self.canvas_visits)
        self.ax_visits = self.canvas_visits.figure.add_subplot(111)
        charts_container.addWidget(left_box)

        # Right Chart
        right_box = QGroupBox("💰 Tren Pemasukan")
        right_box.setStyleSheet("font-weight: bold; background-color: white; border: 1px solid #dcdde1; border-radius: 8px;")
        right_layout = QVBoxLayout(right_box)
        self.canvas_income = FigureCanvas(Figure(figsize=(5, 4), dpi=100))
        right_layout.addWidget(self.canvas_income)
        self.ax_income = self.canvas_income.figure.add_subplot(111)
        charts_container.addWidget(right_box)

        layout.addLayout(charts_container)

        self.btn_apply.clicked.connect(self.refresh_data)
        self.refresh_data()

    def format_rupiah(self, amount):
        return f"Rp {amount:,.0f}".replace(",", ".")

    def refresh_data(self):
        start_date = self.date_start.date().toPython()
        end_date = self.date_end.date().toPython()
        
        visits = self.db.get_all_visits()
        patients = self.db.get_patients()

        filtered_visits = []
        for v in visits:
            dt = v["date"]
            if isinstance(dt, str):
                try: dt = datetime.fromisoformat(dt)
                except: continue
            if start_date <= dt.date() <= end_date:
                filtered_visits.append({**v, "date": dt})

        self.val_patients.setText(str(len(patients)))
        self.val_visits.setText(str(len(filtered_visits)))
        self.val_income.setText(self.format_rupiah(sum(v["price"] for v in filtered_visits)))

        visits_per_month = defaultdict(int)
        income_per_month = defaultdict(int)

        for v in filtered_visits:
            key = v["date"].strftime("%Y-%m")
            visits_per_month[key] += 1
            income_per_month[key] += v["price"]

        self.plot_visits(visits_per_month)
        self.plot_income(income_per_month)

    def plot_visits(self, data):
        ax = self.ax_visits
        ax.clear()
        if not data: 
            self.canvas_visits.draw()
            return
            
        months = sorted(data.keys())
        values = [data[m] for m in months]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months]

        bars = ax.bar(labels, values, color="#3498db", alpha=0.7)
        ax.set_title("Kunjungan per Bulan", fontsize=10, pad=10)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}', ha='center', va='bottom', fontsize=8)
            
        self.canvas_visits.figure.tight_layout()
        self.canvas_visits.draw()

    def plot_income(self, data):
        ax = self.ax_income
        ax.clear()
        if not data:
            self.canvas_income.draw()
            return

        months = sorted(data.keys())
        values = [data[m] for m in months]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months]

        ax.plot(labels, values, marker='o', color="#2ecc71", linewidth=2, markersize=6)
        ax.fill_between(labels, values, color="#2ecc71", alpha=0.1)
        ax.set_title("Pemasukan per Bulan", fontsize=10, pad=10)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        self.canvas_income.figure.tight_layout()
        self.canvas_income.draw()
