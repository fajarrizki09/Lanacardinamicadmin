from PySide6.QtCore import QThread, Signal
from helpers.invoice_helper import InvoiceHelper

class InvoiceThread(QThread):
    finished = Signal(bool, str)

    def __init__(self, patient_data, visit_data):
        super().__init__()
        self.patient_data = patient_data
        self.visit_data = visit_data
        self.helper = InvoiceHelper()

    def run(self):
        try:
            # Generate PDF
            invoice_path = self.helper.generate_invoice(self.patient_data, self.visit_data)
            self.finished.emit(True, invoice_path)
        except Exception as e:
            self.finished.emit(False, str(e))
