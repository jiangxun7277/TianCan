import sys
from PySide6.QtWidgets import QApplication
from gui import CompilerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerApp()
    window.show()
    sys.exit(app.exec())