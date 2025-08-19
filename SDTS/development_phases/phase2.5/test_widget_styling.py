#!/usr/bin/env python3
"""
Test script to debug widget background color styling issues
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

class TestWidget(QWidget):
    """Simple test widget to test background styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TestWidget")
        self.setup_ui()
        self.apply_styling()
        
    def setup_ui(self):
        """Setup UI with some buttons"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Add some buttons
        btn1 = QPushButton("Button 1", self)
        btn2 = QPushButton("Button 2", self)
        btn3 = QPushButton("Button 3", self)
        
        layout.addWidget(btn1)
        layout.addWidget(btn2) 
        layout.addWidget(btn3)
        
    def apply_styling(self):
        """Apply CSS styling"""
        print("🎨 Applying CSS styling to TestWidget...")
        
        # Enable auto fill background
        self.setAutoFillBackground(True)
        
        # Try CSS styling
        self.setStyleSheet("""
            QWidget#TestWidget {
                background-color: rgb(255, 0, 0);
                border: 3px solid rgb(0, 255, 0);
                border-radius: 10px;
                padding: 5px;
            }
            
            QPushButton {
                background-color: rgb(0, 0, 255);
                color: white;
                border: 1px solid white;
                border-radius: 3px;
                padding: 5px;
                margin: 2px;
            }
            
            QPushButton:hover {
                background-color: rgb(0, 100, 255);
            }
        """)
        
class TestWidgetPalette(QWidget):
    """Test widget using QPalette instead of CSS"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TestWidgetPalette")
        self.setup_ui()
        self.apply_palette_styling()
        
    def setup_ui(self):
        """Setup UI with some buttons"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Add some buttons
        btn1 = QPushButton("Palette 1", self)
        btn2 = QPushButton("Palette 2", self) 
        btn3 = QPushButton("Palette 3", self)
        
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        
    def apply_palette_styling(self):
        """Apply styling using QPalette"""
        print("🎨 Applying QPalette styling to TestWidgetPalette...")
        
        # Set auto fill background
        self.setAutoFillBackground(True)
        
        # Create and set palette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 165, 0))  # Orange
        self.setPalette(palette)


class TestMainWindow(QMainWindow):
    """Main window for testing widget styling"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Widget Background Styling Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Add title
        title = QLabel("Widget Background Styling Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        layout.addWidget(title)
        
        # Test 1: CSS Styling
        css_label = QLabel("Test 1: CSS Styling (should be RED background)")
        css_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        layout.addWidget(css_label)
        
        self.css_widget = TestWidget()
        self.css_widget.setFixedSize(400, 60)
        layout.addWidget(self.css_widget)
        
        # Test 2: QPalette Styling  
        palette_label = QLabel("Test 2: QPalette Styling (should be ORANGE background)")
        palette_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        layout.addWidget(palette_label)
        
        self.palette_widget = TestWidgetPalette()
        self.palette_widget.setFixedSize(400, 60)
        layout.addWidget(self.palette_widget)
        
        # Test 3: Direct CSS on widget
        direct_label = QLabel("Test 3: Direct CSS (should be GREEN background)")
        direct_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        layout.addWidget(direct_label)
        
        self.direct_widget = QWidget()
        self.direct_widget.setFixedSize(400, 60)
        self.direct_widget.setAutoFillBackground(True)
        self.direct_widget.setStyleSheet("""
            background-color: rgb(0, 255, 0);
            border: 2px solid rgb(0, 200, 0);
            border-radius: 8px;
        """)
        layout.addWidget(self.direct_widget)
        
        # Test 4: Frame widget
        frame_label = QLabel("Test 4: QFrame (should be BLUE background)")
        frame_label.setStyleSheet("font-weight: bold; color: #3498db;")
        layout.addWidget(frame_label)
        
        self.frame_widget = QFrame()
        self.frame_widget.setFixedSize(400, 60)
        self.frame_widget.setAutoFillBackground(True)
        self.frame_widget.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.frame_widget.setStyleSheet("""
            QFrame {
                background-color: rgb(0, 0, 255);
                border: 2px solid rgb(100, 100, 255);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.frame_widget)
        
        # Add debugging info
        debug_label = QLabel("Debug Info:")
        debug_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(debug_label)
        
        self.print_debug_info()
        
    def print_debug_info(self):
        """Print debug information"""
        # Wait a moment for widgets to be fully initialized
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_debug_info)
        
    def _delayed_debug_info(self):
        """Print debug info after widgets are initialized"""
        print("\n" + "="*50)
        print("🔍 DEBUG INFORMATION (after initialization)")
        print("="*50)
        
        print(f"CSS Widget:")
        print(f"  - Object name: {self.css_widget.objectName()}")
        print(f"  - Auto fill background: {self.css_widget.autoFillBackground()}")
        print(f"  - StyleSheet: {self.css_widget.styleSheet()[:100]}...")
        print(f"  - Visible: {self.css_widget.isVisible()}")
        
        print(f"\nPalette Widget:")
        print(f"  - Object name: {self.palette_widget.objectName()}")
        print(f"  - Auto fill background: {self.palette_widget.autoFillBackground()}")
        palette_color = self.palette_widget.palette().color(QPalette.Window)
        print(f"  - Palette window color: {palette_color.name()}")
        print(f"  - Visible: {self.palette_widget.isVisible()}")
        
        print(f"\nDirect Widget:")
        print(f"  - Auto fill background: {self.direct_widget.autoFillBackground()}")
        print(f"  - StyleSheet: {self.direct_widget.styleSheet()}")
        print(f"  - Visible: {self.direct_widget.isVisible()}")
        
        print(f"\nFrame Widget:")
        print(f"  - Auto fill background: {self.frame_widget.autoFillBackground()}")
        print(f"  - Frame style: {self.frame_widget.frameStyle()}")
        print(f"  - StyleSheet: {self.frame_widget.styleSheet()}")
        print(f"  - Visible: {self.frame_widget.isVisible()}")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    print("🚀 Starting Widget Styling Test...")
    
    # Create and show main window
    window = TestMainWindow()
    window.show()
    
    print("\n📋 Instructions:")
    print("1. Check if the widgets show the expected background colors:")
    print("   - Test 1: RED background")
    print("   - Test 2: ORANGE background") 
    print("   - Test 3: GREEN background")
    print("   - Test 4: BLUE background")
    print("2. If any don't show backgrounds, that indicates the styling issue")
    print("3. Close the window to exit")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
