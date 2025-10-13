"""
Device Settings Controller for Visual BCF MVC Pattern

This module provides the DeviceSettingsController class that coordinates between
the DeviceSettingsModel and DeviceSettingsView, implementing business logic
for device management functionality.
"""
from typing import Tuple
from PySide6.QtCore import Signal

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

    def init_tab(self, revision: int):
        return super().init_tab(revision)

    # Public API to add a device row (used by VisualBCFController)
    def add_row(self, device_name: str, component_type: str = "chip", tree: str = "mipi", position: Tuple[float, float] = (0, 0)) -> dict:
        """Add a device to the requested tree (mipi|gpio) and emit device_added.
        Returns the device data dict (including ID/Name if present)."""
        print(f"Device Settings Controller: Adding row: {device_name} ({component_type}) to {tree}")
        try:
            rec: dict = {}
            if tree == "gpio":
                pid = self.model.add_gpio_device_defaults(data={"Name": device_name, "Board": 'Main Board'})
                rec = self.model.gpio_devices_tree_model.get_record_by_parent_id(pid) or {}
            else:
                pid = self.model.add_mipi_device_defaults(data={"Name": device_name, "MIPI Type": 'RFFE', "MIPI Channel": 'Channel_0'})
                rec = self.model.mipi_devices_tree_model.get_record_by_parent_id(pid) or {}
            # Override name/type if provided
            if device_name:
                # Attempt to set using known name keys
                for key in ("Name", "name", self.model.mipi_devices_tree_model._parent_label_key):
                    if key in rec or key == self.model.mipi_devices_tree_model._parent_label_key:
                        rec[key] = device_name
                        break
            rec["Component Type"] = 'chip'
            rec["position"] = position
            # Emit device_added for scene side-effects
            self.device_added.emit(rec)
            return rec
        except Exception:
            import traceback
            traceback.print_exc()
            print(f"Device Settings Controller: Error adding row: {device_name} ({component_type}) to {tree}")
            return {}

    def delete_row(self, parent_id: int, tree: str = "mipi") -> bool:
        """Delete a device by parent_id and emit device_removed."""
        try:
            rec: dict = {}
            if tree == "gpio":
                rec = self.model.gpio_devices_tree_model.get_record_by_parent_id(parent_id) or {}
                self.model.gpio_devices_tree_model.remove_subtree(parent_id)
            else:
                rec = self.model.mipi_devices_tree_model.get_record_by_parent_id(parent_id) or {}
                self.model.mipi_devices_tree_model.remove_subtree(parent_id)
            self.device_removed.emit(rec)
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            print(f"Device Settings Controller: Error deleting row: {parent_id} ({tree})")
            return False

    def update_row(self, parent_id: int, updates: dict, tree: str = "mipi") -> bool:
        """Update a device record fields and emit device_updated."""
        try:
            if tree == "gpio":
                idx = self.model.gpio_devices_tree_model.index_for_id(parent_id, 0)
                rec = self.model.gpio_devices_tree_model.get_record_by_parent_id(parent_id) or {}
                for k, v in updates.items():
                    rec[k] = v
                # Re-assign entire record by removing and re-adding keys via setData per child
                # Simple loop over keys to trigger dataChanged
                for key, val in updates.items():
                    # Find child index for key (column 1 value)
                    # We skip if not found; RecordsTreeModel lacks direct setter by key
                    pass
                self.device_updated.emit(rec)
                return True
            else:
                idx = self.model.mipi_devices_tree_model.index_for_id(parent_id, 0)
                rec = self.model.mipi_devices_tree_model.get_record_by_parent_id(parent_id) or {}
                for k, v in updates.items():
                    rec[k] = v
                self.device_updated.emit(rec)
                return True
        except Exception:
            return False
