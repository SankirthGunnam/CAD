from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QLabel, QMessageBox, QFrame, QGroupBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QBrush, QColor, QFont

from progress_tracker import ProgressTracker
from dialog_tab import (DialogTab, TextInputDialog, CheckboxDialog,
                       RadioDialog, NumberInputDialog)


class ArrowButton(QPushButton):
    """Custom arrow button for navigation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("→")
        self.setFixedSize(60, 60)
        self.setToolTip("Click to proceed to next step")
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)


class InteractiveWidget(QWidget):
    """Main interactive widget with progress tracker, tabs, and arrow button"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Interactive PySide6 Widget")
        self.setMinimumSize(900, 700)

        # Data storage
        self.tab_data = {}  # Store selected values from each tab
        self.dialog_types = [TextInputDialog, CheckboxDialog, RadioDialog, NumberInputDialog]
        self.current_dialog_index = 0

        self.setupUI()
        self.applyMainStyling()

    def setupUI(self):
        """Setup the main UI layout"""
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # Progress tracker (first item)
        self.progress_tracker = ProgressTracker()
        main_layout.addWidget(self.progress_tracker)

        # Tab widget (second item)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
        main_layout.addWidget(self.tab_widget)

        # Bottom layout for arrow button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()  # Push button to the right

        self.arrow_button = ArrowButton()
        self.arrow_button.clicked.connect(self.onArrowButtonClicked)
        bottom_layout.addWidget(self.arrow_button)

        main_layout.addLayout(bottom_layout)

        # Add initial tab
        self.addNewTab()

    def applyMainStyling(self):
        """Apply main widget styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }
        """)

    def addNewTab(self):
        """Add a new tab with a dialog widget"""
        if self.current_dialog_index >= len(self.dialog_types):
            # Reset to first dialog type if we've used all
            self.current_dialog_index = 0

        dialog_class = self.dialog_types[self.current_dialog_index]
        tab_title = f"Step {self.tab_widget.count() + 1}"

        # Create dialog widget
        dialog_widget = dialog_class(tab_title)
        dialog_widget.selection_changed.connect(self.onDialogSelectionChanged)

        # Add to tab widget
        self.tab_widget.addTab(dialog_widget, tab_title)

        # Add step to progress tracker
        self.progress_tracker.addStep(tab_title)

        # Move to the new tab
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

        # Enable arrow button
        self.arrow_button.setEnabled(True)

        self.current_dialog_index += 1

    def onDialogSelectionChanged(self, tab_title, selected_value):
        """Handle selection changes from dialog widgets"""
        self.tab_data[tab_title] = selected_value
        print(f"Tab '{tab_title}' selection changed: {selected_value}")

    def onArrowButtonClicked(self):
        """Handle arrow button click"""
        current_tab_index = self.tab_widget.currentIndex()
        current_tab = self.tab_widget.currentWidget()

        if current_tab:
            # Get selected value from current tab
            selected_value = current_tab.getSelectedValue()
            tab_title = self.tab_widget.tabText(current_tab_index)

            # Store the data
            self.tab_data[tab_title] = selected_value

            # Print the selected value
            print(f"Arrow button clicked! Selected value from '{tab_title}': {selected_value}")

            # Complete current step in progress tracker
            self.progress_tracker.completeCurrentStep()

            # Add new tab
            self.addNewTab()

            # Show summary of all collected data
            self.showDataSummary()
        else:
            QMessageBox.warning(self, "Warning", "No tab selected!")

    def showDataSummary(self):
        """Show a summary of all collected data"""
        if len(self.tab_data) > 1:  # Only show if we have more than one tab
            summary = "Collected Data Summary:\n"
            for tab_title, value in self.tab_data.items():
                summary += f"- {tab_title}: {value}\n"

            # Show in a message box (optional - you can remove this if not needed)
            msg = QMessageBox(self)
            msg.setWindowTitle("Data Summary")
            msg.setText(summary)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()

    def getCollectedData(self):
        """Get all collected data"""
        return self.tab_data.copy()

    def resetWidget(self):
        """Reset the widget to initial state"""
        # Clear tab widget
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # Clear progress tracker
        self.progress_tracker.reset()

        # Clear data
        self.tab_data.clear()
        self.current_dialog_index = 0

        # Re-add initial tab
        self.addNewTab()