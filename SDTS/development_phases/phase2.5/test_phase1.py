#!/usr/bin/env python3
"""
Test application for Phase 1: Basic UI Layout
Run this to test the Phase 1 implementation
"""

import sys
import os

# Add the BCF path to Python path
bcf_path = os.path.join(os.path.dirname(__file__), 'apps', 'RBM5', 'BCF')
if bcf_path not in sys.path:
    sys.path.insert(0, bcf_path)

from PySide6.QtWidgets import QApplication, QMainWindow
from gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager

def main():
    """Test Phase 1 Visual BCF Manager"""
    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("SDTS - Phase 1: Basic UI Layout")
    main_window.setGeometry(100, 100, 1200, 800)

    # Create Visual BCF Manager (Phase 1)
    print("Creating Phase 1 Visual BCF Manager...")
    bcf_manager = VisualBCFManager()
    main_window.setCentralWidget(bcf_manager)

    print("Phase 1 Features:")
    print("- ✅ Basic graphics view and scene")
    print("- ✅ Toolbar with placeholder buttons")
    print("- ✅ Status updates and error handling")
    print("- ✅ Clean UI layout and styling")
    print("- ✅ Foundation for future expansion")
    print()
    print("Try clicking the buttons to see placeholders for future functionality!")

    # Show window
    main_window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
