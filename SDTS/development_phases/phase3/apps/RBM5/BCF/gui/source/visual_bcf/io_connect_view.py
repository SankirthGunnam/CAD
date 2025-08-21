"""
IO Connect View for Visual BCF MVC Pattern

This module provides the IOConnectView class with a simple layout
containing just a single connections table.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView,

                               QPushButton, QLabel, QHeaderView, QMessageBox)
from PySide6.QtCore import Signal, Qt, QModelIndex


class IOConnectView(QWidget):
    """
    Simple IO Connect View with a single connections table.

    Contains:
    - Connection table
    - Action buttons (Add, Update, Delete, Auto Connect, Refresh)
    """

    # Signals for user actions
    connection_add_requested = Signal(dict)  # connection_data
    connection_remove_requested = Signal(str)  # connection_id
    connection_update_requested = Signal(
        str, dict)  # connection_id, updated_data
    connection_selection_changed = Signal(str)  # selected_connection_id
    auto_connect_requested = Signal()
    refresh_requested = Signal()

    def __init__(self, parent=None):
        """Initialize the IO connect view."""
        super().__init__(parent)
        self.setObjectName("IOConnectView")

        # UI components
        self.connection_table = None
        self.add_button = None
        self.update_button = None
        self.delete_button = None
        self.auto_connect_button = None
        self.refresh_button = None

        # Current selection
        self._selected_connection_id = None

        # Setup UI
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the simple layout with a single table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("IO Connections")
        title_label.setStyleSheet(
            "font-weight: bold; font-size: 16px; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Connections table
        self._setup_connections_table(layout)

        # Action buttons
        self._setup_action_buttons(layout)

    def _setup_connections_table(self, parent_layout):
        """Setup the connections table."""
        # Label
        table_label = QLabel("Connection List")
        table_label.setStyleSheet(
            "font-weight: bold; color: #34495e; font-size: 14px;")
        parent_layout.addWidget(table_label)

        # Table
        self.connection_table = QTableView()
        self.connection_table.setObjectName("connection_table")
        self.connection_table.setSelectionBehavior(QTableView.SelectRows)
        self.connection_table.setSelectionMode(QTableView.SingleSelection)
        self.connection_table.setAlternatingRowColors(True)
        self.connection_table.setSortingEnabled(True)
        self.connection_table.setMinimumHeight(400)

        # Configure headers
        header = self.connection_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        parent_layout.addWidget(self.connection_table)

    def _setup_action_buttons(self, parent_layout):
        """Setup action buttons."""
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Connection")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)

        self.update_button = QPushButton("Update Connection")
        self.update_button.setEnabled(False)
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

        self.delete_button = QPushButton("Delete Connection")
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)

        self.auto_connect_button = QPushButton("Auto Connect")
        self.auto_connect_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.auto_connect_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()

        parent_layout.addLayout(button_layout)

    def _connect_signals(self):
        """Connect internal signals."""
        # Button signals
        self.add_button.clicked.connect(self._on_add_clicked)
        self.update_button.clicked.connect(self._on_update_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.auto_connect_button.clicked.connect(self._on_auto_connect_clicked)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)

        # Table selection signals
        if self.connection_table:
            self.connection_table.clicked.connect(self._on_selection_changed)

    def set_model(self, model):
        """
        Set the model for the connections table.

        Args:
            model: The connections model
        """
        if self.connection_table:
            self.connection_table.setModel(model)

    def _on_selection_changed(self, index):
        """Handle table selection changes."""
        if index.isValid():
            model = self.connection_table.model()
            if model:
                # Get connection ID from first column (assuming ID is in first
                # column)
                connection_id = model.data(
                    model.index(index.row(), 0), Qt.DisplayRole)
                if connection_id:
                    self._selected_connection_id = connection_id
                    self.update_button.setEnabled(True)
                    self.delete_button.setEnabled(True)
                    self.connection_selection_changed.emit(connection_id)
        else:
            self._clear_selection()

    def _clear_selection(self):
        """Clear table selection and update button states."""
        self.connection_table.clearSelection()
        self._selected_connection_id = None
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def _on_add_clicked(self):
        """Handle add connection button click."""
        # For now, emit with empty data - in a real application,
        # this would open a dialog to collect connection data
        connection_data = {
            'source_device': 'CPU_MAIN',
            'source_pin': 'DATA_OUT',
            'dest_device': 'MEM_DDR4',
            'dest_pin': 'DATA_BUS',
            'type': 'Data'
        }
        self.connection_add_requested.emit(connection_data)

    def _on_update_clicked(self):
        """Handle update connection button click."""
        if self._selected_connection_id:
            # For now, emit with sample data - in a real application,
            # this would open a dialog with current connection data
            updated_data = {
                'source_device': 'CPU_MAIN',
                'source_pin': 'DATA_OUT_UPDATED',
                'dest_device': 'MEM_DDR4',
                'dest_pin': 'DATA_BUS',
                'type': 'Data'
            }
            self.connection_update_requested.emit(
                self._selected_connection_id, updated_data)

    def _on_delete_clicked(self):
        """Handle delete connection button click."""
        if self._selected_connection_id:
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete connection '{
                    self._selected_connection_id}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.connection_remove_requested.emit(
                    self._selected_connection_id)
                self._clear_selection()

    def _on_auto_connect_clicked(self):
        """Handle auto connect button click."""
        reply = QMessageBox.question(
            self,
            "Auto Connect",
            "Do you want to automatically create connections between compatible devices?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.auto_connect_requested.emit()

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self.refresh_requested.emit()
        self._clear_selection()

    def get_selected_connection(self):
        """Get currently selected connection ID."""
        return self._selected_connection_id

    def clear_form(self):
        """Clear form (compatibility method)."""
        self._clear_selection()

    def clear_selection(self):
        """Clear selections (compatibility method)."""
        self._clear_selection()

    def enable_update_delete_buttons(self, enabled: bool):
        """Enable/disable update and delete buttons."""
        self.update_button.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)

    def enable_auto_connect_button(self, enabled: bool):
        """Enable/disable auto connect button."""
        self.auto_connect_button.setEnabled(enabled)

    def populate_form(self, connection_data: dict):
        """Populate form with connection data (compatibility method)."""
        # This simplified view doesn't have a form, so this is a no-op
        pass

    def show_message(
            self,
            title: str,
            message: str,
            message_type: str = "info"):
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
            'selected_connection': self._selected_connection_id
        }

    def refresh(self):
        """Refresh the view."""
        self._clear_selection()
