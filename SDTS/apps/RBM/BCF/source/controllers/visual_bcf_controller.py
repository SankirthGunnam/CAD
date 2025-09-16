"""
Visual BCF Controller

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QMessageBox, QApplication
import logging

from ..models.visual_bcf_data_model import VisualBCFDataModel, ComponentData, ConnectionData
from ...gui.source.visual_bcf.scene import RFScene
from ...gui.source.visual_bcf.view import RFView
from ...gui.custom_widgets.components.chip import Chip
from ...gui.custom_widgets.components.rfic_chip import RFICChip
from ..RDB.rdb_manager import RDBManager

logger = logging.getLogger(__name__)


class ComponentGraphicsItem:
    """Lightweight graphics item that references data model"""
    def __init__(self, component_id: str, graphics_item):
        self.component_id = component_id
        self.graphics_item = graphics_item

    def update_from_model(self, component_data: ComponentData):
        """Update graphics item from model data"""
        # Update position
        pos = component_data.visual_properties['position']
        self.graphics_item.setPos(pos['x'], pos['y'])

        # Update properties if graphics item supports it
        if hasattr(self.graphics_item, 'update_properties'):
            self.graphics_item.update_properties(component_data.properties)


class ConnectionGraphicsItem:
    """Lightweight graphics item for connections that references data model"""
    def __init__(self, connection_id: str, graphics_item):
        self.connection_id = connection_id
        self.graphics_item = graphics_item

    def update_from_model(self, connection_data: ConnectionData):
        """Update graphics item from model data"""
        # Update visual properties if graphics item supports it
        if hasattr(self.graphics_item, 'update_visual_properties'):
            self.graphics_item.update_visual_properties(connection_data.visual_properties)


class VisualBCFController(QObject):
    """
    Controller for Visual BCF that implements MVC pattern.

    Responsibilities:
    - Handle user interactions from scene/view
    - Coordinate between graphics items and data model
    - Manage component and connection operations
    - Synchronize with Legacy BCF when needed
    """

    # Signals
    component_selected = Signal(str)  # component_id
    connection_selected = Signal(str)  # connection_id
    selection_changed = Signal(list)  # list of selected item IDs
    operation_completed = Signal(str, str)  # operation_type, message
    error_occurred = Signal(str)  # error_message
    component_removed_by_user = Signal(str)  # component_name - NEW signal for user deletions

    def __init__(self, view: RFView, data_model: VisualBCFDataModel):
        super().__init__()
        self.view = view
        self.scene = self.view.scene()
        self.data_model = data_model

        # Maps to track graphics items
        self._component_graphics_items: Dict[str, ComponentGraphicsItem] = {}
        self._connection_graphics_items: Dict[str, ConnectionGraphicsItem] = {}

        # Connect scene signals
        self._connect_scene_signals()

        # Connect model signals
        self._connect_model_signals()

        # Load existing data
        self._load_existing_data()

        # Current mode (select, connect, etc.)
        self.current_mode = "select"

        # Clipboard for copy/paste
        self.clipboard_data: List[Dict[str, Any]] = []

        logger.info("VisualBCFController initialized")

    # Business Logic Methods (moved from VisualBCFManager for proper MVC separation)

    def add_lte_modem(self, position: tuple = None, name: str = None) -> str:
        """Add LTE modem component"""
        try:
            if not position:
                # Use default position if none provided
                position = (0, 0)
            if not name:
                modems = self.data_model.get_components_by_type('modem')
                name = f"LTE_Modem_{len(modems) + 1}"

            properties = {
                'function_type': 'LTE',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 1}},
                'config': {'usid': f'LTE{len(self.data_model.get_all_components()) + 1:03d}'}
            }

            return self.add_component(name, 'modem', position, properties)
        except Exception as e:
            logger.error(f"Error adding LTE modem: {e}")
            self.error_occurred.emit(f"Failed to add LTE modem: {str(e)}")
            return ""

    def add_5g_modem(self, position: tuple = None, name: str = None) -> str:
        """Add 5G modem component"""
        try:
            if not position:
                position = (150, 0)
            if not name:
                modems = self.data_model.get_components_by_type('modem')
                name = f"5G_Modem_{len(modems) + 1}"

            properties = {
                'function_type': '5G',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 2}},
                'config': {'usid': f'5G{len(self.data_model.get_all_components()) + 1:03d}'}
            }

            return self.add_component(name, 'modem', position, properties)
        except Exception as e:
            logger.error(f"Error adding 5G modem: {e}")
            self.error_occurred.emit(f"Failed to add 5G modem: {str(e)}")
            return ""

    def add_rfic_chip(self, position: tuple = None, name: str = None) -> str:
        """Add RFIC chip component"""
        try:
            if not position:
                position = (0, 150)
            if not name:
                rfics = self.data_model.get_components_by_type('rfic')
                name = f"RFIC_{len(rfics) + 1}"

            properties = {
                'function_type': 'RFIC',
                'frequency_range': '600MHz - 6GHz',
                'technology': 'CMOS',
                'package': 'BGA',
                'rf_bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B8', 'B20', 'B28']
            }

            return self.add_component(name, 'rfic', position, properties)
        except Exception as e:
            logger.error(f"Error adding RFIC chip: {e}")
            self.error_occurred.emit(f"Failed to add RFIC chip: {str(e)}")
            return ""

    def add_generic_chip(self, position: tuple = None, name: str = None) -> str:
        """Add generic chip component"""
        try:
            if not position:
                position = (300, 0)
            if not name:
                all_components = self.data_model.get_all_components()
                name = f"Chip_{len(all_components) + 1}"

            properties = {'function_type': 'generic'}

            return self.add_component(name, 'chip', position, properties)
        except Exception as e:
            logger.error(f"Error adding generic chip: {e}")
            self.error_occurred.emit(f"Failed to add generic chip: {str(e)}")
            return ""

    def _connect_scene_signals(self):
        """Connect to scene signals"""
        self.scene.add_chip_requested.connect(self._on_add_chip_requested)
        self.scene.chip_selected.connect(self._on_component_selected)
        self.scene.selection_changed.connect(self._on_selection_changed)

        # Connect to graphics view events if needed
        # Note: More specific event handling can be added here

    def _connect_model_signals(self):
        """Connect to data model signals"""
        self.data_model.component_added.connect(self._on_model_component_added)
        self.data_model.component_removed.connect(self._on_model_component_removed)
        self.data_model.component_updated.connect(self._on_model_component_updated)
        self.data_model.connection_added.connect(self._on_model_connection_added)
        self.data_model.connection_removed.connect(self._on_model_connection_removed)
        self.data_model.connection_updated.connect(self._on_model_connection_updated)
        self.data_model.data_synchronized.connect(self._on_data_synchronized)

    def _load_existing_data(self):
        """Load existing data from model and create graphics items"""
        try:
            # Load components
            components = self.data_model.get_all_components()
            for component_id, component_data in components.items():
                self._create_graphics_component(component_id, component_data)

            # Load connections
            connections = self.data_model.get_all_connections()
            for connection_id, connection_data in connections.items():
                self._create_graphics_connection(connection_id, connection_data)

            logger.info(f"Loaded {len(components)} components and {len(connections)} connections")

        except Exception as e:
            logger.error(f"Error loading existing data: {e}")
            self.error_occurred.emit(f"Failed to load existing data: {str(e)}")

    # Model event handlers

    def _on_model_component_added(self, component_id: str):
        """Handle component added to model"""
        try:
            component_data = self.data_model.get_component(component_id)
            if component_data:
                self._create_graphics_component(component_id, component_data)

        except Exception as e:
            logger.error(f"Error handling model component added: {e}")

    def _on_model_component_removed(self, component_id: str):
        """Handle component removed from model"""
        try:
            if component_id in self._component_graphics_items:
                graphics_item = self._component_graphics_items[component_id]
                self.scene.removeItem(graphics_item.graphics_item)
                del self._component_graphics_items[component_id]

        except Exception as e:
            logger.error(f"Error handling model component removed: {e}")

    def _on_model_component_updated(self, component_id: str, updated_data: Dict[str, Any]):
        """Handle component updated in model"""
        try:
            if component_id in self._component_graphics_items:
                component_data = self.data_model.get_component(component_id)
                if component_data:
                    graphics_item = self._component_graphics_items[component_id]
                    graphics_item.update_from_model(component_data)

        except Exception as e:
            logger.error(f"Error handling model component updated: {e}")

    def _on_model_connection_added(self, connection_id: str):
        """Handle connection added to model"""
        try:
            connection_data = self.data_model.get_connection(connection_id)
            if connection_data:
                self._create_graphics_connection(connection_id, connection_data)

        except Exception as e:
            logger.error(f"Error handling model connection added: {e}")

    def _on_model_connection_removed(self, connection_id: str):
        """Handle connection removed from model"""
        try:
            if connection_id in self._connection_graphics_items:
                graphics_item = self._connection_graphics_items[connection_id]
                self.scene.removeItem(graphics_item.graphics_item)
                del self._connection_graphics_items[connection_id]

        except Exception as e:
            logger.error(f"Error handling model connection removed: {e}")

    def _on_model_connection_updated(self, connection_id: str, updated_data: Dict[str, Any]):
        """Handle connection updated in model"""
        try:
            if connection_id in self._connection_graphics_items:
                connection_data = self.data_model.get_connection(connection_id)
                if connection_data:
                    graphics_item = self._connection_graphics_items[connection_id]
                    graphics_item.update_from_model(connection_data)

        except Exception as e:
            logger.error(f"Error handling model connection updated: {e}")

    def _on_data_synchronized(self):
        """Handle data synchronization complete"""
        logger.info("Data synchronized with database")
        self.operation_completed.emit("sync", "Data synchronized successfully")

    # Scene event handlers

    def _on_add_chip_requested(self, position: QPointF):
        """Handle add chip request from scene"""
        try:
            # For now, add a simple chip. In real implementation,
            # this could open a dialog to select chip type
            self.add_component(
                name=f"Chip_{len(self.data_model.get_all_components()) + 1}",
                component_type="chip",
                position=(position.x(), position.y()),
                properties={"function_type": "generic"}
            )

        except Exception as e:
            logger.error(f"Error handling add chip request: {e}")
            self.error_occurred.emit(f"Failed to add chip: {str(e)}")

    def _on_component_selected(self, graphics_component):
        """Handle component selection from scene"""
        try:
            # Find the component ID for this graphics item
            for component_id, graphics_item in self._component_graphics_items.items():
                if graphics_item.graphics_item == graphics_component:
                    self.component_selected.emit(component_id)
                    break

        except Exception as e:
            logger.error(f"Error handling component selection: {e}")

    def _on_selection_changed(self, has_selection: bool):
        """Handle selection changed from scene"""
        try:
            selected_items = self.scene.selectedItems()
            selected_ids = []

            for item in selected_items:
                # Find corresponding component or connection ID
                for component_id, graphics_item in self._component_graphics_items.items():
                    if graphics_item.graphics_item == item:
                        selected_ids.append(component_id)
                        break

                for connection_id, graphics_item in self._connection_graphics_items.items():
                    if graphics_item.graphics_item == item:
                        selected_ids.append(connection_id)
                        break

            self.selection_changed.emit(selected_ids)

        except Exception as e:
            logger.error(f"Error handling selection changed: {e}")

    # Public methods for component operations

    def add_component(self, name: str, component_type: str, position: Tuple[float, float],
                     properties: Dict[str, Any] = None) -> str:
        """Add a new component"""
        try:
            component_id = self.data_model.add_component(name, component_type, position, properties)
            if component_id:
                self.operation_completed.emit("add_component", f"Added component: {name}")
                logger.info(f"Successfully added component: {name} at {position}")
            return component_id

        except Exception as e:
            logger.error(f"Error adding component: {e}")
            self.error_occurred.emit(f"Failed to add component: {str(e)}")
            return ""

    def remove_component(self, component_id: str, emit_user_signal: bool = False) -> bool:
        """Remove a component"""
        try:
            component_data = self.data_model.get_component(component_id)
            if not component_data:
                return False

            component_name = component_data.name
            success = self.data_model.remove_component(component_id)
            if success:
                self.operation_completed.emit("remove_component", f"Removed component: {component_name}")

                # Emit user deletion signal if this was a user-initiated deletion
                if emit_user_signal:
                    self.component_removed_by_user.emit(component_name)
                    logger.info(f"User removed component: {component_name} - will sync to Legacy BCF")

                logger.info(f"Successfully removed component: {component_name}")
            return success

        except Exception as e:
            logger.error(f"Error removing component: {e}")
            self.error_occurred.emit(f"Failed to remove component: {str(e)}")
            return False

    def remove_component_by_name(self, name: str) -> bool:
        """Remove a component by name"""
        try:
            success = self.data_model.remove_component_by_name(name)
            if success:
                self.operation_completed.emit("remove_component", f"Removed component: {name}")
                logger.info(f"Successfully removed component: {name}")
            return success

        except Exception as e:
            logger.error(f"Error removing component by name: {e}")
            self.error_occurred.emit(f"Failed to remove component: {str(e)}")
            return False

    def update_component_position(self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position"""
        try:
            return self.data_model.update_component_position(component_id, position)

        except Exception as e:
            logger.error(f"Error updating component position: {e}")
            return False

    def update_component_properties(self, component_id: str, properties: Dict[str, Any]) -> bool:
        """Update component properties"""
        try:
            success = self.data_model.update_component_properties(component_id, properties)
            if success:
                component_data = self.data_model.get_component(component_id)
                self.operation_completed.emit("update_properties",
                    f"Updated properties for: {component_data.name if component_data else component_id}")
            return success

        except Exception as e:
            logger.error(f"Error updating component properties: {e}")
            self.error_occurred.emit(f"Failed to update component properties: {str(e)}")
            return False

    # Public methods for connection operations

    def add_connection(self, from_component_id: str, from_pin_id: str,
                      to_component_id: str, to_pin_id: str) -> str:
        """Add a connection between two pins"""
        try:
            connection_id = self.data_model.add_connection(
                from_component_id, from_pin_id, to_component_id, to_pin_id
            )
            if connection_id:
                self.operation_completed.emit("add_connection", "Added connection")
                logger.info(f"Successfully added connection: {connection_id}")
            return connection_id

        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            self.error_occurred.emit(f"Failed to add connection: {str(e)}")
            return ""

    def remove_connection(self, connection_id: str) -> bool:
        """Remove a connection"""
        try:
            success = self.data_model.remove_connection(connection_id)
            if success:
                self.operation_completed.emit("remove_connection", "Removed connection")
                logger.info(f"Successfully removed connection: {connection_id}")
            return success

        except Exception as e:
            logger.error(f"Error removing connection: {e}")
            self.error_occurred.emit(f"Failed to remove connection: {str(e)}")
            return False

    # Selection and clipboard operations

    def get_selected_components(self) -> List[str]:
        """Get IDs of selected components"""
        selected_items = self.scene.selectedItems()
        selected_ids = []

        for item in selected_items:
            for component_id, graphics_item in self._component_graphics_items.items():
                if graphics_item.graphics_item == item:
                    selected_ids.append(component_id)
                    break

        return selected_ids

    def copy_selected_components(self):
        """Copy selected components to clipboard"""
        try:
            selected_ids = self.get_selected_components()
            if not selected_ids:
                return

            self.clipboard_data = []
            for component_id in selected_ids:
                component_data = self.data_model.get_component(component_id)
                if component_data:
                    self.clipboard_data.append({
                        'type': 'component',
                        'data': component_data.to_dict()
                    })

            self.operation_completed.emit("copy", f"Copied {len(self.clipboard_data)} components")
            logger.info(f"Copied {len(self.clipboard_data)} components to clipboard")

        except Exception as e:
            logger.error(f"Error copying components: {e}")
            self.error_occurred.emit(f"Failed to copy components: {str(e)}")

    def paste_components(self, position: Tuple[float, float] = None):
        """Paste components from clipboard"""
        try:
            if not self.clipboard_data:
                return

            # Use current view center as default position
            if position is None:
                center = self.view.mapToScene(self.view.viewport().rect().center())
                base_x, base_y = center.x(), center.y()
            else:
                base_x, base_y = position

            pasted_count = 0

            for i, clip_item in enumerate(self.clipboard_data):
                if clip_item['type'] == 'component':
                    comp_data = clip_item['data']
                    # Offset each pasted component to avoid overlap
                    offset_x = base_x + (i % 3) * 50  # Arrange in grid pattern
                    offset_y = base_y + (i // 3) * 50

                    new_name = f"{comp_data['name']}_copy_{i+1}"
                    self.add_component(
                        name=new_name,
                        component_type=comp_data['component_type'],
                        position=(offset_x, offset_y),
                        properties=comp_data['properties']
                    )
                    pasted_count += 1

            if pasted_count > 0:
                self.operation_completed.emit("paste", f"Pasted {pasted_count} components")
                logger.info(f"Pasted {pasted_count} components")

        except Exception as e:
            logger.error(f"Error pasting components: {e}")
            self.error_occurred.emit(f"Failed to paste components: {str(e)}")

    def delete_selected_components(self):
        """Delete selected components (user-initiated)"""
        try:
            selected_ids = self.get_selected_components()
            if not selected_ids:
                return

            # Show confirmation dialog
            reply = QMessageBox.question(
                None,
                "Delete Components",
                f"Are you sure you want to delete {len(selected_ids)} component(s)?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                deleted_count = 0
                for component_id in selected_ids:
                    # Use emit_user_signal=True for user-initiated deletions
                    if self.remove_component(component_id, emit_user_signal=True):
                        deleted_count += 1

                if deleted_count > 0:
                    self.operation_completed.emit("delete", f"Deleted {deleted_count} components")
                    logger.info(f"Deleted {deleted_count} components")

        except Exception as e:
            logger.error(f"Error deleting components: {e}")
            self.error_occurred.emit(f"Failed to delete components: {str(e)}")

    # Legacy BCF integration

    def sync_with_legacy_bcf(self):
        """Synchronize with Legacy BCF data"""
        try:
            self.data_model.sync_with_legacy_bcf()
            self.operation_completed.emit("sync_legacy", "Synchronized with Legacy BCF")

        except Exception as e:
            logger.error(f"Error syncing with Legacy BCF: {e}")
            self.error_occurred.emit(f"Failed to sync with Legacy BCF: {str(e)}")

    def export_to_legacy_bcf(self):
        """Export Visual BCF data to Legacy BCF format"""
        try:
            self.data_model.export_to_legacy_bcf()
            self.operation_completed.emit("export_legacy", "Exported to Legacy BCF")

        except Exception as e:
            logger.error(f"Error exporting to Legacy BCF: {e}")
            self.error_occurred.emit(f"Failed to export to Legacy BCF: {str(e)}")

    def import_from_legacy_bcf(self, component_names: List[str] = None) -> Dict[str, int]:
        """Import components from Legacy BCF with duplicate prevention"""
        try:
            # Get access to RDB manager through data model
            rdb_manager = self.data_model.rdb_manager
            if not rdb_manager:
                raise Exception("RDB manager not available")

            # Get Legacy BCF device settings
            device_settings = rdb_manager.get_table("config.device.settings")

            # Get existing components to avoid duplicates
            existing_components = self.data_model.get_all_components()
            existing_names = {comp.name for comp in existing_components.values()}

            imported_count = 0
            skipped_count = 0

            for i, device in enumerate(device_settings):
                device_name = device.get('name', f'Device_{i}')

                # Skip if specific components requested and this isn't one of them
                if component_names and device_name not in component_names:
                    continue

                # Skip if component already exists (prevent duplicates)
                if device_name in existing_names:
                    skipped_count += 1
                    continue

                # Determine component type based on function type
                function_type = device.get('function_type', '').upper()
                if function_type in ['LTE', '5G']:
                    component_type = 'modem'
                elif function_type == 'RFIC':
                    component_type = 'rfic'
                else:
                    component_type = 'device'

                # Create component with Legacy BCF properties
                properties = {
                    'function_type': function_type,
                    'interface_type': device.get('interface_type', ''),
                    'interface': device.get('interface', {}),
                    'config': device.get('config', {})
                }

                # Add with automatic positioning
                position = (100 + (imported_count * 150), 100 + (imported_count * 100))

                component_id = self.add_component(
                    name=device_name,
                    component_type=component_type,
                    position=position,
                    properties=properties
                )

                if component_id:
                    imported_count += 1
                    existing_names.add(device_name)  # Track newly added

            result = {
                'imported': imported_count,
                'skipped': skipped_count
            }

            if imported_count > 0 or skipped_count > 0:
                message = f"Imported {imported_count} new devices, skipped {skipped_count} duplicates"
                self.operation_completed.emit("import_legacy", message)
                logger.info(message)

            return result

        except Exception as e:
            error_msg = f"Failed to import from Legacy BCF: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {'imported': 0, 'skipped': 0}

    def auto_import_on_startup(self) -> Dict[str, int]:
        """Auto-import devices from Legacy BCF on startup"""
        try:
            logger.info("🔄 Auto-importing devices from Legacy BCF on startup...")

            # Get access to RDB manager through data model
            rdb_manager = self.data_model.rdb_manager
            if not rdb_manager:
                raise Exception("RDB manager not available")

            # Check if there are any Legacy BCF devices to import
            device_settings = rdb_manager.get_table("config.device.settings")

            if device_settings:
                # Import all devices from Legacy BCF
                result = self.import_from_legacy_bcf()
                logger.info(f"Auto-import: imported {result['imported']}, skipped {result['skipped']} devices")
            else:
                # No Legacy BCF devices exist, add default RFIC instead
                logger.info("No Legacy BCF devices found, adding default RFIC")
                default_id = self.add_default_rfic()
                result = {'imported': 1 if default_id else 0, 'skipped': 0}

            # Emit startup import complete signal
            self.operation_completed.emit("auto_import_startup", "Auto-imported devices from Legacy BCF on startup")
            logger.info("✅ Auto-import on startup completed")

            return result

        except Exception as e:
            error_msg = f"Auto-import failed: {str(e)}"
            logger.error(f"Error during auto-import on startup: {e}")
            self.error_occurred.emit(error_msg)
            return {'imported': 0, 'skipped': 0}

    def add_default_rfic(self) -> str:
        """Add default RFIC chip component (only if no components exist)"""
        try:
            # Check if any components already exist in the database
            existing_components = self.data_model.get_all_components()
            if existing_components:
                # Components already exist, no need to add default
                logger.info("Components already exist, skipping default RFIC")
                return ""

            # Add a default RFIC chip at center
            name = "Default RFIC Chip"
            position = (0, 0)
            component_type = "rfic"
            properties = {
                'function_type': 'RFIC',
                'frequency_range': '600MHz - 6GHz',
                'technology': 'CMOS',
                'package': 'BGA',
                'rf_bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B8', 'B20', 'B28']
            }

            component_id = self.add_component(name, component_type, position, properties)

            if component_id:
                logger.info(f"Added default RFIC chip: {name}")

            return component_id

        except Exception as e:
            error_msg = f"Error adding default RFIC chip: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return ""

    # Utility methods

    def clear_scene(self, show_confirmation: bool = False):
        """Clear all components and connections"""
        try:
            should_clear = True

            if show_confirmation:
                # Show confirmation dialog only if requested
                reply = QMessageBox.question(
                    None,
                    "Clear Scene",
                    "Are you sure you want to clear all components and connections?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                should_clear = (reply == QMessageBox.Yes)

            if should_clear:
                self.data_model.clear_all_data()
                self.operation_completed.emit("clear", "Cleared all components and connections")
                logger.info("Cleared all data")

        except Exception as e:
            logger.error(f"Error clearing scene: {e}")
            self.error_occurred.emit(f"Failed to clear scene: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about current data"""
        return self.data_model.get_statistics()

    # Private helper methods

    def _create_graphics_component(self, component_id: str, component_data: ComponentData):
        """Create graphics item for component"""
        try:
            # Get visual properties
            size = component_data.visual_properties.get('size', {'width': 100, 'height': 80})
            width = size['width']
            height = size['height']

            # Create appropriate model based on component type
            if component_data.component_type == "rfic" or component_data.function_type == "RFIC":
                from ...source.models.rfic_chip import RFICChipModel

                # Create RFIC model with component properties
                chip_model = RFICChipModel(
                    name=component_data.name,
                    width=width,
                    height=height
                )

                # Update model properties from component data
                chip_model.properties.update(component_data.properties)

                # Create graphics item
                graphics_item = RFICChip(chip_model)

            elif component_data.component_type in ["modem", "device"] or component_data.function_type in ["LTE", "5G", "WLAN"]:
                from ...source.models.chip import ChipModel

                # Create specialized chip model for modems/devices
                chip_model = ChipModel(
                    name=component_data.name,
                    width=width,
                    height=height
                )

                # Update model properties from component data
                chip_model.properties.update(component_data.properties)
                chip_model.properties.update({
                    "function": f"{component_data.function_type} {component_data.component_type.capitalize()}",
                    "interface_type": component_data.properties.get('interface_type', ''),
                    "type": component_data.component_type.capitalize()
                })

                # Create graphics item
                graphics_item = Chip(chip_model)

            else:
                # Create generic chip model
                from ...source.models.chip import ChipModel

                chip_model = ChipModel(
                    name=component_data.name,
                    width=width,
                    height=height
                )

                # Update model properties from component data
                chip_model.properties.update(component_data.properties)
                chip_model.properties.update({
                    "function": component_data.properties.get('function_type', 'Generic Chip'),
                    "type": component_data.component_type.capitalize()
                })

                # Create graphics item
                graphics_item = Chip(chip_model)

            # Set position
            pos = component_data.visual_properties['position']
            graphics_item.setPos(pos['x'], pos['y'])

            # Set additional visual properties if supported
            if hasattr(graphics_item, 'set_rotation'):
                rotation = component_data.visual_properties.get('rotation', 0)
                graphics_item.set_rotation(rotation)

            # Add to scene using the scene's method to handle pins properly
            self.scene.add_component(graphics_item)

            # Create wrapper and store
            component_graphics_item = ComponentGraphicsItem(component_id, graphics_item)
            self._component_graphics_items[component_id] = component_graphics_item

            logger.info(f"Created graphics item for component: {component_data.name} (type: {component_data.component_type})")

        except Exception as e:
            logger.error(f"Error creating graphics component: {e}")
            logger.exception("Full traceback:")

    def _create_graphics_connection(self, connection_id: str, connection_data: ConnectionData):
        """Create graphics item for connection"""
        try:
            # For now, create a simple connection graphics item
            # In a full implementation, this would create the actual connection graphics
            from ...gui.custom_widgets.components.connection import Connection as ConnectionComponent

            # Find the source and target components
            from_graphics = self._component_graphics_items.get(connection_data.from_component_id)
            to_graphics = self._component_graphics_items.get(connection_data.to_component_id)

            if from_graphics and to_graphics:
                # Create connection graphics item
                # This is simplified - in practice you'd need to find the actual pins
                connection_graphics = ConnectionComponent(from_graphics.graphics_item)

                # Add to scene
                self.scene.addItem(connection_graphics)

                # Create wrapper and store
                connection_graphics_item = ConnectionGraphicsItem(connection_id, connection_graphics)
                self._connection_graphics_items[connection_id] = connection_graphics_item

                logger.info(f"Created graphics item for connection: {connection_id}")

        except Exception as e:
            logger.error(f"Error creating graphics connection: {e}")

    def set_mode(self, mode: str):
        """Set the current interaction mode"""
        self.current_mode = mode
        logger.info(f"Set mode to: {mode}")

    def get_mode(self) -> str:
        """Get the current interaction mode"""
        return self.current_mode

    def delete_component_by_graphics_item(self, graphics_item) -> bool:
        """Delete a component by its graphics item (user-initiated from scene)"""
        try:
            # Find the component ID for this graphics item
            for component_id, graphics_wrapper in self._component_graphics_items.items():
                if graphics_wrapper.graphics_item == graphics_item:
                    return self.remove_component(component_id, emit_user_signal=True)

            logger.warning(f"Graphics item not found in component mapping")
            return False

        except Exception as e:
            logger.error(f"Error deleting component by graphics item: {e}")
            return False

    def delete_selected_components_by_graphics_items(self, graphics_items: list) -> int:
        """Delete multiple components by their graphics items (user-initiated from scene)"""
        try:
            deleted_count = 0

            for graphics_item in graphics_items:
                # Find the component ID for this graphics item
                for component_id, graphics_wrapper in self._component_graphics_items.items():
                    if graphics_wrapper.graphics_item == graphics_item:
                        if self.remove_component(component_id, emit_user_signal=True):
                            deleted_count += 1
                        break

            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting components by graphics items: {e}")
            return 0
