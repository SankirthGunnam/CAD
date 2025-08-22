"""
Visual BCF Controller - Refactored

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

import logging
from typing import Dict, List, Any, Tuple

from PySide6.QtCore import QObject, Signal, QTimer, Qt, QPoint
from PySide6.QtWidgets import QWidget

from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import (

    VisualBCFDataModel, ComponentData, ConnectionData)
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, Wire
from apps.RBM5.BCF.gui.source.visual_bcf.floating_toolbar import FloatingToolbar

logger = logging.getLogger(__name__)


class ComponentGraphicsItem:
    """Lightweight graphics item that references data model"""

    def __init__(self, component_id: str, graphics_item):
        self.component_id = component_id
        self.graphics_item = graphics_item


class ConnectionGraphicsItem:
    """Lightweight graphics item for connections that references data model"""

    def __init__(self, connection_id: str, graphics_item):
        self.connection_id = connection_id
        self.graphics_item = graphics_item


class VisualBCFController(QObject):
    """
    Controller for Visual BCF that implements MVC pattern.

    Responsibilities:
    - Handle user interactions from scene/view
    - Coordinate between graphics items and data model
    - Manage component and connection operations
    """

    # Signals
    operation_completed = Signal(str, str)  # operation_type, message
    error_occurred = Signal(str)  # error_message

    def __init__(self, parent_widget: QWidget, data_model: VisualBCFDataModel):
        super().__init__()
        self.parent_widget = parent_widget
        self.data_model = data_model

        # Create scene and view
        self.scene = ComponentScene(controller=self)
        self.scene.setParent(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        self.view = CustomGraphicsView(self.scene)
        self.view.setObjectName("BCFGraphicsView")
        self.view.setMinimumSize(600, 400)

        # Maps to track graphics items
        self._component_graphics_items: Dict[str, ComponentGraphicsItem] = {}
        self._connection_graphics_items: Dict[str, ConnectionGraphicsItem] = {}

        # Component placement state
        self.placement_mode = False
        self.selected_component_type = "chip"

        # Create floating toolbar
        self.floating_toolbar = None

        # Connect signals
        self._connect_signals()

        # Load existing data
        self.load_scene()

        # Setup toolbar after everything else is initialized
        self._setup_toolbar()

        # Setup periodic cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_stale_graphics_items)
        self.cleanup_timer.start(5000)  # Clean up every 5 seconds

        logger.info("VisualBCFController initialized with own view and scene")

    def _setup_toolbar(self):
        """Create floating toolbar with component placement functionality"""
        self.floating_toolbar = FloatingToolbar(
            parent=self.parent_widget)

        # Connect toolbar signals immediately
        self.floating_toolbar.add_chip_requested.connect(
            lambda: self._set_component_type("chip"))
        self.floating_toolbar.add_resistor_requested.connect(
            lambda: self._set_component_type("resistor"))
        self.floating_toolbar.add_capacitor_requested.connect(
            lambda: self._set_component_type("capacitor"))
        self.floating_toolbar.select_mode_requested.connect(
            self._set_select_mode)
        self.floating_toolbar.connection_mode_requested.connect(
            self._set_select_mode)
        self.floating_toolbar.delete_selected_requested.connect(
            self._on_delete_selected)
        self.floating_toolbar.clear_scene_requested.connect(
            self._on_clear_scene)
        self.floating_toolbar.zoom_fit_requested.connect(self._on_zoom_fit)
        
        # Connect scene operation signals
        self.floating_toolbar.save_scene_requested.connect(
            self._on_save_scene)
        self.floating_toolbar.load_scene_requested.connect(
            self._on_load_scene)

        # Connect zoom signals to view
        if self.view:
            self.floating_toolbar.zoom_in_requested.connect(self.view.zoom_in)
            self.floating_toolbar.zoom_out_requested.connect(
                self.view.zoom_out)
            self.floating_toolbar.zoom_reset_requested.connect(
                self.view.reset_zoom)

        # Use QTimer to delay positioning until the parent widget is fully
        # ready
        QTimer.singleShot(100, self._finalize_toolbar_setup)

    def _finalize_toolbar_setup(self):
        """Finalize toolbar setup after parent widget is fully initialized"""
        if self.floating_toolbar:
            # Make sure the toolbar is visible and on top
            self.floating_toolbar.raise_()
            self.floating_toolbar.show()
            self._position_toolbar_on_graphics_view()

    def _position_toolbar_on_graphics_view(self):
        """Position the floating toolbar at the top-center of the graphics view"""
        if not self.view or not self.floating_toolbar:
            return

        if not self.parent_widget:
            return

        # Get the graphics view's geometry within the parent widget
        view_rect = self.view.geometry()
        self.floating_toolbar.adjustSize()
        actual_toolbar_size = self.floating_toolbar.size()

        # Calculate the graphics view's position relative to the parent widget
        view_global_pos = self.view.mapTo(self.parent_widget, QPoint(0, 0))

        # Position toolbar at the top-center of the graphics view
        x = view_global_pos.x() + max(10,
                                      (view_rect.width() - actual_toolbar_size.width()) // 2)
        y = view_global_pos.y() + 10  # 10px from top of graphics view

        # Ensure the toolbar is within the parent's bounds
        x = max(0, min(x, self.parent_widget.width() - actual_toolbar_size.width()))
        y = max(0, min(y, self.parent_widget.height() -
                actual_toolbar_size.height()))

        self.floating_toolbar.move(x, y)

        # Debug logging
        logger.info(
            f"Positioned floating toolbar at ({x}, {y}) relative to graphics view at {view_global_pos}")

    def _set_component_type(self, component_type: str):
        """Set the component type for placement"""
        self.selected_component_type = component_type
        self.placement_mode = True

    def _set_select_mode(self):
        """Set to select mode"""
        self.placement_mode = False

    def _on_delete_selected(self):
        """Handle delete selected request from toolbar"""
        try:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    if isinstance(item, ComponentWithPins):
                        # Find component ID and remove
                        for component_id, wrapper in self._component_graphics_items.items():
                            if wrapper.graphics_item == item:
                                self.remove_component(
                                    component_id, emit_user_signal=True)
                                break
                    elif isinstance(item, Wire):
                        # Find connection ID and remove
                        for connection_id, wrapper in self._connection_graphics_items.items():
                            if wrapper.graphics_item == item:
                                self.remove_connection(connection_id)
                                break

                self.operation_completed.emit(
                    "delete", f"Deleted {
                        len(selected_items)} selected items")
        except Exception as e:
            logger.error(f"Error deleting selected items: {e}")
            self.error_occurred.emit(
                f"Failed to delete selected items: {
                    str(e)}")

    def _on_clear_scene(self):
        """Handle clear scene request from toolbar"""
        try:
            self.clear_scene(show_confirmation=False)
            self.operation_completed.emit("clear", "Scene cleared")
        except Exception as e:
            logger.error(f"Error clearing scene: {e}")
            self.error_occurred.emit(f"Failed to clear scene: {str(e)}")

    def _on_save_scene(self):
        """Handle save scene request from toolbar"""
        try:
            # Use the existing save_scene method
            success = self.save_scene()
            if success:
                self.operation_completed.emit("save", "Scene saved successfully")
            else:
                self.error_occurred.emit("Failed to save scene")
        except Exception as e:
            logger.error(f"Error saving scene: {e}")
            self.error_occurred.emit(f"Failed to save scene: {str(e)}")

    def _on_load_scene(self):
        """Handle load scene request from toolbar"""
        try:
            # Use the existing load_scene method
            success = self.load_scene()
            if success:
                self.operation_completed.emit("load", "Scene loaded successfully")
            else:
                self.error_occurred.emit("Failed to load scene")
        except Exception as e:
            logger.error(f"Error loading scene: {e}")
            self.error_occurred.emit(f"Failed to load scene: {str(e)}")

    def _on_zoom_fit(self):
        """Handle zoom fit request from toolbar"""
        try:
            if self.view:
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        except Exception as e:
            logger.error(f"Error zooming to fit: {e}")

    def _connect_signals(self):
        """Connect to model signals"""
        self.data_model.component_added.connect(self._on_model_component_added)
        self.data_model.component_removed.connect(
            self._on_model_component_removed)
        self.data_model.connection_added.connect(
            self._on_model_connection_added)
        self.data_model.connection_removed.connect(
            self._on_model_connection_removed)
        
        # Connect to scene signals for new wires
        if self.scene:
            self.scene.wire_added.connect(self._on_scene_wire_added)
            self.scene.wire_removed.connect(self._on_scene_wire_removed)

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

                # Clean up any wires connected to this component
                if hasattr(graphics_item.graphics_item, 'connected_wires'):
                    for wire in list(
                            graphics_item.graphics_item.connected_wires):
                        try:
                            self.scene.removeItem(wire)
                            if hasattr(
                                    self.scene,
                                    'wires') and wire in self.scene.wires:
                                self.scene.wires.remove(wire)
                            # Remove wire from other connected component
                            if hasattr(
                                    wire, 'start_pin') and wire.start_pin and hasattr(
                                    wire.start_pin, 'parent_component'):
                                other_component = wire.start_pin.parent_component
                                if other_component != graphics_item.graphics_item and hasattr(
                                        other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                            if hasattr(
                                    wire, 'end_pin') and wire.end_pin and hasattr(
                                    wire.end_pin, 'parent_component'):
                                other_component = wire.end_pin.parent_component
                                if other_component != graphics_item.graphics_item and hasattr(
                                        other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                        except Exception as e:
                            logger.warning(
                                f"Error cleaning up wire during component removal: {e}")

                self.scene.removeItem(graphics_item.graphics_item)
                if graphics_item.graphics_item in self.scene.components:
                    self.scene.components.remove(graphics_item.graphics_item)

                del self._component_graphics_items[component_id]
        except Exception as e:
            logger.error(f"Error handling model component removed: {e}")

    def _on_model_connection_added(self, connection_id: str):
        """Handle connection added to model"""
        try:
            connection_data = self.data_model.get_connection(connection_id)
            if connection_data:
                self._create_graphics_connection(
                    connection_id, connection_data)
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

    def cleanup(self):
        """Clean up resources and stop timers"""
        try:
            if hasattr(self, 'cleanup_timer'):
                self.cleanup_timer.stop()
                self.cleanup_timer.deleteLater()
            logger.info("VisualBCFController cleanup completed")
        except Exception as e:
            logger.error(f"Error during controller cleanup: {e}")

    def _cleanup_stale_graphics_items(self):
        """Clean up stale graphics items that are no longer valid"""
        try:
            stale_component_ids = []
            stale_connection_ids = []

            # Check component graphics items
            for component_id, wrapper in list(
                    self._component_graphics_items.items()):
                try:
                    if (not wrapper or
                        not wrapper.graphics_item or
                            not hasattr(wrapper.graphics_item, 'pos')):
                        stale_component_ids.append(component_id)
                except Exception:
                    stale_component_ids.append(component_id)

            # Check connection graphics items
            for connection_id, wrapper in list(
                    self._connection_graphics_items.items()):
                try:
                    if (not wrapper or
                        not wrapper.graphics_item or
                            not hasattr(wrapper.graphics_item, 'line')):
                        stale_connection_ids.append(connection_id)
                except Exception:
                    stale_connection_ids.append(connection_id)

            # Remove stale items
            for component_id in stale_component_ids:
                del self._component_graphics_items[component_id]

            for connection_id in stale_connection_ids:
                del self._connection_graphics_items[connection_id]

            if stale_component_ids or stale_connection_ids:
                logger.info(
                    f"Cleaned up {
                        len(stale_component_ids)} stale component items and {
                        len(stale_connection_ids)} stale connection items")

        except Exception as e:
            logger.error(f"Error during graphics items cleanup: {e}")

    def on_graphics_component_moved(self, graphics_component):
        """Handle graphics component movement and sync to model"""
        try:
            # Validate the graphics component
            if not graphics_component:
                return

            # Check if the graphics component is still valid
            try:
                pos = graphics_component.pos()
                if not hasattr(pos, 'x') or not hasattr(pos, 'y'):
                    return
            except Exception:
                return

            # Find the component ID for this graphics item
            component_id = None
            for cid, wrapper in self._component_graphics_items.items():
                try:
                    if (wrapper and wrapper.graphics_item and
                            wrapper.graphics_item == graphics_component):
                        component_id = cid
                        break
                except Exception:
                    continue

            if component_id:
                try:
                    pos = graphics_component.pos()
                    new_position = (pos.x(), pos.y())
                    success = self.data_model.update_component_position(
                        component_id, new_position)
                    if success:
                        logger.debug(
                            f"Successfully synced position for component {component_id}: {new_position}")
                except Exception as e:
                    logger.error(
                        f"Error updating model position for component {component_id}: {e}")

        except Exception as e:
            logger.error(f"Error syncing graphics position to model: {e}")

    # Public methods for component operations

    def add_component(self,
                      name: str,
                      component_type: str,
                      position: Tuple[float,
                                      float],
                      properties: Dict[str,
                                       Any] = None) -> str:
        """Add a new component"""
        try:
            component_id = self.data_model.add_component(
                name, component_type, position, properties)
            if component_id:
                self.operation_completed.emit(
                    "add_component", f"Added component: {name}")
                logger.info(
                    f"Successfully added component: {name} at {position}")
            return component_id
        except Exception as e:
            logger.error(f"Error adding component: {e}")
            self.error_occurred.emit(f"Failed to add component: {str(e)}")
            return ""

    def remove_component(
            self,
            component_id: str,
            emit_user_signal: bool = False) -> bool:
        """Remove a component"""
        try:
            component_data = self.data_model.get_component(component_id)
            if not component_data:
                return False

            component_name = component_data.name
            success = self.data_model.remove_component(component_id)
            if success:
                self.operation_completed.emit(
                    "remove_component", f"Removed component: {component_name}")
                logger.info(
                    f"Successfully removed component: {component_name}")
            return success
        except Exception as e:
            logger.error(f"Error removing component: {e}")
            self.error_occurred.emit(f"Failed to remove component: {str(e)}")
            return False

    def update_component_position(
            self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position"""
        try:
            return self.data_model.update_component_position(
                component_id, position)
        except Exception as e:
            logger.error(f"Error updating component position: {e}")
            return False

    def add_connection(self, from_component_id: str, from_pin_id: str,
                       to_component_id: str, to_pin_id: str) -> str:
        """Add a new connection"""
        try:
            connection_id = self.data_model.add_connection(
                from_component_id, from_pin_id, to_component_id, to_pin_id
            )
            if connection_id:
                self.operation_completed.emit(
                    "add_connection", f"Added connection")
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
                self.operation_completed.emit(
                    "remove_connection", f"Removed connection")
                logger.info(
                    f"Successfully removed connection: {connection_id}")
            return success
        except Exception as e:
            logger.error(f"Error removing connection: {e}")
            self.error_occurred.emit(f"Failed to remove connection: {str(e)}")
            return False

    def clear_scene(self, show_confirmation: bool = False):
        """Clear the entire scene"""
        try:
            # Clear all data from model
            self.data_model.clear_all_data()

            # Clear graphics items
            self._clear_graphics_items()

            self.operation_completed.emit("clear", "Scene cleared")
            logger.info("Scene cleared successfully")

        except Exception as e:
            logger.error(f"Error clearing scene: {e}")
            self.error_occurred.emit(f"Failed to clear scene: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current scene statistics"""
        try:
            components = self.data_model.get_all_components()
            connections = self.data_model.get_all_connections()

            return {
                'component_count': len(components),
                'connection_count': len(connections),
                'graphics_components_count': len(
                    self._component_graphics_items),
                'graphics_connections_count': len(
                    self._connection_graphics_items)}
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'component_count': 0,
                'connection_count': 0,
                'graphics_components_count': 0,
                'graphics_connections_count': 0,
                'error': str(e)
            }

    def save_scene(self, file_path: str = None) -> bool:
        """Save current scene via data model"""
        try:
            # First, ensure all current graphics state is synced to the data model
            self._sync_graphics_to_model()
            
            stats = self.get_statistics()
            component_count = stats.get('component_count', 0)
            connection_count = stats.get('connection_count', 0)

            success = self.data_model.save_visual_bcf_to_file(
                file_path) if file_path else self.data_model.save_visual_bcf_data()

            if success:
                message = f"Scene saved with {component_count} components and {connection_count} connections"
                self.operation_completed.emit("save_scene", message)
                return True
            else:
                error_msg = "Failed to save scene through data model"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
        except Exception as e:
            error_msg = f"Failed to save scene: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def load_scene(self, file_path: str = None) -> bool:
        """Load scene from JSON file or database"""
        try:
            scene_data = None

            if file_path:
                # Load from specific file path
                import json
                with open(file_path, 'r') as f:
                    raw_data = json.load(f)
                logger.info(f"Scene loaded from file: {file_path}")

                # Extract scene data from RDB JSON structure
                if "config" in raw_data and "visual_bcf" in raw_data["config"]:
                    visual_bcf_data = raw_data["config"]["visual_bcf"]
                    tables_components = visual_bcf_data.get("components", [])
                    tables_connections = visual_bcf_data.get("connections", [])

                    # Reconstruct scene from normalized tables
                    id_to_name = {}
                    components_list = []
                    for comp in tables_components:
                        name = comp.get("name", "")
                        comp_id = comp.get("id", name)
                        id_to_name[comp_id] = name
                        pos = comp.get(
                            "visual_properties", {}).get(
                            "position", {
                                "x": 0, "y": 0})
                        components_list.append({
                            "id": comp_id,
                            "name": name,
                            "type": comp.get("component_type", "chip"),
                            "position": {"x": pos.get("x", 0), "y": pos.get("y", 0)},
                            "properties": comp.get("properties", {}),
                            "visual_properties": comp.get("visual_properties", {})
                        })

                    connections_list = []
                    for conn in tables_connections:
                        connections_list.append(
                            {
                                "id": conn.get(
                                    "id", ""), "start_component": id_to_name.get(
                                    conn.get(
                                        "from_component_id", ""), ""), "end_component": id_to_name.get(
                                    conn.get(
                                        "to_component_id", ""), ""), "start_pin": conn.get(
                                    "from_pin_id", ""), "end_pin": conn.get(
                                    "to_pin_id", ""), "properties": conn.get(
                                        "properties", {}), "visual_properties": conn.get(
                                            "visual_properties", {})})

                    scene_data = {
                        "components": components_list,
                        "connections": connections_list
                    }
            else:
                # Load from default scene location through model
                scene_data = self.data_model.load_scene_data()
                if scene_data:
                    logger.info(
                        "Scene loaded from default location through model")
                else:
                    logger.info("No default scene found in model")
                    return False

            if scene_data:
                # Clear current model data
                self.data_model.clear_all_data()

                # Load components into the model first
                components_data = scene_data.get("components", [])
                logger.info(f"Found {len(components_data)} components to load")

                for comp_data in components_data:
                    component_id = self.data_model.add_component(
                        name=comp_data.get("name", ""),
                        component_type=comp_data.get("type", "chip"),
                        position=(comp_data.get("position", {}).get("x", 0),
                                  comp_data.get("position", {}).get("y", 0)),
                        properties=comp_data.get("properties", {})
                    )

                # Load connections into the model
                connections_data = scene_data.get("connections", [])
                logger.info(
                    f"Found {
                        len(connections_data)} connections to load")

                for conn_data in connections_data:
                    # Find component IDs by name
                    start_comp = self.data_model.get_component_by_name(
                        conn_data.get("start_component", ""))
                    end_comp = self.data_model.get_component_by_name(
                        conn_data.get("end_component", ""))

                    if start_comp and end_comp:
                        self.data_model.add_connection(
                            from_component_id=start_comp.id,
                            from_pin_id=conn_data.get("start_pin", ""),
                            to_component_id=end_comp.id,
                            to_pin_id=conn_data.get("end_pin", "")
                        )

                # Clear any existing graphics items to prevent conflicts
                self._clear_graphics_items()

                # Create graphics items through the controller to ensure proper
                # tracking
                components = self.data_model.get_all_components()
                for component_id, component_data in components.items():
                    self._create_graphics_component(
                        component_id, component_data)

                connections = self.data_model.get_all_connections()
                for connection_id, connection_data in connections.items():
                    self._create_graphics_connection(
                        connection_id, connection_data)

                # Get final statistics
                stats = self.get_statistics()
                component_count = stats.get('component_count', 0)
                connection_count = stats.get('connection_count', 0)

                # Clean up any stale graphics items to prevent C++ object
                # deletion errors
                self._cleanup_stale_graphics_items()

                self.operation_completed.emit(
                    "load_scene",
                    f"Scene loaded: {component_count} components, {connection_count} connections")
                logger.info(
                    f"Successfully loaded {component_count} components and {connection_count} connections")
                return True
            else:
                logger.warning("No scene data to load")
                return False

        except Exception as e:
            error_msg = f"Failed to load scene: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def export_scene(self, file_path: str) -> bool:
        """Export current scene to external JSON file"""
        return self.save_scene(file_path)

    def import_scene(self, file_path: str) -> bool:
        """Import scene from external JSON file"""
        return self.load_scene(file_path)

    # Private helper methods

    def _sync_graphics_to_model(self):
        """Sync current graphics state to the data model before saving"""
        try:
            logger.info(f"Starting graphics-to-model sync. Found {len(self._component_graphics_items)} components and {len(self._connection_graphics_items)} connections")
            
            # Sync component positions
            for component_id, wrapper in self._component_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    try:
                        pos = wrapper.graphics_item.pos()
                        self.data_model.update_component_position(component_id, (pos.x(), pos.y()))
                    except Exception as e:
                        logger.warning(f"Error syncing position for component {component_id}: {e}")
            
            # Sync connections - ensure all visible connections are in the data model
            connections_synced = 0
            for connection_id, wrapper in self._connection_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    try:
                        wire = wrapper.graphics_item
                        logger.info(f"Processing connection {connection_id}: wire={wire}, start_pin={getattr(wire, 'start_pin', None)}, end_pin={getattr(wire, 'end_pin', None)}")
                        
                        if hasattr(wire, 'start_pin') and hasattr(wire, 'end_pin') and wire.start_pin and wire.end_pin:
                            # Check if this connection exists in the data model
                            connection_data = self.data_model.get_connection(connection_id)
                            logger.info(f"Connection {connection_id} in data model: {connection_data is not None}")
                            
                            if not connection_data:
                                # Create the connection in the data model if it doesn't exist
                                start_comp_id = None
                                end_comp_id = None
                                
                                # Find component IDs for the pins
                                for cid, comp_wrapper in self._component_graphics_items.items():
                                    if comp_wrapper.graphics_item == wire.start_pin.parent_component:
                                        start_comp_id = cid
                                        logger.info(f"Found start component ID: {start_comp_id} for pin {wire.start_pin.pin_id}")
                                    if comp_wrapper.graphics_item == wire.end_pin.parent_component:
                                        end_comp_id = cid
                                        logger.info(f"Found end component ID: {end_comp_id} for pin {wire.end_pin.pin_id}")
                                
                                if start_comp_id and end_comp_id:
                                    logger.info(f"Adding connection to data model: {start_comp_id}:{wire.start_pin.pin_id} -> {end_comp_id}:{wire.end_pin.pin_id}")
                                    result = self.data_model.add_connection(
                                        start_comp_id, wire.start_pin.pin_id,
                                        end_comp_id, wire.end_pin.pin_id
                                    )
                                    if result:
                                        connections_synced += 1
                                        logger.info(f"Successfully added connection {result} to data model")
                                    else:
                                        logger.warning(f"Failed to add connection to data model")
                                else:
                                    logger.warning(f"Could not find component IDs: start={start_comp_id}, end={end_comp_id}")
                            else:
                                logger.info(f"Connection {connection_id} already exists in data model")
                        else:
                            logger.warning(f"Wire {connection_id} missing pins: start_pin={getattr(wire, 'start_pin', None)}, end_pin={getattr(wire, 'end_pin', None)}")
                    except Exception as e:
                        logger.warning(f"Error syncing connection {connection_id}: {e}")
                        logger.exception("Full traceback:")
            
            logger.info(f"Graphics state synced to data model. Synced {connections_synced} new connections")
        except Exception as e:
            logger.error(f"Error syncing graphics to model: {e}")
            logger.exception("Full traceback:")

    def _clear_graphics_items(self):
        """Clear all graphics items from the scene and tracking dictionaries"""
        try:
            # Remove all graphics items from the scene
            for component_id, wrapper in list(
                    self._component_graphics_items.items()):
                try:
                    if wrapper and wrapper.graphics_item:
                        self.scene.removeItem(wrapper.graphics_item)
                except Exception as e:
                    logger.warning(
                        f"Error removing component graphics item {component_id}: {e}")

            for connection_id, wrapper in list(
                    self._connection_graphics_items.items()):
                try:
                    if wrapper and wrapper.graphics_item:
                        self.scene.removeItem(wrapper.graphics_item)
                except Exception as e:
                    logger.warning(
                        f"Error removing connection graphics item {connection_id}: {e}")

            # Clear the tracking dictionaries
            self._component_graphics_items.clear()
            self._connection_graphics_items.clear()

            # Clear scene's component and wire lists
            if hasattr(self.scene, 'components'):
                self.scene.components.clear()
            if hasattr(self.scene, 'wires'):
                self.scene.wires.clear()

            logger.info(
                "Cleared all graphics items from scene and tracking dictionaries")

        except Exception as e:
            logger.error(f"Error clearing graphics items: {e}")

    def _create_graphics_component(
            self,
            component_id: str,
            component_data: ComponentData):
        """Create graphics item for component"""
        try:
            # Create the actual graphics component
            graphics_component = ComponentWithPins(
                name=component_data.name,
                component_type=component_data.component_type,
                width=component_data.visual_properties.get(
                    'size',
                    {}).get(
                    'width',
                    100),
                height=component_data.visual_properties.get(
                    'size',
                    {}).get(
                    'height',
                    60))

            # Set position from component data
            pos = component_data.visual_properties['position']
            graphics_component.setPos(pos['x'], pos['y'])

            # Add to scene
            self.scene.addItem(graphics_component)

            # Also add to scene's component list for serialization
            if graphics_component not in self.scene.components:
                self.scene.components.append(graphics_component)

            # Create wrapper and store
            graphics_item = ComponentGraphicsItem(
                component_id, graphics_component)
            self._component_graphics_items[component_id] = graphics_item

            logger.info(
                f"Created graphics item for component: {
                    component_data.name} (type: {
                    component_data.component_type})")

        except Exception as e:
            logger.error(f"Error creating graphics component: {e}")
            logger.exception("Full traceback:")

    def _create_graphics_connection(
            self,
            connection_id: str,
            connection_data: ConnectionData):
        """Create graphics item for connection"""
        try:
            # Find the source and target components
            from_graphics = self._component_graphics_items.get(
                connection_data.from_component_id)
            to_graphics = self._component_graphics_items.get(
                connection_data.to_component_id)

            if from_graphics and to_graphics:
                try:
                    def _find_pin_by_id(graphics_item, pin_id):
                        """Find pin by its specific ID instead of edge preference"""
                        if hasattr(
                                graphics_item,
                                'pins') and graphics_item.pins:
                            for pin in graphics_item.pins:
                                if hasattr(
                                        pin, 'pin_id') and pin.pin_id == pin_id:
                                    return pin
                        return None

                    # Use the actual pin IDs from the connection data
                    start_pin = _find_pin_by_id(
                        from_graphics.graphics_item, connection_data.from_pin_id)
                    end_pin = _find_pin_by_id(
                        to_graphics.graphics_item, connection_data.to_pin_id)

                    if start_pin is None or end_pin is None:
                        logger.warning(
                            f"Connection {connection_id}: Pin not found - from_pin_id: {
                                connection_data.from_pin_id}, to_pin_id: {
                                connection_data.to_pin_id}")
                        # Fallback to edge-based pin selection if specific pins
                        # not found

                        def _find_pin_by_edge(graphics_item, preferred_edges):
                            if hasattr(
                                    graphics_item,
                                    'pins') and graphics_item.pins:
                                for edge in preferred_edges:
                                    for pin in graphics_item.pins:
                                        if getattr(pin, 'edge', None) == edge:
                                            return pin
                                # Fallback to first pin
                                return graphics_item.pins[0]
                            return None

                        start_pin = _find_pin_by_edge(
                            from_graphics.graphics_item, ['right'])
                        end_pin = _find_pin_by_edge(
                            to_graphics.graphics_item, ['left'])

                        if start_pin is None or end_pin is None:
                            logger.info(
                                f"Connection {connection_id} exists but suitable pins not found for visual wire")
                            return

                    # Avoid duplicate wires for the same connection_id
                    if connection_id in self._connection_graphics_items:
                        return

                    connection_graphics = Wire(start_pin, scene=self.scene)
                    if connection_graphics.complete_wire(end_pin):
                        self.scene.addItem(connection_graphics)
                        if hasattr(
                                self.scene,
                                'wires') and connection_graphics not in self.scene.wires:
                            self.scene.wires.append(connection_graphics)

                        # Register wire with both connected components so they
                        # can update it when moved
                        start_component = start_pin.parent_component
                        end_component = end_pin.parent_component
                        if hasattr(start_component, 'add_wire'):
                            start_component.add_wire(connection_graphics)
                        if hasattr(end_component, 'add_wire'):
                            end_component.add_wire(connection_graphics)

                        connection_graphics_item = ConnectionGraphicsItem(
                            connection_id, connection_graphics)
                        self._connection_graphics_items[connection_id] = connection_graphics_item
                        logger.info(
                            f"Created graphics wire for connection: {connection_id}")
                    else:
                        logger.info(
                            f"Connection {connection_id} could not complete visual wire")
                except Exception as wire_error:
                    logger.warning(
                        f"Failed to create wire graphics for connection {connection_id}: {wire_error}")
                    logger.info(
                        f"Connection {connection_id} exists in data model but not visually displayed")
            else:
                logger.warning(
                    f"Cannot create graphics connection - missing component graphics: from={
                        connection_data.from_component_id}, to={
                        connection_data.to_component_id}")

        except Exception as e:
            logger.error(f"Error creating graphics connection: {e}")

    # Getter methods

    def get_view(self) -> CustomGraphicsView:
        """Get the graphics view"""
        return self.view

    def get_scene(self) -> ComponentScene:
        """Get the graphics scene"""
        return self.scene

    def get_toolbar(self) -> FloatingToolbar:
        """Get the floating toolbar"""
        return self.floating_toolbar

    def _on_scene_wire_added(self, start_component: str, start_pin: str, end_component: str, end_pin: str):
        """Handle new wire added to scene - add it to data model and tracking"""
        try:
            logger.info(f"Scene wire added: {start_component}.{start_pin} -> {end_component}.{end_pin}")
            
            # Find the component IDs by name
            start_comp_id = None
            end_comp_id = None
            
            for comp_id, comp_data in self.data_model.get_all_components().items():
                if comp_data.name == start_component:
                    start_comp_id = comp_id
                if comp_data.name == end_component:
                    end_comp_id = comp_id
                if start_comp_id and end_comp_id:
                    break
            
            if start_comp_id and end_comp_id:
                # Add connection to data model
                connection_id = self.data_model.add_connection(
                    start_comp_id, start_pin, end_comp_id, end_pin
                )
                
                if connection_id:
                    logger.info(f"Added new connection {connection_id} to data model")
                    
                    # Find the wire in the scene and add it to controller tracking
                    wire_found = False
                    for wire in self.scene.wires:
                        if (hasattr(wire, 'start_pin') and wire.start_pin and 
                            hasattr(wire, 'end_pin') and wire.end_pin):
                            
                            start_comp_name = wire.start_pin.parent_component.name
                            start_pin_id = wire.start_pin.pin_id
                            end_comp_name = wire.end_pin.parent_component.name
                            end_pin_id = wire.end_pin.pin_id
                            
                            if (start_comp_name == start_component and
                                start_pin_id == start_pin and
                                end_comp_name == end_component and
                                end_pin_id == end_pin):
                                
                                # Add to controller tracking
                                connection_graphics_item = ConnectionGraphicsItem(connection_id, wire)
                                self._connection_graphics_items[connection_id] = connection_graphics_item
                                
                                logger.info(f"Added wire to controller tracking: {connection_id}")
                                wire_found = True
                                break
                    
                    if not wire_found:
                        logger.warning(f"Could not find wire in scene.wires for connection: {start_component}.{start_pin} -> {end_component}.{end_pin}")
                        # Try to find any wire that might match (fallback)
                        for wire in self.scene.wires:
                            if (hasattr(wire, 'start_pin') and wire.start_pin and 
                                hasattr(wire, 'end_pin') and wire.end_pin):
                                logger.info(f"Fallback: Found wire {wire.start_pin.parent_component.name}.{wire.start_pin.pin_id} -> {wire.end_pin.parent_component.name}.{wire.end_pin.pin_id}")
                                # Add to controller tracking anyway
                                connection_graphics_item = ConnectionGraphicsItem(connection_id, wire)
                                self._connection_graphics_items[connection_id] = connection_graphics_item
                                logger.info(f"Added wire to controller tracking (fallback): {connection_id}")
                                break
                else:
                    logger.warning(f"Failed to add connection to data model")
            else:
                logger.warning(f"Could not find component IDs for wire: {start_component} -> {end_component}")
                
        except Exception as e:
            logger.error(f"Error handling scene wire added: {e}")
            logger.exception("Full traceback:")

    def _on_scene_wire_removed(self, start_component: str, start_pin: str, end_component: str, end_pin: str):
        """Handle wire removed from scene - remove it from data model and tracking"""
        try:
            logger.info(f"Scene wire removed: {start_component}.{start_pin} -> {end_component}.{end_pin}")
            
            # Find the connection ID in our tracking
            connection_id_to_remove = None
            for connection_id, wrapper in self._connection_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    wire = wrapper.graphics_item
                    if (hasattr(wire, 'start_pin') and wire.start_pin and 
                        hasattr(wire, 'end_pin') and wire.end_pin and
                        wire.start_pin.parent_component.name == start_component and
                        wire.start_pin.pin_id == start_pin and
                        wire.end_pin.parent_component.name == end_component and
                        wire.end_pin.pin_id == end_pin):
                        connection_id_to_remove = connection_id
                        break
            
            if connection_id_to_remove:
                # Remove from controller tracking
                del self._connection_graphics_items[connection_id_to_remove]
                
                # Remove from data model
                success = self.data_model.remove_connection(connection_id_to_remove)
                if success:
                    logger.info(f"Removed connection {connection_id_to_remove} from data model")
                else:
                    logger.warning(f"Failed to remove connection {connection_id_to_remove} from data model")
            else:
                logger.warning(f"Could not find connection to remove: {start_component}.{start_pin} -> {end_component}.{end_pin}")
                
        except Exception as e:
            logger.error(f"Error handling scene wire removed: {e}")
            logger.exception("Full traceback:")
