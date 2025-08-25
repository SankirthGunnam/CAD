"""
Device Settings Controller for Visual BCF MVC Pattern

This module provides the DeviceSettingsController class that coordinates between
the DeviceSettingsModel and DeviceSettingsView, implementing business logic
for device management functionality.
"""

import typing

from PySide6.QtCore import QModelIndex

from apps.RBM5.BCF.source.controllers.abstract_controller import AbstractController
from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import DeviceSettingsModel
from apps.RBM5.BCF.gui.source.visual_bcf.device_settings_view import DeviceSettingsView

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
        """
        super().__init__(parent)

        self.rdb_manager = rdb_manager

        # Create Model and View instances
        self._model = DeviceSettingsModel(parent=self, rdb=rdb_manager)
        self._view = DeviceSettingsView(parent=parent)

        # Initialize MVC connections
        self._setup_mvc_connections()
        self.init_signals()

    def _setup_mvc_connections(self):
        """Setup connections between Model, View, and Controller."""
        # Connect View signals to Controller business logic methods
        self._view.device_add_requested.connect(self._handle_add_device)
        self._view.device_remove_requested.connect(self._handle_remove_device)
        self._view.device_update_requested.connect(self._handle_update_device)
        self._view.device_selection_changed.connect(
            self._handle_selection_changed)
        self._view.refresh_requested.connect(self._handle_refresh)

        # Set models to views (for two tables)
        if hasattr(self._model, 'all_devices_model'):
            # For now, we'll use the all_devices_model for the main table
            # This would be extended to support both tables in the view
            self._view.set_model(self._model.all_devices_model)

    def init_tab(self, revision: int):
        """
        Initialize the tab with specified revision.

        Args:
            revision (int): The revision number for initialization
        """
        # Load data for the specified revision
        self._load_revision_data(revision)

        # Update view with current data
        self._refresh_view_data()

        # Enable/disable UI components based on data state
        self._update_ui_state()

    def set_data(self,
                 widget: str,
                 index: typing.Union[QModelIndex,
                                     int],
                 data: typing.Any):
        """
        Set data for a specific widget at given index.

        Args:
            widget (str): Widget identifier ('all_devices' or 'selected_devices')
            index (Union[QModelIndex, int]): Index to set data at
            data (Any): Data to set
        """
        try:
            if widget == "all_devices" and hasattr(
                    self._model, 'all_devices_model'):
                if isinstance(index, int):
                    # Convert integer index to QModelIndex if needed
                    model_index = self._model.all_devices_model.index(index, 0)
                else:
                    model_index = index

                # Set data in model
                success = self._model.all_devices_model.setData(
                    model_index, data)
                if success:
                    self._update_ui_state()
                    self.gui_event.emit(
                        "data_updated", {
                            "widget": widget, "index": index, "data": data})

            elif widget == "selected_devices" and hasattr(self._model, 'selected_devices_model'):
                if isinstance(index, int):
                    model_index = self._model.selected_devices_model.index(
                        index, 0)
                else:
                    model_index = index

                success = self._model.selected_devices_model.setData(
                    model_index, data)
                if success:
                    self._update_ui_state()
                    self.gui_event.emit(
                        "data_updated", {
                            "widget": widget, "index": index, "data": data})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Failed to set data: {str(e)}"})

    def _handle_add_device(self, device_data: dict):
        """
        Handle add device request from view.

        Args:
            device_data (dict): Device data to add
        """
        try:
            # Validate device data
            if not self._validate_device_data(device_data):
                self.gui_event.emit(
                    "validation_error", {
                        "message": "Invalid device data provided"})
                return

            # Check for duplicate device names
            if self._device_name_exists(device_data.get('name', '')):
                self.gui_event.emit(
                    "validation_error", {
                        "message": f"Device '{device_data['name']}' already exists"})
                return

            # Add device through model
            success = self._add_device_to_model(device_data)

            if success:
                # Clear form fields in view
                self._view.clear_form()

                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit("device_added", {"device": device_data})
            else:
                self.gui_event.emit("error",
                                    {"message": "Failed to add device"})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error adding device: {str(e)}"})

    def _handle_remove_device(self, device_name: str):
        """
        Handle remove device request from view.

        Args:
            device_name (str): Name of device to remove
        """
        try:
            # Check if device can be safely removed
            if not self._can_remove_device(device_name):
                self.gui_event.emit(
                    "validation_error", {
                        "message": f"Cannot remove device '{device_name}' - it may have dependencies"})
                return

            # Remove device through model
            success = self._remove_device_from_model(device_name)

            if success:
                # Clear form and selection in view
                self._view.clear_form()
                self._view.clear_selection()

                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit(
                    "device_removed", {
                        "device_name": device_name})
            else:
                self.gui_event.emit(
                    "error", {
                        "message": f"Failed to remove device '{device_name}'"})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error removing device: {str(e)}"})

    def _handle_update_device(self, device_name: str, updated_data: dict):
        """
        Handle update device request from view.

        Args:
            device_name (str): Name of device to update
            updated_data (dict): Updated device data
        """
        try:
            # Validate updated data
            if not self._validate_device_data(updated_data):
                self.gui_event.emit(
                    "validation_error", {
                        "message": "Invalid device data provided"})
                return

            # Update device through model
            success = self._update_device_in_model(device_name, updated_data)

            if success:
                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit(
                    "device_updated", {
                        "device_name": device_name, "data": updated_data})
            else:
                self.gui_event.emit(
                    "error", {
                        "message": f"Failed to update device '{device_name}'"})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error updating device: {str(e)}"})

    def _handle_selection_changed(self, device_name: str):
        """
        Handle device selection change from view.

        Args:
            device_name (str): Name of selected device
        """
        try:
            # Load device data into form
            device_data = self._get_device_data(device_name)

            if device_data:
                self._view.populate_form(device_data)
                self._view.enable_update_delete_buttons(True)
            else:
                self._view.clear_form()
                self._view.enable_update_delete_buttons(False)

            self.gui_event.emit(
                "selection_changed", {
                    "device_name": device_name})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error handling selection: {str(e)}"})

    def _handle_refresh(self):
        """Handle refresh request from view."""
        try:
            # Refresh model data
            if hasattr(self._model, 'change_model_data'):
                self._model.change_model_data()

            # Refresh view
            self._refresh_view_data()

            self.gui_event.emit("refreshed", {})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error refreshing data: {str(e)}"})

    def _validate_device_data(self, device_data: dict) -> bool:
        """
        Validate device data.

        Args:
            device_data (dict): Device data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['name', 'type', 'function']

        for field in required_fields:
            if field not in device_data or not device_data[field].strip():
                return False

        # Additional validation logic can be added here
        return True

    def _device_name_exists(self, device_name: str) -> bool:
        """
        Check if device name already exists.

        Args:
            device_name (str): Device name to check

        Returns:
            bool: True if exists, False otherwise
        """
        # This would query the model/database to check for existing device
        # For now, we'll implement basic logic
        try:
            if hasattr(self._model, 'all_devices_model'):
                # Check if device name exists in model
                for row in range(self._model.all_devices_model.rowCount()):
                    index = self._model.all_devices_model.index(
                        row, 0)  # Assuming name is in column 0
                    existing_name = self._model.all_devices_model.data(index)
                    if existing_name == device_name:
                        return True
            return False
        except BaseException:
            return False

    def _can_remove_device(self, device_name: str) -> bool:
        """
        Check if device can be safely removed.

        Args:
            device_name (str): Device name to check

        Returns:
            bool: True if can be removed, False otherwise
        """
        # Business logic to check dependencies
        # For example, check if device is used in connections
        # This would integrate with other models/controllers
        return True  # For now, allow all removals

    def _add_device_to_model(self, device_data: dict) -> bool:
        """Add device to model."""
        try:
            # Add to appropriate model (would be extended for two-table setup)
            if hasattr(self._model, 'all_devices_model'):
                return self._model.all_devices_model.insertRow(
                    self._model.all_devices_model.rowCount())
            return False
        except BaseException:
            return False

    def _remove_device_from_model(self, device_name: str) -> bool:
        """Remove device from model."""
        try:
            if hasattr(self._model, 'all_devices_model'):
                # Find device row and remove it
                for row in range(self._model.all_devices_model.rowCount()):
                    index = self._model.all_devices_model.index(row, 0)
                    if self._model.all_devices_model.data(
                            index) == device_name:
                        return self._model.all_devices_model.removeRow(row)
            return False
        except BaseException:
            return False

    def _update_device_in_model(
            self,
            device_name: str,
            updated_data: dict) -> bool:
        """Update device in model."""
        try:
            # Find and update device data in model
            # Implementation would depend on model structure
            return True  # Placeholder
        except BaseException:
            return False

    def _get_device_data(self, device_name: str) -> typing.Optional[dict]:
        """Get device data from model."""
        try:
            # Retrieve device data from model
            # Implementation would depend on model structure
            return {
                "name": device_name,
                "type": "Unknown",
                "function": "Unknown",
                "status": "Active"}
        except BaseException:
            return None

    def _load_revision_data(self, revision: int):
        """Load data for specific revision."""
        # Load revision-specific data
        # This would integrate with RDB manager
        pass

    def _refresh_view_data(self):
        """Refresh view with current model data."""
        try:
            # Refresh table views
            if hasattr(
                    self._view,
                    'table_view') and self._view.table_view.model():
                self._view.table_view.model().layoutChanged.emit()

            # Update other UI components as needed
            self._update_ui_state()

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error refreshing view: {str(e)}"})

    def _update_ui_state(self):
        """Update UI state based on current data."""
        try:
            # Enable/disable buttons based on current state
            has_selection = self._view.get_selected_device() is not None
            self._view.enable_update_delete_buttons(has_selection)

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error updating UI state: {str(e)}"})

    def get_widget(self):
        """
        Get the main widget for this controller.

        Returns:
            QWidget: The main view widget
        """
        return self._view

    def move_device_to_selected(self, device_name: str):
        """
        Business logic: Move device from available to selected list.

        Args:
            device_name (str): Name of device to move
        """
        try:
            # Get device data from all_devices_model
            device_data = self._get_device_data(device_name)

            if device_data and hasattr(self._model, 'selected_devices_model'):
                # Add to selected devices model
                success = self._model.selected_devices_model.insertRow(
                    self._model.selected_devices_model.rowCount()
                )

                if success:
                    # Optionally remove from all_devices if needed
                    self.gui_event.emit(
                        "device_moved_to_selected", {
                            "device_name": device_name})

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error moving device: {str(e)}"})

    def move_device_to_available(self, device_name: str):
        """
        Business logic: Move device from selected to available list.

        Args:
            device_name (str): Name of device to move
        """
        try:
            # Remove from selected devices model
            if hasattr(self._model, 'selected_devices_model'):
                for row in range(
                        self._model.selected_devices_model.rowCount()):
                    index = self._model.selected_devices_model.index(row, 0)
                    if self._model.selected_devices_model.data(
                            index) == device_name:
                        success = self._model.selected_devices_model.removeRow(
                            row)

                        if success:
                            self.gui_event.emit(
                                "device_moved_to_available", {
                                    "device_name": device_name})
                        break

        except Exception as e:
            self.gui_event.emit(
                "error", {
                    "message": f"Error moving device: {str(e)}"})
