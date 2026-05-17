from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QMessageBox, QGridLayout, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from collections import defaultdict
from viewmodels.analytics_view_model import AnalyticsViewModel

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDateEdit, QMessageBox, QGridLayout, QSizePolicy, QGroupBox, QScrollArea, QWidget, QFrame, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from collections import defaultdict

class AnalyticsDialog(QDialog):
    def __init__(self, analytics_source, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Analitik Kunjungan & Pemasukan")
        self.resize(1100, 850)
        if isinstance(analytics_source, AnalyticsViewModel):
            self.analytics_vm = analytics_source
        else:
            # Kompatibilitas constructor lama: AnalyticsDialog(db, parent)
            self.analytics_vm = AnalyticsViewModel(analytics_source)

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

        self.period_filter = QComboBox()
        self.period_filter.addItem("7 Hari", "7d")
        self.period_filter.addItem("30 Hari", "30d")
        self.period_filter.addItem("6 Bulan", "6m")
        self.period_filter.addItem("1 Tahun", "1y")
        self.period_filter.addItem("Semua", "all")
        self.period_filter.setCurrentIndex(2)
        self.period_filter.setFixedWidth(140)
        self.period_filter.setStyleSheet("padding: 8px; border: 1px solid #ced4da; border-radius: 6px;")

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

        filter_layout.addWidget(QLabel("Periode:"))
        filter_layout.addWidget(self.period_filter)
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
        self.card_visits, self.val_visits, self.foot_visits = create_stat_card("Total Transaksi", "#2980b9", "🩺")
        self.card_income, self.val_income, self.foot_income = create_stat_card("Total Pemasukan", "#27ae60", "💰")
        self.card_avg, self.val_avg, self.foot_avg = create_stat_card("Rata-rata/Transaksi", "#8e44ad", "📈")
        self.card_stock_alert, self.val_stock_alert, self.foot_stock_alert = create_stat_card("Stok Menipis", "#e67e22", "⚠️")

        stats_layout.addWidget(self.card_patients)
        stats_layout.addWidget(self.card_visits)
        stats_layout.addWidget(self.card_income)
        stats_layout.addWidget(self.card_avg)
        stats_layout.addWidget(self.card_stock_alert)
        layout.addLayout(stats_layout)

        profit_box = QGroupBox("Neraca Laba Rugi")
        profit_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)
        profit_layout = QGridLayout(profit_box)
        profit_layout.setContentsMargins(20, 18, 20, 18)
        profit_layout.setHorizontalSpacing(24)
        profit_layout.setVerticalSpacing(10)

        self.operational_expense_input = QDoubleSpinBox()
        self.operational_expense_input.setRange(0, 1000000000)
        self.operational_expense_input.setPrefix("Rp ")
        self.operational_expense_input.setGroupSeparatorShown(True)
        self.operational_expense_input.setDecimals(0)
        self.operational_expense_input.valueChanged.connect(self.refresh_profit_labels)

        self.val_service_income = QLabel("Rp 0")
        self.val_herbal_income = QLabel("Rp 0")
        self.val_herbal_cogs = QLabel("Rp 0")
        self.val_gross_profit = QLabel("Rp 0")
        self.val_net_profit = QLabel("Rp 0")
        for label in [
            self.val_service_income, self.val_herbal_income, self.val_herbal_cogs,
            self.val_gross_profit, self.val_net_profit,
        ]:
            label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")

        profit_layout.addWidget(QLabel("Pendapatan Layanan:"), 0, 0)
        profit_layout.addWidget(self.val_service_income, 0, 1)
        profit_layout.addWidget(QLabel("Penjualan Herbal:"), 0, 2)
        profit_layout.addWidget(self.val_herbal_income, 0, 3)
        profit_layout.addWidget(QLabel("HPP Herbal:"), 1, 0)
        profit_layout.addWidget(self.val_herbal_cogs, 1, 1)
        profit_layout.addWidget(QLabel("Laba Kotor:"), 1, 2)
        profit_layout.addWidget(self.val_gross_profit, 1, 3)
        profit_layout.addWidget(QLabel("Biaya Operasional:"), 2, 0)
        profit_layout.addWidget(self.operational_expense_input, 2, 1)
        profit_layout.addWidget(QLabel("Laba Bersih:"), 2, 2)
        profit_layout.addWidget(self.val_net_profit, 2, 3)
        layout.addWidget(profit_box)

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
        self.period_filter.currentIndexChanged.connect(self.refresh_data)
        self.current_profit_data = {}
        self.refresh_data()

    def format_rupiah(self, amount):
        return f"Rp {amount:,.0f}".replace(",", ".")

    def refresh_data(self):
        data = self.analytics_vm.get_analytics_data(self.period_filter.currentData())
        self.current_profit_data = data

        self.val_patients.setText(str(data["total_patients"]))
        self.val_visits.setText(str(data.get("total_transactions", data["total_visits"])))
        total_income = data["total_income"]
        self.val_income.setText(self.format_rupiah(total_income))

        self.val_avg.setText(self.format_rupiah(data["avg_income"]))

        stock_data = self.analytics_vm.get_inventory_status()
        inventory = stock_data["inventory"]

        self.val_stock_alert.setText(str(stock_data["low_stock_count"]))
        self.foot_stock_alert.setText("Alat & Herbal")

        visits_per_month = {
            label: value for label, value in zip(data["monthly_labels"], data["monthly_visits"])
        }
        income_per_month = {
            label: value for label, value in zip(data["monthly_labels"], data["monthly_income"])
        }

        self.plot_visits(visits_per_month)
        self.plot_income(income_per_month)
        self.plot_inventory(inventory)
        self.refresh_profit_labels()

    def refresh_profit_labels(self):
        data = getattr(self, "current_profit_data", {}) or {}
        gross_profit = float(data.get("gross_profit", 0) or 0)
        operational_expense = float(self.operational_expense_input.value()) if hasattr(self, "operational_expense_input") else 0
        self.val_service_income.setText(self.format_rupiah(float(data.get("net_visit_revenue", 0) or 0)))
        self.val_herbal_income.setText(self.format_rupiah(float(data.get("net_herbal_sales", 0) or 0)))
        self.val_herbal_cogs.setText(self.format_rupiah(float(data.get("herbal_cogs", 0) or 0)))
        self.val_gross_profit.setText(self.format_rupiah(gross_profit))
        self.val_net_profit.setText(self.format_rupiah(gross_profit - operational_expense))

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
            
        months = list(data.keys())
        values = [data[m] for m in months]
        labels = []
        for m in months:
            try:
                labels.append(datetime.strptime(m, "%Y-%m").strftime("%b %y"))
            except ValueError:
                labels.append(m)

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

        months = list(data.keys())
        values = [data[m] for m in months]
        labels = []
        for m in months:
            try:
                labels.append(datetime.strptime(m, "%Y-%m").strftime("%b %y"))
            except ValueError:
                labels.append(m)

        ax.plot(labels, values, marker='o', color="#27ae60", linewidth=3, markersize=10, 
                markerfacecolor='white', markeredgewidth=3, markeredgecolor="#27ae60",
                label="Pemasukan")
        ax.fill_between(labels, values, color="#2ecc71", alpha=0.1)
        
        ax.set_title("Performa Pendapatan Kunjungan & Herbal", fontsize=12, fontweight='bold', pad=20, color="#34495e")
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
