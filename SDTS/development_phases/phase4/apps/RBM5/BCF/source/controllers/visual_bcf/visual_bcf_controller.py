"""
Visual BCF Controller - Refactored

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

import logging
import traceback
from typing import Dict, List, Any, Tuple, Optional

from PySide6.QtCore import QObject, Signal, QTimer, Qt, QPoint, QEvent
from PySide6.QtWidgets import QWidget, QGraphicsTextItem, QMessageBox

from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView, MiniMapView
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
        # Guard to prevent selection feedback loops between scene and trees
        self._suppress_table_center = False

        # Component placement state
        self.placement_mode = False
        self.selected_component_type = "chip"
        self.selected_component_data = None

        # Create floating toolbar
        self.floating_toolbar = None
        self.minimap = None

        # Connect signals
        self._connect_signals()

        # Load existing data
        self.load_scene()

        # Setup toolbar after everything else is initialized
        self._setup_toolbar()
        self._setup_minimap()

        # Restore view scroll and zoom from persisted visual properties (if present)
        QTimer.singleShot(150, self._restore_view_state)

        # Persist view state shortly after scrollbars change (debounced)
        self._save_view_state_timer = QTimer(self)
        self._save_view_state_timer.setSingleShot(True)
        self._save_view_state_timer.setInterval(150)
        try:
            self.view.horizontalScrollBar().valueChanged.connect(self._schedule_save_view_state)
            self.view.verticalScrollBar().valueChanged.connect(self._schedule_save_view_state)
            # Reposition overlay widgets (toolbar/minimap) on scroll
            self.view.horizontalScrollBar().valueChanged.connect(self._position_toolbar_on_graphics_view)
            self.view.verticalScrollBar().valueChanged.connect(self._position_toolbar_on_graphics_view)
        except Exception:
            pass

        # Track parent resize/move to reposition overlays
        try:
            if self.parent_widget:
                self.parent_widget.installEventFilter(self)
        except Exception:
            pass

        logger.info("VisualBCFController initialized with own view and scene")

    def _setup_toolbar(self):
        """Create floating toolbar with component placement functionality"""
        self.floating_toolbar = FloatingToolbar(parent=self.parent_widget, device_data_provider=self)
        # Connect toolbar signals immediately
        self.floating_toolbar.add_chip_requested.connect(
            lambda: self._set_component_type("chip"))
        self.floating_toolbar.add_resistor_requested.connect(
            lambda: self._set_component_type("resistor"))
        self.floating_toolbar.add_capacitor_requested.connect(
            lambda: self._set_component_type("capacitor"))
        self.floating_toolbar.add_component_requested.connect(
            self._on_component_selected)
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

        # Also position minimap at bottom-right of the graphics view
        try:
            if self.minimap:
                mx = view_global_pos.x() + view_rect.width() - self.minimap.width() - 10
                my = view_global_pos.y() + view_rect.height() - self.minimap.height() - 10
                self.minimap.move(max(0, mx), max(0, my))
        except Exception:
            pass

    def _setup_minimap(self):
        try:
            self.minimap = MiniMapView(self.scene, self.view, parent=self.parent_widget)
            self.minimap.setWindowFlag(self.minimap.windowFlags())
            self.minimap.raise_()
            self.minimap.show()
            # Keep minimap viewport rectangle updated when main view changes
            try:
                if hasattr(self.view, 'view_transform_changed'):
                    def _update_minimap():
                        try:
                            self.minimap.viewport().update()
                            self._position_toolbar_on_graphics_view()
                        except Exception:
                            pass
                    self.view.view_transform_changed.connect(_update_minimap)
            except Exception:
                pass
        except Exception:
            self.minimap = None

    def eventFilter(self, obj, event):
        try:
            if obj is self.parent_widget and event.type() in (QEvent.Resize, QEvent.Move):
                self._position_toolbar_on_graphics_view()
        except Exception:
            pass
        return False

    def _set_component_type(self, component_type: str):
        """Set the component type for placement"""
        self.selected_component_type = component_type
        self.placement_mode = True

    def _on_component_selected(self, component_data: Dict[str, Any]):
        """Handle component selection from dialog"""
        print(f"BCF Controller: Component selected: {component_data}")
        self.selected_component_data = component_data
        self.selected_component_type = component_data.get('Component Type', 'chip')
        # Immediate placement path (e.g., triggered from Device Settings Add Device)
        if component_data.get('__place_immediately'):
            try:
                component_name = component_data.get('Name') or component_data.get('name') or 'New Device'
                component_config = self.data_model.component_dcf(component_name)
                comp = ComponentWithPins(
                    component_name,
                    self.selected_component_type,
                    component_config=component_config,
                )
                comp.setPos(0, 0)
                self.scene.addItem(comp)
                # Track/persist via controller API
                self.add_component(comp, self.selected_component_type, (0.0, 0.0))
                return
            except Exception as e:
                logger.error("Immediate placement failed, falling back to placement mode: %s", e)
        self.placement_mode = True
        
        # Update cursor to indicate placement mode
        if self.view:
            self.view.setCursor(Qt.CrossCursor)

    def _set_select_mode(self):
        """Set to select mode"""
        self.placement_mode = False
        self.selected_component_data = None
        
        # Clear preview component if it exists
        if hasattr(self.scene, '_clear_preview_component'):
            self.scene._clear_preview_component()
        
        # Reset cursor
        if self.view:
            self.view.setCursor(Qt.ArrowCursor)

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

    def connect_table_controllers(self, device_settings_controller, io_connect_controller):
        """Connect table controllers to handle table changes"""
        self.device_settings_controller = device_settings_controller
        self.io_connect_controller = io_connect_controller
        if device_settings_controller:
            device_settings_controller.device_added.connect(self._on_table_device_added)
            device_settings_controller.device_removed.connect(self._on_table_device_removed)
            device_settings_controller.device_updated.connect(self._on_table_device_updated)
            # Center on component when user selects in tree
            try:
                if hasattr(device_settings_controller, 'view') and hasattr(device_settings_controller.view, 'selection_changed'):
                    device_settings_controller.view.selection_changed.connect(self._on_table_selection_changed)
            except Exception:
                pass
        if io_connect_controller:
            io_connect_controller.connection_added.connect(self._on_table_connection_added)
            io_connect_controller.connection_removed.connect(self._on_table_connection_removed)
            io_connect_controller.connection_updated.connect(self._on_table_connection_updated)

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

    def _on_table_device_added(self, device_data: dict):
        """Handle device added to table - add to graphics scene"""
        print(f"BCF Controller: Device added to table: {device_data}")
        try:
            device_name = device_data.get('Name', device_data.get('name', 'Unknown'))
            device_id = device_data.get('ID', device_data.get('id', ''))
            device_type = device_data.get('Component Type', device_data.get('component_type', 'chip'))
            
            if not device_id:
                logger.warning("Device added to table without ID: %s", device_name)
                return

            # Check if component already exists in scene
            if device_id in self._component_graphics_items:
                logger.info("Component %s already exists in scene", device_name)
                return

            # Get component configuration
            component_config = self.data_model.component_dcf(device_name)
            
            # Create component graphics item
            component = ComponentWithPins(
                device_name,
                device_type,
                component_config=component_config
            )

            # Set position (default to center)
            pos = device_data.get('position', None)
            if pos is not None:
                self.scene.addItem(component)
                component.setPos(*pos)

            # Track the graphics item
            self._component_graphics_items[device_id] = component
            component.component_id = device_id
            component.properties = device_data.get('Properties', device_data.get('properties', {}))

            # Track in data model without triggering signals
            self.track_loaded_component(component, device_id)

            logger.info("Component %s (%s) added to scene from table", device_id, device_name)

        except Exception as e:
            logger.error("Error adding device from table to scene: %s", e)

    def _on_table_device_removed(self, device_data: dict):
        """Handle device removed from table - remove from graphics scene"""
        print(f"BCF Controller: Device removed from table: {device_data}")
        try:
            device_id = device_data.get('ID', device_data.get('id', ''))
            device_name = device_data.get('Name', device_data.get('name', 'Unknown'))
            
            if not device_id:
                logger.warning("Device removed from table without ID: %s", device_name)
                return

            # Find and remove component from scene
            if device_id in self._component_graphics_items:
                component = self._component_graphics_items[device_id]
                
                # Clean up any wires connected to this component
                if hasattr(component, 'connected_wires'):
                    for wire in list(component.connected_wires):
                        try:
                            self.scene.removeItem(wire)
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
                            logger.warning(f"Error cleaning up wire during component removal: {e}")

                # Remove from scene
                self.scene.removeItem(component)
                del self._component_graphics_items[device_id]

                logger.info("Component %s (%s) removed from scene via table", device_id, device_name)
            else:
                logger.warning("Component %s not found in scene for removal", device_name)

        except Exception as e:
            logger.error("Error removing device from scene via table: %s", e)

    def _on_table_device_updated(self, device_data: dict):
        """Handle device updated in table - update graphics scene"""
        try:
            device_id = device_data.get('ID', device_data.get('id', ''))
            device_name = device_data.get('Name', device_data.get('name', 'Unknown'))
            
            if not device_id:
                logger.warning("Device updated in table without ID: %s", device_name)
                return

            # Find component in scene and update properties
            if device_id in self._component_graphics_items:
                component = self._component_graphics_items[device_id]
                
                # Update component properties
                component.properties = device_data.get('Properties', device_data.get('properties', {}))
                
                # Update component name if changed
                if device_name != component.name:
                    component.name = device_name
                    component.update()  # Force visual update

                logger.info("Component %s (%s) updated in scene via table", device_id, device_name)
            else:
                logger.warning("Component %s not found in scene for update", device_name)

        except Exception as e:
            logger.error("Error updating device in scene via table: %s", e)

    def _on_table_selection_changed(self, device_rec: dict):
        """Center the view on the component selected in the tree."""
        try:
            if self._suppress_table_center:
                return
            if not isinstance(device_rec, dict):
                return
            device_id = device_rec.get('ID') or device_rec.get('id')
            component = None
            if device_id:
                component = self._component_graphics_items.get(device_id)
            if component is None:
                # Fallback by name
                device_name = device_rec.get('Name') or device_rec.get('name')
                if device_name:
                    for cid, comp in self._component_graphics_items.items():
                        if getattr(comp, 'name', None) == device_name:
                            component = comp
                            break
            if component is None:
                return
            # Ensure in scene
            if self.view and component.scene() is self.scene:
                self.view.centerOn(component)
        except Exception as e:
            logger.warning(f"Center on selection failed: {e}")

    def on_graphics_component_selected(self, component: ComponentWithPins):
        """Select and scroll to the corresponding item in the device settings tree."""
        try:
            if not component:
                return
            device_id = getattr(component, 'component_id', None)
            tree_key = 'mipi'
            pid = -1
            if device_id and hasattr(self.device_settings_controller, 'model'):
                pid = self.device_settings_controller.model.mipi_devices_tree_model.find_parent_id_by_key_value('ID', device_id)
                if pid == -1:
                    pid = self.device_settings_controller.model.gpio_devices_tree_model.find_parent_id_by_key_value('ID', device_id)
                    if pid != -1:
                        tree_key = 'gpio'
            if pid == -1:
                # fallback by name
                name = getattr(component, 'name', None)
                if name:
                    # search both models
                    pid = self.device_settings_controller.model.mipi_devices_tree_model.find_parent_id_by_key_value(self.device_settings_controller.model.mipi_devices_tree_model._parent_label_key, name)
                    if pid == -1:
                        pid = self.device_settings_controller.model.gpio_devices_tree_model.find_parent_id_by_key_value(self.device_settings_controller.model.gpio_devices_tree_model._parent_label_key, name)
                        if pid != -1:
                            tree_key = 'gpio'
            if pid != -1 and hasattr(self.device_settings_controller, 'view'):
                # Suppress centering back to scene while we update the tree selection
                self._suppress_table_center = True
                try:
                    self.device_settings_controller.view.select_by_parent_id(tree_key, pid)
                finally:
                    self._suppress_table_center = False
        except Exception as e:
            logger.warning(f"Could not select tree item for component: {e}")

    def _on_table_connection_added(self, connection_data: dict):
        """Handle connection added to table - add to graphics scene"""
        try:
            connection_id = connection_data.get('Connection ID', connection_data.get('id', ''))
            from_device = connection_data.get('Source Device', connection_data.get('source_device', ''))
            to_device = connection_data.get('Dest Device', connection_data.get('dest_device', ''))
            from_pin = connection_data.get('Source Pin', connection_data.get('source_pin', ''))
            to_pin = connection_data.get('Dest Pin', connection_data.get('dest_pin', ''))
            
            if not all([connection_id, from_device, to_device, from_pin, to_pin]):
                logger.warning("Incomplete connection data from table: %s", connection_data)
                return

            # Check if connection already exists
            if connection_id in self._connection_graphics_items:
                logger.info("Connection %s already exists in scene", connection_id)
                return

            if not connection_data.get('add_to_scene', True):
                return

            # Find component graphics items
            from_component_id = self._get_component_id(from_device)
            to_component_id = self._get_component_id(to_device)

            from_comp = self._component_graphics_items.get(from_component_id)
            to_comp = self._component_graphics_items.get(to_component_id)

            if not from_comp or not to_comp:
                logger.warning("Could not find component graphics for connection %s", connection_id)
                return

            # Find the pins on the components
            from_pin_obj = None
            to_pin_obj = None

            # Match pins by name
            for pin in from_comp.pins:
                pin_name = getattr(pin, 'pin_name', None) or getattr(pin, 'pin_id', None)
                if pin_name == from_pin:
                    from_pin_obj = pin
                    break

            for pin in to_comp.pins:
                pin_name = getattr(pin, 'pin_name', None) or getattr(pin, 'pin_id', None)
                if pin_name == to_pin:
                    to_pin_obj = pin
                    break

            if not from_pin_obj or not to_pin_obj:
                logger.warning("Could not find pins for connection %s", connection_id)
                return

            # Create the wire
            wire = Wire(from_pin_obj, end_pin=to_pin_obj, scene=self.scene)
            if wire.complete_wire(to_pin_obj):
                # Add wire to scene
                self.scene.addItem(wire)

                # Register wire with both connected components
                from_comp.add_wire(wire)
                to_comp.add_wire(wire)

                # Track the graphics item
                self._connection_graphics_items[connection_id] = wire
                wire.connection_id = connection_id
                wire.properties = connection_data.get("Properties", {})

                logger.info("Connection %s added to scene from table", connection_id)
            else:
                logger.warning("Failed to complete wire for connection %s", connection_id)

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error("Error adding connection from table to scene: %s", e)

    def _on_table_connection_removed(self, connection_data: dict):
        """Handle connection removed from table - remove from graphics scene"""
        try:
            connection_id = connection_data.get('Connection ID', connection_data.get('id', ''))
            
            if not connection_id:
                # Fallback: attempt to match by endpoints
                from_device = connection_data.get('Source Device', connection_data.get('source_device', ''))
                to_device = connection_data.get('Dest Device', connection_data.get('dest_device', ''))
                from_pin = connection_data.get('Source Pin', connection_data.get('source_pin', ''))
                to_pin = connection_data.get('Dest Pin', connection_data.get('dest_pin', ''))
                removed_any = False
                try:
                    for cid, wire in list(self._connection_graphics_items.items()):
                        s_comp = getattr(wire.start_pin, 'parent_component', None)
                        e_comp = getattr(wire.end_pin, 'parent_component', None)
                        s_name = getattr(s_comp, 'name', '') if s_comp else ''
                        e_name = getattr(e_comp, 'name', '') if e_comp else ''
                        s_pin_name = getattr(wire.start_pin, 'pin_name', getattr(wire.start_pin, 'pin_id', ''))
                        e_pin_name = getattr(wire.end_pin, 'pin_name', getattr(wire.end_pin, 'pin_id', ''))
                        if s_name == from_device and e_name == to_device and s_pin_name == from_pin and e_pin_name == to_pin:
                            if hasattr(wire, 'start_pin') and wire.start_pin and hasattr(wire.start_pin, 'parent_component'):
                                wire.start_pin.parent_component.remove_wire(wire)
                            if hasattr(wire, 'end_pin') and wire.end_pin and hasattr(wire.end_pin, 'parent_component'):
                                wire.end_pin.parent_component.remove_wire(wire)
                            wire.setVisible(False)
                            self.scene.removeItem(wire)
                            del self._connection_graphics_items[cid]
                            removed_any = True
                    if removed_any:
                        # Force refresh to clear any stale painting
                        self.scene.update()
                        if self.view:
                            self.view.viewport().update()
                        logger.info("Connection(s) removed via endpoint fallback match")
                        return
                except Exception:
                    pass
                logger.warning("Connection removed from table without ID and no matching wire found")
                return

            # Find and remove connection from scene
            if connection_id in self._connection_graphics_items:
                wire = self._connection_graphics_items[connection_id]
                
                # Remove from connected components
                if hasattr(wire, 'start_pin') and wire.start_pin and hasattr(wire.start_pin, 'parent_component'):
                    wire.start_pin.parent_component.remove_wire(wire)
                if hasattr(wire, 'end_pin') and wire.end_pin and hasattr(wire.end_pin, 'parent_component'):
                    wire.end_pin.parent_component.remove_wire(wire)

                # Remove from scene
                wire.setVisible(False)
                self.scene.removeItem(wire)
                del self._connection_graphics_items[connection_id]

                logger.info("Connection %s removed from scene via table", connection_id)
            else:
                logger.warning("Connection %s not found in scene for removal", connection_id)

            # Force refresh to ensure wire is no longer painted
            self.scene.update()
            if self.view:
                self.view.viewport().update()

        except Exception as e:
            logger.error("Error removing connection from scene via table: %s", e)

    def _on_table_connection_updated(self, connection_data: dict):
        """Handle connection updated in table - update graphics scene"""
        try:
            connection_id = connection_data.get('Connection ID', connection_data.get('id', ''))
            
            if not connection_id:
                logger.warning("Connection updated in table without ID")
                return

            # Find connection in scene and update properties
            if connection_id in self._connection_graphics_items:
                wire = self._connection_graphics_items[connection_id]
                
                # Update wire properties
                wire.properties = connection_data.get("Properties", {})
                
                # Force wire to recalculate its path
                wire.update_path()
                wire.force_intersection_recalculation()
                wire.update()

                logger.info("Connection %s updated in scene via table", connection_id)
            else:
                logger.warning("Connection %s not found in scene for update", connection_id)

        except Exception as e:
            logger.error("Error updating connection in scene via table: %s", e)

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
                logger.warning("Could not find component ID for moved component: %s, %s", component.name, component_id)
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
                      position: Tuple[float,float] = None) -> str:
        """Add a new component"""
        try:
            logger.info(f"BCF Controller: Adding component: {component.name} ({component_type}) at {position}")
            self.device_settings_controller.add_row(component.name, 'chip', tree="mipi" if component_type.lower() == 'mipi' else 'gpio', position=position)

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
            print(f"BCF Controller: Removing component: {component.name}, {component_id}")
            if not component_id:
                logger.warning("Could not find component ID for deleted component: %s", component.name)
                return False

            component_data = self.data_model.get_component(component_id)
            if not component_data:
                print(f"BCF Controller: Component data not found for component: {component.name}")
                return False

            component_name = component_data.get('Name', 'Unknown')

            # Route deletion via DeviceSettingsController (single flow)
            parent_id = -1
            tree = "mipi"
            try:
                # Prefer MIPI by default, fallback to GPIO if not found
                parent_id = self.device_settings_controller.model.mipi_devices_tree_model.find_parent_id_by_key_value("ID", component_id)
                if parent_id == -1:
                    parent_id = self.device_settings_controller.model.gpio_devices_tree_model.find_parent_id_by_key_value("ID", component_id)
                    tree = "gpio" if parent_id != -1 else tree
            except Exception:
                pass

            if parent_id == -1:
                logger.warning("Could not map component ID to table parent_id: %s", component_id)
                return False

            ok = self.device_settings_controller.delete_row(parent_id, tree=tree)
            if ok:
                # Table signal handler will remove graphics via _on_table_device_removed
                self.operation_completed.emit(
                    "remove_component", f"Removed component: {component_name}")
                logger.info(f"Successfully removed component via controller: {component_name}")
                return True
            return False
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
            from_pin_name = wire.start_pin.pin_name
            to_component_id = self._get_component_id(wire.end_pin.parent_component)
            to_pin_id = wire.end_pin.pin_id
            to_pin_name = wire.end_pin.pin_name

            if not from_component_id or not to_component_id:
                logger.error("Could not find component IDs for connection")
                return ""

            # Route via IOConnectController for unified flow
            if hasattr(self, 'io_connect_controller') and self.io_connect_controller is not None:
                source_device = self.data_model.get_component(from_component_id).get('Name', 'Unknown')
                dest_device = self.data_model.get_component(to_component_id).get('Name', 'Unknown')
                import uuid
                rec = {
                    'Connection ID': str(uuid.uuid4()),
                    'Source Device': source_device,
                    'Source Pin': from_pin_name,
                    'Dest Device': dest_device,
                    'Dest Pin': to_pin_name,
                }
                created = self.io_connect_controller.add_row(rec, add_to_scene=False)
                self._connection_graphics_items[created['Connection ID']] = wire
                self.operation_completed.emit("add_connection", "Added connection")
                logger.info("Successfully added connection via controller")
                # Connection ID is stored in data model; return empty string placeholder
                return ""
            # Fallback: original data model path
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

    def remove_connection(self, wire: Wire|str) -> bool:
        """Remove a connection that was deleted from the scene"""
        try:
            # If we have a connection id string, try to resolve to table parent_id
            if isinstance(wire, str):
                connection_id = wire
            else:
                connection_id = self._get_connection_id(wire)
            if not connection_id:
                logger.warning("Could not find connection ID for deleted wire")
                return False

            # Route via IOConnectController for unified flow
            if hasattr(self, 'io_connect_controller') and self.io_connect_controller is not None:
                try:
                    pid = self.io_connect_controller.model.tree_model.find_parent_id_by_key_value('Connection ID', connection_id)
                    if pid == -1:
                        # Fallback generic key
                        pid = self.io_connect_controller.model.tree_model.find_parent_id_by_key_value('id', connection_id)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    pid = -1
                if pid != -1:
                    ok = self.io_connect_controller.delete_row(pid)
                    if ok:
                        self.operation_completed.emit("remove_connection", f"Removed connection")
                        logger.info("Successfully removed connection via controller")
                        return True
                    return False

            # Fallback: original data model path
            success = self.data_model.remove_connection(connection_id)
            if success:
                connection = self._connection_graphics_items.pop(connection_id)
                if connection:
                    self.scene.removeItem(connection)
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
        """Get component ID by name or component object"""
        if isinstance(component, str):
            # Debug: Print available component names
            available_names = [item.name for item in self._component_graphics_items.values()]
            logger.debug(f"Looking for component: '{component}', Available names: {available_names}")
            
            # Try exact match first
            for component_id, component_item in self._component_graphics_items.items():
                if component_item.name == component:
                    return component_id
            
            # Try case-insensitive match
            for component_id, component_item in self._component_graphics_items.items():
                if component_item.name.lower() == component.lower():
                    return component_id
            
            # Try partial match
            for component_id, component_item in self._component_graphics_items.items():
                if component in component_item.name or component_item.name in component:
                    return component_id
            
            logger.warning(f"Could not find component ID for name: {component}")
            return None

        # Direct component object match
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
                # Get component ID from the loaded data - handle both "ID" and "id" fields
                component_id = comp_data.get("ID") or comp_data.get("id")
                component_name = comp_data.get("Name", comp_data.get("name", "Unknown"))
                component_type = comp_data.get("Component Type", comp_data.get("component_type", "chip"))

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

                # Set position - handle both possible position formats
                pos = self.data_model.visual_properties(component_id).get("position", {})
                if isinstance(pos, dict):
                    component.setPos(pos.get("x", 0), pos.get("y", 0))
                else:
                    component.setPos(0, 0)

                # Add to scene
                self.scene.addItem(component)

                # Track the graphics item in the controller
                self._component_graphics_items[component_id] = component

                # Set component properties - DON'T re-add to data model to avoid infinite loop
                component.component_id = component_id
                component.properties = comp_data.get("Properties", comp_data.get("properties", {}))

                # Use track_loaded_component instead of add_component to avoid infinite loops
                self.track_loaded_component(component, component_id)

                logger.info("Component %s (%s) added to scene", component_id, component_name)

            except Exception as e:
                logger.error("Error loading component %s: %s", comp_data.get('Name', comp_data.get('name', 'Unknown')), e)

    def _load_connections(self):
        """Load connections from the data model"""
        for conn_data in self.data_model.connections:
            try:
                # Get connection ID from the loaded data
                connection_id = conn_data.get("Connection ID")

                if not connection_id:
                    logger.warning("Connection missing ID: %s", conn_data)
                    continue

                # Get component IDs and pin IDs
                from_component = conn_data.get("Source Device")
                to_component = conn_data.get("Dest Device")
                from_pin_name = conn_data.get("Source Pin")
                to_pin_name = conn_data.get("Dest Pin")

                if not all([from_component, to_component, from_pin_name, to_pin_name]):
                    logger.warning("Connection missing required data: %s", conn_data)
                    continue

                from_component_id = self._get_component_id(from_component)
                to_component_id = self._get_component_id(to_component)

                # Find the component graphics items
                from_comp = self._component_graphics_items.get(from_component_id)
                to_comp = self._component_graphics_items.get(to_component_id)

                if not from_comp or not to_comp:
                    logger.warning("Could not find component graphics for connection %s", connection_id)
                    continue

                # Find the pins on the components
                from_pin_obj = None
                to_pin_obj = None

                # Match pins by name - check both pin_name and pin_id attributes
                for pin in from_comp.pins:
                    pin_name = getattr(pin, 'pin_name', None) or getattr(pin, 'pin_id', None)
                    if pin_name == from_pin_name:
                        from_pin_obj = pin
                        break

                for pin in to_comp.pins:
                    pin_name = getattr(pin, 'pin_name', None) or getattr(pin, 'pin_id', None)
                    if pin_name == to_pin_name:
                        to_pin_obj = pin
                        break

                if not from_pin_obj or not to_pin_obj:
                    logger.warning("Could not find pins for connection %s (from_pin: %s, to_pin: %s)",
                                    connection_id, from_pin_name, to_pin_name)
                    continue

                # Create the wire using the scene's wire creation logic
                wire = Wire(from_pin_obj, end_pin=to_pin_obj, scene=self.scene)
                if wire.complete_wire(to_pin_obj):
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
                    wire.properties = conn_data.get("Properties", {})

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
            # Restore scroll/zoom after items are laid out
            QTimer.singleShot(50, self._restore_view_state)
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

    # ---------------- View state persistence ----------------
    def _restore_view_state(self):
        try:
            vp = self.data_model.rdb_manager.get_value("config.visual_bcf.view_state") or {}
            if not vp:
                return
            h = vp.get("h_scroll", 0)
            v = vp.get("v_scroll", 0)
            z = vp.get("zoom", 1.0)
            try:
                if hasattr(self.view, 'set_zoom_factor'):
                    self.view.set_zoom_factor(float(z))
            except Exception:
                pass
            try:
                self.view.horizontalScrollBar().setValue(int(h))
                self.view.verticalScrollBar().setValue(int(v))
            except Exception:
                pass
        except Exception:
            pass

    def save_view_state(self):
        try:
            state = {
                "h_scroll": int(self.view.horizontalScrollBar().value()),
                "v_scroll": int(self.view.verticalScrollBar().value()),
                "zoom": float(getattr(self.view, 'zoom_factor', 1.0)),
            }
            existing = self.data_model.rdb_manager.get_value("config.visual_bcf.view_state") or {}
            existing.update(state)
            self.data_model.rdb_manager.set_value("config.visual_bcf.view_state", existing)
        except Exception:
            pass

    def _schedule_save_view_state(self, *args, **kwargs):
        try:
            if self._save_view_state_timer.isActive():
                self._save_view_state_timer.stop()
            self._save_view_state_timer.timeout.connect(self.save_view_state)
            self._save_view_state_timer.start()
        except Exception:
            # Fallback: save immediately if timer wiring fails
            self.save_view_state()
