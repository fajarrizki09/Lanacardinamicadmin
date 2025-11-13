from PySide6.QtCore import QThread, Signal
import time


class SearchThread(QThread):
    results_ready = Signal(list)

    def __init__(self, all_patients, query):
        super().__init__()
        self.all_patients = all_patients
        self.query = query.lower()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        results = []
        check_interval = 100

        for idx, patient in enumerate(self.all_patients):
            if self._is_cancelled:
                return

            pid, name, phone = patient
            if name.lower().startswith(self.query) or phone.startswith(self.query):
                results.append(patient)

            if idx % check_interval == 0:
                time.sleep(0.001)

        if not self._is_cancelled:
            self.results_ready.emit(results)
