"""
Visual BCF Manager - Phase 2: Component Placement
Builds on Phase 1 by adding basic component placement functionality.
"""

import sys
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
                              QGraphicsScene, QPushButton, QLabel, QMessageBox,
                              QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
                              QInputDialog, QMenu)
from PySide6.QtCore import Signal, Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from typing import Dict, Any, List

class BasicComponent(QGraphicsRectItem):
    """Basic component that can be placed on the scene"""

    def __init__(self, name: str, component_type: str, width: float = 100, height: float = 60):
        super().__init__(0, 0, width, height)

        # Component properties
        self.name = name
        self.component_type = component_type
        self.is_selected = False

        # Visual properties
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        # Set appearance based on type
        self._setup_appearance()

        # Add text label
        self.text_item = QGraphicsTextItem(name, self)
        self.text_item.setPos(10, height//2 - 10)
        self.text_item.setFont(QFont("Arial", 8))

    def _setup_appearance(self):
        """Set visual appearance based on component type"""
        if self.component_type == "chip":
            self.setBrush(QBrush(QColor(100, 150, 200)))  # Blue
            self.setPen(QPen(QColor(50, 100, 150), 2))
        elif self.component_type == "resistor":
            self.setBrush(QBrush(QColor(200, 150, 100)))  # Brown
            self.setPen(QPen(QColor(150, 100, 50), 2))
        elif self.component_type == "capacitor":
            self.setBrush(QBrush(QColor(150, 200, 100)))  # Green
            self.setPen(QPen(QColor(100, 150, 50), 2))
        else:
            self.setBrush(QBrush(QColor(180, 180, 180)))  # Gray
            self.setPen(QPen(QColor(120, 120, 120), 2))

    def contextMenuEvent(self, event):
        """Show context menu on right click"""
        menu = QMenu()

        # Add properties action
        properties_action = menu.addAction("Properties")
        delete_action = menu.addAction("Delete")

        action = menu.exec(event.screenPos())

        if action == properties_action:
            self._show_properties()
        elif action == delete_action:
            self._delete_component()

    def _show_properties(self):
        """Show component properties dialog"""
        QMessageBox.information(
            None,
            f"{self.name} Properties",
            f"Name: {self.name}\n"
            f"Type: {self.component_type}\n"
            f"Position: ({self.x():.1f}, {self.y():.1f})\n"
            f"Size: {self.rect().width()}x{self.rect().height()}"
        )

    def _delete_component(self):
        """Delete this component"""
        if hasattr(self.scene(), 'remove_component'):
            self.scene().remove_component(self)
        else:
            self.scene().removeItem(self)


class ComponentScene(QGraphicsScene):
    """Custom scene that handles component placement"""

    component_added = Signal(str, str, QPointF)  # name, type, position
    component_removed = Signal(str)  # name

    def __init__(self):
        super().__init__()
        self.components = []
        self.component_counter = 1

    def mousePressEvent(self, event):
        """Handle mouse press for component placement mode"""
        if hasattr(self.parent(), 'placement_mode') and self.parent().placement_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                self.add_component_at_position(event.scenePos())

        super().mousePressEvent(event)

    def add_component_at_position(self, position: QPointF):
        """Add component at the specified position"""
        if hasattr(self.parent(), 'selected_component_type'):
            component_type = self.parent().selected_component_type
            name = f"{component_type.title()}{self.component_counter}"

            component = BasicComponent(name, component_type)
            component.setPos(position.x() - component.rect().width()/2,
                           position.y() - component.rect().height()/2)

            self.addItem(component)
            self.components.append(component)
            self.component_counter += 1

            self.component_added.emit(name, component_type, position)

    def remove_component(self, component: BasicComponent):
        """Remove component from scene"""
        if component in self.components:
            self.components.remove(component)
        self.removeItem(component)
        self.component_removed.emit(component.name)


class VisualBCFManager(QWidget):
    """
    Visual BCF Manager - Phase 2 Implementation

    This phase adds component placement functionality:
    - Click-to-place components
    - Multiple component types (chip, resistor, capacitor)
    - Component properties and deletion
    - Selection and movement
    - Basic scene management
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

        # Initial status
        self.status_updated.emit("Visual BCF Manager initialized - Phase 2")

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

        self.view = QGraphicsView(self.scene)
        self.view.setObjectName("BCFGraphicsView")
        self.view.setMinimumSize(800, 600)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # Add info label
        info_label = QLabel("Visual BCF Manager - Phase 2: Component Placement")
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
        from PySide6.QtCore import Qt
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

        info_text = f"""
        <h3>Phase 2: Component Placement</h3>
        <p><b>Development Period:</b> Week 3-4</p>
        <p><b>Status:</b> ✅ Completed</p>

        <h4>Current Scene:</h4>
        <ul>
        <li><b>Components:</b> {component_count}</li>
        <li><b>Mode:</b> {'Placement' if self.placement_mode else 'Selection'}</li>
        <li><b>Selected Type:</b> {self.selected_component_type if self.placement_mode else 'N/A'}</li>
        </ul>

        <h4>Features Implemented:</h4>
        <ul>
        <li>✅ Click-to-place component functionality</li>
        <li>✅ Multiple component types (chip, resistor, capacitor)</li>
        <li>✅ Component selection and movement</li>
        <li>✅ Right-click context menus</li>
        <li>✅ Component properties dialog</li>
        <li>✅ Component deletion</li>
        <li>✅ Mode switching (placement/selection)</li>
        <li>✅ Visual feedback and status updates</li>
        </ul>

        <h4>How to Use:</h4>
        <ol>
        <li>Click component type button (Chip/Resistor/Capacitor)</li>
        <li>Click on scene to place components</li>
        <li>Right-click components for properties/delete</li>
        <li>Use Select Mode to move components</li>
        <li>Clear Scene to remove all components</li>
        </ol>

        <h4>Next Phase Preview:</h4>
        <p><b>Phase 3:</b> Data Management</p>
        <ul>
        <li>🔄 Save/Load scene data</li>
        <li>🔄 Component properties editor</li>
        <li>🔄 Undo/Redo functionality</li>
        <li>🔄 Export capabilities</li>
        </ul>
        """

        QMessageBox.information(self, "Development Phase Information", info_text)

    # Public interface methods
    def get_scene_data(self) -> Dict[str, Any]:
        """Get current scene data"""
        components_data = []
        if self.scene:
            for component in self.scene.components:
                components_data.append({
                    "name": component.name,
                    "type": component.component_type,
                    "position": [component.x(), component.y()],
                    "size": [component.rect().width(), component.rect().height()]
                })

        return {
            "phase": "2",
            "components": components_data,
            "connections": [],
            "scene_rect": [self.scene.sceneRect().x(), self.scene.sceneRect().y(),
                          self.scene.sceneRect().width(), self.scene.sceneRect().height()],
            "component_count": len(components_data)
        }

    def load_scene_data(self, data: Dict[str, Any]):
        """Load scene data"""
        if data.get("phase") != "2":
            self.error_occurred.emit("Data is not from Phase 2")
            return

        # Clear current scene
        self.scene.clear()
        self.scene.components = []

        # Load components
        for comp_data in data.get("components", []):
            component = BasicComponent(
                comp_data["name"],
                comp_data["type"],
                comp_data["size"][0],
                comp_data["size"][1]
            )
            component.setPos(comp_data["position"][0], comp_data["position"][1])
            self.scene.addItem(component)
            self.scene.components.append(component)

        self.status_updated.emit(f"Loaded {len(data.get('components', []))} components")

    def export_data(self) -> Dict[str, Any]:
        """Export scene data"""
        return self.get_scene_data()


# Test function for standalone running
def main():
    """Test the Phase 2 Visual BCF Manager"""
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("SDTS - Visual BCF Manager (Phase 2)")
    main_window.setGeometry(100, 100, 1200, 800)

    # Create and set Visual BCF Manager
    bcf_manager = VisualBCFManager()
    main_window.setCentralWidget(bcf_manager)

    # Show window
    main_window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
