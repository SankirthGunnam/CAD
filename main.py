import sys
from PySide6.QtWidgets import QApplication
from gui.src.main_window import MainWindow
from gui.src.styles import load_stylesheet


def main():
    """Main entry point for the RF CAD application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Apply stylesheet
    app.setStyleSheet(load_stylesheet())

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
