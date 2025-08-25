"""
Visual BCF Controller - Refactored

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

import logging
from typing import Dict, List, Any, Tuple

from PySide6.QtCore import QObject, Signal, QTimer, Qt, QPoint
from PySide6.QtWidgets import QWidget, QGraphicsTextItem

from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, Wire, ComponentPin
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
                    "delete", f"Deleted {len(selected_items)} selected items")
        except Exception as e:
            logger.error("Error deleting selected items: %s", e)
            self.error_occurred.emit(
                f"Failed to delete selected items: {str(e)}")

    def _on_clear_scene(self):
        """Handle clear scene request from toolbar"""
        try:
            self.clear_scene(show_confirmation=False)
            self.operation_completed.emit("clear", "Scene cleared")
        except Exception as e:
            logger.error("Error clearing scene: %s", e)
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
            logger.error("Error saving scene: %s", e)
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
            logger.error("Error loading scene: %s", e)
            self.error_occurred.emit(f"Failed to load scene: {str(e)}")

    def _on_zoom_fit(self):
        """Handle zoom fit request from toolbar"""
        try:
            if self.view:
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        except Exception as e:
            logger.error("Error zooming to fit: %s", e)

    def _connect_signals(self):
        """Connect to model signals"""
        self.data_model.component_added.connect(self._on_model_component_added)
        self.data_model.component_removed.connect(
            self._on_model_component_removed)
        self.data_model.connection_added.connect(
            self._on_model_connection_added)
        self.data_model.connection_removed.connect(
            self._on_model_connection_removed)
        
        # Connect scene signals
        self.scene.component_removed.connect(self.remove_component_from_scene)
        self.scene.wire_removed.connect(self.remove_wire_from_scene)
        
        # Note: Scene signals are now handled directly in the new methods:
        # - component_added -> add_component_from_scene()
        # - wire_added -> add_wire_from_scene()
        # - component_removed -> remove_component_from_scene()
        # - wire_removed -> remove_wire_from_scene()

    def _on_model_component_added(self, component_id: str):
        """Handle component added to model"""
        try:
            # Components are now created by the scene, not by the controller
            # The controller just tracks what's already in the scene
            logger.info("Component %s added to model - graphics already exist in scene", component_id)
        except Exception as e:
            logger.error("Error handling model component added: %s", e)

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
                            # Wire is already removed from scene graphics, no need to manage separate lists
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
                # Component is already removed from scene graphics, no need to manage separate lists

                del self._component_graphics_items[component_id]
        except Exception as e:
            logger.error("Error handling model component removed: %s", e)

    def _on_model_connection_added(self, connection_id: str):
        """Handle connection added to model"""
        try:
            # Connections are now created by the scene, not by the controller
            # The controller just tracks what's already in the scene
            logger.info("Connection %s added to model - graphics already exist in scene", connection_id)
        except Exception as e:
            logger.error("Error handling model connection added: %s", e)

    def _on_model_connection_removed(self, connection_id: str):
        """Handle connection removed from model"""
        try:
            if connection_id in self._connection_graphics_items:
                graphics_item = self._connection_graphics_items[connection_id]
                self.scene.removeItem(graphics_item.graphics_item)
                del self._connection_graphics_items[connection_id]
        except Exception as e:
            logger.error("Error handling model connection removed: %s", e)

    def cleanup(self):
        """Clean up resources and stop timers"""
        try:
            if hasattr(self, 'cleanup_timer'):
                self.cleanup_timer.stop()
                self.cleanup_timer.deleteLater()
            logger.info("VisualBCFController cleanup completed")
        except Exception as e:
            logger.error("Error during controller cleanup: %s", e)

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
                            not (hasattr(wrapper.graphics_item, 'line') or 
                                 hasattr(wrapper.graphics_item, 'wire_path'))):
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
                    f"Cleaned up {len(stale_component_ids)} stale component items and {len(stale_connection_ids)} stale connection items")

        except Exception as e:
            logger.error("Error during graphics items cleanup: %s", e)

    def _force_scene_refresh(self):
        """Force a complete scene refresh to ensure no leftover items"""
        try:
            # Get all items currently in the scene
            all_scene_items = list(self.scene.items())
            
            # Identify any items that shouldn't be there
            unexpected_items = []
            for item in all_scene_items:
                # Skip certain item types that are expected during normal operation
                if isinstance(item, (QGraphicsTextItem, ComponentPin)):
                    # These are UI elements that are part of components, don't remove them
                    continue
                
                # Check if this item is properly tracked
                is_tracked = False
                
                # Check if it's a tracked component
                for wrapper in self._component_graphics_items.values():
                    if wrapper and wrapper.graphics_item == item:
                        is_tracked = True
                        break
                
                # Check if it's a tracked connection
                if not is_tracked:
                    for wrapper in self._connection_graphics_items.values():
                        if wrapper and wrapper.graphics_item == item:
                            is_tracked = True
                            break
                
                # If item is not tracked, mark it for removal
                if not is_tracked:
                    unexpected_items.append(item)
            
            # Remove any unexpected items
            for item in unexpected_items:
                try:
                    self.scene.removeItem(item)
                    logger.info("Removed unexpected item during scene refresh: %s", type(item).__name__)
                except Exception as e:
                    logger.warning("Error removing unexpected item during scene refresh: %s", e)
            
            if unexpected_items:
                logger.info("Scene refresh completed: removed %s unexpected items", len(unexpected_items))
            
        except Exception as e:
            logger.error("Error during scene refresh: %s", e)

    def _track_wire_for_saving(self, wire):
        """Track a wire created through the scene for proper saving"""
        try:
            if not wire or not hasattr(wire, 'start_pin') or not hasattr(wire, 'end_pin'):
                logger.warning("Cannot track wire: missing pins")
                return
            
            # Find the component IDs from the data model by name
            start_comp_name = wire.start_pin.parent_component.name
            end_comp_name = wire.end_pin.parent_component.name
            start_pin_id = wire.start_pin.pin_id
            end_pin_id = wire.end_pin.pin_id
            
            start_comp_id = None
            end_comp_id = None
            
            # Find component IDs in the data model
            for comp_id, comp_data in self.data_model.get_all_components().items():
                if comp_data.get('name') == start_comp_name:
                    start_comp_id = comp_id
                if comp_data.get('name') == end_comp_name:
                    end_comp_id = comp_id
                if start_comp_id and end_comp_id:
                    break
            
            if not start_comp_id or not end_comp_id:
                logger.warning("Cannot track wire: component IDs not found for %s or %s", start_comp_name, end_comp_name)
                return
            
            # Add the connection to the data model to get a proper connection ID
            connection_id = self.data_model.add_connection(
                start_comp_id, start_pin_id, end_comp_id, end_pin_id
            )
            
            if not connection_id:
                logger.warning("Failed to add connection to data model for wire tracking")
                return
            
            # Create a wrapper for the wire using the data model's connection ID
            wire_wrapper = ConnectionGraphicsItem(connection_id, wire)
            
            # Add to tracking dictionary
            self._connection_graphics_items[connection_id] = wire_wrapper
            
            logger.info("Tracked wire for saving: %s (%s.%s -> %s.%s)", connection_id, start_comp_name, start_pin_id, end_comp_name, end_pin_id)
            
        except Exception as e:
            logger.error("Error tracking wire for saving: %s", e)

    def _track_component_for_saving(self, component, name, component_type):
        """Track a component created through the scene for proper saving"""
        try:
            if not component:
                logger.warning("Cannot track component: component is None")
                return
            
            # Add the component to the data model first to get the proper UUID
            position = (component.pos().x(), component.pos().y())
            properties = getattr(component, 'properties', {})
            component_id = self.data_model.add_component(name, component_type, position, properties)
            
            if not component_id:
                logger.warning("Failed to add component to data model: %s", name)
                return
            
            # Now update the component in the data model to include pin information
            if hasattr(component, 'pins') and component.pins:
                # Collect pin data
                pins_data = []
                for pin in component.pins:
                    if hasattr(pin, 'pin_id'):
                        pin_data = {
                            'pin_id': pin.pin_id,
                            'position': {
                                'x': pin.pos().x(),
                                'y': pin.pos().y()
                            },
                            'edge': getattr(pin, 'edge', 'unknown')
                        }
                        pins_data.append(pin_data)
                
                # Update the component with pin information
                if pins_data:
                    success = self.data_model.update_component_pins(component_id, pins_data)
                    if success:
                        logger.info("Updated component %s with %s pins", name, len(pins_data))
                    else:
                        logger.warning("Failed to update component %s with pins", name)
            
            # Create a wrapper for the component using the data model's UUID
            component_wrapper = ComponentGraphicsItem(component_id, component)
            
            # Add to tracking dictionary
            self._component_graphics_items[component_id] = component_wrapper
            
            logger.info("Tracked component for saving: %s (%s, %s)", component_id, name, component_type)
            
        except Exception as e:
            logger.error("Error tracking component for saving: %s", e)

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
            logger.error("Error syncing graphics position to model: %s", e)

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
            logger.error("Error adding component: %s", e)
            self.error_occurred.emit(f"Failed to add component: {str(e)}")
            return ""

    def remove_component_from_scene(self, component: ComponentWithPins) -> bool:
        """Remove a component that was deleted from the scene"""
        try:
            # Find the component ID by looking up the graphics item
            component_id = None
            for cid, wrapper in self._component_graphics_items.items():
                if wrapper and wrapper.graphics_item == component:
                    component_id = cid
                    break
            
            if component_id:
                return self.remove_component(component_id)
            else:
                logger.warning("Could not find component ID for deleted component: %s", component.name)
                return False
                
        except Exception as e:
            logger.error("Error removing component from scene: %s", e)
            return False

    def remove_wire_from_scene(self, wire: Wire) -> bool:
        """Remove a wire that was deleted from the scene"""
        try:
            # Find the connection ID by looking up the graphics item
            connection_id = None
            for cid, wrapper in self._connection_graphics_items.items():
                if wrapper and wrapper.graphics_item == wire:
                    connection_id = cid
                    break
            
            if connection_id:
                return self.remove_connection(connection_id)
            else:
                logger.warning("Could not find connection ID for deleted wire")
                return False
                
        except Exception as e:
            logger.error("Error removing wire from scene: %s", e)
            return False

    def remove_component(
            self,
            component_id: str,
            emit_user_signal: bool = False) -> bool:
        """Remove a component"""
        try:
            component_data = self.data_model.get_component(component_id)
            if not component_data:
                return False

            component_name = component_data.get('name', 'Unknown')
            success = self.data_model.remove_component(component_id)
            if success:
                # Remove from graphics tracking
                if component_id in self._component_graphics_items:
                    wrapper = self._component_graphics_items[component_id]
                    if wrapper and wrapper.graphics_item:
                        # Remove from scene
                        self.scene.removeItem(wrapper.graphics_item)
                    del self._component_graphics_items[component_id]
                
                # Remove any connections to this component
                connections_to_remove = []
                for conn_id, conn_wrapper in self._connection_graphics_items.items():
                    if conn_wrapper and conn_wrapper.graphics_item:
                        wire = conn_wrapper.graphics_item
                        if (hasattr(wire, 'start_pin') and wire.start_pin and 
                            hasattr(wire.start_pin, 'parent_component') and 
                            wire.start_pin.parent_component == wrapper.graphics_item):
                            connections_to_remove.append(conn_id)
                        elif (hasattr(wire, 'end_pin') and wire.end_pin and 
                              hasattr(wire.end_pin, 'parent_component') and 
                              wire.end_pin.parent_component == wrapper.graphics_item):
                            connections_to_remove.append(conn_id)
                
                # Remove connections
                for conn_id in connections_to_remove:
                    self.remove_connection(conn_id)
                    if conn_id in self._connection_graphics_items:
                        del self._connection_graphics_items[conn_id]
                
                self.operation_completed.emit(
                    "remove_component", f"Removed component: {component_name}")
                logger.info(
                    f"Successfully removed component: {component_name}")
            return success
        except Exception as e:
            logger.error("Error removing component: %s", e)
            self.error_occurred.emit(f"Failed to remove component: {str(e)}")
            return False

    def update_component_position(
            self, component_id: str, position: Tuple[float, float]) -> bool:
        """Update component position"""
        try:
            return self.data_model.update_component_position(
                component_id, position)
        except Exception as e:
            logger.error("Error updating component position: %s", e)
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
                logger.info("Successfully added connection: %s", connection_id)
            return connection_id
        except Exception as e:
            logger.error("Error adding connection: %s", e)
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
            logger.error("Error removing connection: %s", e)
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
            logger.error("Error clearing scene: %s", e)
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
            logger.error("Error getting statistics: %s", e)
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

            # First save the scene data to RDB tables so it can be loaded later
            scene_data = self.serialize_scene_data()
            if scene_data:
                self.data_model.save_scene_data(scene_data)
                logger.info("Scene data saved to RDB tables: %s components, %s connections", len(scene_data.get('components', [])), len(scene_data.get('connections', [])))

            # Then save to file or persist to disk
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
                logger.info("Scene loaded from file: %s", file_path)

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
                print('calling load_scene')
                scene_data = self.data_model.load_scene_data()
                if scene_data:
                    logger.info("Scene loaded from default location through model")
                else:
                    logger.info("No default scene found in model")
                    return False

            if scene_data:
                # Clear current graphics items to prevent conflicts
                self._clear_graphics_items()
                
                # Load components by creating graphics items in the scene
                components_data = scene_data.get("components", [])
                logger.info("Found %s components to load", len(components_data))

                for comp_data in components_data:
                    try:
                        # Get component ID from the loaded data
                        component_id = comp_data.get("id")
                        component_name = comp_data.get("name", "Unknown")
                        component_type = comp_data.get("type", "chip")
                        
                        if not component_id:
                            logger.warning("Component missing ID: %s", component_name)
                            continue
                            
                        # Create the component graphics item directly (like the scene does)
                        component = ComponentWithPins(component_name, component_type)
                        
                        # Set position
                        pos = comp_data.get("position", {"x": 0, "y": 0})
                        component.setPos(pos.get("x", 0), pos.get("y", 0))
                        
                        # Add to scene
                        self.scene.addItem(component)
                        
                        # Track the graphics item in the controller
                        wrapper = ComponentGraphicsItem(component_id, component)
                        self._component_graphics_items[component_id] = wrapper
                        
                        # Set component properties
                        component.component_id = component_id
                        component.properties = comp_data.get("properties", {})
                        
                        logger.info("Component %s (%s) added to scene", component_id, component_name)
                            
                    except Exception as e:
                        logger.error("Error loading component %s: %s", comp_data.get('name', 'Unknown'), e)

                # Load connections by creating wire graphics items in the scene
                connections_data = scene_data.get("connections", [])
                logger.info("Found %s connections to load", len(connections_data))

                for conn_data in connections_data:
                    try:
                        # Get connection ID from the loaded data
                        connection_id = conn_data.get("id")
                        
                        if not connection_id:
                            logger.warning("Connection missing ID: %s", conn_data)
                            continue
                            
                        # Get component IDs and pin IDs
                        from_component_id = conn_data.get("from_component_id")
                        to_component_id = conn_data.get("to_component_id")
                        from_pin_id = conn_data.get("from_pin_id")
                        to_pin_id = conn_data.get("to_pin_id")
                        
                        if not all([from_component_id, to_component_id, from_pin_id, to_pin_id]):
                            logger.warning("Connection missing required data: %s", conn_data)
                            continue
                        
                        # Find the component graphics items
                        from_comp_wrapper = self._component_graphics_items.get(from_component_id)
                        to_comp_wrapper = self._component_graphics_items.get(to_component_id)
                        
                        if not from_comp_wrapper or not to_comp_wrapper:
                            logger.warning("Could not find component graphics for connection %s", connection_id)
                            continue
                        
                        # Find the pins on the components
                        from_pin = None
                        to_pin = None
                        
                        for pin in from_comp_wrapper.graphics_item.pins:
                            if pin.pin_id == from_pin_id:
                                from_pin = pin
                                break
                                
                        for pin in to_comp_wrapper.graphics_item.pins:
                            if pin.pin_id == to_pin_id:
                                to_pin = pin
                                break
                        
                        if not from_pin or not to_pin:
                            logger.warning("Could not find pins for connection %s", connection_id)
                            continue
                        
                        # Create the wire using the scene's wire creation logic
                        wire = Wire(from_pin, scene=self.scene)
                        if wire.complete_wire(to_pin):
                            # Force wire to recalculate its path and update graphics
                            wire.update_path()
                            wire.force_intersection_recalculation()
                            
                            # Add wire to scene
                            self.scene.addItem(wire)
                            
                            # Force wire to update its geometry
                            wire.update()
                            
                            # Register wire with both connected components
                            from_comp_wrapper.graphics_item.add_wire(wire)
                            to_comp_wrapper.graphics_item.add_wire(wire)
                            
                            # Track the graphics item in the controller
                            wrapper = ConnectionGraphicsItem(connection_id, wire)
                            self._connection_graphics_items[connection_id] = wrapper
                            
                            # Set wire properties
                            wire.connection_id = connection_id
                            wire.properties = conn_data.get("properties", {})
                            
                            # Force scene update for this wire and ensure it's visible
                            self.scene.update(wire.sceneBoundingRect())
                            
                            # Additional visibility fixes
                            wire.setVisible(True)
                            wire.show()
                            
                            logger.info("Connection %s added to scene", connection_id)
                        else:
                            logger.warning("Failed to complete wire for connection %s", connection_id)
                            
                    except Exception as e:
                        logger.error("Error loading connection %s: %s", connection_id, e)

                # Get final statistics
                stats = self.get_statistics()
                component_count = stats.get('component_count', 0)
                connection_count = stats.get('connection_count', 0)

                # Update all wires to ensure they're properly positioned and visible
                for connection_id, wrapper in self._connection_graphics_items.items():
                    if wrapper and wrapper.graphics_item:
                        wire = wrapper.graphics_item
                        wire.update_path()
                        wire.update()
                
                # Force scene and viewport updates
                self.scene.update()
                self.view.viewport().update()
                
                # Clean up any stale graphics items to prevent C++ object
                # deletion errors
                self._cleanup_stale_graphics_items()
                
                # Force a complete scene refresh to ensure no leftover items
                self._force_scene_refresh()

                self.operation_completed.emit(
                    "load_scene",
                    f"Scene loaded: {component_count} components, {connection_count} connections")
                logger.info("Successfully loaded %s components and %s connections", component_count, connection_count)
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
            logger.info("Starting graphics-to-model sync. Found %s components and %s connections", len(self._component_graphics_items), len(self._connection_graphics_items))
            
            # Sync component positions
            for component_id, wrapper in self._component_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    try:
                        pos = wrapper.graphics_item.pos()
                        self.data_model.update_component_position(component_id, (pos.x(), pos.y()))
                    except Exception as e:
                        logger.warning("Error syncing position for component %s: %s", component_id, e)
            
            # Sync connections - ensure all visible connections are in the data model
            connections_synced = 0
            # Create a copy of the items to avoid dictionary size change during iteration
            connection_items = list(self._connection_graphics_items.items())
            for connection_id, wrapper in connection_items:
                if wrapper and wrapper.graphics_item:
                    try:
                        wire = wrapper.graphics_item
                        logger.info("Processing connection %s: wire=%s, start_pin=%s, end_pin=%s", connection_id, wire, getattr(wire, 'start_pin', None), getattr(wire, 'end_pin', None))
                        
                        if hasattr(wire, 'start_pin') and hasattr(wire, 'end_pin') and wire.start_pin and wire.end_pin:
                            # Check if this connection exists in the data model
                            connection_data = self.data_model.get_connection(connection_id)
                            logger.info("Connection %s in data model: %s", connection_id, connection_data is not None)
                            
                            if not connection_data:
                                # Create the connection in the data model if it doesn't exist
                                start_comp_id = None
                                end_comp_id = None
                                
                                # Find component IDs for the pins
                                for cid, comp_wrapper in self._component_graphics_items.items():
                                    if comp_wrapper.graphics_item == wire.start_pin.parent_component:
                                        start_comp_id = cid
                                        logger.info("Found start component ID: %s for pin %s", start_comp_id, wire.start_pin.pin_id)
                                    if comp_wrapper.graphics_item == wire.end_pin.parent_component:
                                        end_comp_id = cid
                                        logger.info("Found end component ID: %s for pin %s", end_comp_id, wire.end_pin.pin_id)
                                
                                if start_comp_id and end_comp_id:
                                    logger.info("Adding connection to data model: %s:%s -> %s:%s", start_comp_id, wire.start_pin.pin_id, end_comp_id, wire.end_pin.pin_id)
                                    result = self.data_model.add_connection(
                                        start_comp_id, wire.start_pin.pin_id,
                                        end_comp_id, wire.end_pin.pin_id
                                    )
                                    if result:
                                        connections_synced += 1
                                        logger.info("Successfully added connection %s to data model", result)
                                    else:
                                        logger.warning("Failed to add connection to data model")
                                else:
                                    logger.warning("Could not find component IDs: start=%s, end=%s", start_comp_id, end_comp_id)
                            else:
                                logger.info("Connection %s already exists in data model", connection_id)
                        else:
                            logger.warning("Wire %s missing pins: start_pin=%s, end_pin=%s", connection_id, getattr(wire, 'start_pin', None), getattr(wire, 'end_pin', None))
                    except Exception as e:
                        logger.warning("Error syncing connection %s: %s", connection_id, e)
                        logger.exception("Full traceback:")
            
            logger.info("Graphics state synced to data model. Synced %s new connections", connections_synced)
        except Exception as e:
            logger.error("Error syncing graphics to model: %s", e)
            logger.exception("Full traceback:")

    def _clear_graphics_items(self):
        """Clear all graphics items from the scene and tracking dictionaries"""
        try:
            # First, clear all items from the scene using QGraphicsScene.clear()
            # This ensures all graphics items are properly removed
            self.scene.clear()
            
            # Clear the tracking dictionaries
            self._component_graphics_items.clear()
            self._connection_graphics_items.clear()

            # Scene is cleared by scene.clear(), no need to manage separate lists
            # Reset scene state
            if hasattr(self.scene, 'current_wire'):
                self.scene.current_wire = None

            logger.info(
                "Cleared all graphics items from scene and tracking dictionaries")

        except Exception as e:
            logger.error("Error clearing graphics items: %s", e)



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



    def add_component_from_scene(self, component: ComponentWithPins, name: str, component_type: str) -> str:
        """
        Add a component that was created in the scene to the data model and tracking.
        
        Args:
            component: The component graphics item
            name: Component name
            component_type: Component type
            
        Returns:
            str: Component ID from data model, or None if failed
        """
        try:
            logger.info("Adding component from scene: %s (%s)", name, component_type)
            
            # Get component position
            position = (component.pos().x(), component.pos().y())
            
            # Add to data model
            component_id = self.data_model.add_component(name, component_type, position, {})
            
            if not component_id:
                logger.error("Failed to add component %s to data model", name)
                return None
            
            # Add pins to data model if available
            if hasattr(component, 'pins') and component.pins:
                pins_data = []
                for pin in component.pins:
                    if hasattr(pin, 'pin_id'):
                        pin_data = {
                            'pin_id': pin.pin_id,
                            'position': {
                                'x': pin.pos().x(),
                                'y': pin.pos().y()
                            },
                            'edge': getattr(pin, 'edge', 'unknown')
                        }
                        pins_data.append(pin_data)
                
                if pins_data:
                    success = self.data_model.update_component_pins(component_id, pins_data)
                    if success:
                        logger.info("Updated component %s with %s pins", name, len(pins_data))
                    else:
                        logger.warning("Failed to update component %s with pins", name)
            
            # Track the graphics item
            component_wrapper = ComponentGraphicsItem(component_id, component)
            self._component_graphics_items[component_id] = component_wrapper
            
            # Update component name to match data model
            component.name = name
            component.component_id = component_id
            
            logger.info("Successfully added component from scene: %s (%s)", component_id, name)
            return component_id
            
        except Exception as e:
            logger.error("Error adding component from scene: %s", e)
            logger.exception("Full traceback:")
            return None

    def add_wire_from_scene(self, wire: Wire, start_component_name: str, start_pin_id: str, 
                           end_component_name: str, end_pin_id: str) -> str:
        """
        Add a wire that was created in the scene to the data model and tracking.
        
        Args:
            wire: The wire graphics item
            start_component_name: Name of start component
            start_pin_id: ID of start pin
            end_component_name: Name of end component
            end_pin_id: ID of end pin
            
        Returns:
            str: Connection ID from data model, or None if failed
        """
        try:
            logger.info("Adding wire from scene: %s.%s -> %s.%s", start_component_name, start_pin_id, end_component_name, end_pin_id)
            
            # Find component IDs in data model
            start_comp_id = None
            end_comp_id = None
            
            for comp_id, comp_data in self.data_model.get_all_components().items():
                if comp_data.get('name') == start_component_name:
                    start_comp_id = comp_id
                if comp_data.get('name') == end_component_name:
                    end_comp_id = comp_id
                if start_comp_id and end_comp_id:
                    break
            
            if not start_comp_id or not end_comp_id:
                logger.error("Could not find component IDs for wire: %s -> %s", start_component_name, end_component_name)
                return None
            
            # Add connection to data model
            connection_id = self.data_model.add_connection(
                start_comp_id, start_pin_id, end_comp_id, end_pin_id
            )
            
            if not connection_id:
                logger.error("Failed to add connection to data model")
                return None
            
            # Track the graphics item
            connection_wrapper = ConnectionGraphicsItem(connection_id, wire)
            self._connection_graphics_items[connection_id] = connection_wrapper
            
            # Update wire with connection ID
            wire.connection_id = connection_id
            
            logger.info("Successfully added wire from scene: %s", connection_id)
            return connection_id
            
        except Exception as e:
            logger.error("Error adding wire from scene: %s", e)
            logger.exception("Full traceback:")
            return None

    def serialize_scene_data(self) -> dict:
        """
        Serialize the current scene data from the controller's perspective.
        This provides a clean interface for the scene to get serialized data.
        
        Returns:
            dict: Scene data with components and connections
        """
        try:
            scene_data = {
                "components": [],
                "connections": []
            }
            
            # Serialize components from data model
            for component_id, wrapper in self._component_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    component = wrapper.graphics_item
                    component_data = {
                        "id": component_id,  # Include the actual component ID
                        "name": getattr(component, 'name', 'Unknown'),
                        "type": getattr(component, 'component_type', 'unknown'),
                        "position": {
                            "x": component.pos().x(),
                            "y": component.pos().y()
                        },
                        "properties": getattr(component, 'properties', {}),
                        "pins": []
                    }
                    
                    # Serialize pins if available
                    if hasattr(component, 'pins'):
                        for pin in component.pins:
                            if hasattr(pin, 'pin_id'):
                                pin_data = {
                                    "pin_id": pin.pin_id,
                                    "position": {
                                        "x": pin.pos().x(),
                                        "y": pin.pos().y()
                                    },
                                    "edge": getattr(pin, 'edge', 'unknown')
                                }
                                component_data["pins"].append(pin_data)
                    
                    scene_data["components"].append(component_data)
            
            # Serialize connections from data model
            for connection_id, wrapper in self._connection_graphics_items.items():
                if wrapper and wrapper.graphics_item:
                    wire = wrapper.graphics_item
                    if hasattr(wire, 'start_pin') and hasattr(wire, 'end_pin') and wire.start_pin and wire.end_pin:
                        # Find component IDs for the pins using a more reliable method
                        start_comp_id = None
                        end_comp_id = None
                        
                        # Method 1: Try to get component ID from the wire's connection_id if available
                        if hasattr(wire, 'connection_id') and wire.connection_id:
                            # Look up the connection in the data model to get component IDs
                            connection_data = self.data_model.get_connection(wire.connection_id)
                            if connection_data:
                                start_comp_id = connection_data.get('from_component_id')
                                end_comp_id = connection_data.get('to_component_id')
                                logger.info("Found component IDs from data model: %s -> %s", start_comp_id, end_comp_id)
                        
                        # Method 2: Fallback to graphics item lookup if Method 1 failed
                        if not start_comp_id or not end_comp_id:
                            for cid, comp_wrapper in self._component_graphics_items.items():
                                if comp_wrapper.graphics_item == wire.start_pin.parent_component:
                                    start_comp_id = cid
                                    logger.info("Found start component ID via graphics lookup: %s", start_comp_id)
                                if comp_wrapper.graphics_item == wire.end_pin.parent_component:
                                    end_comp_id = cid
                                    logger.info("Found end component ID via graphics lookup: %s", end_comp_id)
                        
                        if start_comp_id and end_comp_id:
                            connection_data = {
                                "id": connection_id,
                                "from_component_id": start_comp_id,  # Use component ID, not name
                                "from_pin_id": wire.start_pin.pin_id,
                                "to_component_id": end_comp_id,      # Use component ID, not name
                                "to_pin_id": wire.end_pin.pin_id,
                                "properties": getattr(wire, 'properties', {})
                            }
                            scene_data["connections"].append(connection_data)
                        else:
                            logger.warning("Could not find component IDs for connection %s", connection_id)
            
            logger.info("Serialized scene data: %s components, %s connections", len(scene_data['components']), len(scene_data['connections']))
            return scene_data
            
        except Exception as e:
            logger.error("Error serializing scene data: %s", e)
            logger.exception("Full traceback:")
            return {"components": [], "connections": []}