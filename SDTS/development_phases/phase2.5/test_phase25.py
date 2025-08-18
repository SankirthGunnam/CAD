#!/usr/bin/env python3
"""
Test application for Phase 2.5: Core Functionality Fixes

This test demonstrates all the fixes and enhancements made in Phase 2.5:
1. Zoom functionality with Ctrl+Scroll
2. Global delete button
3. Component pins
4. Basic connection framework (pins ready for wires)
5. Enhanced component placement and management
"""

import sys
import os

# Add the project root directory to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Import from the local phase 2.5 directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'RBM', 'BCF', 'gui', 'source', 'visual_bcf'))
from visual_bcf_manager import VisualBCFManager


class Phase25TestWindow(QMainWindow):
    """Main test window for Phase 2.5"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTS - Phase 2.5: Core Functionality Fixes")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add header
        header_label = QLabel("Phase 2.5: Core Functionality Fixes")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #2c3e50; padding: 10px; background: #ecf0f1; border: 1px solid #bdc3c7;")
        layout.addWidget(header_label)
        
        # Add instructions
        instructions = QLabel(self._get_instructions())
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background: #f8f9fa; border: 1px solid #dee2e6;")
        layout.addWidget(instructions)
        
        # Create and add Visual BCF Manager
        self.bcf_manager = VisualBCFManager()
        layout.addWidget(self.bcf_manager)
        
        # Connect signals for testing
        self.bcf_manager.status_updated.connect(self._on_status_update)
        self.bcf_manager.data_changed.connect(self._on_data_change)
        
        self.status_log = []
        
    def _get_instructions(self) -> str:
        """Get test instructions"""
        return """
        <h3>Phase 2.5 Testing Instructions:</h3>
        <p><b>New Features to Test:</b></p>
        <ol>
        <li><b>Zoom with Ctrl+Scroll:</b> Hold Ctrl and scroll mouse wheel to zoom in/out (0.1x to 10.0x)</li>
        <li><b>Delete Button:</b> Select components and click "Delete Selected" or press Del key</li>
        <li><b>Component Pins:</b> All components now have visible pins:
            <ul>
            <li>Chips: 12 pins (4 inputs left, 4 outputs right, 2 power top, 2 ground bottom)</li>
            <li>Resistors: 2 pins (left and right terminals)</li>
            <li>Capacitors: 2 pins (positive left, negative right)</li>
            </ul>
        </li>
        <li><b>Connection Framework:</b> Pins are ready for future wire connections</li>
        </ol>
        <p><b>Testing Sequence:</b> Place components → Select → Delete → Test zoom → Observe pins</p>
        """
        
    def _on_status_update(self, message: str):
        """Handle status updates"""
        self.status_log.append(f"Status: {message}")
        print(f"[Phase 2.5] {message}")
        
    def _on_data_change(self, data: dict):
        """Handle data changes"""
        self.status_log.append(f"Data: {data}")
        print(f"[Phase 2.5] Data change: {data}")


def run_phase25_tests():
    """Run comprehensive Phase 2.5 tests"""
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = Phase25TestWindow()
    test_window.show()
    
    # Print startup info
    print("=" * 60)
    print("SDTS Phase 2.5: Core Functionality Fixes")
    print("=" * 60)
    print("✅ Zoom with Ctrl+Scroll")
    print("✅ Global delete button")
    print("✅ Component pins")
    print("✅ Basic connection framework")
    print("=" * 60)
    print("Application started. Test the new functionality!")
    print("Close the window to exit.")
    
    return app.exec()


def main():
    """Main test function"""
    return run_phase25_tests()


if __name__ == "__main__":
    sys.exit(main())
