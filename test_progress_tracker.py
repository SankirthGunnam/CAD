#!/usr/bin/env python3
"""
Simple test script to verify progress tracker layout
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from progress_tracker import ProgressTracker


class TestWindow(QMainWindow):
    """Test window for progress tracker"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Tracker Test")
        self.setGeometry(100, 100, 800, 200)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Add title
        title_label = QLabel("Progress Tracker - Continuous Layout Test")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Add the progress tracker
        self.progress_tracker = ProgressTracker()
        layout.addWidget(self.progress_tracker)
        
        # Add control buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Step")
        add_button.clicked.connect(self.addStep)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(add_button)
        
        complete_button = QPushButton("Complete Current")
        complete_button.clicked.connect(self.completeCurrent)
        complete_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(complete_button)
        
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        button_layout.addWidget(reset_button)
        
        layout.addLayout(button_layout)
        
        self.step_count = 0
        
    def addStep(self):
        """Add a new step"""
        self.step_count += 1
        self.progress_tracker.addStep(f"Step {self.step_count}")
        print(f"Added Step {self.step_count}")
        
    def completeCurrent(self):
        """Complete current step"""
        self.progress_tracker.completeCurrentStep()
        print("Completed current step")
        
    def reset(self):
        """Reset progress tracker"""
        self.progress_tracker.reset()
        self.step_count = 0
        print("Reset progress tracker")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = TestWindow()
    window.show()
    
    print("Progress Tracker Test Started!")
    print("Instructions:")
    print("1. Click 'Add Step' to add progress bubbles")
    print("2. Click 'Complete Current' to mark current step as done")
    print("3. Click 'Reset' to start over")
    print("4. Notice how arrows and bubbles connect seamlessly")
    print("\nStarting test...\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
