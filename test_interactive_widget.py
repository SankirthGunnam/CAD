#!/usr/bin/env python3
"""
Test script for the Interactive PySide6 Widget
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

from main_widget import InteractiveWidget


class TestMainWindow(QMainWindow):
    """Test main window for the interactive widget"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Widget Test")
        self.setGeometry(100, 100, 1000, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Add title
        title_label = QLabel("Interactive PySide6 Widget Demo")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333333;
                padding: 20px;
            }
        """)
        layout.addWidget(title_label)

        # Add the interactive widget
        self.interactive_widget = InteractiveWidget()
        layout.addWidget(self.interactive_widget)

        # Add control buttons
        button_layout = QVBoxLayout()

        # Reset button
        self.reset_button = QPushButton("Reset Widget")
        self.reset_button.clicked.connect(self.resetWidget)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        button_layout.addWidget(self.reset_button)

        # Show data button
        self.show_data_button = QPushButton("Show Collected Data")
        self.show_data_button.clicked.connect(self.showCollectedData)
        self.show_data_button.setStyleSheet("""
            QPushButton {
                background-color: #4ecdc4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45b7b8;
            }
        """)
        button_layout.addWidget(self.show_data_button)

        layout.addLayout(button_layout)

    def resetWidget(self):
        """Reset the interactive widget"""
        self.interactive_widget.resetWidget()
        print("Widget reset!")

    def showCollectedData(self):
        """Show all collected data"""
        data = self.interactive_widget.getCollectedData()
        print("\n" + "="*50)
        print("COLLECTED DATA SUMMARY:")
        print("="*50)
        for tab_title, value in data.items():
            print(f"{tab_title}: {value}")
        print("="*50 + "\n")


def main():
    """Main function to run the test"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    window = TestMainWindow()
    window.show()

    print("Interactive Widget Test Started!")
    print("Instructions:")
    print("1. Make selections in the current tab")
    print("2. Click the green arrow button to proceed to next step")
    print("3. Hover over progress bubbles to see tab titles")
    print("4. Use 'Reset Widget' to start over")
    print("5. Use 'Show Collected Data' to see all selections")
    print("\nStarting application...\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
