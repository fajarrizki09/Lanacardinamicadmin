from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QComboBox, QTextEdit, QFrame
)
from PySide6.QtCore import Qt
from utils.styles import STYLES


class PatientForm(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Tambah Pasien")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        # ROOT
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(4, 4, 4, 4)

        # CARD
        card = QFrame()
        card.setStyleSheet(STYLES["card"])
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("👤 Tambah Pasien")
        title.setStyleSheet("font-size:13px;font-weight:700;color:#2c3e50;")
        layout.addWidget(title)

        label_style = STYLES["transaction_label"] + "font-size:12px;"

        # 🔧 INPUT STYLE KHUSUS (FIX TERPOTONG)
        input_style = STYLES["search_input"] + """
            QLineEdit, QComboBox {
                font-size: 12px;
                padding: 4px 6px;
            }
            QTextEdit {
                font-size: 12px;
                padding: 4px 6px;
            }
        """

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(label_style)
            return l

        field_h = 30  # ✅ aman untuk font 12px

        # ================= ROW 1 =================
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nama pasien")
        self.name_input.setFixedHeight(field_h)
        self.name_input.setStyleSheet(input_style)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("No HP / sementara")
        self.phone_input.setFixedHeight(field_h)
        self.phone_input.setStyleSheet(input_style)

        row1.addWidget(lbl("Nama"))
        row1.addWidget(self.name_input, 2)
        row1.addSpacing(6)
        row1.addWidget(lbl("No HP"))
        row1.addWidget(self.phone_input, 1)

        # ================= ROW 2 =================
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Laki-laki", "Perempuan"])
        self.gender_combo.setFixedHeight(field_h)
        self.gender_combo.setStyleSheet(input_style)

        row2.addWidget(lbl("Kelamin"))
        row2.addWidget(self.gender_combo)
        row2.addStretch()

        # ================= ROW 3 =================
        row3 = QVBoxLayout()
        row3.setSpacing(2)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Alamat...")
        self.address_input.setFixedHeight(52)  # cukup 2 baris
        self.address_input.setStyleSheet(input_style)

        row3.addWidget(lbl("Alamat"))
        row3.addWidget(self.address_input)

        # ================= ROW 4 =================
        row4 = QHBoxLayout()

        self.add_btn = QPushButton("➕ Tambah")
        self.add_btn.setFixedHeight(30)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setToolTip("Tambah pasien baru")
        self.add_btn.setStyleSheet(STYLES["add_button_compact"])

        row4.addStretch()
        row4.addWidget(self.add_btn)

        # ASSEMBLE
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addLayout(row4)

        root.addWidget(card)

    # ================= LOGIC (TIDAK DIUBAH) =================
    def get_inputs(self):
        return (
            self.name_input.text().strip(),
            self.phone_input.text().strip(),
            self.address_input.toPlainText().strip(),
            self.gender_combo.currentText()
        )

    def clear_inputs(self):
        self.name_input.clear()
        self.phone_input.clear()
        self.address_input.clear()
        self.gender_combo.setCurrentIndex(0)
