import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

from apps.RBM.BCF.src.RBM_Main import RBMMain


class SDTSMainWindow(QMainWindow):
    """Main window for SDTS that hosts various tools including RBM"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTS - Schematic Design Tool Suite")
        self.setMinimumSize(1200, 800)

        # Create RBM main window
        self.rbm = RBMMain(self)
        self.setCentralWidget(self.rbm)


def main():
    """Main entry point for the SDTS application"""
    app = QApplication(sys.argv)
    window = SDTSMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
