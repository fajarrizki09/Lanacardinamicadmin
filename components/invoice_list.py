import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QHeaderView, QLabel,
    QFrame, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt, QSize
from utils.styles import STYLES

class InvoiceList(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.invoice_dir = "invoices"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header Area
        header_layout = QHBoxLayout()
        title = QLabel("📂 Manajemen Invoice PDF")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cari nama pasien atau tanggal...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet(STYLES["search_input"])
        self.search_input.textChanged.connect(self.refresh_list)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedSize(100, 36)
        refresh_btn.setStyleSheet(STYLES["update_button"])
        refresh_btn.clicked.connect(self.refresh_list)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        # Table Card
        card = QFrame()
        card.setStyleSheet(STYLES["card"])
        card_layout = QVBoxLayout(card)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tanggal Kunjungan", "Nama Pasien", "Total Harga", "Aksi"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget { border: none; background: white; }
            QHeaderView::section { background: #f8f9fa; padding: 10px; font-weight: bold; border: none; }
        """)

        card_layout.addWidget(self.table)
        layout.addWidget(card)

        self.refresh_list()

    def refresh_list(self):
        search_text = self.search_input.text().lower()
        visits = self.db.get_all_visits()
        patients = {p.id: p.name for p in self.db.get_all_patients()}
        
        # Filter only visits with invoice_path
        data = []
        for v in visits:
            p_name = patients.get(v['patient_id'], "Unknown")
            date_str = v['date'].strftime("%d/%m/%Y %H:%M")
            if v['invoice_path'] and os.path.exists(v['invoice_path']):
                if search_text in p_name.lower() or search_text in date_str:
                    data.append({
                        "date": date_str,
                        "name": p_name,
                        "price": v['price'],
                        "path": v['invoice_path']
                    })

        data.sort(key=lambda x: x['date'], reverse=True)
        
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item['date']))
            self.table.setItem(row, 1, QTableWidgetItem(item['name']))
            
            price_item = QTableWidgetItem(f"Rp {item['price']:,}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, price_item)

            # Action Buttons
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(5)

            open_btn = QPushButton("👁️ Buka")
            open_btn.setFixedSize(70, 28)
            open_btn.setStyleSheet("background: #3498db; color: white; border-radius: 4px; font-weight: bold;")
            open_btn.clicked.connect(lambda ch, p=item['path']: self.open_invoice(p))

            folder_btn = QPushButton("📁")
            folder_btn.setFixedSize(30, 28)
            folder_btn.setStyleSheet("background: #f1f2f6; border: 1px solid #dcdde1; border-radius: 4px;")
            folder_btn.clicked.connect(lambda ch, p=item['path']: self.open_folder(p))

            btn_layout.addWidget(open_btn)
            btn_layout.addWidget(folder_btn)
            self.table.setCellWidget(row, 3, btn_container)

    def open_invoice(self, path):
        if os.path.exists(path):
            os.startfile(path) if hasattr(os, 'startfile') else os.system(f"xdg-open '{path}'")
        else:
            QMessageBox.warning(self, "File Tidak Ditemukan", "File invoice tidak ditemukan di folder tujuan.")

    def open_folder(self, path):
        folder = os.path.dirname(os.path.abspath(path))
        if os.path.exists(folder):
            os.startfile(folder) if hasattr(os, 'startfile') else os.system(f"xdg-open '{folder}'")
