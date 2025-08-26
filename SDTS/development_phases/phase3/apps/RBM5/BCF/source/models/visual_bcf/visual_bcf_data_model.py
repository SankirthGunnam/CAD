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
    VISUAL_BCF_CONNECTIONS,
    DCF_DEVICES_AVAILABLE,
    BCF_DEV_MIPI,
    BCF_DB_IO_CONNECT_ENHANCED
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
    - Manage device settings and IO connections
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

        # Table paths using centralized paths from paths.py
        self.components_table_path = str(VISUAL_BCF_COMPONENTS)
        self.connections_table_path = str(VISUAL_BCF_CONNECTIONS)

        # Connect to database changes
        self.rdb_manager.data_changed.connect(self._on_data_changed)

        # Initialize database structure if needed
        self._initialize_visual_bcf_tables()
        self._initialize_device_settings_tables()
        self._initialize_io_connect_tables()

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

    def _initialize_device_settings_tables(self):
        """Initialize device settings tables in the database if they don't exist"""
        try:
            # Check if device settings section exists
            device_settings = self.rdb_manager.get_value(str(DCF_DEVICES_AVAILABLE))
            if not device_settings:
                # Create the device settings section with empty tables
                initial_data = {
                    "devices": [],
                    "mips": []
                }
                self.rdb_manager.set_value(str(DCF_DEVICES_AVAILABLE), initial_data)
                logger.info("Initialized device settings tables in database")

        except Exception as e:
            logger.error("Error initializing device settings tables: %s", e)

    def _initialize_io_connect_tables(self):
        """Initialize IO connect tables in the database if they don't exist"""
        try:
            # Check if IO connect section exists
            io_connect = self.rdb_manager.get_value(str(BCF_DB_IO_CONNECT_ENHANCED))
            if not io_connect:
                # Create the IO connect section with empty tables
                initial_data = {
                    "io_connects": []
                }
                self.rdb_manager.set_value(str(BCF_DB_IO_CONNECT_ENHANCED), initial_data)
                logger.info("Initialized IO connect tables in database")

        except Exception as e:
            logger.error("Error initializing IO connect tables: %s", e)


    def _on_data_changed(self, changed_path: str):
        """Handle database changes"""
        if changed_path.startswith("config.visual_bcf"):
            # Data changed in RDB, emit signal for other parts to refresh
            self.data_synchronized.emit()
        elif changed_path.startswith(str(DCF_DEVICES_AVAILABLE)):
            self.data_synchronized.emit()
        elif changed_path.startswith(str(BCF_DB_IO_CONNECT_ENHANCED)):
            self.data_synchronized.emit()

    # Component Management Methods

    def add_component(self,
                      name: str,
                      component_type: str,
                      position: Tuple[float,
                                      float],
                      properties: Dict[str,
                                       Any] = None) -> str:
        """Add a new component to the scene"""
        try:
            component_id = str(uuid.uuid4())

            component_data = {
                'id': component_id,
                'name': name,
                'component_type': component_type,
                'function_type': properties.get('function_type', '') if properties else '',
                'properties': properties or {},
                'visual_properties': {
                    'position': {'x': position[0], 'y': position[1]},
                    'size': {'width': properties.get('width', 100) if properties else 100,
                             'height': properties.get('height', 80) if properties else 80},
                    'rotation': 0
                },
                'pins': []
            }

            # Add directly to RDB
            components_table = self.rdb_manager.get_table(self.components_table_path)
            components_table.append(component_data)
            self.rdb_manager.set_table(self.components_table_path, components_table)

            # Auto-export to Legacy BCF if component is a device/modem
            self._auto_export_component_to_legacy_bcf(component_data)

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
            
            if not component_found:
                return False

            # Remove all connections involving this component
            connections_to_remove = []
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            for connection in connections_table:
                if (connection.get('from_component_id') == component_id or
                        connection.get('to_component_id') == component_id):
                    connections_to_remove.append(connection.get('id'))

            for conn_id in connections_to_remove:
                self.remove_connection(conn_id)

            # Remove component from components table
            components_table = [comp for comp in components_table if comp.get('id') != component_id]
            self.rdb_manager.set_table(self.components_table_path, components_table)

            # Emit signal
            self.component_removed.emit(component_id)

            logger.info(
                f"Removed component: {component_name} ({component_id})")
            return True

        except Exception as e:
            logger.error("Error removing component: %s", e)
            return False

    def update_component_position(
            self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            
            # Find and update the component
            for component in components_table:
                if component.get('id') == component_id:
                    if 'visual_properties' not in component:
                        component['visual_properties'] = {}
                    component['visual_properties']['position'] = {
                        'x': position[0], 'y': position[1]
                    }
                    
                    # Update the table
                    self.rdb_manager.set_table(self.components_table_path, components_table)
                    
                    # Emit signal
                    self.component_updated.emit(component_id, {'position': position})
                    
                    return True
            
            return False

        except Exception as e:
            logger.error("Error updating component position: %s", e)
            return False

    def update_component_properties(
            self, component_id: str, properties: Dict[str, Any]) -> bool:
        """Update component properties directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            
            # Find and update the component
            for component in components_table:
                if component.get('id') == component_id:
                    if 'properties' not in component:
                        component['properties'] = {}
                    component['properties'].update(properties)
                    
                    # Update the table
                    self.rdb_manager.set_table(self.components_table_path, components_table)
                    
                    # Emit signal
                    self.component_updated.emit(
                        component_id, {'properties': properties})
                    
                    return True
            
            return False

        except Exception as e:
            logger.error("Error updating component properties: %s", e)
            return False

    def update_component_pins(self, component_id: str, pins: List[Dict[str, Any]]) -> bool:
        """Update component pins directly in RDB"""
        try:
            components_table = self.rdb_manager.get_table(self.components_table_path)
            
            # Find and update the component
            for component in components_table:
                if component.get('id') == component_id:
                    component['pins'] = pins
                    
                    # Update the table
                    self.rdb_manager.set_table(self.components_table_path, components_table)
                    
                    # Emit signal
                    self.component_updated.emit(component_id, {'pins': pins})

                    logger.info("Updated component %s with %s pins", component_id, len(pins))
                    return True
            
            return False

        except Exception as e:
            logger.error("Error updating component pins: %s", e)
            return False

    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get component data by ID directly from RDB"""
        components_table = self.rdb_manager.get_table(self.components_table_path)
        for component in components_table:
            if component.get('id') == component_id:
                return component
        return None

    def get_all_components(self) -> Dict[str, Dict[str, Any]]:
        """Get all components directly from RDB"""
        components_table = self.rdb_manager.get_table(self.components_table_path)
        return {comp.get('id'): comp for comp in components_table if comp.get('id')}

    def get_components_by_type(
            self, component_type: str) -> Dict[str, Dict[str, Any]]:
        """Get components of a specific type directly from RDB"""
        components_table = self.rdb_manager.get_table(self.components_table_path)
        return {
            comp.get('id'): comp
            for comp in components_table
            if comp.get('id') and comp.get('component_type') == component_type
        }

    def get_component_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get component by name directly from RDB"""
        components_table = self.rdb_manager.get_table(self.components_table_path)
        for component in components_table:
            if component.get('name') == name:
                return component
        return None

    def remove_component_by_name(self, name: str) -> bool:
        """Remove a component by name directly from RDB"""
        components_table = self.rdb_manager.get_table(self.components_table_path)
        for component in components_table:
            if component.get('name') == name:
                return self.remove_component(component.get('id'))
        return False

    # Connection Management Methods

    def add_connection(self, from_component_id: str, from_pin_id: str,
                       to_component_id: str, to_pin_id: str) -> str:
        """Add a connection between two pins"""
        try:
            # Validate components exist
            components_table = self.rdb_manager.get_table(self.components_table_path)
            component_ids = [comp.get('id') for comp in components_table if comp.get('id')]
            if (from_component_id not in component_ids or
                    to_component_id not in component_ids):
                return ""

            connection_id = str(uuid.uuid4())

            connection_data = {
                'id': connection_id,
                'from_component_id': from_component_id,
                'from_pin_id': from_pin_id,
                'to_component_id': to_component_id,
                'to_pin_id': to_pin_id,
                'connection_type': 'wire',
                'properties': {},
                'visual_properties': {
                    'path_points': [],
                    'line_style': 'solid',
                    'color': '#000000'
                }
            }

            # Add directly to RDB
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            connections_table.append(connection_data)
            self.rdb_manager.set_table(self.connections_table_path, connections_table)

            # Emit signal
            self.connection_added.emit(connection_id)

            logger.info(
                f"Added connection: {from_component_id}:{from_pin_id} -> {to_component_id}:{to_pin_id}")
            return connection_id

        except Exception as e:
            logger.error("Error adding connection: %s", e)
            return ""

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection directly from RDB"""
        try:
            connections_table = self.rdb_manager.get_table(self.connections_table_path)
            
            # Find and remove the connection
            for i, connection in enumerate(connections_table):
                if connection.get('id') == connection_id:
                    connections_table.pop(i)
                    self.rdb_manager.set_table(self.connections_table_path, connections_table)
                    
                    # Emit signal
                    self.connection_removed.emit(connection_id)
                    
                    logger.info("Removed connection: %s", connection_id)
                    return True
            
            return False

        except Exception as e:
            logger.error("Error removing connection: %s", e)
            return False

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection data by ID directly from RDB"""
        connections_table = self.rdb_manager.get_table(self.connections_table_path)
        for connection in connections_table:
            if connection.get('id') == connection_id:
                return connection
        return None

    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get all connections directly from RDB"""
        connections_table = self.rdb_manager.get_table(self.connections_table_path)
        return {conn.get('id'): conn for conn in connections_table if conn.get('id')}

    def get_component_connections(
            self, component_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all connections for a specific component directly from RDB"""
        connections_table = self.rdb_manager.get_table(self.connections_table_path)
        return {
            conn.get('id'): conn
            for conn in connections_table
            if conn.get('id') and (conn.get('from_component_id') == component_id or
                                  conn.get('to_component_id') == component_id)
        }

    # New methods for proper MVC architecture

    def get_legacy_bcf_devices(self) -> List[Dict[str, Any]]:
        """Get Legacy BCF device settings through RDB manager"""
        try:
            return self.rdb_manager.get_table(DCF_DEVICES_AVAILABLE)
        except Exception as e:
            logger.error("Error getting Legacy BCF devices: %s", e)
            return []

    def save_scene_data(self, scene_data: Dict[str, Any]) -> bool:
        """Save scene data to default location"""
        try:
            # Save only via normalized tables (components/connections)
            # Convert scene components to table form
            components_list = []
            for comp in scene_data.get("components", []):
                comp_dict = {
                    'id': comp.get('id', comp.get('name', '')),
                    'name': comp.get('name', ''),
                    'component_type': comp.get('type', comp.get('component_type', 'chip')),
                    'function_type': comp.get('properties', {}).get('function_type', ''),
                    'properties': comp.get('properties', {}),
                    'visual_properties': comp.get('visual_properties', {
                        'position': comp.get('position', {'x': 0, 'y': 0}),
                        'size': {'width': 100, 'height': 80},
                        'rotation': 0
                    }),
                    'pins': comp.get('pins', [])
                }
                components_list.append(comp_dict)
            connections_list = []
            for conn in scene_data.get("connections", []):
                # Map by component names -> we'll resolve to IDs if present in
                # components_list
                connections_list.append({
                    'id': conn.get('id', ''),
                    'from_component_id': conn.get('from_component_id', ''),
                    'from_pin_id': conn.get('start_pin', conn.get('from_pin_id', '')),
                    'to_component_id': conn.get('to_component_id', ''),
                    'to_pin_id': conn.get('end_pin', conn.get('to_pin_id', '')),
                    'connection_type': conn.get('connection_type', 'wire'),
                    'properties': conn.get('properties', {}),
                    'visual_properties': conn.get('visual_properties', {
                        'path_points': [], 'line_style': 'solid', 'color': '#000000'
                    })
                })
            self.rdb_manager.set_table(
                self.components_table_path, components_list)
            self.rdb_manager.set_table(
                self.connections_table_path, connections_list)
            # Explicitly persist to disk
            if hasattr(self.rdb_manager.db, 'save'):
                self.rdb_manager.db.save()
            logger.info("Scene data saved to database")
            return True
        except Exception as e:
            logger.error("Error saving scene data: %s", e)
            return False

    def load_scene_data(self) -> Optional[Dict[str, Any]]:
        """Load scene data from default location"""
        try:
            # Build scene-like dict from normalized tables only
            components = self.rdb_manager.get_table(
                self.components_table_path) or []
            connections = self.rdb_manager.get_table(
                self.connections_table_path) or []
            id_to_name = {
                c.get(
                    'id',
                    c.get(
                        'name',
                        '')): c.get(
                    'name',
                    '') for c in components}
            scene_components = []
            for comp in components:
                pos = comp.get(
                    'visual_properties', {}).get(
                    'position', {
                        'x': 0, 'y': 0})
                scene_components.append({
                    'id': comp.get('id', comp.get('name', '')),
                    'name': comp.get('name', ''),
                    'type': comp.get('component_type', 'chip'),
                    'position': {'x': pos.get('x', 0), 'y': pos.get('y', 0)},
                    'properties': comp.get('properties', {}),
                    'visual_properties': comp.get('visual_properties', {})
                })
            scene_connections = []
            for conn in connections:
                scene_connections.append({
                    'id': conn.get('id', ''),
                    'from_component_id': conn.get('from_component_id', ''),  # ✅ Keep component ID
                    'to_component_id': conn.get('to_component_id', ''),     # ✅ Keep component ID
                    'from_pin_id': conn.get('from_pin_id', ''),            # ✅ Use correct key name
                    'to_pin_id': conn.get('to_pin_id', ''),                # ✅ Use correct key name
                    'properties': conn.get('properties', {}),
                    'visual_properties': conn.get('visual_properties', {})
                })
            scene = {
                'components': scene_components,
                'connections': scene_connections}
            logger.info("Scene data reconstructed from tables")
            return scene
        except Exception as e:
            logger.error("Error loading scene data: %s", e)
            return None

    def save_visual_bcf_data(self) -> bool:
        """Save visual BCF data to default database location"""
        try:
            # Data is already saved to RDB directly, just persist to disk
            if hasattr(self.rdb_manager.db, 'save'):
                self.rdb_manager.db.save()

            logger.info("Visual BCF data saved to database")
            return True
        except Exception as e:
            logger.error("Error saving visual BCF data: %s", e)
            return False

    def save_visual_bcf_to_file(self, file_path: str) -> bool:
        """Save visual BCF data to a specific file"""
        try:
            # Get the complete data structure from RDB manager (data is already up-to-date)
            complete_data = self.rdb_manager.db.data

            # Save to the specified file
            import json
            with open(file_path, 'w') as f:
                json.dump(complete_data, f, indent=2)

            logger.info("Visual BCF data saved to file: %s", file_path)
            return True
        except Exception as e:
            logger.error("Error saving visual BCF data to file: %s", e)
            return False

    # Legacy BCF Integration Methods

    def sync_with_legacy_bcf(self):
        """Synchronize with Legacy BCF component definitions"""
        try:
            # Read component definitions from Legacy BCF tables
            device_settings = self.rdb_manager.get_table(DCF_DEVICES_AVAILABLE)

            # Get components from RDB
            components_table = self.rdb_manager.get_table(self.components_table_path)

            # Update component properties based on Legacy BCF data
            for component in components_table:
                comp_id = component.get('id')
                comp_name = component.get('name')
                
                # Find matching device in Legacy BCF
                for device in device_settings:
                    if device.get('name') == comp_name:
                        # Update component properties from Legacy BCF
                        if 'properties' not in component:
                            component['properties'] = {}
                        
                        component['properties'].update({
                            'function_type': device.get('function_type', ''),
                            'interface_type': device.get('interface_type', ''),
                            'interface': device.get('interface', {}),
                            'config': device.get('config', {})
                        })

                        # Emit update signal
                        self.component_updated.emit(comp_id, component)
                        break

            # Update the components table in RDB
            self.rdb_manager.set_table(self.components_table_path, components_table)

            logger.info("Synchronized with Legacy BCF data")
            self.data_synchronized.emit()

        except Exception as e:
            logger.error("Error syncing with Legacy BCF: %s", e)

    def export_to_legacy_bcf(self):
        """Export Visual BCF components to Legacy BCF format"""
        try:
            # Convert Visual BCF components to Legacy BCF device settings
            device_settings = []

            # Get components from RDB
            components_table = self.rdb_manager.get_table(self.components_table_path)

            for component in components_table:
                if component.get('component_type') in ['modem', 'device']:
                    device_entry = {
                        'name': component.get('name', ''), 
                        'function_type': component.get('properties', {}).get('function_type', ''), 
                        'interface_type': component.get('properties', {}).get('interface_type', ''), 
                        'interface': component.get('properties', {}).get('interface', {}), 
                        'config': component.get('properties', {}).get('config', {})
                    }
                    device_settings.append(device_entry)

            # Update Legacy BCF table
            if device_settings:
                self.rdb_manager.set_table(
                    DCF_DEVICES_AVAILABLE, device_settings)
                logger.info(
                    f"Exported {len(device_settings)} components to Legacy BCF")

        except Exception as e:
            logger.error("Error exporting to Legacy BCF: %s", e)

    # Private helper methods



    def _auto_export_component_to_legacy_bcf(
            self, component_data: Dict[str, Any]):
        """Auto-export a component to Legacy BCF if it should appear in the device settings table"""
        try:
            # Export most component types to Legacy BCF (except pure visual
            # elements)
            exportable_types = ['modem', 'device', 'rfic',
                                'chip']  # Added 'chip' for generic chips

            if component_data.get('component_type') in exportable_types:
                # Get existing Legacy BCF device settings
                device_settings = self.rdb_manager.get_table(DCF_DEVICES_AVAILABLE)

                # Check if component already exists in Legacy BCF (avoid
                # duplicates)
                existing_names = {device.get('name', '')
                                  for device in device_settings}
                if component_data.get('name') not in existing_names:
                    # Determine function_type
                    function_type = component_data.get('properties', {}).get(
                        'function_type', component_data.get('function_type', ''))
                    if not function_type:
                        function_type = component_data.get('component_type', '').upper()

                    # Create new device entry for Legacy BCF
                    device_entry = {
                        'name': component_data.get('name', ''), 
                        'function_type': function_type, 
                        'interface_type': component_data.get('properties', {}).get(
                            'interface_type', 'MIPI' if component_data.get('component_type') in [
                                'modem', 'device'] else 'Generic'), 
                        'interface': component_data.get('properties', {}).get(
                            'interface', {
                                'mipi': {
                                    'channel': len(device_settings) + 1}} if component_data.get('component_type') in [
                                'modem', 'device'] else {}), 
                        'config': component_data.get('properties', {}).get(
                            'config', {
                                'usid': f'{
                                    function_type.upper()}{
                                    len(device_settings) + 1:03d}'})}

                    # Add to Legacy BCF table
                    device_settings.append(device_entry)
                    self.rdb_manager.set_table(
                        DCF_DEVICES_AVAILABLE, device_settings)

                    logger.info(
                        f"✅ Auto-exported component '{component_data.get('name')}' (type: {component_data.get('component_type')}, function: {function_type}) to Legacy BCF")
                else:
                    logger.info(
                        f"⏭️ Component '{component_data.get('name')}' already exists in Legacy BCF, skipping export")
            else:
                                    logger.info(
                        f"⏭️ Component '{component_data.get('name')}' type '{component_data.get('component_type')}' not exported to Legacy BCF")

        except Exception as e:
            logger.error(
                f"❌ Error auto-exporting component '{component_data.get('name') if component_data else 'unknown'}' to Legacy BCF: {e}")

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

    # Device Settings Management Methods

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get all available devices from DCF devices table"""
        try:
            devices = self.rdb_manager.get_table(str(DCF_DEVICES_AVAILABLE()) + ".devices")
            return devices or []
        except Exception as e:
            logger.error("Error getting available devices: %s", e)
            return []

    def add_available_device(self, device_data: Dict[str, Any]) -> bool:
        """Add a new available device to DCF devices table"""
        try:
            devices = self.rdb_manager.get_table(str(DCF_DEVICES_AVAILABLE()) + ".devices") or []
            
            # Ensure required columns are present
            required_columns = [
                "Device Name", "Control Type\n(MIPI / GPIO)", "Module", "USID\n(Default)",
                "MID\n(MSB)", "MID\n(LSB)", "PID", "EXT PID", "REV ID", "DCF Type"
            ]
            
            # Create device entry with all required columns
            device_entry = {}
            for col in required_columns:
                device_entry[col] = device_data.get(col, "")
            
            devices.append(device_entry)
            self.rdb_manager.set_table(str(DCF_DEVICES_AVAILABLE()) + ".devices", devices)
            
            logger.info(f"Added available device: {device_data.get('Device Name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error("Error adding available device: %s", e)
            return False

    def get_selected_devices(self, revision: int = 1) -> List[Dict[str, Any]]:
        """Get selected devices for a specific revision from BCF dev MIPI table"""
        try:
            mipi_path = str(BCF_DEV_MIPI(revision)) + ".mips"
            devices = self.rdb_manager.get_table(mipi_path)
            return devices or []
        except Exception as e:
            logger.error("Error getting selected devices for revision %d: %s", revision, e)
            return []

    def add_selected_device(self, device_data: Dict[str, Any], revision: int = 1) -> bool:
        """Add a selected device for a specific revision to BCF dev MIPI table"""
        try:
            mipi_path = str(BCF_DEV_MIPI(revision)) + ".mips"
            devices = self.rdb_manager.get_table(mipi_path) or []
            
            # Ensure required columns are present
            required_columns = ["DCF", "Name", "USID"]
            
            # Create device entry with all required columns
            device_entry = {}
            for col in required_columns:
                device_entry[col] = device_data.get(col, "")
            
            devices.append(device_entry)
            self.rdb_manager.set_table(mipi_path, devices)
            
            logger.info(f"Added selected device for revision {revision}: {device_data.get('Name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error("Error adding selected device for revision %d: %s", revision, e)
            return False

    # IO Connect Management Methods

    def get_io_connections(self) -> List[Dict[str, Any]]:
        """Get all IO connections from the enhanced IO connect table"""
        try:
            connections = self.rdb_manager.get_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects")
            return connections or []
        except Exception as e:
            logger.error("Error getting IO connections: %s", e)
            return []

    def add_io_connection(self, connection_data: Dict[str, Any]) -> bool:
        """Add a new IO connection to the enhanced IO connect table"""
        try:
            connections = self.rdb_manager.get_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects") or []
            
            # Ensure required columns are present (including new Source/Dest Sub Block columns)
            required_columns = [
                "Connection ID", "Source Device", "Source Pin", "Dest Device", "Dest Pin",
                "Connection Type", "Status", "Source Sub Block", "Dest Sub Block"
            ]
            
            # Create connection entry with all required columns
            connection_entry = {}
            for col in required_columns:
                connection_entry[col] = connection_data.get(col, "")
            
            connections.append(connection_entry)
            self.rdb_manager.set_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects", connections)
            
            logger.info(f"Added IO connection: {connection_data.get('Connection ID', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error("Error adding IO connection: %s", e)
            return False

    def update_io_connection(self, connection_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update an existing IO connection in the enhanced IO connect table"""
        try:
            connections = self.rdb_manager.get_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects") or []
            
            # Find and update the connection
            for i, connection in enumerate(connections):
                if connection.get("Connection ID") == connection_id:
                    connections[i].update(updated_data)
                    self.rdb_manager.set_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects", connections)
                    
                    logger.info(f"Updated IO connection: {connection_id}")
                    return True
            
            logger.warning(f"IO connection not found: {connection_id}")
            return False
            
        except Exception as e:
            logger.error("Error updating IO connection %s: %s", connection_id, e)
            return False

    def remove_io_connection(self, connection_id: str) -> bool:
        """Remove an IO connection from the enhanced IO connect table"""
        try:
            connections = self.rdb_manager.get_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects") or []
            
            # Find and remove the connection
            for i, connection in enumerate(connections):
                if connection.get("Connection ID") == connection_id:
                    removed_connection = connections.pop(i)
                    self.rdb_manager.set_table(str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects", connections)
                    
                    logger.info(f"Removed IO connection: {connection_id}")
                    return True
            
            logger.warning(f"IO connection not found: {connection_id}")
            return False
            
        except Exception as e:
            logger.error("Error removing IO connection %s: %s", connection_id, e)
            return False
