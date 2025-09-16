"""
Visual BCF Controller - Refactored

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

import logging
import traceback
from typing import Dict, List, Any, Tuple, Optional

from PySide6.QtCore import QObject, Signal, QTimer, Qt, QPoint
from PySide6.QtWidgets import QWidget, QGraphicsTextItem, QMessageBox

from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, Wire, ComponentPin
from apps.RBM5.BCF.gui.source.visual_bcf.floating_toolbar import FloatingToolbar

logger = logging.getLogger(__name__)


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
    data_synchronized = Signal() # Signal to notify that data model is synchronized

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
        self._component_graphics_items: Dict[str, ComponentWithPins] = {}
        self._connection_graphics_items: Dict[str, Wire] = {}

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

        logger.info("VisualBCFController initialized with own view and scene")

    def _setup_toolbar(self):
        """Create floating toolbar with component placement functionality"""
        self.floating_toolbar = FloatingToolbar(parent=self.parent_widget)
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
        x = (view_global_pos.x() +
             max(10, (view_rect.width() - actual_toolbar_size.width()) // 2))
        y = view_global_pos.y() + 10  # 10px from top of graphics view

        # Ensure the toolbar is within the parent's bounds
        x = max(0, min(x, self.parent_widget.width() - actual_toolbar_size.width()))
        y = max(0, min(y, self.parent_widget.height() - actual_toolbar_size.height()))

        self.floating_toolbar.move(x, y)

        # # Debug logging
        # logger.info(f"Positioned floating toolbar at ({x}, {y}) "
        #             f"relative to graphics view at {view_global_pos}")

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
                        self.remove_component(item)
                    elif isinstance(item, Wire):
                        # Find connection ID and remove
                        self.remove_connection(item)

                self.operation_completed.emit(
                    "delete", f"Deleted {len(selected_items)} selected items")
        except Exception as e:
            logger.error("Error deleting selected items: %s", e)
            self.error_occurred.emit(
                f"Failed to delete selected items: {str(e)}")

    def _on_clear_scene(self):
        """Handle clear scene request from toolbar"""
        try:
            success = self.clear_scene(show_confirmation=True)
            if success:
                self.operation_completed.emit("clear", "Scene cleared")
        except Exception as e:
            pass

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
        self.data_model.component_removed.connect(self._on_model_component_removed)
        self.data_model.connection_added.connect(self._on_model_connection_added)
        self.data_model.connection_removed.connect(self._on_model_connection_removed)

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
                component = self._component_graphics_items[component_id]

                # Clean up any wires connected to this component
                if hasattr(component, 'connected_wires'):
                    for wire in list(component.connected_wires):
                        try:
                            self.scene.removeItem(wire)
                            # Wire is already removed from scene graphics, no need to manage separate lists
                            # Remove wire from other connected component
                            if hasattr(wire, 'start_pin') and wire.start_pin and \
                                hasattr(wire.start_pin, 'parent_component'):
                                other_component = wire.start_pin.parent_component
                                if other_component != component and hasattr(other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                            if hasattr(wire, 'end_pin') and wire.end_pin and \
                                hasattr(wire.end_pin, 'parent_component'):
                                other_component = wire.end_pin.parent_component
                                if other_component != component and hasattr(other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                        except Exception as e:
                            logger.warning(
                                f"Error cleaning up wire during component removal: {e}")

                self.scene.removeItem(component)
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
                wire = self._connection_graphics_items[connection_id]
                self.scene.removeItem(wire)
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
                component_id = self._get_component_id(item)
                if component_id:
                    is_tracked = True

                # Check if it's a tracked connection
                if not is_tracked:
                    connection_id = self._get_connection_id(item)
                    if connection_id:
                        is_tracked = True

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

    def on_graphics_component_moved(self, component: ComponentWithPins):
        """Handle graphics component movement and sync to model"""
        try:
            pos = component.pos()
            component_id = self._get_component_id(component)
            if not component_id:
                logger.warning("Could not find component ID for moved component: %s", component.name)
                return

            new_position = (pos.x(), pos.y())
            success = self.data_model.update_component_position(component_id, new_position)
            if success:
                logger.debug(f"Successfully synced position for component {component_id}: {new_position}")
            else:
                logger.error(f"Error updating model position for component {component_id}: {new_position}")
        except Exception as e:
            logger.error("Error syncing graphics position to model: %s", e)

    def add_component(self,
                      component: ComponentWithPins,
                      component_type: str,
                      position: Tuple[float,float]) -> str:
        """Add a new component"""
        try:
            logger.info(f"BCF Controller: Adding component: {component.name} ({component_type}) at {position}")
            name = component.name
            properties = getattr(component, 'properties', {})
            component_id = self.data_model.add_component(
                name, component_type, position, properties)
            if component_id:
                self._component_graphics_items[component_id] = component
                self.operation_completed.emit(
                    "add_component", f"Added component: {name}")
                logger.info(
                    f"Successfully added component: {name} at {position}")
            return component_id
        except Exception as e:
            logger.error("BCF Controller: Error adding component: %s", e)
            self.error_occurred.emit(f"Failed to add component: {str(e)}")
            return ""

    def track_loaded_component(self, component: ComponentWithPins, component_id: str):
        """Track a component that was loaded from existing data (don't add to data model)"""
        try:
            # Just track the component in our graphics items mapping
            # Don't call data_model.add_component to avoid infinite loops
            self._component_graphics_items[component_id] = component
            # logger.info(f"Tracking loaded component: {component.name} with ID: {component_id}")
        except Exception as e:
            logger.error("Error tracking loaded component: %s", e)

    def remove_component(self, component: ComponentWithPins, emit_user_signal: bool = False) -> bool:
        """Remove a component that was deleted from the scene"""
        try:
            component_id = self._get_component_id(component)
            if not component_id:
                logger.warning("Could not find component ID for deleted component: %s", component.name)
                return False

            component_data = self.data_model.get_component(component_id)
            if not component_data:
                return False

            component_name = component_data.get('name', 'Unknown')
            success = self.data_model.remove_component(component_id)
            if success:
                # Remove from graphics tracking
                if component_id in self._component_graphics_items:
                    component = self._component_graphics_items[component_id]
                    if component:
                        # Remove from scene
                        self.scene.removeItem(component)
                    del self._component_graphics_items[component_id]

                # Remove any connections to this component
                connections_to_remove = []
                for conn_id, wire in self._connection_graphics_items.items():
                    if wire:
                        if (hasattr(wire, 'start_pin') and wire.start_pin and
                            hasattr(wire.start_pin, 'parent_component') and
                            wire.start_pin.parent_component == component):
                            connections_to_remove.append(conn_id)
                        elif (hasattr(wire, 'end_pin') and wire.end_pin and
                              hasattr(wire.end_pin, 'parent_component') and
                              wire.end_pin.parent_component == component):
                            connections_to_remove.append(conn_id)

                # Remove connections
                for conn_id in connections_to_remove:
                    self.remove_connection(wire)
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

    def add_connection(self, wire: Wire) -> str:
        """Add a new connection"""
        try:
            # Get component IDs, not names
            from_component_id = self._get_component_id(wire.start_pin.parent_component)
            from_pin_id = wire.start_pin.pin_id
            to_component_id = self._get_component_id(wire.end_pin.parent_component)
            to_pin_id = wire.end_pin.pin_id

            if not from_component_id or not to_component_id:
                logger.error("Could not find component IDs for connection")
                return ""

            connection_id = self.data_model.add_connection(
                from_component_id, from_pin_id, to_component_id, to_pin_id
            )
            print(f"BCF Controller: Connection ID: {connection_id}")
            if connection_id:
                self.operation_completed.emit(
                    "add_connection", f"Added connection")
                logger.info("Successfully added connection: %s", connection_id)
            return connection_id
        except Exception as e:
            logger.error("Error adding connection: %s", e)
            self.error_occurred.emit(f"Failed to add connection: {str(e)}")
            return ""

    def remove_connection(self, wire: Wire) -> bool:
        """Remove a connection that was deleted from the scene"""
        try:
            connection_id = self._get_connection_id(wire)
            if not connection_id:
                logger.warning("Could not find connection ID for deleted wire")
                return False

            success = self.data_model.remove_connection(connection_id)
            if success:
                self._connection_graphics_items.pop(connection_id)
                self.operation_completed.emit("remove_connection", f"Removed connection")
                logger.info(f"Successfully removed connection: {connection_id}")

            return success
        except Exception as e:
            logger.error("Error removing connection: %s", e)
            print(traceback.format_exc())
            self.error_occurred.emit(f"Failed to remove connection: {str(e)}")
            return False

    def clear_scene(self, show_confirmation: bool = False):
        """Clear the entire scene"""
        try:
            if show_confirmation:
                confirmation = QMessageBox.question(
                    self.parent_widget,
                    "Clear Scene",
                    "Are you sure you want to clear the scene?",
                    QMessageBox.Yes | QMessageBox.No)

                if confirmation == QMessageBox.No:
                    return False

            # Clear all data from model
            self.data_model.clear_all_data()

            # Clear graphics items
            self._clear_graphics_items()

            self.operation_completed.emit("clear", "Scene cleared")
            logger.info("Scene cleared successfully")

        except Exception as e:
            logger.error("Error clearing scene: %s", e)
            self.error_occurred.emit(f"Failed to clear scene: {str(e)}")
            raise e
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get current scene statistics"""
        try:
            components = self.data_model.components
            connections = self.data_model.connections

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

    # Private helper methods
    def _get_component_id(self, component: ComponentWithPins| str) -> Optional[str]:
        """Get component ID by name"""
        if isinstance(component, str):
            for component_id, component_item in self._component_graphics_items.items():
                if component_item.name == component:
                    return component_id
            return None

        for component_id, component_item in self._component_graphics_items.items():
            if component_item == component:
                return component_id
        return None

    def _get_connection_id(self, wire: Wire) -> Optional[str]:
        """Get connection ID by wire"""
        for connection_id, wire_item in self._connection_graphics_items.items():
            if wire_item == wire:
                return connection_id
        return None

    def _load_components(self):
        """Load components from the data model"""
        for comp_data in self.data_model.components:
            try:
                # Get component ID from the loaded data
                component_id = comp_data.get("id")
                component_name = comp_data.get("name", "Unknown")
                component_type = comp_data.get("component_type", "chip")

                if not component_id:
                    logger.warning("Component missing ID: %s", component_name)
                    continue

                # Get component configuration for pin information
                component_config = self.data_model.component_dcf(component_name)
                
                # Create the component graphics item with configuration
                component = ComponentWithPins(
                    component_name, 
                    component_type,
                    component_config=component_config
                )

                # Set position
                pos = self.data_model.visual_properties(component_id).get("position")
                component.setPos(pos.get("x", 0), pos.get("y", 0))

                # Add to scene
                self.scene.addItem(component)

                # Track the graphics item in the controller
                self._component_graphics_items[component_id] = component

                # Set component properties - DON'T re-add to data model to avoid infinite loop
                component.component_id = component_id
                component.properties = comp_data.get("properties", {})

                # Use track_loaded_component instead of add_component to avoid infinite loops
                self.track_loaded_component(component, component_id)

                # logger.info("Component %s (%s) added to scene", component_id, component_name)

            except Exception as e:
                logger.error("Error loading component %s: %s", comp_data.get('name', 'Unknown'), e)

    def _load_connections(self):
        """Load connections from the data model"""
        for conn_data in self.data_model.connections:
            try:
                # Get connection ID from the loaded data
                connection_id = conn_data.get("id")

                if not connection_id:
                    logger.warning("Connection missing ID: %s", conn_data)
                    continue

                # Get component IDs and pin IDs
                from_component_id = conn_data.get("source_device")
                to_component_id = conn_data.get("dest_device")
                from_pin_id = conn_data.get("source_pin")
                to_pin_id = conn_data.get("dest_pin")

                if not all([from_component_id, to_component_id, from_pin_id, to_pin_id]):
                    logger.warning("Connection missing required data: %s", conn_data)
                    continue
                
                from_component_id = self._get_component_id(from_component_id)
                to_component_id = self._get_component_id(to_component_id)

                # Find the component graphics items
                from_comp = self._component_graphics_items.get(from_component_id)
                to_comp = self._component_graphics_items.get(to_component_id)


                if not from_comp or not to_comp:
                    logger.warning("Could not find component graphics for connection %s", connection_id)
                    continue

                # Find the pins on the components
                from_pin = None
                to_pin = None

                # Match pins by ID since we're now saving pin IDs consistently
                for pin in from_comp.pins:
                    if hasattr(pin, 'pin_id') and pin.pin_name == from_pin_id:
                        from_pin = pin
                        break

                for pin in to_comp.pins:
                    if hasattr(pin, 'pin_id') and pin.pin_name == to_pin_id:
                        to_pin = pin
                        break


                if not from_pin or not to_pin:
                    logger.warning("Could not find pins for connection %s (from_pin: %s, to_pin: %s)",
                                    connection_id, from_pin_id, to_pin_id)
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
                    from_comp.add_wire(wire)
                    to_comp.add_wire(wire)

                    # Track the graphics item in the controller
                    self._connection_graphics_items[connection_id] = wire

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

    def load_scene(self) -> bool:
        """Load scene from JSON file or database"""
        try:
            # Clear current graphics items to prevent conflicts
            self._clear_graphics_items()

            # Load components by creating graphics items in the scene
            logger.info("Found %s components to load", len(self.data_model.components))
            self._load_components()
            self._load_connections()

            # Get final statistics
            stats = self.get_statistics()
            component_count = stats.get('component_count', 0)
            connection_count = stats.get('connection_count', 0)

            # Update all wires to ensure they're properly positioned and visible
            for _, wire in self._connection_graphics_items.items():
                if wire:
                    wire.update_path()
                    wire.update()

            # Force scene and viewport updates
            self.scene.update()
            self.view.viewport().update()
            self.operation_completed.emit(
                "load_scene",
                f"Scene loaded: {component_count} components, {connection_count} connections")
            logger.info("Successfully loaded %s components and %s connections", component_count, connection_count)
            return True
        except Exception as e:
            error_msg = f"Failed to load scene: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def export_scene(self, file_path: str) -> bool:
        """Export current scene to external JSON file"""
        pass

    def import_scene(self, file_path: str) -> bool:
        """Import scene from external JSON file"""
        pass

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
