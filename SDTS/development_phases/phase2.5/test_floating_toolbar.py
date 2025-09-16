#!/usr/bin/env python3
"""
Test floating toolbar integration - Quick display test
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Import the Visual BCF Manager
from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

def main():
    """Test the floating toolbar"""
    try:
        print("🚀 Testing Floating Toolbar Integration...")

        # Initialize Qt application
        app = QApplication(sys.argv)

        # Create RDB manager
        print("✅ Creating RDB Manager...")
        rdb_manager = RDBManager("test_device_config.json")

        # Create and show Visual BCF Manager
        print("✅ Creating Visual BCF Manager with Floating Toolbar...")
        bcf_manager = VisualBCFManager(rdb_manager=rdb_manager)

        # Create main window
        main_window = QMainWindow()
        main_window.setWindowTitle("SDTS - Visual BCF Manager with Floating Toolbar")
        main_window.setGeometry(100, 100, 1400, 900)
        main_window.setCentralWidget(bcf_manager)
        main_window.show()

        print("✅ Application launched successfully!")
        print("🎯 Features available:")
        print("   🔲 Add Chip button")
        print("   ⧈  Add Resistor button")
        print("   ⧇  Add Capacitor button")
        print("   📏 Zoom controls (+, -, reset, fit)")
        print("   🗑  Delete selected button")
        print("   🗋  Clear scene button")
        print("   S/C Mode selection buttons")
        print("   ℹ  Phase info button")
        print("")
        print("🎮 You can now:")
        print("   1. Click on component buttons to select placement mode")
        print("   2. Use zoom buttons to zoom in/out")
        print("   3. Drag the toolbar around the screen")
        print("   4. Click on the scene to place components")
        print("   5. Use Delete button to remove selected components")
        print("")
        print("⏰ Application will stay open - close window to exit...")

        # Keep app running until manually closed
        # QTimer.singleShot(10000, app.quit)

        return app.exec()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
