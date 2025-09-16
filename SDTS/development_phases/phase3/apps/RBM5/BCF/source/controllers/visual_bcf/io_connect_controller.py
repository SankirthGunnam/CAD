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

class IOConnectController(AbstractController):
    """
    Controller for IO connection functionality.

    This controller manages the interaction between the IOConnectModel
    and IOConnectView, handling business logic for IO connection management
    operations including CRUD operations, validation, auto-connections, and data synchronization.
    """

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

    def init_tab(self, revision: int):
        return super().init_tab(revision)
