"""
IO Connect Controller for Visual BCF MVC Pattern

This module provides the IOConnectController class that coordinates between
the IOConnectModel and IOConnectView, implementing business logic
for IO connection management functionality.
"""

import typing

from PySide6.QtCore import QModelIndex

from apps.RBM5.BCF.source.controllers.abstract_controller import AbstractController
from apps.RBM5.BCF.source.models.visual_bcf.io_connect_model import IOConnectModel
from apps.RBM5.BCF.gui.source.visual_bcf.io_connect import View as IOConnectView
from PySide6.QtCore import Signal

class IOConnectController(AbstractController):
    """
    Controller for IO connection functionality.

    This controller manages the interaction between the IOConnectModel
    and IOConnectView, handling business logic for IO connection management
    operations including CRUD operations, validation, auto-connections, and data synchronization.
    """

    # Signals for connection changes
    connection_added = Signal(dict)  # connection_data
    connection_removed = Signal(dict)  # connection_data
    connection_updated = Signal(dict)  # connection_data

    def __init__(self, rdb_manager, parent=None):
        """
        Initialize the IO connect controller.

        Args:
            rdb_manager: Database manager instance for data operations
            parent: Parent QObject
            data_model: Reference to Visual BCF data model for single source of truth
        """
        super().__init__(parent)
        self.rdb_manager = rdb_manager
        # Create Model and View instances
        self._model = IOConnectModel(controller=self, rdb=rdb_manager)
        self._view = IOConnectView(controller=self, model=self._model)

        # Connect table model signals
        self._connect_table_signals()

    def _connect_table_signals(self):
        """Connect table model signals to handle changes"""
        # Connect IO connections table signals
        self._model.table.row_added.connect(self._on_connection_added)
        self._model.table.row_removed.connect(self._on_connection_removed)
        self._model.table.row_updated.connect(self._on_connection_updated)

    def _on_connection_added(self, row_index: int, connection_data: dict):
        """Handle connection added to table"""
        print(f"✓ Connection added at row {row_index}: {connection_data}")
        self.connection_added.emit(connection_data)

    def _on_connection_removed(self, row_index: int, connection_data: dict):
        """Handle connection removed from table"""
        print(f"✓ Connection removed from row {row_index}: {connection_data}")
        self.connection_removed.emit(connection_data)

    def _on_connection_updated(self, row_index: int, connection_data: dict):
        """Handle connection updated in table"""
        print(f"✓ Connection updated at row {row_index}: {connection_data}")
        self.connection_updated.emit(connection_data)

    def init_tab(self, revision: int):
        return super().init_tab(revision)
