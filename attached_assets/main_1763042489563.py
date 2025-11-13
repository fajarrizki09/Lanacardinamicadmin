from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from database import Database
from settings import AppSettings
import sys

def main():
    app = QApplication(sys.argv)
    
    db = Database("sqlite:///data.db")
    settings = AppSettings("settings.json")
    
    window = MainWindow(db, settings)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
