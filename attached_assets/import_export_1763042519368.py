from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
import os

class ImportExportHelper:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

    def export_data(self):
        options = ["JSON", "Excel"]
        format_choice, ok = QInputDialog.getItem(
            self.parent, "Export Data", "Pilih format ekspor:", options, 0, False
        )
        if not ok:
            return

        if format_choice == "JSON":
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Simpan file JSON", "", "JSON Files (*.json)"
            )
            if file_path:
                if not file_path.endswith(".json"):
                    file_path += ".json"
                if os.path.exists(file_path):
                    overwrite = QMessageBox.question(
                        self.parent, "Konfirmasi Overwrite",
                        f"File {file_path} sudah ada. Ganti file ini?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if overwrite != QMessageBox.Yes:
                        return
                try:
                    QMessageBox.information(self.parent, "Info", "Export JSON belum diimplementasi")
                except Exception as e:
                    QMessageBox.critical(self.parent, "Error", f"Gagal ekspor data:\n{e}")
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Simpan file Excel", "", "Excel Files (*.xlsx)"
            )
            if file_path:
                if not file_path.endswith(".xlsx"):
                    file_path += ".xlsx"
                if os.path.exists(file_path):
                    overwrite = QMessageBox.question(
                        self.parent, "Konfirmasi Overwrite",
                        f"File {file_path} sudah ada. Ganti file ini?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if overwrite != QMessageBox.Yes:
                        return
                try:
                    QMessageBox.information(self.parent, "Info", "Export Excel belum diimplementasi")
                except Exception as e:
                    QMessageBox.critical(self.parent, "Error", f"Gagal ekspor data:\n{e}")

    def import_data(self):
        options = ["JSON", "Excel"]
        format_choice, ok = QInputDialog.getItem(
            self.parent, "Import Data", "Pilih format impor:", options, 0, False
        )
        if not ok:
            return False

        confirm = QMessageBox.question(
            self.parent, "Konfirmasi Impor",
            "Data lama mungkin akan tertimpa. Lanjutkan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return False

        QMessageBox.information(self.parent, "Info", "Import belum diimplementasi")
        return False
