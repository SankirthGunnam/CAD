import sys
import os
from PySide6.QtWidgets import QApplication

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from apps.RBM.BCF.src.RBM_Main import RBMMain

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = RBMMain()
    main.show()
    sys.exit(app.exec())
