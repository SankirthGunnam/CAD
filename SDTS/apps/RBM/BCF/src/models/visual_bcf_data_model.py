"""
Visual BCF Data Access Model

This model acts as a bridge between Visual BCF graphics components and Legacy BCF table data.
It provides a unified interface for Visual BCF to access component data, connection data,
and properties data from the underlying JSON database tables used by Legacy BCF.
"""

from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal
from ..RDB.rdb_manager import RDBManager
import uuid
import logging

logger = logging.getLogger(__name__)


class ComponentData:
    """Represents a component with its properties and position"""
    def __init__(self, component_id: str, data: Dict[str, Any]):
        self.id = component_id
        self.name = data.get('name', '')
        self.component_type = data.get('component_type', 'chip')
        self.function_type = data.get('function_type', '')
        self.properties = data.get('properties', {})
        
        # Visual properties (stored separately from functional properties)
        self.visual_properties = data.get('visual_properties', {
            'position': {'x': 0, 'y': 0},
            'size': {'width': 100, 'height': 80},
            'rotation': 0
        })
        
        # Pin information
        self.pins = data.get('pins', [])
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'name': self.name,
            'component_type': self.component_type,
            'function_type': self.function_type,
            'properties': self.properties,
            'visual_properties': self.visual_properties,
            'pins': self.pins
        }


