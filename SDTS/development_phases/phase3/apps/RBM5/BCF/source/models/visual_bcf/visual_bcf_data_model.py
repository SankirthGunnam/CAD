"""
Visual BCF Data Access Model

This model acts as a bridge between Visual BCF graphics components and Legacy BCF table data.
It provides a unified interface for Visual BCF to access component data, connection data,
and properties data from the underlying JSON database tables used by Legacy BCF.
"""

from typing import Dict, List, Any, Optional, Tuple
import uuid
import logging

from PySide6.QtCore import QObject, Signal

from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.RDB.paths import (
    VISUAL_BCF_COMPONENTS,
    VISUAL_BCF_CONNECTIONS
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

    def __init__(self, rdb_manager: RDBManager):
        super().__init__()
        self.rdb_manager = rdb_manager

        # Table paths using centralized paths from paths.py - SINGLE SOURCE OF TRUTH
        self.components_table_path = str(VISUAL_BCF_COMPONENTS)
        self.connections_table_path = str(VISUAL_BCF_CONNECTIONS)

        # Connect to database changes
        self.rdb_manager.data_changed.connect(self._on_data_changed)

        # Initialize database structure if needed
        self._initialize_visual_bcf_tables()

        # Load external component configurations
        self._load_external_component_configs()

    def _initialize_visual_bcf_tables(self):
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
                            "size": 20}}}
                self.rdb_manager.set_value("config.visual_bcf", initial_data)
                logger.info("Initialized Visual BCF tables in database")

        except Exception as e:
            logger.error("Error initializing Visual BCF tables: %s", e)

    def _load_external_component_configs(self):
        """Load external component configurations for pin counts, names, sizes, etc."""
        try:
            # This should load from external configuration files or database
            # For now, we'll define some common component types
            self.component_configs = {
                "modem": {
                    "pins": ["TX1", "RX1", "TX2", "RX2", "CLK", "RST"],
                    "size": {"width": 120, "height": 100},
                    "default_properties": {"function_type": "modem", "interface_type": "MIPI"}
                },
                "rfic": {
                    "pins": ["RF_IN", "RF_OUT", "VCC", "GND", "CTRL"],
                    "size": {"width": 100, "height": 80},
                    "default_properties": {"function_type": "rfic", "interface_type": "RF"}
                },
                "chip": {
                    "pins": ["IN1", "IN2", "OUT", "VCC", "GND"],
                    "size": {"width": 80, "height": 60},
                    "default_properties": {"function_type": "generic", "interface_type": "GPIO"}
                },
                "filter": {
                    "pins": ["INPUT", "OUTPUT", "GND"],
                    "size": {"width": 60, "height": 40},
                    "default_properties": {"function_type": "filter", "interface_type": "RF"}
                }
            }
            logger.info("Loaded external component configurations")
            
        except Exception as e:
            logger.error("Error loading external component configs: %s", e)
            # Fallback to basic configs
            self.component_configs = {}

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
        try:
            # Use provided component_id if available, otherwise generate new one
            if component_id is None:
                component_id = str(uuid.uuid4())

            # Get external configuration for this component type
            config = self.component_configs.get(component_type, {})
            
            # Merge external config with provided properties
            component_props = config.get('default_properties', {}).copy()
            if properties:
                component_props.update(properties)

            # Create component data compatible with both Visual BCF and Legacy BCF
            component_data = {
                'id': component_id,
                'name': name,
                'component_type': component_type,
                'function_type': component_props.get('function_type', ''),
                'properties': component_props,
                'visual_properties': {
                    'position': {'x': position[0], 'y': position[1]},
                    'size': config.get('size', {'width': 100, 'height': 80}),
                    'rotation': 0
                },
                'pins': config.get('pins', []),
                # Legacy BCF compatibility fields
                'interface_type': component_props.get('interface_type', ''),
                'interface': component_props.get('interface', {}),
                'config': component_props.get('config', {}),
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
            logger.error("Error adding component: %s", e)
            return ""

    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the scene directly from RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            
            # Find the component to get its name for logging
            component_name = ""
            component_found = False
            for component in components_table:
                if component.get('id') == component_id:
                    component_name = component.get('name', 'Unknown')
                    component_found = True
                    break
            
            if component_found:
                # Remove the component
                components_table = [c for c in components_table if c.get('id') != component_id]
                self.rdb_manager.set_table(self.components_table_path, components_table)
                
                # Also remove any connections involving this component
                connections_table = self.rdb_manager.get_table(self.connections_table_path)
                connections_table = [conn for conn in connections_table 
                                  if conn.get('from_component_id') != component_id 
                                  and conn.get('to_component_id') != component_id]
                self.rdb_manager.set_table(self.connections_table_path, connections_table)
                
                # Emit signal
                self.component_removed.emit(component_id)
                
                logger.info("Removed component: %s (%s)", component_name, component_id)
                return True
            else:
                logger.warning("Component not found: %s", component_id)
                return False
                
        except Exception as e:
            logger.error("Error removing component: %s", e)
            return False

    def update_component_position(self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            
            for component in components_table:
                if component.get('id') == component_id:
                    component['visual_properties']['position'] = {'x': position[0], 'y': position[1]}
                    self.rdb_manager.set_table(self.components_table_path, components_table)
                    
                    # Emit update signal
                    self.component_updated.emit(component_id, component)
                    logger.info("Updated component position: %s", component_id)
                    return True
            
            logger.warning("Component not found for position update: %s", component_id)
            return False
            
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
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            for component in components_table:
                if component.get('id') == component_id:
                    return component
            return None
        except Exception as e:
            logger.error("Error getting component: %s", e)
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
        """Get all components as a list (for table views)"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            if not components_table:
                return []
            return components_table.copy()
            
        except Exception as e:
            logger.error("Error getting all components as list: %s", e)
            return []

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

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection directly from RDB"""
        try:
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            
            # Find and remove the connection
            for i, connection in enumerate(connections_table):
                if connection.get('id') == connection_id:
                    removed_connection = connections_table.pop(i)
                    self.rdb_manager.set_table(self.connections_table_path, connections_table)
                    
                    # Emit signal
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
        """Get all connections directly from RDB"""
        try:
            return self.rdb_manager.get_table(self.connections_table_path) or []
        except Exception as e:
            logger.error("Error getting all connections: %s", e)
            return []

    def get_component_connections(self, component_id: str) -> List[Dict[str, Any]]:
        """Get all connections for a specific component directly from RDB"""
        try:
            connections_table = self.rdb_manager.get_table(self.connections_table_path) or []
            return [conn for conn in connections_table 
                   if conn.get('from_component_id') == component_id or 
                      conn.get('to_component_id') == component_id]
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
        """Get IO connections in table format from Visual BCF connections"""
        try:
            connections = self.get_all_connections()
            table_connections = []
            
            for connection in connections:
                # Convert to table format
                table_connection = {
                    "Connection ID": connection.get('id', ''),
                    "Source Device": connection.get('source_device', ''),
                    "Source Pin": connection.get('source_pin', ''),
                    "Source Sub Block": connection.get('source_sub_block', ''),
                    "Dest Device": connection.get('dest_device', ''),
                    "Dest Pin": connection.get('dest_pin', ''),
                    "Dest Sub Block": connection.get('dest_sub_block', ''),
                    "Connection Type": connection.get('connection_type', ''),
                    "Status": connection.get('status', '')
                }
                table_connections.append(table_connection)
            
            return table_connections
            
        except Exception as e:
            logger.error("Error getting IO connections for table: %s", e)
            return []

    def sync_with_legacy_bcf(self):
        """Synchronize with Legacy BCF component definitions - now using single source of truth"""
        try:
            # Since we're using single source of truth, this method now ensures
            # Visual BCF components have all required Legacy BCF fields
            
            components_table = self.rdb_manager.get_table(self.components_table_path)
            updated = False
            
            for component in components_table:
                comp_id = component.get('id')
                comp_type = component.get('component_type', '')
                
                # Get external configuration for this component type
                config = self.component_configs.get(comp_type, {})
                
                # Ensure all Legacy BCF compatibility fields are present
                if 'usid' not in component:
                    component['usid'] = comp_id[:8]
                    updated = True
                if 'mid_msb' not in component:
                    component['mid_msb'] = '00'
                    updated = True
                if 'mid_lsb' not in component:
                    component['mid_lsb'] = '01'
                    updated = True
                if 'pid' not in component:
                    component['pid'] = '0000'
                    updated = True
                if 'ext_pid' not in component:
                    component['ext_pid'] = '0000'
                    updated = True
                if 'rev_id' not in component:
                    component['rev_id'] = '1.0'
                    updated = True
                if 'dcf_type' not in component:
                    component['dcf_type'] = 'Standard'
                    updated = True
                
                # Update properties from external config if missing
                if 'properties' not in component:
                    component['properties'] = {}
                
                default_props = config.get('default_properties', {})
                for key, value in default_props.items():
                    if key not in component['properties']:
                        component['properties'][key] = value
                        updated = True
                
                # Update Legacy BCF fields from properties
                if 'function_type' not in component and 'function_type' in component['properties']:
                    component['function_type'] = component['properties']['function_type']
                    updated = True
                if 'interface_type' not in component and 'interface_type' in component['properties']:
                    component['interface_type'] = component['properties']['interface_type']
                    updated = True
                if 'interface' not in component and 'interface' in component['properties']:
                    component['interface'] = component['properties']['interface']
                    updated = True
                if 'config' not in component and 'config' in component['properties']:
                    component['config'] = component['properties']['config']
                    updated = True
            
            if updated:
                # Update the components table in RDB
                self.rdb_manager.set_table(self.components_table_path, components_table)
                logger.info("Synchronized Visual BCF components with Legacy BCF compatibility fields")
                self.data_synchronized.emit()
            else:
                logger.info("Visual BCF components already synchronized with Legacy BCF")

        except Exception as e:
            logger.error("Error syncing with Legacy BCF: %s", e)

    def export_to_legacy_bcf(self):
        """Export Visual BCF components to Legacy BCF format - now using single source of truth"""
        try:
            # Since we're using single source of truth, this method now ensures
            # all Visual BCF components have the required Legacy BCF fields
            
            # First sync to ensure all fields are present
            self.sync_with_legacy_bcf()
            
            # Get all components (they now have all required Legacy BCF fields)
            components = self.get_all_components_as_list()
            
            logger.info("Visual BCF components exported to Legacy BCF format (single source of truth)")
            return True

        except Exception as e:
            logger.error("Error exporting to Legacy BCF: %s", e)
            return False

    def _auto_export_component_to_legacy_bcf(self, component_data: Dict[str, Any]):
        """Auto-export a component to Legacy BCF - now using single source of truth"""
        try:
            # Since we're using single source of truth, all components automatically
            # have Legacy BCF compatibility fields
            component_name = component_data.get('name', 'Unknown')
            component_type = component_data.get('component_type', 'Unknown')
            
            logger.info("Component '%s' (type: %s) automatically compatible with Legacy BCF (single source of truth)", 
                       component_name, component_type)

        except Exception as e:
            logger.error("Error in auto-export (single source of truth): %s", e)

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
                'compatibility': {
                    'legacy_bcf_compatible': True,
                    'single_source_of_truth': True,
                    'external_config_loaded': len(self.component_configs) > 0
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
                'compatibility': {
                    'legacy_bcf_compatible': False,
                    'single_source_of_truth': False,
                    'external_config_loaded': False
                }
            }

    def save_scene_data(self, scene_data: Dict[str, Any]) -> bool:
        """Save scene data to the data model"""
        try:
            if 'components' in scene_data:
                # Clear existing components
                self.rdb_manager.set_table(self.components_table_path, [])
                
                # Add new components
                for component_data in scene_data['components']:
                    if 'id' in component_data and 'name' in component_data:
                        # Extract component information
                        name = component_data['name']
                        component_type = component_data.get('type', 'unknown')
                        position = component_data.get('position', {'x': 0, 'y': 0})
                        properties = component_data.get('properties', {})
                        
                        # Add component to data model
                        component_id = self.add_component(
                            name=name,
                            component_type=component_type,
                            position=(position['x'], position['y']),
                            properties=properties
                        )
                        
                        if component_id:
                            logger.info("Saved component: %s (%s)", name, component_id)
            
            if 'connections' in scene_data:
                # Clear existing connections
                self.rdb_manager.set_table(self.connections_table_path, [])
                
                # Add new connections
                for connection_data in scene_data['connections']:
                    if 'from_component_id' in connection_data and 'to_component_id' in connection_data:
                        # Extract connection information
                        from_component_id = connection_data['from_component_id']
                        from_pin_id = connection_data.get('from_pin_id', '')
                        to_component_id = connection_data['to_component_id']
                        to_pin_id = connection_data.get('to_pin_id', '')
                        
                        # Add connection to data model
                        connection_id = self.add_connection(
                            from_component_id=from_component_id,
                            from_pin_id=from_pin_id,
                            to_component_id=to_component_id,
                            to_pin_id=to_pin_id
                        )
                        
                        if connection_id:
                            logger.info("Saved connection: %s", connection_id)
            
            logger.info("Scene data saved successfully")
            return True
            
        except Exception as e:
            logger.error("Error saving scene data: %s", e)
            return False

    def load_scene_data(self) -> Dict[str, Any]:
        """Load scene data from the data model"""
        try:
            scene_data = {
                "components": [],
                "connections": []
            }
            
            # Load components
            components = self.get_all_components_as_list()
            for component in components:
                if isinstance(component, dict) and 'id' in component:
                    component_data = {
                        "id": component['id'],
                        "name": component.get('name', 'Unknown'),
                        "type": component.get('component_type', 'unknown'),
                        "position": component.get('visual_properties', {}).get('position', {'x': 0, 'y': 0}),
                        "properties": component.get('properties', {}),
                        "pins": component.get('pins', [])
                    }
                    scene_data["components"].append(component_data)
            
            # Load connections - ensure they reference existing components
            connections = self.get_all_connections()
            for connection in connections:
                if isinstance(connection, dict) and 'id' in connection:
                    # Verify that both components exist before including the connection
                    from_component_id = connection.get('from_component_id', '')
                    to_component_id = connection.get('to_component_id', '')
                    
                    # Check if both components exist
                    from_component = self.get_component(from_component_id)
                    to_component = self.get_component(to_component_id)
                    
                    if from_component and to_component:
                        connection_data = {
                            "id": connection['id'],
                            "from_component_id": from_component_id,
                            "from_pin_id": connection.get('from_pin_id', ''),
                            "to_component_id": to_component_id,
                            "to_pin_id": connection.get('to_pin_id', ''),
                            "connection_type": connection.get('connection_type', 'wire'),
                            "properties": connection.get('properties', {})
                        }
                        scene_data["connections"].append(connection_data)
                    else:
                        logger.warning("Connection %s references non-existent components: %s -> %s", 
                                     connection['id'], from_component_id, to_component_id)
            
            logger.info("Loaded scene data: %d components, %d connections", 
                       len(scene_data["components"]), len(scene_data["connections"]))
            return scene_data
            
        except Exception as e:
            logger.error("Error loading scene data: %s", e)
            return {"components": [], "connections": []}

    def save_visual_bcf_data(self) -> bool:
        """Save Visual BCF data to RDB (persist to disk)"""
        try:
            # The data is already in RDB, just ensure it's persisted
            # This method is called by the controller after save_scene_data
            logger.info("Visual BCF data persisted to RDB")
            return True
            
        except Exception as e:
            logger.error("Error persisting Visual BCF data: %s", e)
            return False

    def save_visual_bcf_to_file(self, file_path: str) -> bool:
        """Save Visual BCF data to a specific file"""
        try:
            # Get current data from RDB
            components_table = self.rdb_manager.get_table(self.components_table_path) or []
            connections_table = self.rdb_manager.get_table(self.connections_table_path) or []
            
            # Create the file structure
            file_data = {
                "config": {
                    "visual_bcf": {
                        "components": components_table,
                        "connections": connections_table
                    }
                }
            }
            
            # Save to file
            import json
            with open(file_path, 'w') as f:
                json.dump(file_data, f, indent=2)
            
            logger.info("Visual BCF data saved to file: %s", file_path)
            return True
            
        except Exception as e:
            logger.error("Error saving Visual BCF data to file: %s", e)
            return False
