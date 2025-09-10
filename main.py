#!/usr/bin/env python3
"""
Example application demonstrating the Interactive PySide6 Widget
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout
from PySide6.QtCore import Qt

from main_widget import InteractiveWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive PySide6 Widget Demo")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create the interactive widget
        self.interactive_widget = InteractiveWidget()
        layout.addWidget(self.interactive_widget)
        
        # Add control buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset Widget")
        self.reset_button.clicked.connect(self.resetWidget)
        button_layout.addWidget(self.reset_button)
        
        self.show_data_button = QPushButton("Show Collected Data")
        self.show_data_button.clicked.connect(self.showCollectedData)
        button_layout.addWidget(self.show_data_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Add text area for output
        self.output_text = QTextEdit()
        self.output_text.setMaximumHeight(150)
        self.output_text.setPlaceholderText("Output will appear here...")
        layout.addWidget(self.output_text)
        
    def resetWidget(self):
        """Reset the interactive widget"""
        self.interactive_widget.resetWidget()
        self.output_text.clear()
        self.appendOutput("Widget reset!")
        
    def showCollectedData(self):
        """Show all collected data"""
        data = self.interactive_widget.getCollectedData()
        if data:
            output = "Collected Data:\n"
            for tab_title, value in data.items():
                output += f"  {tab_title}: {value}\n"
            self.appendOutput(output)
        else:
            self.appendOutput("No data collected yet.")
            
    def appendOutput(self, text):
        """Append text to output area"""
        self.output_text.append(text)
        self.output_text.ensureCursorVisible()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Interactive PySide6 Widget Demo")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()