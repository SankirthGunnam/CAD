"""
Chip Selection Dialog for Visual BCF

This dialog allows users to select a component from the available devices
in the All Devices table from Device Settings.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QAbstractItemView,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
from typing import List, Dict, Any, Optional


class ChipSelectionDialog(QDialog):
    """
    Dialog for selecting a component to add to the scene.
    
    Shows available components from the All Devices table
    and allows user to select one for placement.
    """
    
    # Signal emitted when a component is selected
    component_selected = Signal(dict)  # component_data
    
    def __init__(self, all_devices: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.all_devices = all_devices
        self.selected_component = None
        
        self.setWindowTitle("Select Component to Add")
        self.setModal(True)
        self.resize(600, 400)
        
        self._setup_ui()
        self._populate_table()
        
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Select a Component to Add to the Scene")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # All Devices Table
        self.devices_table = QTableWidget()
        self.devices_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.devices_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setSortingEnabled(True)
        
        # Set up table columns
        headers = ["ID", "Name", "Control Type", "Module"]
        self.devices_table.setColumnCount(len(headers))
        self.devices_table.setHorizontalHeaderLabels(headers)
        
        # Configure table
        header = self.devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.devices_table)
        
        # Connect table selection signals
        self.devices_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Double-click to select
        self.devices_table.itemDoubleClicked.connect(self._on_double_clicked)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("Select Component")
        self.select_button.setEnabled(False)
        self.select_button.clicked.connect(self._on_select_clicked)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def _populate_table(self):
        """Populate the table with device data"""
        # Populate devices table
        self.devices_table.setRowCount(len(self.all_devices))
        for row, device in enumerate(self.all_devices):
            self.devices_table.setItem(row, 0, QTableWidgetItem(str(device.get('ID', ''))))
            self.devices_table.setItem(row, 1, QTableWidgetItem(str(device.get('Name', ''))))
            self.devices_table.setItem(row, 2, QTableWidgetItem(str(device.get('Control Type', ''))))
            self.devices_table.setItem(row, 3, QTableWidgetItem(str(device.get('Module', ''))))
    
    def _on_selection_changed(self):
        """Handle table selection change"""
        self._update_selection()
    
    def _update_selection(self):
        """Update the selected component based on current selection"""
        current_row = self.devices_table.currentRow()
        if current_row >= 0 and current_row < len(self.all_devices):
            self.selected_component = self.all_devices[current_row].copy()
            # Determine component type based on control type or other criteria
            control_type = self.selected_component.get('Control Type', '').lower()
            if 'mipi' in control_type or 'csi' in control_type or 'dsi' in control_type:
                self.selected_component['Component Type'] = 'mipi'
            else:
                self.selected_component['Component Type'] = 'gpio'
            self.select_button.setEnabled(True)
            return
        
        # No selection
        self.selected_component = None
        self.select_button.setEnabled(False)
    
    def _on_double_clicked(self, item):
        """Handle table double-click"""
        self._on_select_clicked()
    
    def _on_select_clicked(self):
        """Handle select button click"""
        if self.selected_component:
            self.component_selected.emit(self.selected_component)
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a component first.")
    
    def get_selected_component(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected component"""
        return self.selected_component