class ConnectionData:
    """Represents a connection between two pins"""
    def __init__(self, connection_id: str, data: Dict[str, Any]):
        self.id = connection_id
        self.from_component_id = data.get('from_component_id', '')
        self.from_pin_id = data.get('from_pin_id', '')
        self.to_component_id = data.get('to_component_id', '')
        self.to_pin_id = data.get('to_pin_id', '')
        self.connection_type = data.get('connection_type', 'wire')
        self.properties = data.get('properties', {})
        
        # Visual properties for connection display
        self.visual_properties = data.get('visual_properties', {
            'path_points': [],
            'line_style': 'solid',
            'color': '#000000'
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'from_component_id': self.from_component_id,
            'from_pin_id': self.from_pin_id,
            'to_component_id': self.to_component_id,
            'to_pin_id': self.to_pin_id,
            'connection_type': self.connection_type,
            'properties': self.properties,
            'visual_properties': self.visual_properties
        }


class VisualBCFDataModel(QObject):
    """
    Data access model for Visual BCF that interfaces with Legacy BCF table data.
    
    This model provides methods to:
    - Read/Write component data from Legacy BCF tables
    - Manage component positions and visual properties
    - Handle connections between components
    - Synchronize with Legacy BCF changes
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
        
        # Table paths in the JSON database
        self.components_table_path = "config.visual_bcf.components"
        self.connections_table_path = "config.visual_bcf.connections"
        
        # In-memory caches for performance
        self._components_cache: Dict[str, ComponentData] = {}
        self._connections_cache: Dict[str, ConnectionData] = {}
        
        # Connect to database changes
        self.rdb_manager.data_changed.connect(self._on_data_changed)
        
        # Initialize database structure if needed
        self._initialize_visual_bcf_tables()
        
        # Load data into cache
        self._load_data()
    
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
                        "scene_rect": {"x": -1000, "y": -1000, "width": 2000, "height": 2000},
                        "grid_settings": {"enabled": True, "size": 20}
                    }
                }
                self.rdb_manager.set_value("config.visual_bcf", initial_data)
                logger.info("Initialized Visual BCF tables in database")
                
        except Exception as e:
            logger.error(f"Error initializing Visual BCF tables: {e}")
    
    def _load_data(self):
        """Load data from database into cache"""
        try:
            # Load components
            components_data = self.rdb_manager.get_table(self.components_table_path)
            self._components_cache.clear()
            for i, comp_data in enumerate(components_data):
                comp_id = comp_data.get('id', f'comp_{i}')
                self._components_cache[comp_id] = ComponentData(comp_id, comp_data)
            
            # Load connections
            connections_data = self.rdb_manager.get_table(self.connections_table_path)
            self._connections_cache.clear()
            for i, conn_data in enumerate(connections_data):
                conn_id = conn_data.get('id', f'conn_{i}')
                self._connections_cache[conn_id] = ConnectionData(conn_id, conn_data)
                
            logger.info(f"Loaded {len(self._components_cache)} components and {len(self._connections_cache)} connections")
                
        except Exception as e:
            logger.error(f"Error loading Visual BCF data: {e}")
    
    def _on_data_changed(self, changed_path: str):
        """Handle database changes"""
        if changed_path.startswith("config.visual_bcf"):
            # Reload data when Visual BCF section changes
            self._load_data()
            self.data_synchronized.emit()
    
    # Component Management Methods
    
    def add_component(self, name: str, component_type: str, position: Tuple[float, float], 
                     properties: Dict[str, Any] = None) -> str:
        """Add a new component to the scene"""
        try:
            component_id = str(uuid.uuid4())
            
            component_data = ComponentData(component_id, {
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
            })
            
            # Add to cache
            self._components_cache[component_id] = component_data
            
            # Update database
            self._update_components_table()
            
            # Emit signal
            self.component_added.emit(component_id)
            
            logger.info(f"Added component: {name} ({component_id})")
            return component_id
            
        except Exception as e:
            logger.error(f"Error adding component: {e}")
            return ""
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the scene"""
        try:
            if component_id not in self._components_cache:
                return False
            
            # Remove all connections involving this component
            connections_to_remove = []
            for conn_id, conn_data in self._connections_cache.items():
                if (conn_data.from_component_id == component_id or 
                    conn_data.to_component_id == component_id):
                    connections_to_remove.append(conn_id)
            
            for conn_id in connections_to_remove:
                self.remove_connection(conn_id)
            
            # Remove from cache
            component_name = self._components_cache[component_id].name
            del self._components_cache[component_id]
            
            # Update database
            self._update_components_table()
            
            # Emit signal
            self.component_removed.emit(component_id)
            
            logger.info(f"Removed component: {component_name} ({component_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error removing component: {e}")
            return False
    
    def update_component_position(self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position"""
        try:
            if component_id not in self._components_cache:
                return False
            
            component = self._components_cache[component_id]
            component.visual_properties['position'] = {'x': position[0], 'y': position[1]}
            
            # Update database
            self._update_components_table()
            
            # Emit signal
            self.component_updated.emit(component_id, {'position': position})
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating component position: {e}")
            return False
    
    def update_component_properties(self, component_id: str, properties: Dict[str, Any]) -> bool:
        """Update component properties"""
        try:
            if component_id not in self._components_cache:
                return False
            
            component = self._components_cache[component_id]
            component.properties.update(properties)
            
            # Update database
            self._update_components_table()
            
            # Emit signal
            self.component_updated.emit(component_id, {'properties': properties})
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating component properties: {e}")
            return False
    
    def get_component(self, component_id: str) -> Optional[ComponentData]:
        """Get component data by ID"""
        return self._components_cache.get(component_id)
    
    def get_all_components(self) -> Dict[str, ComponentData]:
        """Get all components"""
        return self._components_cache.copy()
    
    def get_components_by_type(self, component_type: str) -> Dict[str, ComponentData]:
        """Get components of a specific type"""
        return {
            comp_id: comp_data 
            for comp_id, comp_data in self._components_cache.items() 
            if comp_data.component_type == component_type
        }
    
    # Connection Management Methods
    
    def add_connection(self, from_component_id: str, from_pin_id: str,
                      to_component_id: str, to_pin_id: str) -> str:
        """Add a connection between two pins"""
        try:
            # Validate components exist
            if (from_component_id not in self._components_cache or 
                to_component_id not in self._components_cache):
                return ""
            
            connection_id = str(uuid.uuid4())
            
            connection_data = ConnectionData(connection_id, {
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
            })
            
            # Add to cache
            self._connections_cache[connection_id] = connection_data
            
            # Update database
            self._update_connections_table()
            
            # Emit signal
            self.connection_added.emit(connection_id)
            
            logger.info(f"Added connection: {from_component_id}:{from_pin_id} -> {to_component_id}:{to_pin_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            return ""
    
    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection"""
        try:
            if connection_id not in self._connections_cache:
                return False
            
            # Remove from cache
            del self._connections_cache[connection_id]
            
            # Update database
            self._update_connections_table()
            
            # Emit signal
            self.connection_removed.emit(connection_id)
            
            logger.info(f"Removed connection: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing connection: {e}")
            return False
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionData]:
        """Get connection data by ID"""
        return self._connections_cache.get(connection_id)
    
    def get_all_connections(self) -> Dict[str, ConnectionData]:
        """Get all connections"""
        return self._connections_cache.copy()
    
    def get_component_connections(self, component_id: str) -> Dict[str, ConnectionData]:
        """Get all connections for a specific component"""
        return {
            conn_id: conn_data
            for conn_id, conn_data in self._connections_cache.items()
            if (conn_data.from_component_id == component_id or 
                conn_data.to_component_id == component_id)
        }
    
    # Legacy BCF Integration Methods
    
    def sync_with_legacy_bcf(self):
        """Synchronize with Legacy BCF component definitions"""
        try:
            # Read component definitions from Legacy BCF tables
            device_settings = self.rdb_manager.get_table("config.device.settings")
            
            # Update component properties based on Legacy BCF data
            for comp_id, comp_data in self._components_cache.items():
                # Find matching device in Legacy BCF
                for device in device_settings:
                    if device.get('name') == comp_data.name:
                        # Update component properties from Legacy BCF
                        comp_data.properties.update({
                            'function_type': device.get('function_type', ''),
                            'interface_type': device.get('interface_type', ''),
                            'interface': device.get('interface', {}),
                            'config': device.get('config', {})
                        })
                        
                        # Emit update signal
                        self.component_updated.emit(comp_id, comp_data.to_dict())
            
            # Update database
            self._update_components_table()
            
            logger.info("Synchronized with Legacy BCF data")
            self.data_synchronized.emit()
            
        except Exception as e:
            logger.error(f"Error syncing with Legacy BCF: {e}")
    
    def export_to_legacy_bcf(self):
        """Export Visual BCF components to Legacy BCF format"""
        try:
            # Convert Visual BCF components to Legacy BCF device settings
            device_settings = []
            
            for comp_data in self._components_cache.values():
                if comp_data.component_type in ['modem', 'device']:
                    device_entry = {
                        'name': comp_data.name,
                        'function_type': comp_data.properties.get('function_type', ''),
                        'interface_type': comp_data.properties.get('interface_type', ''),
                        'interface': comp_data.properties.get('interface', {}),
                        'config': comp_data.properties.get('config', {})
                    }
                    device_settings.append(device_entry)
            
            # Update Legacy BCF table
            if device_settings:
                self.rdb_manager.set_table("config.device.settings", device_settings)
                logger.info(f"Exported {len(device_settings)} components to Legacy BCF")
            
        except Exception as e:
            logger.error(f"Error exporting to Legacy BCF: {e}")
    
    # Private helper methods
    
    def _update_components_table(self):
        """Update the components table in the database"""
        try:
            components_list = []
            for comp_data in self._components_cache.values():
                comp_dict = comp_data.to_dict()
                comp_dict['id'] = comp_data.id  # Ensure ID is included
                components_list.append(comp_dict)
            
            self.rdb_manager.set_table(self.components_table_path, components_list)
            
        except Exception as e:
            logger.error(f"Error updating components table: {e}")
    
    def _update_connections_table(self):
        """Update the connections table in the database"""
        try:
            connections_list = []
            for conn_data in self._connections_cache.values():
                conn_dict = conn_data.to_dict()
                conn_dict['id'] = conn_data.id  # Ensure ID is included
                connections_list.append(conn_dict)
            
            self.rdb_manager.set_table(self.connections_table_path, connections_list)
            
        except Exception as e:
            logger.error(f"Error updating connections table: {e}")
    
    # Utility methods
    
    def clear_all_data(self):
        """Clear all components and connections"""
        try:
            self._components_cache.clear()
            self._connections_cache.clear()
            
            self._update_components_table()
            self._update_connections_table()
            
            logger.info("Cleared all Visual BCF data")
            self.data_synchronized.emit()
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current data"""
        return {
            'total_components': len(self._components_cache),
            'total_connections': len(self._connections_cache),
            'components_by_type': {
                comp_type: len([c for c in self._components_cache.values() if c.component_type == comp_type])
                for comp_type in set(c.component_type for c in self._components_cache.values())
            }
        }
