from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QLineEdit, QCheckBox, QRadioButton, QButtonGroup, QSpinBox, 
                             QDoubleSpinBox, QTextEdit, QGroupBox, QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QPalette


class DialogTab(QDialog):
    """Base dialog widget for use in tabs"""
    
    # Signal emitted when user makes a selection
    selection_changed = Signal(str, object)  # tab_title, selected_value
    
    def __init__(self, title="Dialog Tab", parent=None):
        super().__init__(parent)
        self.title = title
        self.setWindowTitle(title)
        
        # Remove dialog buttons (OK/Cancel)
        self.setWindowFlags(Qt.Widget)
        
        self.setupUI()
        self.applyStyling()
        
    def setupUI(self):
        """Setup the UI - override in subclasses"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a group box for better visual organization
        self.group_box = QGroupBox(f"Configuration: {self.title}")
        self.group_box.setFont(QFont("Arial", 12, QFont.Bold))
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        
        # Default content
        label = QLabel(f"Please make your selection for {self.title}")
        label.setFont(QFont("Arial", 10))
        group_layout.addWidget(label)
        
        # Example input widget
        self.combo = QComboBox()
        self.combo.addItems(["Option 1", "Option 2", "Option 3"])
        self.combo.currentTextChanged.connect(self.onSelectionChanged)
        group_layout.addWidget(self.combo)
        
        layout.addWidget(self.group_box)
        
    def applyStyling(self):
        """Apply consistent styling to the dialog"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #333333;
            }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4CAF50;
            }
            QCheckBox, QRadioButton {
                font-size: 11px;
                spacing: 8px;
            }
            QLabel {
                color: #555555;
                font-size: 11px;
            }
        """)
        
    def onSelectionChanged(self, value):
        """Handle selection changes"""
        self.selection_changed.emit(self.title, value)
        
    def getSelectedValue(self):
        """Get the currently selected value"""
        return self.combo.currentText()


class TextInputDialog(DialogTab):
    """Dialog with text input"""
    
    def __init__(self, title="Text Input", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a group box for better visual organization
        self.group_box = QGroupBox(f"Text Input: {self.title}")
        self.group_box.setFont(QFont("Arial", 12, QFont.Bold))
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        
        label = QLabel(f"Enter your text for {self.title}:")
        label.setFont(QFont("Arial", 10))
        group_layout.addWidget(label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type your text here...")
        self.text_input.textChanged.connect(self.onSelectionChanged)
        group_layout.addWidget(self.text_input)
        
        layout.addWidget(self.group_box)
        self.applyStyling()
        
    def onSelectionChanged(self, value):
        self.selection_changed.emit(self.title, value)
        
    def getSelectedValue(self):
        return self.text_input.text()


class CheckboxDialog(DialogTab):
    """Dialog with checkboxes"""
    
    def __init__(self, title="Checkbox Selection", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a group box for better visual organization
        self.group_box = QGroupBox(f"Multiple Selection: {self.title}")
        self.group_box.setFont(QFont("Arial", 12, QFont.Bold))
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        
        label = QLabel(f"Select one or more options for {self.title}:")
        label.setFont(QFont("Arial", 10))
        group_layout.addWidget(label)
        
        self.checkboxes = []
        options = ["Option A", "Option B", "Option C", "Option D"]
        
        for option in options:
            checkbox = QCheckBox(option)
            checkbox.toggled.connect(self.onSelectionChanged)
            self.checkboxes.append(checkbox)
            group_layout.addWidget(checkbox)
            
        layout.addWidget(self.group_box)
        self.applyStyling()
            
    def onSelectionChanged(self):
        selected = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        self.selection_changed.emit(self.title, selected)
        
    def getSelectedValue(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


class RadioDialog(DialogTab):
    """Dialog with radio buttons"""
    
    def __init__(self, title="Radio Selection", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a group box for better visual organization
        self.group_box = QGroupBox(f"Single Selection: {self.title}")
        self.group_box.setFont(QFont("Arial", 12, QFont.Bold))
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        
        label = QLabel(f"Choose one option for {self.title}:")
        label.setFont(QFont("Arial", 10))
        group_layout.addWidget(label)
        
        self.button_group = QButtonGroup()
        options = ["Choice 1", "Choice 2", "Choice 3", "Choice 4"]
        
        for i, option in enumerate(options):
            radio = QRadioButton(option)
            self.button_group.addButton(radio, i)
            radio.toggled.connect(self.onSelectionChanged)
            group_layout.addWidget(radio)
            
        layout.addWidget(self.group_box)
        self.applyStyling()
            
    def onSelectionChanged(self):
        checked_button = self.button_group.checkedButton()
        if checked_button:
            self.selection_changed.emit(self.title, checked_button.text())
        
    def getSelectedValue(self):
        checked_button = self.button_group.checkedButton()
        return checked_button.text() if checked_button else ""


class NumberInputDialog(DialogTab):
    """Dialog with number input"""
    
    def __init__(self, title="Number Input", parent=None):
        super().__init__(title, parent)
        
    def setupUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create a group box for better visual organization
        self.group_box = QGroupBox(f"Number Input: {self.title}")
        self.group_box.setFont(QFont("Arial", 12, QFont.Bold))
        group_layout = QVBoxLayout(self.group_box)
        group_layout.setSpacing(10)
        
        label = QLabel(f"Enter a number for {self.title}:")
        label.setFont(QFont("Arial", 10))
        group_layout.addWidget(label)
        
        self.spin_box = QSpinBox()
        self.spin_box.setRange(0, 100)
        self.spin_box.setValue(0)
        self.spin_box.valueChanged.connect(self.onSelectionChanged)
        group_layout.addWidget(self.spin_box)
        
        layout.addWidget(self.group_box)
        self.applyStyling()
        
    def onSelectionChanged(self, value):
        self.selection_changed.emit(self.title, value)
        
    def getSelectedValue(self):
        return self.spin_box.value()