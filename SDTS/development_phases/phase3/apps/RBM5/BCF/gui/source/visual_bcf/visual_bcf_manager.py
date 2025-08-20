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
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController


class VisualBCFManager(QMainWindow):
    """
    Visual BCF Manager - Phase 3 Implementation
    
    Minimal orchestrator that creates Model and Controller only.
    The Controller owns the View/Scene and handles all UI and business logic.
    
    Architecture:
    - Manager: Creates Model and Controller only
    - Controller: Owns View/Scene, handles UI and business logic  
    - Model: Handles all data operations and database communication
    """
    
    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    status_updated = Signal(str)
    
    def __init__(self, parent=None, parent_controller=None, rdb_manager=None):
        super().__init__(parent)
        self.setObjectName("VisualBCFManager")
        self.setWindowTitle("Visual BCF Manager - Phase 3 (Controller-centric MVC)")
        
        # Store references
        self.parent_controller = parent_controller
        self.rdb_manager = rdb_manager
        
        # Initialize properties - controller will create these
        self.vbcf_info_tab_widget = None
        self.device_list_controller = None
        self.io_connect_controller = None
        
        # MVC components - only model and controller
        self.data_model = None
        self.visual_bcf_controller = None
        
        # Setup MVC architecture - this is now the main responsibility
        self._setup_mvc_components()
        
        # Setup minimal UI layout with controller's view
        self._setup_ui_layout()
        
        # Setup tab widget  
        self._setup_tab_widget()
        
        # Connect controller signals
        self._connect_controller_signals()
        
        # Setup status bar
        self._setup_status_bar()
        
        # Initial status
        self.status_updated.emit("Visual BCF Manager initialized - Phase 3 (Controller-centric MVC)")
        
    def _setup_mvc_components(self):
        """Setup MVC components: Model and Controller (Controller creates View/Scene)"""
        try:
            if self.rdb_manager:
                # Create the data model first
                self.data_model = VisualBCFDataModel(self.rdb_manager)
                print("✓ VisualBCFDataModel created successfully")
                
                # Create controller immediately - it will create its own view/scene
                self.visual_bcf_controller = VisualBCFController(parent_widget=self, data_model=self.data_model)
                print("✓ VisualBCFController created successfully with own view/scene")
                
            else:
                print("⚠️ No RDB manager available - MVC components not initialized")
                
        except Exception as e:
            print(f"❌ Error setting up MVC components: {e}")
            self.data_model = None
            self.visual_bcf_controller = None
    
    def _finalize_mvc_setup(self):
        """Finalize MVC setup by creating the controller after view is available"""
        try:
            if self.data_model and self.view:
                # Create the VisualBCF controller now that view is available
                self.visual_bcf_controller = VisualBCFController(self.view, self.data_model)
                print("✓ VisualBCFController created successfully")
                
                # Connect controller signals if needed
                self._connect_controller_signals()
                
            else:
                print("⚠️ Cannot create controller - missing data model or view")
                self.visual_bcf_controller = None
                
        except Exception as e:
            print(f"❌ Error creating VisualBCFController: {e}")
            self.visual_bcf_controller = None
    
    def _connect_controller_signals(self):
        """Connect controller signals to manager"""
        if self.visual_bcf_controller:
            try:
                # Connect controller operation signals to status updates
                self.visual_bcf_controller.operation_completed.connect(
                    lambda op_type, message: self.status_updated.emit(f"Controller: {message}")
                )
                self.visual_bcf_controller.error_occurred.connect(
                    lambda error: self.error_occurred.emit(f"Controller Error: {error}")
                )
                print("✓ Controller signals connected to manager")
                
            except Exception as e:
                print(f"⚠️ Error connecting controller signals: {e}")
    
    def _setup_ui_layout(self):
        """Setup minimal UI layout using controller's view"""
        if not self.visual_bcf_controller:
            print("⚠️ No controller available - cannot setup UI layout")
            return
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout for central widget
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Add info label
        info_label = QLabel("Visual BCF Manager - Phase 3: Controller-centric MVC Architecture")
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        layout.addWidget(info_label)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side: Graphics view from controller
        controller_view = self.visual_bcf_controller.get_view()
        if controller_view:
            splitter.addWidget(controller_view)
            print("✓ Controller's view added to layout")
        else:
            print("⚠️ No view available from controller")
        
        # Right side: Tab widget (will be setup after this)
        # Placeholder for now - will be added by _setup_tab_widget
        # Set splitter proportions (70% graphics view, 30% tabs)
        splitter.setStretchFactor(0, 7)  # Graphics view
        splitter.setStretchFactor(1, 3)  # Tab widget
        
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
        
        # Add tab widget to the splitter (get splitter from central widget)
        central_widget = self.centralWidget()
        if central_widget:
            layout = central_widget.layout()
            if layout:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and isinstance(item.widget(), QSplitter):
                        splitter = item.widget()
                        splitter.addWidget(self.vbcf_info_tab_widget)
                        print("✓ Tab widget added to splitter")
                        break
        
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
        
    # Toolbar setup is now handled by the controller
        
        
    def _connect_tab_controller_signals(self):
        """Connect tab controller signals"""
        self.status_updated.connect(self._update_status_display)
        self.error_occurred.connect(self._handle_error)
            
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
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Error: {error_message}")
        print(f"VisualBCFManager Error: {error_message}")
            
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
        
    # Component/scene action methods removed - controller handles these directly
        
    # Public interface methods - delegate to controller
    def get_scene_data(self) -> Dict[str, Any]:
        """Get current scene data from controller"""
        if self.visual_bcf_controller:
            return self.visual_bcf_controller.get_statistics()
        return {"phase": "3", "components": [], "connections": []}
        
    def export_data(self) -> Dict[str, Any]:
        """Export scene data via controller"""
        return self.get_scene_data()


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
