#!/usr/bin/env python3
"""
Test application for Phase 2: Component Placement
Run this to test the Phase 2 implementation
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
    """Test Phase 2 Visual BCF Manager"""
    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("SDTS - Phase 2: Component Placement")
    main_window.setGeometry(100, 100, 1200, 800)

    # Create Visual BCF Manager (Phase 2)
    print("Creating Phase 2 Visual BCF Manager...")
    bcf_manager = VisualBCFManager()
    main_window.setCentralWidget(bcf_manager)

    print("\nPhase 2 Features:")
    print("- ✅ Click-to-place component functionality")
    print("- ✅ Multiple component types (chip, resistor, capacitor)")
    print("- ✅ Component selection and movement")
    print("- ✅ Right-click context menus")
    print("- ✅ Component properties dialog")
    print("- ✅ Component deletion")
    print("- ✅ Mode switching (placement/selection)")
    print("- ✅ Visual feedback and status updates")
    print()
    print("How to test:")
    print("1. Click 'Add Chip', 'Add Resistor', or 'Add Capacitor'")
    print("2. Click anywhere on the scene to place components")
    print("3. Right-click components to see properties or delete")
    print("4. Use 'Select Mode' to move components around")
    print("5. Try 'Clear Scene' to remove all components")
    print("6. Click 'Phase Info' to see development progress")

    # Show window
    main_window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
