"""
Visual BCF Manager - Phase 2.5: Core Functionality Fixes

This phase fixes core functionality issues and implements modular structure:
- Zoom with Ctrl+Scroll
- Global delete button
- Component pins
- Wire connections between components
- Enhanced component placement and management
- Modular architecture with separate files for components
"""

import sys
from typing import Dict, Any, List

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLabel, QMessageBox, QSplitter, QTabWidget)
from PySide6.QtCore import Signal, Qt, QPointF

from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, ComponentPin, Wire
from apps.RBM5.BCF.gui.source.visual_bcf.floating_toolbar import FloatingToolbar as FloatingToolbarPalette
from apps.RBM5.BCF.source.controllers.visual_bcf.device_settings_controller import DeviceSettingsController
from apps.RBM5.BCF.source.controllers.visual_bcf.io_connect_controller import IOConnectController


class VisualBCFManager(QMainWindow):
    """
    Visual BCF Manager - Phase 2.5 Implementation

    This phase fixes core functionality issues:
    - Zoom with Ctrl+Scroll
    - Global delete button
    - Component pins
    - Wire connections between components
    - Enhanced component placement and management
    - Modular architecture with separate files
    """

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    status_updated = Signal(str)

    def __init__(self, parent=None, parent_controller=None, rdb_manager=None):
        super().__init__(parent)
        self.setObjectName("VisualBCFManager")
        self.setWindowTitle("Visual BCF Manager - Phase 2.5")

        # Store references
        self.parent_controller = parent_controller
        self.rdb_manager = rdb_manager

        # Component placement state
        self.placement_mode = False
        self.selected_component_type = "chip"

        # Initialize properties
        self.scene = None
        self.view = None
        self.vbcf_info_tab_widget = None
        self.device_list_controller = None
        self.io_connect_controller = None
        self.floating_toolbar = None

        # Setup UI components
        self._setup_ui()
        self._setup_toolbar()
        self._connect_signals()

        # Initial status
        self.status_updated.emit("Visual BCF Manager initialized - Phase 2.5")

    def _setup_ui(self):
        """Initialize the UI layout"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for central widget
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Add info label
        info_label = QLabel("Visual BCF Manager - Phase 2.5: Core Functionality Fixes")
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        layout.addWidget(info_label)

        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left side: Graphics view
        self._setup_graphics_view()
        splitter.addWidget(self.view)

        # Right side: Tab widget
        self._setup_tab_widget()
        splitter.addWidget(self.vbcf_info_tab_widget)

        # Set splitter proportions (70% graphics view, 30% tabs)
        splitter.setStretchFactor(0, 7)  # Graphics view
        splitter.setStretchFactor(1, 3)  # Tab widget

        # Status bar
        self._setup_status_bar()

    def _setup_graphics_view(self):
        """Setup the graphics scene and view"""
        # Create custom graphics scene and view
        self.scene = ComponentScene()
        self.scene.setParent(self)  # Set parent for access to placement_mode
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)

        self.view = CustomGraphicsView(self.scene)
        self.view.setObjectName("BCFGraphicsView")
        self.view.setMinimumSize(600, 400)

    def _setup_tab_widget(self):
        """Setup the tab widget with Device Settings and IO Connect tabs"""
        self.vbcf_info_tab_widget = QTabWidget()
        self.vbcf_info_tab_widget.setObjectName("vbcf_info_tab_widget")

        # Set tab position to west (left side)
        self.vbcf_info_tab_widget.setTabPosition(QTabWidget.West)

        # Create Device Settings tab using new MVC controller
        if DeviceSettingsController:
            try:
                # Create controller with proper RDB manager
                self.device_settings_controller = DeviceSettingsController(
                    rdb_manager=self.rdb_manager,
                    parent=self
                )
                print("created device settings controller", self.device_settings_controller)
                # For backward compatibility, also store as device_list_controller
                self.device_list_controller = self.device_settings_controller

                # Get the view widget from controller
                device_widget = self.device_settings_controller.view
                if device_widget:
                    self.vbcf_info_tab_widget.addTab(device_widget, "Device Settings")
                    print("✓ Device Settings tab added successfully")
                else:
                    print("✗ Failed to get Device Settings widget")
            except Exception as e:
                print(f"✗ Failed to create Device Settings controller: {e}")
                self.device_settings_controller = None
                self.device_list_controller = None
        else:
            print("✗ DeviceSettingsController not available")
            self.device_settings_controller = None
            self.device_list_controller = None

        # Create IO Connect tab using new MVC controller
        if IOConnectController:
            try:
                # Create controller with proper RDB manager
                self.io_connect_controller = IOConnectController(
                    rdb_manager=self.rdb_manager,
                    parent=self
                )

                # Get the view widget from controller
                io_widget = self.io_connect_controller.get_widget()
                if io_widget:
                    self.vbcf_info_tab_widget.addTab(io_widget, "IO Connect")
                    print("✓ IO Connect tab added successfully")
                else:
                    print("✗ Failed to get IO Connect widget")
            except Exception as e:
                print(f"✗ Failed to create IO Connect controller: {e}")
                self.io_connect_controller = None
        else:
            print("✗ IOConnectController not available")
            self.io_connect_controller = None

        # Set minimum size for tab widget
        self.vbcf_info_tab_widget.setMinimumWidth(350)

        # Initialize controllers if they were created successfully
        try:
            if self.device_settings_controller:
                # Initialize with default revision
                self.device_settings_controller.init_tab(revision=1)
                print("✓ Device Settings controller initialized")
        except Exception as e:
            print(f"✗ Failed to initialize Device Settings controller: {e}")

        try:
            if self.io_connect_controller:
                # Initialize with default revision
                self.io_connect_controller.init_tab(revision=1)
                print("✓ IO Connect controller initialized")
        except Exception as e:
            print(f"✗ Failed to initialize IO Connect controller: {e}")

    def _setup_status_bar(self):
        """Setup the status bar"""
        self.status_label = QLabel("Ready - Click 'Add Component' then click on scene")
        self.status_label.setStyleSheet("padding: 5px; background: #ecf0f1; border-top: 1px solid #bdc3c7;")
        self.statusBar().addWidget(self.status_label)

    def _setup_toolbar(self):
        """Create floating toolbar with component placement functionality"""
        print("🔧 VisualBCFManager: Setting up floating toolbar...")
        # Create floating toolbar using working QPalette implementation
        central_widget = self.centralWidget()
        self.floating_toolbar = FloatingToolbarPalette(parent=central_widget)
        print(f"🔧 VisualBCFManager: Created floating toolbar: {self.floating_toolbar}")

        # Show the floating toolbar first
        print("🔧 VisualBCFManager: Calling show() on floating toolbar...")
        self.floating_toolbar.show()
        print(f"🔧 VisualBCFManager: Toolbar visibility after show: {self.floating_toolbar.isVisible()}")

        # Position the toolbar at top-center of the graphics view
        self._position_toolbar_on_graphics_view()
        print(f"🔧 VisualBCFManager: Positioned toolbar at: {self.floating_toolbar.pos()}")

        # Force layout update and visibility
        self.floating_toolbar.adjustSize()  # Adjust to content size
        self.floating_toolbar.show()  # Ensure visible
        self.floating_toolbar.raise_()  # Bring to front
        self.floating_toolbar.activateWindow()  # Activate

        print(f"🔧 VisualBCFManager: Final toolbar visibility: {self.floating_toolbar.isVisible()}")
        print(f"🔧 VisualBCFManager: Toolbar size: {self.floating_toolbar.size()}")
        print(f"🔧 VisualBCFManager: Toolbar geometry: {self.floating_toolbar.geometry()}")

        # Connect toolbar signals to existing methods
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

        # Get the central widget to position within it
        central_widget = self.centralWidget()
        if not central_widget:
            return

        # Get central widget size
        central_size = central_widget.size()

        # Get the actual toolbar size after adjustSize
        self.floating_toolbar.adjustSize()
        actual_toolbar_size = self.floating_toolbar.size()

        # Position it more towards the graphics view area (left side of splitter)
        graphics_area_width = int(central_size.width() * 0.7)  # 70% for graphics view
        x = max(10, (graphics_area_width - actual_toolbar_size.width()) // 2)
        y = 50  # 50px from top to account for the info label

        print(f"🔧 VisualBCFManager: Central widget size: {central_size}")
        print(f"🔧 VisualBCFManager: Actual toolbar size: {actual_toolbar_size}")
        print(f"🔧 VisualBCFManager: Graphics area width: {graphics_area_width}")
        print(f"🔧 VisualBCFManager: Calculated toolbar position: ({x}, {y})")

        # Position the toolbar
        self.floating_toolbar.move(x, y)


    def _connect_signals(self):
        """Connect internal signals"""
        self.status_updated.connect(self._update_status_display)
        self.error_occurred.connect(self._handle_error)

        # Connect scene signals
        if self.scene:
            self.scene.component_added.connect(self._on_component_added)
            self.scene.component_removed.connect(self._on_component_removed)
            self.scene.wire_added.connect(self._on_wire_added)

        # Connect tab controller signals (using new MVC structure)
        if self.device_list_controller:
            # Connect to MVC controller signals
            if hasattr(self.device_list_controller, 'gui_event'):
                self.device_list_controller.gui_event.connect(self._on_controller_gui_event)
            # Try to connect legacy signals if available
            elif hasattr(self.device_list_controller, 'device_selected'):
                self.device_list_controller.device_selected.connect(self._on_device_selected)
                self.device_list_controller.device_modified.connect(self._on_device_modified)

        if self.io_connect_controller:
            # Connect to MVC controller signals
            if hasattr(self.io_connect_controller, 'gui_event'):
                self.io_connect_controller.gui_event.connect(self._on_controller_gui_event)
            # Try to connect legacy signals if available
            elif hasattr(self.io_connect_controller, 'connection_selected'):
                self.io_connect_controller.connection_selected.connect(self._on_connection_selected)
                self.io_connect_controller.connection_modified.connect(self._on_connection_modified)

    def _update_status_display(self, message: str):
        """Update status label"""
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Status: {message}")

    def _handle_error(self, error_message: str):
        """Handle error messages"""
        self.status_label.setText(f"Error: {error_message}")
        print(f"VisualBCFManager Error: {error_message}")

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

    def _on_component_added(self, name: str, component_type: str, position: QPointF):
        """Handle component added to scene"""
        self.data_changed.emit({
            "action": "component_added",
            "name": name,
            "type": component_type,
            "position": [position.x(), position.y()]
        })

        count = len(self.scene.components)
        self.status_updated.emit(f"Added {name} at ({position.x():.1f}, {position.y():.1f}) - Total: {count}")

    def _on_component_removed(self, name: str):
        """Handle component removed from scene"""
        self.data_changed.emit({
            "action": "component_removed",
            "name": name
        })

        count = len(self.scene.components)
        self.status_updated.emit(f"Removed {name} - Total components: {count}")

    def _on_wire_added(self, start_component: str, start_pin: str, end_component: str, end_pin: str):
        """Handle wire added to scene"""
        self.data_changed.emit({
            "action": "wire_added",
            "start_component": start_component,
            "start_pin": start_pin,
            "end_component": end_component,
            "end_pin": end_pin
        })

        wire_count = len(self.scene.wires)
        self.status_updated.emit(f"Wire connected: {start_component}.{start_pin} → {end_component}.{end_pin} - Total wires: {wire_count}")

    def _on_device_selected(self, device_name: str):
        """Handle device selected in Device Settings tab"""
        self.status_updated.emit(f"Device selected: {device_name}")

    def _on_device_modified(self, device_data: dict):
        """Handle device modified in Device Settings tab"""
        if device_data.get('action') == 'deleted':
            device_name = device_data.get('device', {}).get('name', 'Unknown')
            self.status_updated.emit(f"Device deleted: {device_name}")
        else:
            device_name = device_data.get('name', 'Unknown')
            self.status_updated.emit(f"Device modified: {device_name}")

        # Refresh IO Connect tab to reflect changes
        if self.io_connect_controller:
            self.io_connect_controller.refresh()

    def _on_connection_selected(self, connection_id: str):
        """Handle connection selected in IO Connect tab"""
        self.status_updated.emit(f"Connection selected: {connection_id}")

    def _on_connection_modified(self, connection_data: dict):
        """Handle connection modified in IO Connect tab"""
        if connection_data.get('action') == 'deleted':
            conn_id = connection_data.get('connection', {}).get('id', 'Unknown')
            self.status_updated.emit(f"Connection deleted: {conn_id}")
        else:
            conn_id = connection_data.get('id', 'Unknown')
            self.status_updated.emit(f"Connection modified: {conn_id}")

    def _on_controller_gui_event(self, event_name: str, event_data: dict):
        """Handle GUI events from MVC controllers."""
        # Handle device-related events
        if event_name == "device_selected":
            device_name = event_data.get('device_name', 'Unknown')
            self._on_device_selected(device_name)
        elif event_name == "device_modified":
            self._on_device_modified(event_data)
        # Handle connection-related events
        elif event_name == "connection_selected":
            connection_id = event_data.get('connection_id', 'Unknown')
            self._on_connection_selected(connection_id)
        elif event_name == "connection_modified":
            self._on_connection_modified(event_data)
        # Handle other events
        elif event_name in ["tab_initialized", "refresh_completed", "controller_refreshed"]:
            # Log these events for debugging
            controller = event_data.get('controller', 'Unknown')
            self.status_updated.emit(f"Controller event: {event_name} from {controller}")
        elif event_name == "auto_connect_completed":
            connections_created = event_data.get('connections_created', 0)
            self.status_updated.emit(f"Auto-connect completed: {connections_created} connections created")
        elif event_name == "devices_updated":
            device_count = event_data.get('device_count', 0)
            self.status_updated.emit(f"Devices updated: {device_count} devices available")

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
        if self.scene and self.scene.components:
            count = len(self.scene.components)
            self.scene.clear()
            self.scene.components = []
            self.scene.component_counter = 1
            self.status_updated.emit(f"Scene cleared - Removed {count} components")
        else:
            self.status_updated.emit("Scene already empty")

    def _on_zoom_fit(self):
        """Fit scene content in view"""
        if self.view and self.scene:
            if self.scene.items():
                self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
                self.status_updated.emit("View fitted to components")
            else:
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
                self.status_updated.emit("View fitted to scene")

    def _show_phase_info(self):
        """Show information about current phase"""
        component_count = len(self.scene.components) if self.scene else 0
        wire_count = len(self.scene.wires) if self.scene else 0

        info_text = f"""
        <h3>Phase 2.5: Core Functionality Fixes</h3>
        <p><b>Development Period:</b> Week 5</p>
        <p><b>Status:</b> ✅ Completed</p>

        <h4>Current Scene:</h4>
        <ul>
        <li><b>Components:</b> {component_count}</li>
        <li><b>Wires:</b> {wire_count}</li>
        <li><b>Mode:</b> {'Placement' if self.placement_mode else 'Selection'}</li>
        <li><b>Selected Type:</b> {self.selected_component_type if self.placement_mode else 'N/A'}</li>
        </ul>

        <h4>New Features in Phase 2.5:</h4>
        <ul>
        <li>✅ Zoom with Ctrl+Scroll wheel (0.1x to 10.0x)</li>
        <li>✅ Global delete button for selected components</li>
        <li>✅ Component pins with proper names and types</li>
        <li>✅ Wire connections between component pins</li>
        <li>✅ Modular code architecture</li>
        <li>✅ Enhanced component placement system</li>
        <li>✅ Improved status updates and feedback</li>
        </ul>

        <h4>Component Types:</h4>
        <ul>
        <li><b>Chips:</b> 24 pins (6 per side) - inputs, outputs, power, ground</li>
        <li><b>Resistors:</b> 2 pins (terminals A and B)</li>
        <li><b>Capacitors:</b> 2 pins (positive and negative)</li>
        </ul>

        <h4>How to Use:</h4>
        <ol>
        <li>Click component type button (Chip/Resistor/Capacitor)</li>
        <li>Click on scene to place components</li>
        <li>Click on component pins to start drawing wires</li>
        <li>Hold Ctrl + scroll wheel to zoom</li>
        <li>Select components and use Delete button or Del key</li>
        <li>Use Select Mode to move components around</li>
        </ol>
        """

        QMessageBox.information(self, "Development Phase Information", info_text)

    # Public interface methods
    def get_scene_data(self) -> Dict[str, Any]:
        """Get current scene data"""
        components_data = []
        wires_data = []

        if self.scene:
            for component in self.scene.components:
                components_data.append({
                    "name": component.name,
                    "type": component.component_type,
                    "position": [component.x(), component.y()],
                    "size": [component.rect().width(), component.rect().height()]
                })

            for wire in self.scene.wires:
                if wire.end_pin:  # Only include completed wires
                    wires_data.append({
                        "start_component": wire.start_pin.parent_component.name,
                        "start_pin": wire.start_pin.pin_id,
                        "end_component": wire.end_pin.parent_component.name,
                        "end_pin": wire.end_pin.pin_id
                    })

        return {
            "phase": "2.5",
            "components": components_data,
            "wires": wires_data,
            "scene_rect": [self.scene.sceneRect().x(), self.scene.sceneRect().y(),
                          self.scene.sceneRect().width(), self.scene.sceneRect().height()],
            "component_count": len(components_data),
            "wire_count": len(wires_data)
        }

    def export_data(self) -> Dict[str, Any]:
        """Export scene data"""
        return self.get_scene_data()

    def keyPressEvent(self, event):
        """Handle keyboard events"""
        if event.key() == Qt.Key.Key_Delete:
            # Delete selected components on Delete key press
            self._on_delete_selected()
        else:
            # Pass other key events to parent
            super().keyPressEvent(event)


# Test function for standalone running
def main():
    """Test the Phase 2.5 Visual BCF Manager"""
    # Use centralized path setup from BCF package
    import apps.RBM5.BCF  # This automatically sets up the path
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("SDTS - Visual BCF Manager (Phase 2.5)")
    main_window.setGeometry(100, 100, 1200, 800)

    # Create and set Visual BCF Manager
    bcf_manager = VisualBCFManager()
    main_window.setCentralWidget(bcf_manager)

    # Show window
    main_window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
