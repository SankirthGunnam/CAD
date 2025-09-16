"""
Device Settings Controller for Visual BCF MVC Pattern

This module provides the DeviceSettingsController class that coordinates between
the DeviceSettingsModel and DeviceSettingsView, implementing business logic
for device management functionality.
"""
from apps.RBM5.BCF.source.controllers.abstract_controller import AbstractController
from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import DeviceSettingsModel
from apps.RBM5.BCF.gui.source.visual_bcf.device_settings import View as DeviceSettingsView


class DeviceSettingsController(AbstractController):
    """
    Controller for device settings functionality.

    This controller manages the interaction between the DeviceSettingsModel
    and DeviceSettingsView, handling business logic for device management
    operations including CRUD operations, validation, and data synchronization.
    """

    def __init__(self, rdb_manager, parent=None):
        """
        Initialize the device settings controller.

        Args:
            rdb_manager: Database manager instance for data operations
            parent: Parent QObject
            data_model: Reference to Visual BCF data model for single source of truth
        """
        super().__init__(parent)
        print(f"✓ Device Settings controller initialized with parent: {parent}")
        self.rdb_manager = rdb_manager

        # Create Model and View instances
        self._model = DeviceSettingsModel(controller=self, rdb=rdb_manager)
        print(f"✓ Device Settings model initialized with controller: {self._model}")
        self._view = DeviceSettingsView(controller=self, model=self._model)
        print(f"✓ Device Settings view initialized with controller: {self._view}")

    def init_tab(self, revision: int):
        return super().init_tab(revision)