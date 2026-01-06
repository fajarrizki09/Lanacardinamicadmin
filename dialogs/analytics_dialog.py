from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QMessageBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from collections import defaultdict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QMessageBox, QGridLayout, QSizePolicy, QGroupBox, QScrollArea, QWidget, QFrame
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
        self.resize(1100, 850)
        self.db = db

        # Main Layout for the Dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area for flexibility
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background-color: #f5f6fa;")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # ---- HEADER / FILTER ----
        filter_card = QGroupBox("Filter Periode")
        filter_card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdde1;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 15, 20, 15)
        filter_layout.setSpacing(15)

        self.date_start = QDateEdit(calendarPopup=True)
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setFixedWidth(140)
        self.date_start.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 6px;")

        self.date_end = QDateEdit(calendarPopup=True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setFixedWidth(140)
        self.date_end.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 6px;")

        self.btn_apply = QPushButton("🔍 Terapkan Filter")
        self.btn_apply.setFixedWidth(180)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)

        filter_layout.addWidget(QLabel("📅 Dari:"))
        filter_layout.addWidget(self.date_start)
        filter_layout.addWidget(QLabel("📅 Sampai:"))
        filter_layout.addWidget(self.date_end)
        filter_layout.addSpacing(20)
        filter_layout.addWidget(self.btn_apply)
        filter_layout.addStretch()

        layout.addWidget(filter_card)

        # ---- SUMMARY CARDS ----
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        def create_stat_card(title, color, icon=""):
            card = QFrame()
            card.setMinimumHeight(130)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {color}, stop:1 {color}CC);
                    border-radius: 12px;
                    border-bottom: 4px solid rgba(0,0,0,0.1);
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(20, 15, 20, 15)
            
            header = QHBoxLayout()
            t_lbl = QLabel(f"{icon} {title}")
            t_lbl.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px; font-weight: bold; text-transform: uppercase;")
            header.addWidget(t_lbl)
            header.addStretch()
            
            v_lbl = QLabel("0")
            v_lbl.setStyleSheet("color: white; font-size: 32px; font-weight: bold; margin-top: 5px;")
            
            footer_lbl = QLabel("vs bulan lalu")
            footer_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 11px;")
            
            c_layout.addLayout(header)
            c_layout.addWidget(v_lbl)
            c_layout.addWidget(footer_lbl)
            c_layout.addStretch()
            return card, v_lbl, footer_lbl

        self.card_patients, self.val_patients, self.foot_patients = create_stat_card("Total Pasien", "#2c3e50", "👥")
        self.card_visits, self.val_visits, self.foot_visits = create_stat_card("Total Kunjungan", "#2980b9", "🩺")
        self.card_income, self.val_income, self.foot_income = create_stat_card("Total Pemasukan", "#27ae60", "💰")
        self.card_avg, self.val_avg, self.foot_avg = create_stat_card("Rata-rata/Visit", "#8e44ad", "📈")
        self.card_stock_alert, self.val_stock_alert, self.foot_stock_alert = create_stat_card("Stok Menipis", "#e67e22", "⚠️")

        stats_layout.addWidget(self.card_patients)
        stats_layout.addWidget(self.card_visits)
        stats_layout.addWidget(self.card_income)
        stats_layout.addWidget(self.card_avg)
        stats_layout.addWidget(self.card_stock_alert)
        layout.addLayout(stats_layout)

        # ---- CHARTS CONTAINER ----
        charts_container = QHBoxLayout()
        charts_container.setSpacing(20)
        
        # Left Chart (Visits)
        left_box = QGroupBox("📈 Tren Kunjungan")
        left_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_box.setMinimumHeight(450)
        left_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(10, 15, 10, 10)
        self.canvas_visits = FigureCanvas(Figure(figsize=(5, 4), dpi=100))
        left_layout.addWidget(self.canvas_visits)
        self.ax_visits = self.canvas_visits.figure.add_subplot(111)
        charts_container.addWidget(left_box)

        # Right Chart (Income)
        right_box = QGroupBox("💰 Tren Pemasukan")
        right_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_box.setMinimumHeight(450)
        right_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(10, 15, 10, 10)
        self.canvas_income = FigureCanvas(Figure(figsize=(5, 4), dpi=100))
        right_layout.addWidget(self.canvas_income)
        self.ax_income = self.canvas_income.figure.add_subplot(111)
        charts_container.addWidget(right_box)

        layout.addLayout(charts_container)
        
        # --- INVENTORY CHART ---
        inv_box = QGroupBox("📦 Status Stok Inventori")
        inv_box.setMinimumHeight(400)
        inv_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)
        inv_layout = QVBoxLayout(inv_box)
        self.canvas_inventory = FigureCanvas(Figure(figsize=(10, 4), dpi=100))
        inv_layout.addWidget(self.canvas_inventory)
        self.ax_inventory = self.canvas_inventory.figure.add_subplot(111)
        layout.addWidget(inv_box)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

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
        total_income = sum(v["price"] for v in filtered_visits)
        self.val_income.setText(self.format_rupiah(total_income))
        
        avg_income = total_income / len(filtered_visits) if filtered_visits else 0
        self.val_avg.setText(self.format_rupiah(avg_income))

        # Inventory & Herbal Data
        inventory = self.db.get_all_inventory()
        herbals = self.db.get_all_herbals()
        
        low_stock_count = 0
        for item in inventory:
            if item["quantity"] <= item["min_stock"]:
                low_stock_count += 1
        for h in herbals:
            if h["stock"] <= 5: # Default threshold for herbals
                low_stock_count += 1
        
        self.val_stock_alert.setText(str(low_stock_count))
        self.foot_stock_alert.setText("Alat & Herbal")

        visits_per_month = defaultdict(int)
        income_per_month = defaultdict(int)

        for v in filtered_visits:
            key = v["date"].strftime("%Y-%m")
            visits_per_month[key] += 1
            income_per_month[key] += v["price"]

        self.plot_visits(visits_per_month)
        self.plot_income(income_per_month)
        self.plot_inventory(inventory)

    def plot_inventory(self, data):
        ax = self.ax_inventory
        ax.clear()
        if not data:
            self.canvas_inventory.draw()
            return
            
        # Show top 10 items or items with low stock
        items = sorted(data, key=lambda x: x["quantity"])[:10]
        names = [i["item_name"][:15] for i in items]
        qtys = [i["quantity"] for i in items]
        mins = [i["min_stock"] for i in items]
        
        x = range(len(names))
        ax.bar(x, qtys, width=0.4, label="Stok Saat Ini", color="#3498db", alpha=0.7)
        ax.bar([i + 0.4 for i in x], mins, width=0.4, label="Batas Minimum", color="#e74c3c", alpha=0.7)
        
        ax.set_xticks([i + 0.2 for i in x])
        ax.set_xticklabels(names, rotation=15, fontsize=9)
        ax.set_title("Perbandingan Stok vs Minimum (Top 10 Item Terendah)", fontsize=11, fontweight='bold', pad=15)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        self.canvas_inventory.figure.tight_layout()
        self.canvas_inventory.draw()

    def plot_visits(self, data):
        ax = self.ax_visits
        ax.clear()
        if not data: 
            self.canvas_visits.draw()
            return
            
        months = sorted(data.keys())
        values = [data[m] for m in months]
        labels = [datetime.strptime(m, "%Y-%m").strftime("%b %y") for m in months]

        bars = ax.bar(labels, values, color="#3498db", alpha=0.7, width=0.6, edgecolor="#2980b9", linewidth=1)
        ax.set_title("Volume Kunjungan Pasien", fontsize=12, fontweight='bold', pad=20, color="#34495e")
        ax.grid(axis='y', linestyle=':', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        ax.tick_params(axis='x', rotation=0, labelsize=9, colors="#7f8c8d")
        ax.tick_params(axis='y', labelsize=9, colors="#7f8c8d")
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{int(height)}', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold', color="#2980b9")
            
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

        ax.plot(labels, values, marker='o', color="#27ae60", linewidth=3, markersize=10, 
                markerfacecolor='white', markeredgewidth=3, markeredgecolor="#27ae60",
                label="Pemasukan")
        ax.fill_between(labels, values, color="#2ecc71", alpha=0.1)
        
        ax.set_title("Performa Pendapatan", fontsize=12, fontweight='bold', pad=20, color="#34495e")
        ax.grid(axis='y', linestyle=':', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bdc3c7')
        ax.spines['bottom'].set_color('#bdc3c7')
        ax.tick_params(axis='x', rotation=0, labelsize=9, colors="#7f8c8d")
        ax.tick_params(axis='y', labelsize=9, colors="#7f8c8d")

        def format_k(x, pos):
            if x >= 1_000_000: return f'{x/1_000_000:.1f}M'
            if x >= 1_000: return f'{x/1_000:.0f}K'
            return str(x)
            
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(format_k))

        self.canvas_income.figure.tight_layout()
        self.canvas_income.draw()
