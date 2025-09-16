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
from apps.RBM5.BCF.gui.source.visual_bcf.io_connect_view import IOConnectView


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
        """
        super().__init__(parent)

        self.rdb_manager = rdb_manager

        # Create Model and View instances
        self._model = IOConnectModel(parent=self, rdb=rdb_manager)
        self._view = IOConnectView(parent=parent)

        # Initialize MVC connections
        self._setup_mvc_connections()
        self.init_signals()

    def _setup_mvc_connections(self):
        """Setup connections between Model, View, and Controller."""
        # Connect View signals to Controller business logic methods
        self._view.connection_add_requested.connect(self._handle_add_connection)
        self._view.connection_remove_requested.connect(self._handle_remove_connection)
        self._view.connection_update_requested.connect(self._handle_update_connection)
        self._view.connection_selection_changed.connect(self._handle_selection_changed)
        self._view.auto_connect_requested.connect(self._handle_auto_connect)
        self._view.refresh_requested.connect(self._handle_refresh)

        # Set model to view (single table)
        if hasattr(self._model, 'connections_model'):
            self._view.set_model(self._model.connections_model)

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

        # Load available devices for connections
        self._load_available_devices()

        # Enable/disable UI components based on data state
        self._update_ui_state()

    def set_data(self, widget: str, index: typing.Union[QModelIndex, int], data: typing.Any):
        """
        Set data for a specific widget at given index.

        Args:
            widget (str): Widget identifier ('connections')
            index (Union[QModelIndex, int]): Index to set data at
            data (Any): Data to set
        """
        try:
            if widget == "connections" and hasattr(self._model, 'connections_model'):
                if isinstance(index, int):
                    # Convert integer index to QModelIndex if needed
                    model_index = self._model.connections_model.index(index, 0)
                else:
                    model_index = index

                # Set data in model
                success = self._model.connections_model.setData(model_index, data)
                if success:
                    self._update_ui_state()
                    self.gui_event.emit("data_updated", {"widget": widget, "index": index, "data": data})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Failed to set data: {str(e)}"})

    def _handle_add_connection(self, connection_data: dict):
        """
        Handle add connection request from view.

        Args:
            connection_data (dict): Connection data to add
        """
        try:
            # Validate connection data
            if not self._validate_connection_data(connection_data):
                self.gui_event.emit("validation_error", {"message": "Invalid connection data provided"})
                return

            # Check for connection conflicts
            conflicts = self._check_connection_conflicts(connection_data)
            if conflicts:
                self.gui_event.emit("validation_error", {"message": f"Connection conflicts detected: {', '.join(conflicts)}"})
                return

            # Add connection through model
            success = self._add_connection_to_model(connection_data)

            if success:
                # Clear form fields in view
                self._view.clear_form()

                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit("connection_added", {"connection": connection_data})
            else:
                self.gui_event.emit("error", {"message": "Failed to add connection"})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error adding connection: {str(e)}"})

    def _handle_remove_connection(self, connection_id: str):
        """
        Handle remove connection request from view.

        Args:
            connection_id (str): ID of connection to remove
        """
        try:
            # Check if connection can be safely removed
            if not self._can_remove_connection(connection_id):
                self.gui_event.emit("validation_error", {
                    "message": f"Cannot remove connection '{connection_id}' - it may be critical"
                })
                return

            # Remove connection through model
            success = self._remove_connection_from_model(connection_id)

            if success:
                # Clear form and selection in view
                self._view.clear_form()
                self._view.clear_selection()

                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit("connection_removed", {"connection_id": connection_id})
            else:
                self.gui_event.emit("error", {"message": f"Failed to remove connection '{connection_id}'"})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error removing connection: {str(e)}"})

    def _handle_update_connection(self, connection_id: str, updated_data: dict):
        """
        Handle update connection request from view.

        Args:
            connection_id (str): ID of connection to update
            updated_data (dict): Updated connection data
        """
        try:
            # Validate updated data
            if not self._validate_connection_data(updated_data):
                self.gui_event.emit("validation_error", {"message": "Invalid connection data provided"})
                return

            # Check for conflicts with the update
            conflicts = self._check_connection_conflicts(updated_data, exclude_id=connection_id)
            if conflicts:
                self.gui_event.emit("validation_error", {"message": f"Update would create conflicts: {', '.join(conflicts)}"})
                return

            # Update connection through model
            success = self._update_connection_in_model(connection_id, updated_data)

            if success:
                # Refresh view
                self._refresh_view_data()

                # Emit success event
                self.gui_event.emit("connection_updated", {"connection_id": connection_id, "data": updated_data})
            else:
                self.gui_event.emit("error", {"message": f"Failed to update connection '{connection_id}'"})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error updating connection: {str(e)}"})

    def _handle_selection_changed(self, connection_id: str):
        """
        Handle connection selection change from view.

        Args:
            connection_id (str): ID of selected connection
        """
        try:
            # Load connection data into form
            connection_data = self._get_connection_data(connection_id)

            if connection_data:
                self._view.populate_form(connection_data)
                self._view.enable_update_delete_buttons(True)
            else:
                self._view.clear_form()
                self._view.enable_update_delete_buttons(False)

            self.gui_event.emit("selection_changed", {"connection_id": connection_id})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error handling selection: {str(e)}"})

    def _handle_auto_connect(self):
        """Handle auto-connect request from view."""
        try:
            # Perform automatic connection logic
            created_connections = self._perform_auto_connect()

            if created_connections:
                # Refresh view to show new connections
                self._refresh_view_data()

                # Emit success event with details
                self.gui_event.emit("auto_connect_completed", {
                    "connections_created": len(created_connections),
                    "connections": created_connections
                })
            else:
                self.gui_event.emit("info", {"message": "No new auto-connections were created"})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error during auto-connect: {str(e)}"})

    def _handle_refresh(self):
        """Handle refresh request from view."""
        try:
            # Refresh model data
            if hasattr(self._model, 'change_model_data'):
                self._model.change_model_data()

            # Reload available devices
            self._load_available_devices()

            # Refresh view
            self._refresh_view_data()

            self.gui_event.emit("refreshed", {})

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error refreshing data: {str(e)}"})

    def _validate_connection_data(self, connection_data: dict) -> bool:
        """
        Validate connection data.

        Args:
            connection_data (dict): Connection data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['source_device', 'source_pin', 'dest_device', 'dest_pin']

        # Check required fields
        for field in required_fields:
            if field not in connection_data or not connection_data[field].strip():
                return False

        # Check that source and destination are different
        if (connection_data['source_device'] == connection_data['dest_device'] and
            connection_data['source_pin'] == connection_data['dest_pin']):
            return False

        # Additional validation logic
        if not self._validate_pin_compatibility(connection_data):
            return False

        return True

    def _validate_pin_compatibility(self, connection_data: dict) -> bool:
        """
        Validate pin compatibility for connection.

        Args:
            connection_data (dict): Connection data to validate

        Returns:
            bool: True if pins are compatible, False otherwise
        """
        # Business logic to check pin compatibility
        # For example, ensure power pins only connect to power pins
        source_pin = connection_data.get('source_pin', '')
        dest_pin = connection_data.get('dest_pin', '')

        # Power pin validation
        power_pins = ['VCC', 'VDD', 'GND', 'VSS']
        if any(pin in source_pin.upper() for pin in power_pins):
            if not any(pin in dest_pin.upper() for pin in power_pins):
                return False

        # Clock pin validation
        if 'CLK' in source_pin.upper() and 'CLK' not in dest_pin.upper():
            # Allow clock to connect to non-clock pins (clock distribution)
            pass

        return True

    def _check_connection_conflicts(self, connection_data: dict, exclude_id: str = None) -> typing.List[str]:
        """
        Check for connection conflicts.

        Args:
            connection_data (dict): Connection data to check
            exclude_id (str): Connection ID to exclude from conflict check

        Returns:
            List[str]: List of conflict messages
        """
        conflicts = []

        try:
            if hasattr(self._model, 'connections_model'):
                # Check for duplicate connections
                for row in range(self._model.connections_model.rowCount()):
                    # Get connection data from model
                    existing_data = self._get_connection_data_by_row(row)
                    if not existing_data:
                        continue

                    # Skip if this is the connection being updated
                    if exclude_id and existing_data.get('id') == exclude_id:
                        continue

                    # Check for exact duplicate
                    if (existing_data.get('source_device') == connection_data.get('source_device') and
                        existing_data.get('source_pin') == connection_data.get('source_pin') and
                        existing_data.get('dest_device') == connection_data.get('dest_device') and
                        existing_data.get('dest_pin') == connection_data.get('dest_pin')):
                        conflicts.append("Duplicate connection already exists")

                    # Check for pin conflicts (same pin used multiple times)
                    if self._pins_conflict(existing_data, connection_data):
                        conflicts.append(f"Pin conflict with existing connection {existing_data.get('id', 'unknown')}")

        except Exception as e:
            # Log error but don't fail validation
            pass

        return conflicts

    def _pins_conflict(self, existing_conn: dict, new_conn: dict) -> bool:
        """
        Check if two connections have pin conflicts.

        Args:
            existing_conn (dict): Existing connection data
            new_conn (dict): New connection data

        Returns:
            bool: True if there's a conflict, False otherwise
        """
        # Check if same source pin is used
        if (existing_conn.get('source_device') == new_conn.get('source_device') and
            existing_conn.get('source_pin') == new_conn.get('source_pin')):
            return True

        # Check if same destination pin is used
        if (existing_conn.get('dest_device') == new_conn.get('dest_device') and
            existing_conn.get('dest_pin') == new_conn.get('dest_pin')):
            return True

        return False

    def _can_remove_connection(self, connection_id: str) -> bool:
        """
        Check if connection can be safely removed.

        Args:
            connection_id (str): Connection ID to check

        Returns:
            bool: True if can be removed, False otherwise
        """
        # Business logic to check if connection is critical
        # For now, allow all removals
        return True

    def _add_connection_to_model(self, connection_data: dict) -> bool:
        """Add connection to model."""
        try:
            if hasattr(self._model, 'connections_model'):
                return self._model.connections_model.insertRow(self._model.connections_model.rowCount())
            return False
        except:
            return False

    def _remove_connection_from_model(self, connection_id: str) -> bool:
        """Remove connection from model."""
        try:
            if hasattr(self._model, 'connections_model'):
                # Find connection row and remove it
                for row in range(self._model.connections_model.rowCount()):
                    index = self._model.connections_model.index(row, 0)
                    if self._model.connections_model.data(index) == connection_id:
                        return self._model.connections_model.removeRow(row)
            return False
        except:
            return False

    def _update_connection_in_model(self, connection_id: str, updated_data: dict) -> bool:
        """Update connection in model."""
        try:
            # Find and update connection data in model
            # Implementation would depend on model structure
            return True  # Placeholder
        except:
            return False

    def _get_connection_data(self, connection_id: str) -> typing.Optional[dict]:
        """Get connection data from model."""
        try:
            # Retrieve connection data from model
            # Implementation would depend on model structure
            return {
                "id": connection_id,
                "source_device": "CPU_MAIN",
                "source_pin": "DATA_OUT",
                "dest_device": "MEM_DDR4",
                "dest_pin": "DATA_BUS",
                "type": "Data",
                "status": "Active"
            }
        except:
            return None

    def _get_connection_data_by_row(self, row: int) -> typing.Optional[dict]:
        """Get connection data by table row."""
        try:
            if hasattr(self._model, 'connections_model'):
                # Get data from model row
                # Implementation would depend on model structure
                return {"id": f"CONN_{row:03d}", "source_device": "Device", "source_pin": "Pin"}
            return None
        except:
            return None

    def _perform_auto_connect(self) -> typing.List[dict]:
        """
        Perform automatic connection logic.

        Returns:
            List[dict]: List of created connections
        """
        created_connections = []

        try:
            # Get available devices
            devices = self._get_available_devices()

            # Auto-connect power pins
            power_connections = self._auto_connect_power_pins(devices)
            created_connections.extend(power_connections)

            # Auto-connect clock pins
            clock_connections = self._auto_connect_clock_pins(devices)
            created_connections.extend(clock_connections)

            # Auto-connect data buses
            data_connections = self._auto_connect_data_buses(devices)
            created_connections.extend(data_connections)

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error during auto-connect: {str(e)}"})

        return created_connections

    def _auto_connect_power_pins(self, devices: typing.List[dict]) -> typing.List[dict]:
        """Auto-connect power pins between devices."""
        connections = []

        # Find devices with power pins
        vcc_devices = [d for d in devices if 'VCC' in d.get('pins', [])]
        gnd_devices = [d for d in devices if 'GND' in d.get('pins', [])]

        # Connect VCC pins in a power distribution pattern
        if len(vcc_devices) > 1:
            source_device = vcc_devices[0]  # Use first as power source
            for dest_device in vcc_devices[1:]:
                connection_data = {
                    'source_device': source_device['name'],
                    'source_pin': 'VCC',
                    'dest_device': dest_device['name'],
                    'dest_pin': 'VCC',
                    'type': 'Power'
                }

                if self._validate_connection_data(connection_data) and not self._check_connection_conflicts(connection_data):
                    if self._add_connection_to_model(connection_data):
                        connections.append(connection_data)

        # Similar for GND pins
        if len(gnd_devices) > 1:
            source_device = gnd_devices[0]
            for dest_device in gnd_devices[1:]:
                connection_data = {
                    'source_device': source_device['name'],
                    'source_pin': 'GND',
                    'dest_device': dest_device['name'],
                    'dest_pin': 'GND',
                    'type': 'Ground'
                }

                if self._validate_connection_data(connection_data) and not self._check_connection_conflicts(connection_data):
                    if self._add_connection_to_model(connection_data):
                        connections.append(connection_data)

        return connections

    def _auto_connect_clock_pins(self, devices: typing.List[dict]) -> typing.List[dict]:
        """Auto-connect clock pins between devices."""
        connections = []

        # Find clock sources and destinations
        clock_sources = [d for d in devices if any('CLK' in pin for pin in d.get('pins', [])) and d.get('type') == 'Processor']
        clock_destinations = [d for d in devices if any('CLK' in pin for pin in d.get('pins', [])) and d.get('type') != 'Processor']

        for source_device in clock_sources:
            source_clk_pins = [pin for pin in source_device.get('pins', []) if 'CLK' in pin]

            for dest_device in clock_destinations:
                dest_clk_pins = [pin for pin in dest_device.get('pins', []) if 'CLK' in pin]

                if source_clk_pins and dest_clk_pins:
                    connection_data = {
                        'source_device': source_device['name'],
                        'source_pin': source_clk_pins[0],
                        'dest_device': dest_device['name'],
                        'dest_pin': dest_clk_pins[0],
                        'type': 'Clock'
                    }

                    if self._validate_connection_data(connection_data) and not self._check_connection_conflicts(connection_data):
                        if self._add_connection_to_model(connection_data):
                            connections.append(connection_data)

        return connections

    def _auto_connect_data_buses(self, devices: typing.List[dict]) -> typing.List[dict]:
        """Auto-connect data buses between compatible devices."""
        connections = []

        # Find processors and memory devices
        processors = [d for d in devices if d.get('type') == 'Processor']
        memories = [d for d in devices if d.get('type') == 'Memory']

        for processor in processors:
            proc_data_pins = [pin for pin in processor.get('pins', []) if 'DATA' in pin]

            for memory in memories:
                mem_data_pins = [pin for pin in memory.get('pins', []) if 'DATA' in pin]

                if proc_data_pins and mem_data_pins:
                    connection_data = {
                        'source_device': processor['name'],
                        'source_pin': proc_data_pins[0],
                        'dest_device': memory['name'],
                        'dest_pin': mem_data_pins[0],
                        'type': 'Data'
                    }

                    if self._validate_connection_data(connection_data) and not self._check_connection_conflicts(connection_data):
                        if self._add_connection_to_model(connection_data):
                            connections.append(connection_data)

        return connections

    def _load_revision_data(self, revision: int):
        """Load data for specific revision."""
        # Load revision-specific data
        # This would integrate with RDB manager
        pass

    def _load_available_devices(self):
        """Load available devices for connections."""
        try:
            # Get devices from device settings or other sources
            devices = self._get_available_devices()

            # Update view with device information
            if hasattr(self._view, 'update_device_tree'):
                self._view.update_device_tree(devices)

            if hasattr(self._view, 'update_device_combos'):
                self._view.update_device_combos(devices)

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error loading devices: {str(e)}"})

    def _get_available_devices(self) -> typing.List[dict]:
        """Get list of available devices for connections."""
        # This would interface with device settings model or RDB
        # For now, return sample data
        return [
            {
                'name': 'CPU_MAIN',
                'type': 'Processor',
                'pins': ['CLK_IN', 'DATA_IN', 'DATA_OUT', 'RESET', 'VCC', 'GND']
            },
            {
                'name': 'MEM_DDR4',
                'type': 'Memory',
                'pins': ['DATA_BUS', 'ADDR_BUS', 'CLK', 'CS', 'WE', 'OE', 'VCC', 'GND']
            },
            {
                'name': 'IO_CTRL',
                'type': 'Input/Output',
                'pins': ['GPIO_0', 'GPIO_1', 'GPIO_2', 'GPIO_3', 'INT_OUT', 'VCC', 'GND']
            }
        ]

    def _refresh_view_data(self):
        """Refresh view with current model data."""
        try:
            # Refresh table view
            if hasattr(self._view, 'connection_table') and self._view.connection_table.model():
                self._view.connection_table.model().layoutChanged.emit()

            # Update other UI components as needed
            self._update_ui_state()

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error refreshing view: {str(e)}"})

    def _update_ui_state(self):
        """Update UI state based on current data."""
        try:
            # Enable/disable buttons based on current state
            has_selection = self._view.get_selected_connection() is not None
            self._view.enable_update_delete_buttons(has_selection)

            # Update device availability
            devices = self._get_available_devices()
            has_devices = len(devices) > 0
            self._view.enable_auto_connect_button(has_devices)

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error updating UI state: {str(e)}"})

    def get_widget(self):
        """
        Get the main widget for this controller.

        Returns:
            QWidget: The main view widget
        """
        return self._view

    def get_connections_for_device(self, device_name: str) -> typing.List[dict]:
        """
        Business logic: Get all connections involving a specific device.

        Args:
            device_name (str): Name of the device

        Returns:
            List[dict]: List of connections involving the device
        """
        connections = []

        try:
            if hasattr(self._model, 'connections_model'):
                for row in range(self._model.connections_model.rowCount()):
                    connection_data = self._get_connection_data_by_row(row)

                    if connection_data and (
                        connection_data.get('source_device') == device_name or
                        connection_data.get('dest_device') == device_name
                    ):
                        connections.append(connection_data)

        except Exception as e:
            self.gui_event.emit("error", {"message": f"Error getting device connections: {str(e)}"})

        return connections

    def validate_all_connections(self) -> typing.List[str]:
        """
        Business logic: Validate all existing connections.

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        try:
            if hasattr(self._model, 'connections_model'):
                for row in range(self._model.connections_model.rowCount()):
                    connection_data = self._get_connection_data_by_row(row)

                    if connection_data:
                        if not self._validate_connection_data(connection_data):
                            errors.append(f"Invalid connection: {connection_data.get('id', 'unknown')}")

        except Exception as e:
            errors.append(f"Error during validation: {str(e)}")

        return errors
