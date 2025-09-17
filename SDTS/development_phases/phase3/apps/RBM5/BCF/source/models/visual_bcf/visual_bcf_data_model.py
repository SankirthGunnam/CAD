"""
Visual BCF Data Access Model

This model acts as a bridge between Visual BCF graphics components and Legacy BCF table data.
It provides a unified interface for Visual BCF to access component data, connection data,
and properties data from the underlying JSON database tables used by Legacy BCF.
"""

import traceback
from typing import Dict, List, Any, Optional, Tuple
import uuid
import logging
from PySide6.QtCore import QObject, Signal

import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.RDB.paths import (
    DCF_DEVICES,
    BCF_DEV_MIPI,
    BCF_DEV_GPIO,
    BCF_DB_IO_CONNECT,
    CURRENT_REVISION,
    BCF_DCF_FOR_BCF
)

logger = logging.getLogger(__name__)


# Removed ComponentData and ConnectionData classes - using RDB dictionaries directly


class VisualBCFDataModel(QObject):
    """
    Data access model for Visual BCF that interfaces with Legacy BCF table data.

    This model provides methods to:
    - Read/Write component data from Legacy BCF tables
    - Manage component positions and visual properties
    - Handle connections between components
    - Synchronize with Legacy BCF changes
    - Manage device settings and IO connections using single source of truth
    """

    # Signals
    component_added = Signal(str)  # component_id
    component_removed = Signal(str)  # component_id
    component_updated = Signal(str, dict)  # component_id, updated_data
    connection_added = Signal(str)  # connection_id
    connection_removed = Signal(str)  # connection_id
    connection_updated = Signal(str, dict)  # connection_id, updated_data
    data_synchronized = Signal()  # When data sync is complete

    @property
    def revision(self):
        return self.rdb_manager[paths.CURRENT_REVISION]

    @property
    def antenn_names(self):
        return self.rdb_manager[paths.BCF_DB_ANT(self.revision)]
    
    def visual_properties(self, component_id: str):
        return self.rdb_manager[paths.VISUAL_PROPERTIES].get(component_id, {"position": {"x": 0, "y": 0}})
    
    def __init__(self, rdb_manager: RDBManager):
        super().__init__()
        self.rdb_manager = rdb_manager

        # Table paths using centralized paths from paths.py - SINGLE SOURCE OF TRUTH
        # Visual components and connections (for graphics scene)
        
        # Device configuration tables (from RDB)
        self.mipi_devices_path = str(BCF_DEV_MIPI("1.0.0"))  # Will be updated with current revision
        self.gpio_devices_path = str(BCF_DEV_GPIO("1.0.0"))  # Will be updated with current revision
        self.io_connections_path = str(BCF_DB_IO_CONNECT)
        self.dcf_devices_path = str(DCF_DEVICES)
        self.dcf_for_bcf_path = str(BCF_DCF_FOR_BCF("1.0.0"))  # Will be updated with current revision
        
        # Component configurations (JSON file)
        self.component_configs = self.rdb_manager[paths.COMPONENT_CONFIGS] or {}

        # Connect to database changes
        self.rdb_manager.data_changed.connect(self._on_data_changed)

        # Initialize database structure if needed
        self.init_tab()

        # Update device table paths with current revision
        self._update_device_table_paths()

    def init_tab(self):
        """Initialize Visual BCF tables in the database if they don't exist"""
        try:
            # Check if Visual BCF section exists
            visual_bcf_data = self.rdb_manager.get_value("config.visual_bcf")
            if not visual_bcf_data:
                # Create the Visual BCF section with empty tables
                initial_data = {
                    "components": [],
                    "connections": [],
                    "layout": {
                        "scene_rect": {
                            "x": -1000,
                            "y": -1000,
                            "width": 2000,
                            "height": 2000},
                        "grid_settings": {
                            "enabled": True,
                            "size": 20}},
                    "visual_properties": {}
                }
                self.rdb_manager.set_value("config.visual_bcf", initial_data)
                logger.info("Initialized Visual BCF tables in database")
        except Exception as e:
            logger.error("Error initializing Visual BCF tables: %s", e)

    def component_dcf(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Device Configuration (DCF) for a specific device name
        
        Args:
            device_name: Name of the device to get configuration for
            
        Returns:
            Dictionary containing device configuration including pins, visual properties, etc.
            Returns None if device not found
        """
        try:
            # First try to get from component configurations
            if device_name in self.component_configs:
                return self.component_configs[device_name]
            
            # If not found in component configs, try to get from DCF_FOR_BCF table
            self._update_device_table_paths()
            dcf_data = self.rdb_manager.get_value(self.dcf_for_bcf_path) or []
            
            # Search for device in DCF_FOR_BCF table
            for device_config in dcf_data:
                if device_config.get('name') == device_name or device_config.get('device_name') == device_name:
                    return device_config
            
            logger.warning(f"Device configuration not found for: {device_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting device configuration for {device_name}: %s", e)
            return None

    def _update_device_table_paths(self):
        """Update device table paths with current revision"""
        try:
            current_revision = self.rdb_manager.get_value(str(CURRENT_REVISION)) or "1.0.0"
            self.mipi_devices_path = str(BCF_DEV_MIPI(current_revision))
            self.gpio_devices_path = str(BCF_DEV_GPIO(current_revision))
            self.dcf_for_bcf_path = str(BCF_DCF_FOR_BCF(current_revision))
            logger.info(f"Updated device table paths for revision: {current_revision}")
        except Exception as e:
            logger.error(f"Error updating device table paths: {e}")

    def _on_data_changed(self, changed_path: str):
        """Handle database changes"""
        if changed_path.startswith("config.visual_bcf"):
            # Data changed in RDB, emit signal for other parts to refresh
            self.data_synchronized.emit()

    # Component Management Methods

    def add_component(self,
                      name: str,
                      component_type: str,
                      position: Tuple[float,
                                      float],
                      properties: Dict[str,
                                       Any] = None,
                      component_id: str = None) -> str:
        """Add a new component to the scene with external configuration"""
        print('BCF Data Model: In Add Component BCF Data Model')
        logger.info("BCF Data Model: Adding component: %s (%s) at %s", name, component_type, position)
        try:
            # Use provided component_id if available, otherwise generate new one
            if component_id is None:
                component_id = str(uuid.uuid4())

            # Create component data compatible with both Visual BCF and Legacy BCF
            component_data = {
                'id': component_id,
                'name': name,
                'component_type': component_type,
                'function_type': properties.get('function_type', '') if properties else '',
                'properties': properties or {},
                'visual_properties': {
                    'position': {'x': position[0], 'y': position[1]},
                    'size': {'width': 100, 'height': 80},
                    'rotation': 0
                },
                'pins': [],  # Will be populated based on component type
                # Legacy BCF compatibility fields
                'interface_type': properties.get('interface_type', '') if properties else '',
                'interface': properties.get('interface', {}) if properties else {},
                'config': properties.get('config', {}) if properties else {},
                'usid': component_id[:8],  # First 8 chars for Legacy BCF compatibility
                'mid_msb': '00',
                'mid_lsb': '01',
                'pid': '0000',
                'ext_pid': '0000',
                'rev_id': '1.0',
                'dcf_type': 'Standard'
            }

            # Add directly to RDB
            components_table = self.rdb_manager.get_table(self.components_table_path)
            components_table.append(component_data)
            self.rdb_manager.set_table(self.components_table_path, components_table)

            # Emit signal
            self.component_added.emit(component_id)

            logger.info("Added component: %s (%s)", name, component_id)
            return component_id

        except Exception as e:
            logger.error("BCF Data Model: Error adding component: %s", e)
            print(traceback.format_exc())
            return ""

    def remove_component(self, component_id: str, emit_signal=False) -> bool:
        """Remove a component from the scene directly from RDB"""
        component_found = False
        components_table = []
        try:
            # Remove the component
            for component in self.rdb_manager[paths.BCF_DEV_MIPI(self.revision)]:
                if component.get('ID') == component_id:
                    component_name = component.get('Name', 'Unknown')
                    components_table = self.rdb_manager[paths.BCF_DEV_MIPI(self.revision)]
                    components_table.remove(component)
                    component_found = True
                    break
            for component in self.rdb_manager[paths.BCF_DEV_GPIO(self.revision)]:
                if component.get('ID') == component_id:
                    component_name = component.get('Name', 'Unknown')
                    components_table = self.rdb_manager[paths.BCF_DEV_GPIO(self.revision)]
                    components_table.remove(component)
                    component_found = True
                    break

            # Find the component to get its name for logging
            if not component_found:
                logger.warning("Component not found: %s", component_id)
                return False

            # Also remove any connections involving this component
            # connections_table = [conn for conn in self.rdb_manager[paths.BCF_DB_IO_CONNECT] if
            #                      conn.get('Source Device') != component_name and
            #                      conn.get('Dest Device') != component_name]
            # self.rdb_manager[paths.BCF_DB_IO_CONNECT] = connections_table
            # Emit signal
            if emit_signal:
                self.component_removed.emit(component_id)

            logger.info("Removed component: %s (%s)", component_name, component_id)
            return True

        except Exception as e:
            logger.error("Error removing component: %s", e)
            return False

    def update_component_position(self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position directly in RDB"""
        try:
            if component_id not in self.rdb_manager[paths.VISUAL_PROPERTIES]:
                self.rdb_manager[paths.VISUAL_PROPERTIES][component_id] = {"position": {"x": 0, "y": 0}}

            self.rdb_manager[paths.VISUAL_PROPERTIES][component_id]['position'] = {'x': position[0], 'y': position[1]}

            # Emit update signal
            self.component_updated.emit(component_id, self.rdb_manager[paths.VISUAL_PROPERTIES][component_id])
            logger.info("Updated component position: %s", component_id)
            return True
        except Exception as e:
            logger.error("Error updating component position: %s", e)
            return False

    def update_component_properties(self, component_id: str, properties: Dict[str, Any]) -> bool:
        """Update component properties directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)

            for component in components_table:
                if component.get('id') == component_id:
                    # Update properties while maintaining compatibility
                    if 'properties' not in component:
                        component['properties'] = {}
                    component['properties'].update(properties)

                    # Update Legacy BCF compatibility fields
                    if 'function_type' in properties:
                        component['function_type'] = properties['function_type']
                    if 'interface_type' in properties:
                        component['interface_type'] = properties['interface_type']
                    if 'interface' in properties:
                        component['interface'] = properties['interface']
                    if 'config' in properties:
                        component['config'] = properties['config']

                    self.rdb_manager.set_table(self.components_table_path, components_table)

                    # Emit update signal
                    self.component_updated.emit(component_id, component)
                    logger.info("Updated component properties: %s", component_id)
                    return True

            logger.warning("Component not found for properties update: %s", component_id)
            return False

        except Exception as e:
            logger.error("Error updating component properties: %s", e)
            return False

    def update_component_pins(self, component_id: str, pins: List[Dict[str, Any]]) -> bool:
        """Update component pins directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)

            for component in components_table:
                if component.get('id') == component_id:
                    component['pins'] = pins
                    self.rdb_manager.set_table(self.components_table_path, components_table)

                    # Emit update signal
                    self.component_updated.emit(component_id, component)
                    logger.info("Updated component pins: %s", component_id)
                    return True

            logger.warning("Component not found for pins update: %s", component_id)
            return False

        except Exception as e:
            logger.error("Error updating component pins: %s", e)
            return False

    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific component directly from RDB"""
        try:
            print(f"BCF Data Model: Getting component: {component_id}")
            for component in self.rdb_manager[paths.BCF_DEV_MIPI(self.revision)]:
                if component.get('ID') == component_id:
                    return component
            print(f"BCF Data Model: Component not found in MIPI: {component_id}")
            for component in self.rdb_manager[paths.BCF_DEV_GPIO(self.revision)]:
                if component.get('ID') == component_id:
                    return component
            print(f"BCF Data Model: Component not found in GPIO: {component_id}")
            return None
        except Exception as e:
            logger.error("Error getting component: %s", e)
            return None

    def get_component_id(self, component_name: str) -> Optional[str]:
        """Get component ID by name"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            for component in components_table:
                if component.get('name') == component_name:
                    return component.get('id', '')
            return None  # Add missing return statement
        except Exception as e:
            logger.error("Error getting component ID: %s", e)
            return None

    def get_all_components(self) -> Dict[str, Dict[str, Any]]:
        """Get all components as a dictionary with component IDs as keys"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            if not components_table:
                return {}

            # Convert list to dictionary with component IDs as keys
            components_dict = {}
            for component in components_table:
                if isinstance(component, dict) and 'id' in component:
                    components_dict[component['id']] = component

            return components_dict

        except Exception as e:
            logger.error("Error getting all components: %s", e)
            return {}

    def get_all_components_as_list(self) -> List[Dict[str, Any]]:
        """Get all components as a list (for table views) - now from device tables"""
        return self.components

    def get_components_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Get components by type directly from RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            return [c for c in components_table if c.get('component_type') == component_type]
        except Exception as e:
            logger.error("Error getting components by type: %s", e)
            return []

    def get_component_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get component by name directly from RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            for component in components_table:
                if component.get('name') == name:
                    return component
            return None
        except Exception as e:
            logger.error("Error getting component by name: %s", e)
            return None

    # Connection Management Methods

    def add_connection(self,
                       from_component_id: str,
                       from_pin_id: str,
                       to_component_id: str,
                       to_pin_id: str,
                       connection_type: str = "wire",
                       properties: Dict[str, Any] = None) -> str:
        """Add a new connection directly to RDB"""
        try:
            connection_id = str(uuid.uuid4())

            # Create connection data compatible with both Visual BCF and Legacy BCF
            connection_data = {
                'id': connection_id,
                'from_component_id': from_component_id,
                'from_pin_id': from_pin_id,
                'to_component_id': to_component_id,
                'to_pin_id': to_pin_id,
                'connection_type': connection_type,
                'properties': properties or {},
                'visual_properties': {
                    'path_points': [],
                    'line_style': 'solid',
                    'color': '#000000'
                },
                # Legacy BCF compatibility fields
                'source_device': self._get_component_name(from_component_id),
                'source_pin': from_pin_id,
                'dest_device': self._get_component_name(to_component_id),
                'dest_pin': to_pin_id,
                'source_sub_block': 'Main Block',
                'dest_sub_block': 'Main Block',
                'status': 'Active'
            }

            # Add directly to RDB
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            connections_table.append(connection_data)
            self.rdb_manager.set_table(self.connections_table_path, connections_table)

            # Emit signal
            self.connection_added.emit(connection_id)

            logger.info("Added connection: %s", connection_id)
            return connection_id

        except Exception as e:
            logger.error("Error adding connection: %s", e)
            return ""

    def update_connection(self, connection_id: str, updated_data: dict) -> bool:
        """Update connection properties in the single source of truth"""
        try:
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            if not connections_table:
                return False

            # Find and update the connection
            for connection in connections_table:
                if isinstance(connection, dict) and connection.get('id') == connection_id:
                    # Update the connection with new data
                    connection.update(updated_data)

                    # Save back to RDB
                    self.rdb_manager.set_table(self.connections_table_path, connections_table)

                    # Emit signal
                    self.connection_updated.emit(connection_id)

                    logger.info("Updated connection: %s", connection_id)
                    return True

            logger.warning("Connection not found for update: %s", connection_id)
            return False

        except Exception as e:
            logger.error("Error updating connection: %s", e)
            return False

    def _get_component_name(self, component_id: str) -> str:
        """Helper method to get component name from ID"""
        try:
            component = self.get_component(component_id)
            return component.get('name', 'Unknown') if component else 'Unknown'
        except Exception:
            return 'Unknown'

    def remove_connection(self, connection_id: str, emit_signal=False) -> bool:
        """Remove a connection directly from RDB"""
        try:
            # connections_table = self.rdb_manager[paths.BCF_DB_IO_CONNECT]
            connections_table = self.rdb_manager.get_value(self.io_connections_path) or []
            # Find and remove the connection
            for i, connection in enumerate(connections_table):
                if connection.get('Connection ID') == connection_id:
                    connections_table.pop(i)
                    # Emit signal
                    if emit_signal:
                        self.connection_removed.emit(connection_id)

                    logger.info("Removed connection: %s", connection_id)
                    return True

            logger.warning("Connection not found: %s", connection_id)
            return False

        except Exception as e:
            logger.error("Error removing connection: %s", e)
            return False

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific connection directly from RDB"""
        try:
            connections_table = self.rdb_manager.get_table(self.connections_table_path) or []
            for connection in connections_table:
                if connection.get('id') == connection_id:
                    return connection
            return None
        except Exception as e:
            logger.error("Error getting connection: %s", e)
            return None

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all connections from IO connections table"""
        return self.connections

    def get_component_connections(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all connections for a specific component from IO connections table"""
        try:
            # Get all connections from IO connections table
            all_connections = self.connections
            component_connections = []

            # Find component name from device tables
            component_name = None
            all_components = self.components
            for component in all_components:
                if component.get('id') == component_id:
                    component_name = component.get('name')
                    break

            if not component_name:
                return []

            # Find connections involving this component
            for connection in all_connections:
                if (connection.get('source_device') == component_name or
                        connection.get('dest_device') == component_name):
                    component_connections.append(connection)

            return component_connections

        except Exception as e:
            logger.error("Error getting component connections: %s", e)
            return []

    # Legacy BCF Integration Methods - Now using single source of truth

    def get_legacy_bcf_devices(self) -> List[Dict[str, Any]]:
        """Get Legacy BCF device settings from Visual BCF components (single source of truth)"""
        try:
            components = self.get_all_components_as_list()
            legacy_devices = []

            for component in components:
                # Convert Visual BCF component to Legacy BCF format
                legacy_device = {
                    'name': component.get('name', ''),
                    'function_type': component.get('function_type', ''),
                    'interface_type': component.get('interface_type', ''),
                    'interface': component.get('interface', {}),
                    'config': component.get('config', {}),
                    'usid': component.get('usid', ''),
                    'mid_msb': component.get('mid_msb', ''),
                    'mid_lsb': component.get('mid_lsb', ''),
                    'pid': component.get('pid', ''),
                    'ext_pid': component.get('ext_pid', ''),
                    'rev_id': component.get('rev_id', ''),
                    'dcf_type': component.get('dcf_type', '')
                }
                legacy_devices.append(legacy_device)

            return legacy_devices

        except Exception as e:
            logger.error("Error getting Legacy BCF devices: %s", e)
            return []

    def get_available_devices_for_table(self) -> List[Dict[str, Any]]:
        """Get available devices in table format from Visual BCF components"""
        try:
            components = self.get_all_components_as_list()
            table_devices = []

            for component in components:
                # Convert to table format
                table_device = {
                    "Device Name": component.get('name', ''),
                    "Control Type\n(MIPI / GPIO)": component.get('interface_type', ''),
                    "Module": component.get('component_type', '').upper(),
                    "USID\n(Default)": component.get('usid', ''),
                    "MID\n(MSB)": component.get('mid_msb', ''),
                    "MID\n(LSB)": component.get('mid_lsb', ''),
                    "PID": component.get('pid', ''),
                    "EXT PID": component.get('ext_pid', ''),
                    "REV ID": component.get('rev_id', ''),
                    "DCF Type": component.get('dcf_type', '')
                }
                table_devices.append(table_device)

            return table_devices

        except Exception as e:
            logger.error("Error getting available devices for table: %s", e)
            return []

    def get_io_connections_for_table(self) -> List[Dict[str, Any]]:
        """Get IO connections in table format from RDB BCF_DB_IO_CONNECT table"""
        try:
            # Get IO connections from RDB using the stored path
            io_connections = self.rdb_manager.get_value(self.io_connections_path) or []
            
            # The data is already in the correct table format from the JSON file
            return io_connections

        except Exception as e:
            logger.error("Error getting IO connections for table: %s", e)
            return []

    def get_dcf_devices_for_table(self) -> List[Dict[str, Any]]:
        """Get DCF devices in table format from RDB (All Devices - read-only)"""
        try:
            # Get DCF devices from RDB - this is the read-only All Devices table
            dcf_devices = self.rdb_manager.get_value(self.dcf_devices_path) or []
            return dcf_devices

        except Exception as e:
            logger.error("Error getting DCF devices for table: %s", e)
            return []

    def get_mipi_devices_for_table(self) -> List[Dict[str, Any]]:
        """Get MIPI devices in table format from RDB"""
        try:
            # Update paths with current revision before getting data
            self._update_device_table_paths()
            mipi_devices = self.rdb_manager.get_value(self.mipi_devices_path) or []
            return mipi_devices

        except Exception as e:
            logger.error("Error getting MIPI devices for table: %s", e)
            return []

    def get_gpio_devices_for_table(self) -> List[Dict[str, Any]]:
        """Get GPIO devices in table format from RDB"""
        try:
            # Update paths with current revision before getting data
            self._update_device_table_paths()
            gpio_devices = self.rdb_manager.get_value(self.gpio_devices_path) or []
            return gpio_devices

        except Exception as e:
            logger.error("Error getting GPIO devices for table: %s", e)
            return []

    # Utility methods

    def clear_all_data(self):
        """Clear all components and connections directly from RDB"""
        try:
            # Clear components table
            self.rdb_manager.set_table(self.components_table_path, [])

            # Clear connections table
            self.rdb_manager.set_table(self.connections_table_path, [])

            logger.info("Cleared all Visual BCF data")
            self.data_synchronized.emit()

        except Exception as e:
            logger.error("Error clearing data: %s", e)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current data directly from RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            connections_table = self.rdb_manager.get_table(self.connections_table_path) or []

            return {
                'component_count': len(components_table),
                'connection_count': len(connections_table),
                'total_components': len(components_table),
                'total_connections': len(connections_table),
                'components_by_type': {
                    comp_type: len([c for c in components_table if c.get('component_type') == comp_type])
                    for comp_type in set(c.get('component_type') for c in components_table if c.get('component_type'))
                }
            }
        except Exception as e:
            logger.error("Error getting statistics: %s", e)
            return {
                'component_count': 0,
                'connection_count': 0,
                'total_components': 0,
                'total_connections': 0,
                'components_by_type': {}
            }

    def get_table_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all tables including compatibility views"""
        try:
            # Get Visual BCF table statistics
            visual_bcf_stats = self.get_statistics()

            # Get table format data counts
            available_devices_count = len(self.get_available_devices_for_table())
            io_connections_count = len(self.get_io_connections_for_table())

            # Combine all statistics
            all_stats = {
                **visual_bcf_stats,
                'available_devices_count': available_devices_count,
                'io_connections_count': io_connections_count,
                'total_tables': 2,  # components, connections (single source of truth)
                'table_status': {
                    'visual_bcf_components': 'Active' if visual_bcf_stats['component_count'] > 0 else 'Empty',
                    'visual_bcf_connections': 'Active' if visual_bcf_stats['connection_count'] > 0 else 'Empty',
                    'available_devices_table_view': 'Active' if available_devices_count > 0 else 'Empty',
                    'io_connections_table_view': 'Active' if io_connections_count > 0 else 'Empty'
                },
                'data_integration': {
                    'direct_table_operations': True,
                    'single_source_of_truth': True,
                    'external_config_loaded': False  # No longer using external configs
                }
            }

            return all_stats

        except Exception as e:
            logger.error("Error getting table statistics: %s", e)
            return {
                'component_count': 0,
                'connection_count': 0,
                'available_devices_count': 0,
                'io_connections_count': 0,
                'total_tables': 2,
                'table_status': {
                    'visual_bcf_components': 'Error',
                    'visual_bcf_connections': 'Error',
                    'available_devices_table_view': 'Error',
                    'io_connections_table_view': 'Error'
                },
                'data_integration': {
                    'direct_table_operations': False,
                    'single_source_of_truth': False,
                    'external_config_loaded': False  # No longer using external configs
                }
            }

    @property
    def components(self) -> List[Dict[str, Any]]:
        """Get all components from device tables (MIPI + GPIO devices only)"""
        try:
            # Update paths with current revision
            self._update_device_table_paths()
            
            # Get only devices that are actually used in the BCF
            mipi_devices = self.rdb_manager[paths.BCF_DEV_MIPI(self.revision)]
            gpio_devices = self.rdb_manager[paths.BCF_DEV_GPIO(self.revision)]
            
            # Convert MIPI devices to component format
            converted_mipi_devices = []
            for device in mipi_devices:
                converted_device = {
                    "ID": device.get("ID"),
                    "Name": device.get("Name"),
                    "Component Type": "mipi",
                    "Module": device.get("Module"),
                    "Properties": {}
                }
                converted_mipi_devices.append(converted_device)
            
            # Convert GPIO devices to component format
            converted_gpio_devices = []
            for device in gpio_devices:
                converted_device = {
                    "ID": device.get("ID"),
                    "Name": device.get("Name"),
                    "Component Type": "gpio",
                    "Module": device.get("Module"),
                    "Properties": {}
                }
                converted_gpio_devices.append(converted_device)
            
            return converted_mipi_devices + converted_gpio_devices
           
        except Exception as e:
            logger.error("Error getting components from device tables: %s", e)
            return []

    @property
    def connections(self) -> List[Dict[str, Any]]:
        """Get all connections from IO connections table"""
        try:
            # Get IO connections from RDB
            io_connections = self.rdb_manager[paths.BCF_DB_IO_CONNECT]
            return io_connections

        except Exception as e:
            logger.error("Error getting connections from IO connections table: %s", e)
            return []
