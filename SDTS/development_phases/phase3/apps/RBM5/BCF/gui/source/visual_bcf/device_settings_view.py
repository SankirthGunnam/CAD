"""
Device Settings View for Visual BCF MVC Pattern

This module provides the DeviceSettingsView class with a simple vertical layout
containing two tables: All Devices and Selected Devices.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                              QPushButton, QLabel, QHeaderView, QMessageBox)
from PySide6.QtCore import Signal, Qt, QModelIndex


class DeviceSettingsView(QWidget):
    """
    Simple Device Settings View with two tables in vertical layout.
    
    Contains:
    - All Devices table (top)
    - Selected Devices table (bottom)
    - Action buttons
    """
    
    # Signals for user actions
    device_add_requested = Signal(dict)  # device_data
    device_remove_requested = Signal(str)  # device_name
    device_update_requested = Signal(str, dict)  # device_name, updated_data
    device_selection_changed = Signal(str)  # selected_device_name
    refresh_requested = Signal()
    device_move_to_selected = Signal(str)  # device_name
    device_move_to_available = Signal(str)  # device_name
    
    def __init__(self, parent=None):
        """
        Initialize the device settings view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setObjectName("DeviceSettingsView")
        
        # UI components
        self.all_devices_table = None
        self.selected_devices_table = None
        self.move_to_selected_button = None
        self.move_to_available_button = None
        self.refresh_button = None
        
        # Current selections
        self._selected_device_name = None
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the simple vertical layout with two tables."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Device Settings")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # All Devices Table
        self._setup_all_devices_table(layout)
        
        # Action buttons between tables
        self._setup_action_buttons(layout)
        
        # Selected Devices Table
        self._setup_selected_devices_table(layout)
        
        # Bottom buttons
        self._setup_bottom_buttons(layout)
        
    def _setup_all_devices_table(self, parent_layout):
        """Setup the All Devices table."""
        # Label
        all_devices_label = QLabel("All Available Devices")
        all_devices_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 14px;")
        parent_layout.addWidget(all_devices_label)
        
        # Table
        self.all_devices_table = QTableView()
        self.all_devices_table.setObjectName("all_devices_table")
        self.all_devices_table.setSelectionBehavior(QTableView.SelectRows)
        self.all_devices_table.setSelectionMode(QTableView.SingleSelection)
        self.all_devices_table.setAlternatingRowColors(True)
        self.all_devices_table.setSortingEnabled(True)
        self.all_devices_table.setMinimumHeight(200)
        
        # Configure headers
        header = self.all_devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        parent_layout.addWidget(self.all_devices_table)
        
    def _setup_action_buttons(self, parent_layout):
        """Setup action buttons between tables."""
        button_layout = QHBoxLayout()
        
        self.move_to_selected_button = QPushButton("Add to Selected ↓")
        self.move_to_selected_button.setEnabled(False)
        self.move_to_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        self.move_to_available_button = QPushButton("Remove from Selected ↑")
        self.move_to_available_button.setEnabled(False)
        self.move_to_available_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        
        button_layout.addWidget(self.move_to_selected_button)
        button_layout.addWidget(self.move_to_available_button)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
        
    def _setup_selected_devices_table(self, parent_layout):
        """Setup the Selected Devices table."""
        # Label
        selected_devices_label = QLabel("Selected Devices")
        selected_devices_label.setStyleSheet("font-weight: bold; color: #34495e; font-size: 14px;")
        parent_layout.addWidget(selected_devices_label)
        
        # Table
        self.selected_devices_table = QTableView()
        self.selected_devices_table.setObjectName("selected_devices_table")
        self.selected_devices_table.setSelectionBehavior(QTableView.SelectRows)
        self.selected_devices_table.setSelectionMode(QTableView.SingleSelection)
        self.selected_devices_table.setAlternatingRowColors(True)
        self.selected_devices_table.setSortingEnabled(True)
        self.selected_devices_table.setMinimumHeight(200)
        
        # Configure headers
        header = self.selected_devices_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        parent_layout.addWidget(self.selected_devices_table)
        
    def _setup_bottom_buttons(self, parent_layout):
        """Setup bottom action buttons."""
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh All")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        
        parent_layout.addLayout(button_layout)
        
    def _connect_signals(self):
        """Connect internal signals."""
        # Button signals
        self.move_to_selected_button.clicked.connect(self._on_move_to_selected)
        self.move_to_available_button.clicked.connect(self._on_move_to_available)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        
        # Table selection signals
        if self.all_devices_table:
            self.all_devices_table.clicked.connect(self._on_all_devices_selection_changed)
            
        if self.selected_devices_table:
            self.selected_devices_table.clicked.connect(self._on_selected_devices_selection_changed)
        
    def set_all_devices_model(self, model):
        """
        Set the model for the all devices table.
        
        Args:
            model: The all devices model
        """
        if self.all_devices_table:
            self.all_devices_table.setModel(model)
            
    def set_selected_devices_model(self, model):
        """
        Set the model for the selected devices table.
        
        Args:
            model: The selected devices model
        """
        if self.selected_devices_table:
            self.selected_devices_table.setModel(model)
            
    def set_model(self, model):
        """
        Set the model for the main table (compatibility method).
        This sets the model for the all devices table by default.
        
        Args:
            model: The model to set
        """
        self.set_all_devices_model(model)
            
    def _on_all_devices_selection_changed(self, index):
        """Handle all devices table selection changes."""
        if index.isValid():
            model = self.all_devices_table.model()
            if model:
                # Get device name from first column
                device_name = model.data(model.index(index.row(), 0), Qt.DisplayRole)
                if device_name:
                    self._selected_device_name = device_name
                    self.move_to_selected_button.setEnabled(True)
                    self.move_to_available_button.setEnabled(False)
                    # Clear selected devices table selection
                    self.selected_devices_table.clearSelection()
                    self.device_selection_changed.emit(device_name)
        else:
            self._update_button_states()
            
    def _on_selected_devices_selection_changed(self, index):
        """Handle selected devices table selection changes."""
        if index.isValid():
            model = self.selected_devices_table.model()
            if model:
                # Get device name from first column
                device_name = model.data(model.index(index.row(), 0), Qt.DisplayRole)
                if device_name:
                    self._selected_device_name = device_name
                    self.move_to_selected_button.setEnabled(False)
                    self.move_to_available_button.setEnabled(True)
                    # Clear all devices table selection
                    self.all_devices_table.clearSelection()
                    self.device_selection_changed.emit(device_name)
        else:
            self._update_button_states()
            
    def _update_button_states(self):
        """Update button enabled states based on selections."""
        self.move_to_selected_button.setEnabled(False)
        self.move_to_available_button.setEnabled(False)
        
    def _on_move_to_selected(self):
        """Handle move to selected button click."""
        if self._selected_device_name:
            self.device_move_to_selected.emit(self._selected_device_name)
            self._clear_selections()
            
    def _on_move_to_available(self):
        """Handle move to available button click."""
        if self._selected_device_name:
            self.device_move_to_available.emit(self._selected_device_name)
            self._clear_selections()
            
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
        self._clear_selections()
        
    def _clear_selections(self):
        """Clear all table selections and reset button states."""
        self.all_devices_table.clearSelection()
        self.selected_devices_table.clearSelection()
        self._selected_device_name = None
        self._update_button_states()
        
    def clear_form(self):
        """Clear form (compatibility method)."""
        self._clear_selections()
        
    def clear_selection(self):
        """Clear selections (compatibility method)."""
        self._clear_selections()
        
    def enable_update_delete_buttons(self, enabled: bool):
        """Enable/disable update and delete buttons (compatibility method)."""
        # This view doesn't have update/delete buttons, so this is a no-op
        pass
        
    def populate_form(self, device_data: dict):
        """Populate form with device data (compatibility method)."""
        # This view doesn't have a form, so this is a no-op
        pass
        
    def get_selected_device(self):
        """Get currently selected device name."""
        return self._selected_device_name
        
    def show_message(self, title: str, message: str, message_type: str = "info"):
        """
        Show a message to the user.
        
        Args:
            title: Message title
            message: Message content
            message_type: Type of message (info, warning, error)
        """
        if message_type == "warning":
            QMessageBox.warning(self, title, message)
        elif message_type == "error":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
            
    def get_state(self) -> dict:
        """
        Get current view state.
        
        Returns:
            Dictionary containing current view state
        """
        return {
            'selected_device': self._selected_device_name
        }
        
    def refresh(self):
        """Refresh the view."""
        self._clear_selections()
