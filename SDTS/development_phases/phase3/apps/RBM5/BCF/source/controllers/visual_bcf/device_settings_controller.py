"""
Device Settings Controller for Visual BCF MVC Pattern

This module provides the DeviceSettingsController class that coordinates between
the DeviceSettingsModel and DeviceSettingsView, implementing business logic
for device management functionality.
"""
from apps.RBM5.BCF.source.controllers.abstract_controller import AbstractController
from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import DeviceSettingsModel
from apps.RBM5.BCF.gui.source.visual_bcf.device_settings import View as DeviceSettingsView
from PySide6.QtCore import Signal


class DeviceSettingsController(AbstractController):
    """
    Controller for device settings functionality.

    This controller manages the interaction between the DeviceSettingsModel
    and DeviceSettingsView, handling business logic for device management
    operations including CRUD operations, validation, and data synchronization.
    """

    # Signals for device changes
    device_added = Signal(dict)  # device_data
    device_removed = Signal(dict)  # device_data
    device_updated = Signal(dict)  # device_data

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

        # Connect table model signals
        self._connect_table_signals()

    def _connect_table_signals(self):
        """Connect table model signals to handle changes"""
        # Connect MIPI devices table signals
        self._model.mipi_devices_model.row_added.connect(self._on_mipi_device_added)
        self._model.mipi_devices_model.row_removed.connect(self._on_mipi_device_removed)
        self._model.mipi_devices_model.row_updated.connect(self._on_mipi_device_updated)

        # Connect GPIO devices table signals
        self._model.gpio_devices_model.row_added.connect(self._on_gpio_device_added)
        self._model.gpio_devices_model.row_removed.connect(self._on_gpio_device_removed)
        self._model.gpio_devices_model.row_updated.connect(self._on_gpio_device_updated)

    def _on_mipi_device_added(self, row_index: int, device_data: dict):
        """Handle MIPI device added to table"""
        print(f"✓ MIPI device added at row {row_index}: {device_data}")
        self.device_added.emit(device_data)

    def _on_mipi_device_removed(self, row_index: int, device_data: dict):
        """Handle MIPI device removed from table"""
        print(f"✓ MIPI device removed from row {row_index}: {device_data}")
        self.device_removed.emit(device_data)

    def _on_mipi_device_updated(self, row_index: int, device_data: dict):
        """Handle MIPI device updated in table"""
        print(f"✓ MIPI device updated at row {row_index}: {device_data}")
        self.device_updated.emit(device_data)

    def _on_gpio_device_added(self, row_index: int, device_data: dict):
        """Handle GPIO device added to table"""
        print(f"✓ GPIO device added at row {row_index}: {device_data}")
        self.device_added.emit(device_data)

    def _on_gpio_device_removed(self, row_index: int, device_data: dict):
        """Handle GPIO device removed from table"""
        print(f"✓ GPIO device removed from row {row_index}: {device_data}")
        self.device_removed.emit(device_data)

    def _on_gpio_device_updated(self, row_index: int, device_data: dict):
        """Handle GPIO device updated in table"""
        print(f"✓ GPIO device updated at row {row_index}: {device_data}")
        self.device_updated.emit(device_data)

    def init_tab(self, revision: int):
        return super().init_tab(revision)