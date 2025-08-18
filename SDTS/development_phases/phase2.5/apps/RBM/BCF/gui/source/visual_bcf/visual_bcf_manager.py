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
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox)
from PySide6.QtCore import Signal, Qt, QPointF
from typing import Dict, Any, List

# Import from our new modular structure
try:
    # Try relative imports first (when imported as a package)
    from .scene import ComponentScene
    from .view import CustomGraphicsView
    from .artifacts import ComponentWithPins, ComponentPin, Wire
except ImportError:
    # Fallback to direct imports (when running directly)
    from scene import ComponentScene
    from view import CustomGraphicsView
    from artifacts import ComponentWithPins, ComponentPin, Wire


class VisualBCFManager(QWidget):
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
        
        # Store references
        self.parent_controller = parent_controller
        self.rdb_manager = rdb_manager
        
        # Component placement state
        self.placement_mode = False
        self.selected_component_type = "chip"
        
        # Initialize properties
        self.scene = None
        self.view = None
        
        # Setup UI components
        self._setup_ui()
        self._setup_toolbar()
        self._connect_signals()
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Initial status
        self.status_updated.emit("Visual BCF Manager initialized - Phase 2.5")
        
    def _setup_ui(self):
        """Initialize the UI layout"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create custom graphics scene and view
        self.scene = ComponentScene()
        self.scene.setParent(self)  # Set parent for access to placement_mode
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        
        self.view = CustomGraphicsView(self.scene)
        self.view.setObjectName("BCFGraphicsView")
        self.view.setMinimumSize(800, 600)
        
        # Add info label
        info_label = QLabel("Visual BCF Manager - Phase 2.5: Core Functionality Fixes")
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        
        # Add components to layout
        layout.addWidget(info_label)
        layout.addWidget(self.view)
        
        # Status bar equivalent
        self.status_label = QLabel("Ready - Click 'Add Component' then click on scene")
        self.status_label.setStyleSheet("padding: 5px; background: #ecf0f1; border-top: 1px solid #bdc3c7;")
        layout.addWidget(self.status_label)
        
    def _setup_toolbar(self):
        """Create toolbar with component placement functionality"""
        # Create toolbar layout
        toolbar_layout = QHBoxLayout()
        
        # Component type buttons
        self.btn_add_chip = QPushButton("Add Chip")
        self.btn_add_chip.setToolTip("Place chip components on scene")
        self.btn_add_chip.clicked.connect(lambda: self._set_component_type("chip"))
        
        self.btn_add_resistor = QPushButton("Add Resistor")
        self.btn_add_resistor.setToolTip("Place resistor components on scene")
        self.btn_add_resistor.clicked.connect(lambda: self._set_component_type("resistor"))
        
        self.btn_add_capacitor = QPushButton("Add Capacitor")
        self.btn_add_capacitor.setToolTip("Place capacitor components on scene")
        self.btn_add_capacitor.clicked.connect(lambda: self._set_component_type("capacitor"))
        
        # Control buttons
        self.btn_select_mode = QPushButton("Select Mode")
        self.btn_select_mode.setToolTip("Switch to selection mode")
        self.btn_select_mode.clicked.connect(self._set_select_mode)
        
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setToolTip("Delete selected components (or use Del key)")
        self.btn_delete.clicked.connect(self._on_delete_selected)
        
        self.btn_clear = QPushButton("Clear Scene")
        self.btn_clear.setToolTip("Clear all components from scene")
        self.btn_clear.clicked.connect(self._on_clear_scene)
        
        self.btn_zoom_fit = QPushButton("Zoom Fit")
        self.btn_zoom_fit.setToolTip("Fit scene in view")
        self.btn_zoom_fit.clicked.connect(self._on_zoom_fit)
        
        self.btn_info = QPushButton("Phase Info")
        self.btn_info.setToolTip("Show phase information")
        self.btn_info.clicked.connect(self._show_phase_info)
        
        # Add buttons to toolbar
        toolbar_layout.addWidget(self.btn_add_chip)
        toolbar_layout.addWidget(self.btn_add_resistor)
        toolbar_layout.addWidget(self.btn_add_capacitor)
        toolbar_layout.addWidget(self.btn_select_mode)
        toolbar_layout.addWidget(self.btn_delete)
        toolbar_layout.addWidget(self.btn_clear)
        toolbar_layout.addWidget(self.btn_zoom_fit)
        toolbar_layout.addWidget(self.btn_info)
        toolbar_layout.addStretch()  # Push buttons to left
        
        # Insert toolbar at top of main layout
        self.layout().insertLayout(1, toolbar_layout)
        
    def _connect_signals(self):
        """Connect internal signals"""
        self.status_updated.connect(self._update_status_display)
        self.error_occurred.connect(self._handle_error)
        
        # Connect scene signals
        if self.scene:
            self.scene.component_added.connect(self._on_component_added)
            self.scene.component_removed.connect(self._on_component_removed)
            self.scene.wire_added.connect(self._on_wire_added)
        
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
        # Reset all buttons
        buttons = [self.btn_add_chip, self.btn_add_resistor, self.btn_add_capacitor, self.btn_select_mode]
        for btn in buttons:
            btn.setStyleSheet("")
            
        # Highlight active button
        if self.placement_mode:
            if self.selected_component_type == "chip":
                self.btn_add_chip.setStyleSheet("background-color: #4CAF50; color: white;")
            elif self.selected_component_type == "resistor":
                self.btn_add_resistor.setStyleSheet("background-color: #4CAF50; color: white;")
            elif self.selected_component_type == "capacitor":
                self.btn_add_capacitor.setStyleSheet("background-color: #4CAF50; color: white;")
        else:
            self.btn_select_mode.setStyleSheet("background-color: #4CAF50; color: white;")
            
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
