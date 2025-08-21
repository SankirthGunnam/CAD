"""
Visual BCF Controller

This controller handles user interactions in the Visual BCF scene and coordinates
between the graphics view/scene and the data model. It implements the Controller
part of the MVC pattern.
"""

from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QPointF, QTimer
from PySide6.QtWidgets import QMessageBox, QApplication
import logging

from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel, ComponentData, ConnectionData
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, ComponentPin, Wire
from apps.RBM5.BCF.gui.source.visual_bcf.floating_toolbar import FloatingToolbar as FloatingToolbarPalette
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import QPointF
# Updated to use artifacts - old custom_widgets Chip class functionality is now in ComponentWithPins
# from apps.RBM5.BCF.gui.custom_widgets.components.chip import Chip
# from apps.RBM5.BCF.gui.custom_widgets.components.rfic_chip import RFICChip
# RDB manager access removed - controller should only communicate through model

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
    status_updated = Signal(str)  # status message
    data_changed = Signal(dict)  # data change notifications
    
    def __init__(self, parent_widget: QWidget, data_model: VisualBCFDataModel):
        super().__init__()
        self.parent_widget = parent_widget  # Parent widget to add view to
        self.data_model = data_model
        
        # Create scene and view - controller now owns these
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
        self._setup_toolbar()
        
        # Connect scene signals
        self._connect_scene_signals()
        
        # Connect model signals
        self._connect_model_signals()
        
        # Load existing data
        self.load_scene()
        
        # Current mode (select, connect, etc.)
        self.current_mode = "select"
        
        # Clipboard for copy/paste
        self.clipboard_data: List[Dict[str, Any]] = []
        
        # Setup periodic cleanup timer to prevent C++ object deletion errors
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_stale_graphics_items)
        self.cleanup_timer.start(5000)  # Clean up every 5 seconds
        
        logger.info("VisualBCFController initialized with own view and scene")
    
    # Toolbar Setup Methods
    
    def _setup_toolbar(self):
        """Create floating toolbar with component placement functionality"""
        print("🔧 VisualBCFController: Setting up floating toolbar...")
        # Create floating toolbar using working QPalette implementation
        self.floating_toolbar = FloatingToolbarPalette(parent=self.parent_widget)
        print(f"🔧 VisualBCFController: Created floating toolbar: {self.floating_toolbar}")
        
        # Show the floating toolbar first
        print("🔧 VisualBCFController: Calling show() on floating toolbar...")
        self.floating_toolbar.show()
        print(f"🔧 VisualBCFController: Toolbar visibility after show: {self.floating_toolbar.isVisible()}")
        
        # Position the toolbar at top-center of the graphics view
        self._position_toolbar_on_graphics_view()
        print(f"🔧 VisualBCFController: Positioned toolbar at: {self.floating_toolbar.pos()}")
        
        # Force layout update and visibility
        self.floating_toolbar.adjustSize()  # Adjust to content size
        self.floating_toolbar.show()  # Ensure visible
        self.floating_toolbar.raise_()  # Bring to front
        self.floating_toolbar.activateWindow()  # Activate
        
        print(f"🔧 VisualBCFController: Final toolbar visibility: {self.floating_toolbar.isVisible()}")
        print(f"🔧 VisualBCFController: Toolbar size: {self.floating_toolbar.size()}")
        print(f"🔧 VisualBCFController: Toolbar geometry: {self.floating_toolbar.geometry()}")
        
        # Connect toolbar signals to controller methods
        self.floating_toolbar.add_chip_requested.connect(lambda: self._set_component_type("chip"))
        self.floating_toolbar.add_resistor_requested.connect(lambda: self._set_component_type("resistor"))
        self.floating_toolbar.add_capacitor_requested.connect(lambda: self._set_component_type("capacitor"))
        self.floating_toolbar.select_mode_requested.connect(self._set_select_mode)
        self.floating_toolbar.connection_mode_requested.connect(self._set_select_mode)  # For now, use select mode
        self.floating_toolbar.delete_selected_requested.connect(self._on_delete_selected)
        self.floating_toolbar.clear_scene_requested.connect(self._on_clear_scene)
        self.floating_toolbar.zoom_fit_requested.connect(self._on_zoom_fit)
        self.floating_toolbar.phase_info_requested.connect(self._show_phase_info)
        
        # Connect zoom signals to view
        if self.view:
            self.floating_toolbar.zoom_in_requested.connect(self.view.zoom_in)
            self.floating_toolbar.zoom_out_requested.connect(self.view.zoom_out) 
            self.floating_toolbar.zoom_reset_requested.connect(self.view.reset_zoom)
    
    def _position_toolbar_on_graphics_view(self):
        """Position the floating toolbar at the top-center of the graphics view"""
        if not self.view or not self.floating_toolbar:
            return
            
        # Get the parent widget to position within it
        if not self.parent_widget:
            return
            
        # Get parent widget size
        parent_size = self.parent_widget.size()
        
        # Get the actual toolbar size after adjustSize
        self.floating_toolbar.adjustSize()
        actual_toolbar_size = self.floating_toolbar.size()
        
        # Position it more towards the graphics view area (left side of splitter)
        graphics_area_width = int(parent_size.width() * 0.7)  # 70% for graphics view
        x = max(10, (graphics_area_width - actual_toolbar_size.width()) // 2)
        y = 50  # 50px from top to account for the info label
        
        print(f"🔧 VisualBCFController: Parent widget size: {parent_size}")
        print(f"🔧 VisualBCFController: Actual toolbar size: {actual_toolbar_size}")
        print(f"🔧 VisualBCFController: Graphics area width: {graphics_area_width}")
        print(f"🔧 VisualBCFController: Calculated toolbar position: ({x}, {y})")
        
        # Position the toolbar
        self.floating_toolbar.move(x, y)
    
    def _set_component_type(self, component_type: str):
        """Set the component type for placement"""
        self.selected_component_type = component_type
        self.placement_mode = True
        
        # Update button states
        self._update_button_states()
        
        self.status_updated.emit(f"Placement mode: {component_type} - Click on scene to place")
        
    def _set_select_mode(self):
        """Switch to selection mode"""
        self.placement_mode = False
        self._update_button_states()
        self.status_updated.emit("Selection mode - Click and drag to select/move components")
        
    def _update_button_states(self):
        """Update button visual states based on current mode"""
        if not self.floating_toolbar:
            return
            
        # Clear all button selections first
        self.floating_toolbar._clear_mode_selection()
        self.floating_toolbar._clear_component_selection()
        
        # Set the appropriate button as checked based on current mode
        if self.placement_mode:
            if self.selected_component_type == "chip":
                self.floating_toolbar.add_chip_btn.setChecked(True)
            elif self.selected_component_type == "resistor":
                self.floating_toolbar.add_resistor_btn.setChecked(True)
            elif self.selected_component_type == "capacitor":
                self.floating_toolbar.add_capacitor_btn.setChecked(True)
        else:
            self.floating_toolbar.select_btn.setChecked(True)
    
    def _on_delete_selected(self):
        """Delete selected components"""
        if not self.scene:
            return
            
        selected_items = self.scene.selectedItems()
        component_items = [item for item in selected_items if isinstance(item, ComponentWithPins)]
        
        if not component_items:
            self.status_updated.emit("No components selected")
            return
            
        # Delete selected components
        deleted_names = []
        for component in component_items:
            deleted_names.append(component.name)
            self.scene.remove_component(component)
            
        count = len(deleted_names)
        if count == 1:
            self.status_updated.emit(f"Deleted {deleted_names[0]}")
        else:
            self.status_updated.emit(f"Deleted {count} components: {', '.join(deleted_names)}")
    
    def _on_clear_scene(self):
        """Clear all components from scene"""
        if self.scene and hasattr(self.scene, 'components'):
            count = len(self.scene.components)
            self.scene.clear()
            if hasattr(self.scene, 'components'):
                self.scene.components = []
            if hasattr(self.scene, 'component_counter'):
                self.scene.component_counter = 1
            self.status_updated.emit(f"Scene cleared - Removed {count} components")
        else:
            self.status_updated.emit("Scene already empty")
        
    def _on_zoom_fit(self):
        """Fit scene content in view"""
        if self.view and self.scene:
            if self.scene.items():
                from PySide6.QtCore import Qt
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
                self.status_updated.emit("View fitted to components")
            else:
                from PySide6.QtCore import Qt
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                self.status_updated.emit("View fitted to scene")
                
    def _show_phase_info(self):
        """Show information about current phase"""
        component_count = len(self.scene.components) if hasattr(self.scene, 'components') else 0
        wire_count = len(self.scene.wires) if hasattr(self.scene, 'wires') else 0
        
        info_text = f"""
        <h3>Phase 3: Data Management & Persistence</h3>
        <p><b>Development Period:</b> Week 6+</p>
        <p><b>Status:</b> 🔄 In Development</p>
        
        <h4>Current Scene:</h4>
        <ul>
        <li><b>Components:</b> {component_count}</li>
        <li><b>Wires:</b> {wire_count}</li>
        <li><b>Mode:</b> {'Placement' if self.placement_mode else 'Selection'}</li>
        <li><b>Selected Type:</b> {self.selected_component_type if self.placement_mode else 'N/A'}</li>
        </ul>
        
        <h4>New Features in Phase 3:</h4>
        <ul>
        <li>🔄 Proper MVC Architecture with Controller-owned Views</li>
        <li>🔄 Data Model Integration and Synchronization</li>
        <li>🔄 JSON-based Scene Save/Load functionality</li>
        <li>🔄 Component Properties Management</li>
        <li>🔄 Project/Session Persistence</li>
        <li>🔄 Legacy BCF Integration and Synchronization</li>
        </ul>
        
        <h4>Architecture:</h4>
        <ul>
        <li><b>Manager:</b> Creates Model and Controller only</li>
        <li><b>Controller:</b> Owns View/Scene, handles UI and business logic</li>
        <li><b>Model:</b> Handles all data operations and database communication</li>
        </ul>
        """
        
        QMessageBox.information(None, "Development Phase Information", info_text)
    
    # Public methods to get view/scene for manager integration
    def get_view(self) -> CustomGraphicsView:
        """Get the graphics view created by this controller"""
        return self.view
    
    def get_scene(self) -> ComponentScene:
        """Get the graphics scene created by this controller"""
        return self.scene
    
    def get_toolbar(self) -> FloatingToolbarPalette:
        """Get the floating toolbar created by this controller"""
        return self.floating_toolbar
    
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
        # Connect to scene signals
        self.scene.component_added.connect(self._on_scene_component_added)
        self.scene.component_removed.connect(self._on_scene_component_removed)
        self.scene.wire_added.connect(self._on_scene_wire_added)
        
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
    
   
    # Model event handlers
    
    def _on_model_component_added(self, component_id: str):
        """Handle component added to model"""
        print('calling on model component added')
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
                    for wire in list(graphics_item.graphics_item.connected_wires):
                        try:
                            # Remove wire from scene
                            self.scene.removeItem(wire)
                            # Remove wire from scene's wire list
                            if hasattr(self.scene, 'wires') and wire in self.scene.wires:
                                self.scene.wires.remove(wire)
                            # Remove wire from other connected component
                            if hasattr(wire, 'start_pin') and wire.start_pin and hasattr(wire.start_pin, 'parent_component'):
                                other_component = wire.start_pin.parent_component
                                if other_component != graphics_item.graphics_item and hasattr(other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                            if hasattr(wire, 'end_pin') and wire.end_pin and hasattr(wire.end_pin, 'parent_component'):
                                other_component = wire.end_pin.parent_component
                                if other_component != graphics_item.graphics_item and hasattr(other_component, 'remove_wire'):
                                    other_component.remove_wire(wire)
                        except Exception as e:
                            logger.warning(f"Error cleaning up wire during component removal: {e}")
                
                self.scene.removeItem(graphics_item.graphics_item)
                
                # Also remove from scene's component list for serialization
                if graphics_item.graphics_item in self.scene.components:
                    self.scene.components.remove(graphics_item.graphics_item)
                
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
    
    def _on_scene_component_added(self, name: str, component_type: str, position: QPointF):
        """Handle component added from scene (e.g., user clicked to place)"""
        try:
            # Add component to data model to keep synchronized
            component_id = self.data_model.add_component(
                name=name,
                component_type=component_type,
                position=(position.x(), position.y()),
                properties={"function_type": component_type}
            )
            
            if component_id:
                logger.info(f"Scene component added and synchronized to model: {name}")
                self.status_updated.emit(f"Added {name} to scene")
            
        except Exception as e:
            logger.error(f"Error handling scene component added: {e}")
    
    def _on_scene_component_removed(self, name: str):
        """Handle component removed from scene"""
        try:
            # Remove from data model to keep synchronized
            success = self.data_model.remove_component_by_name(name)
            if success:
                logger.info(f"Scene component removed and synchronized to model: {name}")
                self.status_updated.emit(f"Removed {name} from scene")
            
        except Exception as e:
            logger.error(f"Error handling scene component removed: {e}")
    
    def _on_scene_wire_added(self, start_component: str, start_pin: str, end_component: str, end_pin: str):
        """Handle wire added from scene (user drew connection)"""
        try:
            # Find component IDs by name
            start_comp = self.data_model.get_component_by_name(start_component)
            end_comp = self.data_model.get_component_by_name(end_component)
            
            if start_comp and end_comp:
                # Add connection to data model to keep synchronized
                connection_id = self.data_model.add_connection(
                    from_component_id=start_comp.id,
                    from_pin_id=start_pin,
                    to_component_id=end_comp.id,
                    to_pin_id=end_pin
                )
                
                if connection_id:
                    logger.info(f"Scene wire added and synchronized to model: {start_component}.{start_pin} -> {end_component}.{end_pin}")
                    self.status_updated.emit(f"Wire connected: {start_component}.{start_pin} → {end_component}.{end_pin}")
                else:
                    logger.warning(f"Failed to add connection to data model: {start_component}.{start_pin} -> {end_component}.{end_pin}")
            else:
                logger.warning(f"Could not find components for wire: {start_component} ({start_comp}) or {end_component} ({end_comp})")
                
        except Exception as e:
            logger.error(f"Error handling scene wire added: {e}")
    
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
            for component_id, wrapper in list(self._component_graphics_items.items()):
                try:
                    if (not wrapper or 
                        not wrapper.graphics_item or 
                        not hasattr(wrapper.graphics_item, 'pos')):
                        stale_component_ids.append(component_id)
                        logger.warning(f"Found stale component graphics item: {component_id}")
                except Exception:
                    stale_component_ids.append(component_id)
                    logger.warning(f"Found invalid component graphics item: {component_id}")
            
            # Check connection graphics items
            for connection_id, wrapper in list(self._connection_graphics_items.items()):
                try:
                    if (not wrapper or 
                        not wrapper.graphics_item or 
                        not hasattr(wrapper.graphics_item, 'line')):
                        stale_connection_ids.append(connection_id)
                        logger.warning(f"Found stale connection graphics item: {connection_id}")
                except Exception:
                    stale_connection_ids.append(connection_id)
                    logger.warning(f"Found invalid connection graphics item: {connection_id}")
            
            # Remove stale items
            for component_id in stale_component_ids:
                del self._component_graphics_items[component_id]
                logger.info(f"Removed stale component graphics item: {component_id}")
                
            for connection_id in stale_connection_ids:
                del self._connection_graphics_items[connection_id]
                logger.info(f"Removed stale connection graphics item: {connection_id}")
                
            if stale_component_ids or stale_connection_ids:
                logger.info(f"Cleaned up {len(stale_component_ids)} stale component items and {len(stale_connection_ids)} stale connection items")
                
        except Exception as e:
            logger.error(f"Error during graphics items cleanup: {e}")

    # Graphics -> Model sync for position updates
    def on_graphics_component_moved(self, graphics_component):
        """Handle graphics component movement and sync to model"""
        try:
            # Validate the graphics component
            if not graphics_component:
                logger.warning("Received null graphics component in on_graphics_component_moved")
                return
                
            # Check if the graphics component is still valid
            try:
                # Test if the C++ object is still alive by accessing a basic property
                pos = graphics_component.pos()
                if not hasattr(pos, 'x') or not hasattr(pos, 'y'):
                    logger.warning("Graphics component position is invalid")
                    return
            except Exception as e:
                logger.warning(f"Graphics component is no longer valid: {e}")
                return
            
            # Find the component ID for this graphics item
            component_id = None
            for cid, wrapper in self._component_graphics_items.items():
                try:
                    # Check if the wrapper's graphics item is still valid
                    if (wrapper and wrapper.graphics_item and 
                        wrapper.graphics_item == graphics_component):
                        component_id = cid
                        break
                except Exception as e:
                    logger.warning(f"Error checking graphics item wrapper {cid}: {e}")
                    continue
            
            if component_id:
                try:
                    # Get the current position
                    pos = graphics_component.pos()
                    new_position = (pos.x(), pos.y())
                    
                    # Update model with new position
                    success = self.data_model.update_component_position(component_id, new_position)
                    if success:
                        logger.debug(f"Successfully synced position for component {component_id}: {new_position}")
                    else:
                        logger.warning(f"Failed to update position in model for component {component_id}")
                        
                except Exception as e:
                    logger.error(f"Error updating model position for component {component_id}: {e}")
            else:
                logger.warning(f"Could not find component ID for graphics component: {graphics_component}")
                
        except Exception as e:
            logger.error(f"Error syncing graphics position to model: {e}")
            # Don't emit error_occurred signal here to avoid spam - just log it
    
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
            # Get Legacy BCF device settings through the model
            device_settings = self.data_model.get_legacy_bcf_devices()
            
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
            
            # Check if there are any Legacy BCF devices to import through the model
            device_settings = self.data_model.get_legacy_bcf_devices()
            
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
                # Get count before clearing for logging
                stats = self.get_statistics()
                component_count = stats.get('component_count', 0)
                connection_count = stats.get('connection_count', 0)
                
                # Clear only in memory; do not persist to disk
                self.data_model.clear_all_data()
                
                # Also clear visual scene components list to ensure proper cleanup
                if hasattr(self.scene, 'components'):
                    self.scene.components.clear()
                if hasattr(self.scene, 'wires'):
                    self.scene.wires.clear()
                    
                # Clear controller's graphics item mappings
                self._component_graphics_items.clear()
                self._connection_graphics_items.clear()
                
                # Clear any remaining scene items (fallback)
                self.scene.clear()
                
                message = f"Cleared {component_count} components and {connection_count} connections"
                self.operation_completed.emit("clear", message)
                logger.info(message)
            
        except Exception as e:
            logger.error(f"Error clearing scene: {e}")
            self.error_occurred.emit(f"Failed to clear scene: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about current data
        
        Returns both data model statistics and controller-specific stats
        for better accuracy and debugging.
        
        Returns:
            Dict[str, Any]: Statistics including component counts, connection counts, etc.
        """
        try:
            # Get base statistics from data model
            stats = self.data_model.get_statistics()
            
            # Add controller-specific statistics
            controller_stats = {
                'graphics_components_count': len(self._component_graphics_items),
                'graphics_connections_count': len(self._connection_graphics_items),
                'scene_components_count': len(self.scene.components) if hasattr(self.scene, 'components') else 0,
                'scene_wires_count': len(self.scene.wires) if hasattr(self.scene, 'wires') else 0,
                'scene_total_items': len(self.scene.items()) if self.scene else 0
            }
            
            # Merge controller stats with model stats
            stats.update(controller_stats)
            
            # Add synchronization status information
            stats['sync_status'] = {
                'model_components_match_graphics': stats.get('component_count', 0) == controller_stats['graphics_components_count'],
                'model_connections_match_graphics': stats.get('connection_count', 0) == controller_stats['graphics_connections_count']
            }
            
            logger.debug(f"Statistics: Model components={stats.get('component_count', 0)}, Graphics components={controller_stats['graphics_components_count']}, Scene components={controller_stats['scene_components_count']}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'component_count': 0,
                'connection_count': 0,
                'graphics_components_count': 0,
                'graphics_connections_count': 0,
                'error': str(e)
            }
    
    # Scene Save/Load Methods
    
    def save_scene(self, file_path: str = None) -> bool:
        """Save current scene via data model and RDB manager
        
        Args:
            file_path (str, optional): File path to save. If None, saves to default location.
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Get current statistics before saving
            stats = self.get_statistics()
            component_count = stats.get('component_count', 0)
            connection_count = stats.get('connection_count', 0)
            
            # Let the data model handle the save through RDB manager
            success = self.data_model.save_visual_bcf_to_file(file_path) if file_path else self.data_model.save_visual_bcf_data()
            
            if success:
                if file_path:
                    logger.info(f"Scene saved to file: {file_path} with {component_count} components and {connection_count} connections")
                    message = f"Scene saved to file with {component_count} components and {connection_count} connections"
                else:
                    logger.info(f"Scene saved to default location with {component_count} components and {connection_count} connections")
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
        """Load scene from JSON file or database
        
        Args:
            file_path (str, optional): File path to load. If None, loads from default scene location.
            
        Returns:
            bool: True if load was successful
        """
        try:
            scene_data = None
            raw_data = None
            
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

                    # Reconstruct scene solely from normalized tables
                    id_to_name = {}
                    components_list = []
                    for comp in tables_components:
                        name = comp.get("name", "")
                        comp_id = comp.get("id", name)
                        id_to_name[comp_id] = name
                        pos = comp.get("visual_properties", {}).get("position", {"x": 0, "y": 0})
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
                        connections_list.append({
                            "id": conn.get("id", ""),
                            "start_component": id_to_name.get(conn.get("from_component_id", ""), ""),
                            "end_component": id_to_name.get(conn.get("to_component_id", ""), ""),
                            "start_pin": conn.get("from_pin_id", ""),
                            "end_pin": conn.get("to_pin_id", ""),
                            "properties": conn.get("properties", {}),
                            "visual_properties": conn.get("visual_properties", {})
                        })

                    scene_data = {
                        "components": components_list,
                        "connections": connections_list,
                    }
                    logger.info(
                        f"Reconstructed scene from tables: {len(components_list)} components, {len(connections_list)} connections"
                    )
                else:
                    # Direct scene format
                    scene_data = raw_data
            else:
                # Load from model default scene
                scene_data = self.data_model.load_scene_data()
                if scene_data:
                    logger.info("Scene loaded from default location through model")
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
                logger.info(f"Found {len(connections_data)} connections to load")
                
                for conn_data in connections_data:
                    # Find component IDs by name
                    start_comp = self.data_model.get_component_by_name(conn_data.get("start_component", ""))
                    end_comp = self.data_model.get_component_by_name(conn_data.get("end_component", ""))
                    
                    if start_comp and end_comp:
                        self.data_model.add_connection(
                            from_component_id=start_comp.id,
                            from_pin_id=conn_data.get("start_pin", ""),
                            to_component_id=end_comp.id,
                            to_pin_id=conn_data.get("end_pin", "")
                        )
                
                # Clear any existing graphics items to prevent conflicts
                self._clear_graphics_items()
                
                # Create graphics items through the controller to ensure proper tracking
                components = self.data_model.get_all_components()
                for component_id, component_data in components.items():
                    self._create_graphics_component(component_id, component_data)
                
                connections = self.data_model.get_all_connections()
                for connection_id, connection_data in connections.items():
                    self._create_graphics_connection(connection_id, connection_data)
                
                # Get final statistics
                stats = self.get_statistics()
                component_count = stats.get('component_count', 0)
                connection_count = stats.get('connection_count', 0)
                
                # Clean up any stale graphics items to prevent C++ object deletion errors
                self._cleanup_stale_graphics_items()
                
                self.operation_completed.emit("load_scene", f"Scene loaded: {component_count} components, {connection_count} connections")
                logger.info(f"Successfully loaded {component_count} components and {connection_count} connections")
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
        """Export current scene to external JSON file
        
        Args:
            file_path (str): File path to export
            
        Returns:
            bool: True if export was successful
        """
        return self.save_scene(file_path)
    
    def import_scene(self, file_path: str) -> bool:
        """Import scene from external JSON file
        
        Args:
            file_path (str): File path to import
            
        Returns:
            bool: True if import was successful
        """
        return self.load_scene(file_path)
    
    # Private helper methods
    
    def _create_scene_data_from_model(self) -> dict:
        """Create scene data structure from current data model state
        
        This ensures save operation uses the most accurate data from the model,
        not potentially stale visual scene data.
        
        Returns:
            dict: Scene data structure ready for serialization
        """
        try:
            # Get all components from model
            components = self.data_model.get_all_components()
            components_list = []
            
            for component_id, component_data in components.items():
                component_dict = {
                    "id": component_id,
                    "name": component_data.name,
                    "type": component_data.component_type,
                    "position": {
                        "x": component_data.visual_properties['position']['x'],
                        "y": component_data.visual_properties['position']['y']
                    },
                    "properties": component_data.properties,
                    "visual_properties": component_data.visual_properties
                }
                components_list.append(component_dict)
            
            # Get all connections from model
            connections = self.data_model.get_all_connections()
            connections_list = []
            
            for connection_id, connection_data in connections.items():
                # Get component names for connection references
                from_component = self.data_model.get_component(connection_data.from_component_id)
                to_component = self.data_model.get_component(connection_data.to_component_id)
                
                if from_component and to_component:
                    connection_dict = {
                        "id": connection_id,
                        "start_component": from_component.name,
                        "end_component": to_component.name,
                        "start_pin": connection_data.from_pin_id,
                        "end_pin": connection_data.to_pin_id,
                        "visual_properties": connection_data.visual_properties
                    }
                    connections_list.append(connection_dict)
            
            # Create scene data structure
            scene_data = {
                "components": components_list,
                "connections": connections_list,
                "metadata": {
                    "version": "1.0",
                    "created_by": "Visual BCF Controller",
                    "component_count": len(components_list),
                    "connection_count": len(connections_list)
                }
            }
            
            logger.info(f"Created scene data from model: {len(components_list)} components, {len(connections_list)} connections")
            return scene_data
            
        except Exception as e:
            logger.error(f"Error creating scene data from model: {e}")
            logger.exception("Full traceback:")
            return {"components": [], "connections": [], "metadata": {}}
    
    def _clear_graphics_items(self):
        """Clear all graphics items from the scene and tracking dictionaries"""
        try:
            # Remove all graphics items from the scene
            for component_id, wrapper in list(self._component_graphics_items.items()):
                try:
                    if wrapper and wrapper.graphics_item:
                        self.scene.removeItem(wrapper.graphics_item)
                except Exception as e:
                    logger.warning(f"Error removing component graphics item {component_id}: {e}")
            
            for connection_id, wrapper in list(self._connection_graphics_items.items()):
                try:
                    if wrapper and wrapper.graphics_item:
                        self.scene.removeItem(wrapper.graphics_item)
                except Exception as e:
                    logger.warning(f"Error removing connection graphics item {connection_id}: {e}")
            
            # Clear the tracking dictionaries
            self._component_graphics_items.clear()
            self._connection_graphics_items.clear()
            
            # Clear scene's component and wire lists
            if hasattr(self.scene, 'components'):
                self.scene.components.clear()
            if hasattr(self.scene, 'wires'):
                self.scene.wires.clear()
                
            logger.info("Cleared all graphics items from scene and tracking dictionaries")
            
        except Exception as e:
            logger.error(f"Error clearing graphics items: {e}")

    def _create_graphics_component(self, component_id: str, component_data: ComponentData):
        """Create graphics item for component"""
        try:
            # Create the actual graphics component
            graphics_component = ComponentWithPins(
                name=component_data.name,
                component_type=component_data.component_type,
                width=component_data.visual_properties.get('size', {}).get('width', 100),
                height=component_data.visual_properties.get('size', {}).get('height', 60)
            )
            
            # Set position from component data
            pos = component_data.visual_properties['position']
            graphics_component.setPos(pos['x'], pos['y'])
            
            # Add to scene
            self.scene.addItem(graphics_component)
            
            # Also add to scene's component list for serialization
            if graphics_component not in self.scene.components:
                self.scene.components.append(graphics_component)
            
            # Create wrapper and store
            graphics_item = ComponentGraphicsItem(component_id, graphics_component)
            self._component_graphics_items[component_id] = graphics_item
            
            logger.info(f"Created graphics item for component: {component_data.name} (type: {component_data.component_type})")
            
        except Exception as e:
            logger.error(f"Error creating graphics component: {e}")
            logger.exception("Full traceback:")
    
    def _create_graphics_connection(self, connection_id: str, connection_data: ConnectionData):
        """Create graphics item for connection"""
        try:
            # Find the source and target components
            from_graphics = self._component_graphics_items.get(connection_data.from_component_id)
            to_graphics = self._component_graphics_items.get(connection_data.to_component_id)
            
            if from_graphics and to_graphics:
                # Create connection using pin-aware Wire API compatible with artifacts.connection.Wire
                try:
                    def _find_pin_by_id(graphics_item, pin_id):
                        """Find pin by its specific ID instead of edge preference"""
                        if hasattr(graphics_item, 'pins') and graphics_item.pins:
                            for pin in graphics_item.pins:
                                if hasattr(pin, 'pin_id') and pin.pin_id == pin_id:
                                    return pin
                        return None

                    # Use the actual pin IDs from the connection data
                    start_pin = _find_pin_by_id(from_graphics.graphics_item, connection_data.from_pin_id)
                    end_pin = _find_pin_by_id(to_graphics.graphics_item, connection_data.to_pin_id)

                    if start_pin is None or end_pin is None:
                        logger.warning(f"Connection {connection_id}: Pin not found - from_pin_id: {connection_data.from_pin_id}, to_pin_id: {connection_data.to_pin_id}")
                        # Fallback to edge-based pin selection if specific pins not found
                        def _find_pin_by_edge(graphics_item, preferred_edges):
                            if hasattr(graphics_item, 'pins') and graphics_item.pins:
                                for edge in preferred_edges:
                                    for pin in graphics_item.pins:
                                        if getattr(pin, 'edge', None) == edge:
                                            return pin
                                # Fallback to first pin
                                return graphics_item.pins[0]
                            return None
                        
                        start_pin = _find_pin_by_edge(from_graphics.graphics_item, ['right'])
                        end_pin = _find_pin_by_edge(to_graphics.graphics_item, ['left'])
                        
                        if start_pin is None or end_pin is None:
                            logger.info(f"Connection {connection_id} exists but suitable pins not found for visual wire")
                            return
                    # Avoid duplicate wires for the same connection_id
                    if connection_id in self._connection_graphics_items:
                        return

                    connection_graphics = Wire(start_pin)
                    if connection_graphics.complete_wire(end_pin):
                        self.scene.addItem(connection_graphics)
                        if hasattr(self.scene, 'wires') and connection_graphics not in self.scene.wires:
                            self.scene.wires.append(connection_graphics)
                        
                        # Register wire with both connected components so they can update it when moved
                        start_component = start_pin.parent_component
                        end_component = end_pin.parent_component
                        if hasattr(start_component, 'add_wire'):
                            start_component.add_wire(connection_graphics)
                        if hasattr(end_component, 'add_wire'):
                            end_component.add_wire(connection_graphics)
                        
                        connection_graphics_item = ConnectionGraphicsItem(connection_id, connection_graphics)
                        self._connection_graphics_items[connection_id] = connection_graphics_item
                        logger.info(f"Created graphics wire for connection: {connection_id}")
                    else:
                        logger.info(f"Connection {connection_id} could not complete visual wire")
                except Exception as wire_error:
                    logger.warning(f"Failed to create wire graphics for connection {connection_id}: {wire_error}")
                    logger.info(f"Connection {connection_id} exists in data model but not visually displayed")
            else:
                logger.warning(f"Cannot create graphics connection - missing component graphics: from={connection_data.from_component_id}, to={connection_data.to_component_id}")
            
        except Exception as e:
            logger.error(f"Error creating graphics connection: {e}")
    
    def _create_device_settings(self) -> list:
        """Create device settings structure for RDB format"""
        try:
            device_settings = []
            components = self.data_model.get_all_components()
            
            for component_id, component_data in components.items():
                # Only add chip/device components to device settings
                if component_data.component_type in ['chip', 'device', 'modem', 'rfic']:
                    function_type = component_data.properties.get('function_type', 'generic')
                    interface_type = component_data.properties.get('interface_type', 'Generic')
                    interface = component_data.properties.get('interface', {})
                    config = component_data.properties.get('config', {'usid': f'GENERIC{len(device_settings)+1:03d}'})
                    
                    device_setting = {
                        "name": component_data.name,
                        "function_type": function_type,
                        "interface_type": interface_type,
                        "interface": interface,
                        "config": config
                    }
                    device_settings.append(device_setting)
            
            return device_settings
        except Exception as e:
            logger.error(f"Error creating device settings: {e}")
            return []
    
    def _create_visual_bcf_components(self) -> list:
        """Create visual BCF components structure for RDB format"""
        try:
            components_list = []
            components = self.data_model.get_all_components()
            
            for component_id, component_data in components.items():
                component_dict = {
                    "name": component_data.name,
                    "component_type": component_data.component_type,
                    "function_type": component_data.properties.get('function_type', ''),
                    "properties": component_data.properties,
                    "visual_properties": component_data.visual_properties,
                    "pins": [],  # TODO: Extract pin data if available
                    "id": component_id
                }
                components_list.append(component_dict)
            
            return components_list
        except Exception as e:
            logger.error(f"Error creating visual BCF components: {e}")
            return []
    
    def _create_visual_bcf_connections(self) -> list:
        """Create visual BCF connections structure for RDB format"""
        try:
            connections_list = []
            connections = self.data_model.get_all_connections()
            
            for connection_id, connection_data in connections.items():
                connection_dict = {
                    "from_component_id": connection_data.from_component_id,
                    "from_pin_id": connection_data.from_pin_id,
                    "to_component_id": connection_data.to_component_id,
                    "to_pin_id": connection_data.to_pin_id,
                    "connection_type": "wire",
                    "properties": {},
                    "visual_properties": connection_data.visual_properties,
                    "id": connection_id
                }
                connections_list.append(connection_dict)
            
            return connections_list
        except Exception as e:
            logger.error(f"Error creating visual BCF connections: {e}")
            return []
    
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
