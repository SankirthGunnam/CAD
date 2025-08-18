"""
Visual BCF Manager - Phase 2: Component Placement
Builds on Phase 1 by adding basic component placement functionality.
"""

import sys
import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, 
                              QGraphicsScene, QPushButton, QLabel, QMessageBox,
                              QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
                              QInputDialog, QMenu, QGraphicsItem, QGraphicsLineItem)
from PySide6.QtCore import Signal, Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from typing import Dict, Any, List, Optional

class ComponentPin(QGraphicsEllipseItem):
    """Enhanced connection pin for components with proper names and smart positioning"""
    
    def __init__(self, pin_id: str, pin_name: str, pin_type: str, parent_component, edge: str = "left"):
        super().__init__(-4, -4, 8, 8)  # Pin size (8x8)
        self.pin_id = pin_id
        self.pin_name = pin_name  # Human-readable name like "VDD", "GND", "DATA_IN", etc.
        self.pin_type = pin_type  # 'input', 'output', 'power', 'gnd', 'terminal', 'positive', 'negative', 'io'
        self.parent_component = parent_component
        self.edge = edge  # Which edge: 'left', 'right', 'top', 'bottom'
        self.is_hovered = False
        
        # Visual appearance based on pin type
        self._setup_pin_appearance()
        
        # Add pin name label
        self._create_pin_label()
        
        # Enable hover and click events
        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(10)  # Pins on top
        
    def _setup_pin_appearance(self):
        """Set pin appearance based on type"""
        if self.pin_type == 'input':
            self.setBrush(QBrush(QColor(100, 200, 100)))  # Green for inputs
            self.setPen(QPen(QColor(50, 150, 50), 2))
        elif self.pin_type == 'output':
            self.setBrush(QBrush(QColor(200, 100, 100)))  # Red for outputs
            self.setPen(QPen(QColor(150, 50, 50), 2))
        elif self.pin_type == 'power':
            self.setBrush(QBrush(QColor(255, 200, 0)))    # Yellow for power
            self.setPen(QPen(QColor(200, 150, 0), 2))
        elif self.pin_type == 'gnd':
            self.setBrush(QBrush(QColor(100, 100, 100)))  # Gray for ground
            self.setPen(QPen(QColor(50, 50, 50), 2))
        else:  # terminal, positive, negative
            self.setBrush(QBrush(QColor(200, 200, 200)))  # Light gray for terminals
            self.setPen(QPen(QColor(100, 100, 100), 2))
        
    def get_connection_point(self) -> QPointF:
        """Get the center point for connections"""
        return self.scenePos() + QPointF(4, 4)  # Center of the pin
    
    def hoverEnterEvent(self, event):
        """Handle hover enter"""
        self.is_hovered = True
        # Highlight on hover
        current_brush = self.brush()
        highlighted_color = current_brush.color().lighter(150)
        self.setBrush(QBrush(highlighted_color))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle hover leave"""
        self.is_hovered = False
        # Restore original appearance
        self._setup_pin_appearance()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for wire connections"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'start_wire_from_pin'):
                scene.start_wire_from_pin(self)
                event.accept()  # Consume the event
                return
        super().mousePressEvent(event)
        
    def _create_pin_label(self):
        """Create pin name label with small font to prevent overlapping"""
        self.pin_label = QGraphicsTextItem(self.pin_name, self)
        self.pin_label.setFont(QFont("Arial", 4))  # Much smaller font
        self.pin_label.setDefaultTextColor(QColor(80, 80, 80))
        
        # Position label based on edge with better spacing
        text_rect = self.pin_label.boundingRect()
        if self.edge == "left":
            self.pin_label.setPos(-text_rect.width() - 8, -text_rect.height()/2)
        elif self.edge == "right":
            self.pin_label.setPos(12, -text_rect.height()/2)
        elif self.edge == "top":
            self.pin_label.setPos(-text_rect.width()/2, -text_rect.height() - 6)
        elif self.edge == "bottom":
            self.pin_label.setPos(-text_rect.width()/2, 10)
        
        self.pin_label.setZValue(9)  # Labels below pins but above components


class ComponentWithPins(QGraphicsRectItem):
    """Enhanced component with visible pins for connections"""
    
    def __init__(self, name: str, component_type: str, width: float = 100, height: float = 60):
        super().__init__(0, 0, width, height)
        
        # Component properties
        self.name = name
        self.component_type = component_type
        self.is_selected = False
        self.pins = []  # List of ComponentPin objects
        self.connected_wires = []  # List of wires connected to this component
        
        # Visual properties
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        
        # Set appearance and create pins based on type
        self._setup_appearance()
        self._create_pins()
        
        # Add centered text label
        self.text_item = QGraphicsTextItem(name, self)
        self.text_item.setFont(QFont("Arial", 8))
        # Center the text properly
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(
            (width - text_rect.width()) / 2,
            (height - text_rect.height()) / 2
        )
        
    def _create_pins(self):
        """Create pins based on component type with comprehensive layouts"""
        width = self.rect().width()
        height = self.rect().height()
        pin_radius = 4  # Pin radius for centering calculations
        
        if self.component_type == "chip":
            # Comprehensive chip: 6 pins on each side (24 total)
            side_pins = 6
            top_bottom_pins = 6
            
            pin_spacing_vertical = height / (side_pins + 1)  # Vertical spacing for left/right pins
            pin_spacing_horizontal = width / (top_bottom_pins + 1)  # Horizontal spacing for top/bottom pins
            
            # Left side pins (inputs) - perfectly centered on left edge
            input_names = ["DATA_IN", "CLK", "RST", "EN", "CS", "WR"]
            for i in range(side_pins):
                pin_name = input_names[i] if i < len(input_names) else f"IN{i+1}"
                pin = ComponentPin(f"L{i+1}", pin_name, "input", self, "left")
                pin.setParentItem(self)
                # Position pin so half extends outside left edge (x=0)
                pin.setPos(-pin_radius, pin_spacing_vertical * (i + 1) - pin_radius)
                self.pins.append(pin)
                
            # Right side pins (outputs) - perfectly centered on right edge
            output_names = ["DATA_OUT", "INT", "RDY", "ACK", "ERR", "STAT"]
            for i in range(side_pins):
                pin_name = output_names[i] if i < len(output_names) else f"OUT{i+1}"
                pin = ComponentPin(f"R{i+1}", pin_name, "output", self, "right")
                pin.setParentItem(self)
                # Position pin so half extends outside right edge (x=width)
                pin.setPos(width - pin_radius, pin_spacing_vertical * (i + 1) - pin_radius)
                self.pins.append(pin)
                
            # Top pins (power/control) - perfectly centered on top edge
            top_names = ["VDD", "VREF", "AVDD", "DVDD", "NC", "TEST"]
            for i in range(top_bottom_pins):
                pin_name = top_names[i] if i < len(top_names) else f"VCC{i+1}"
                pin_type = "power" if "VDD" in pin_name or "V" in pin_name else "io"
                pin = ComponentPin(f"T{i+1}", pin_name, pin_type, self, "top")
                pin.setParentItem(self)
                # Position pin so half extends outside top edge (y=0)
                pin.setPos(pin_spacing_horizontal * (i + 1) - pin_radius, -pin_radius)
                self.pins.append(pin)
                
            # Bottom pins (ground/control) - perfectly centered on bottom edge
            bottom_names = ["GND", "AGND", "DGND", "VSS", "BIAS", "SHDN"]
            for i in range(top_bottom_pins):
                pin_name = bottom_names[i] if i < len(bottom_names) else f"GND{i+1}"
                pin_type = "gnd" if "GND" in pin_name or "VSS" in pin_name else "io"
                pin = ComponentPin(f"B{i+1}", pin_name, pin_type, self, "bottom")
                pin.setParentItem(self)
                # Position pin so half extends outside bottom edge (y=height)
                pin.setPos(pin_spacing_horizontal * (i + 1) - pin_radius, height - pin_radius)
                self.pins.append(pin)
                
        elif self.component_type == "resistor":
            # Resistor: 2 pins (left and right) - centered on edges
            pin1 = ComponentPin("A", "A", "terminal", self, "left")
            pin1.setParentItem(self)
            pin1.setPos(-pin_radius, height/2 - pin_radius)
            self.pins.append(pin1)
            
            pin2 = ComponentPin("B", "B", "terminal", self, "right")
            pin2.setParentItem(self)
            pin2.setPos(width - pin_radius, height/2 - pin_radius)
            self.pins.append(pin2)
            
        elif self.component_type == "capacitor":
            # Capacitor: 2 pins (left and right) - centered on edges
            pin1 = ComponentPin("POS", "+", "positive", self, "left")
            pin1.setParentItem(self)
            pin1.setPos(-pin_radius, height/2 - pin_radius)
            self.pins.append(pin1)
            
            pin2 = ComponentPin("NEG", "-", "negative", self, "right")
            pin2.setParentItem(self)
            pin2.setPos(width - pin_radius, height/2 - pin_radius)
            self.pins.append(pin2)
        
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
            
    def add_wire(self, wire):
        """Add a wire connection to this component"""
        if wire not in self.connected_wires:
            self.connected_wires.append(wire)
            
    def remove_wire(self, wire):
        """Remove a wire connection from this component"""
        if wire in self.connected_wires:
            self.connected_wires.remove(wire)
            
    def update_connected_wires(self):
        """Update all connected wires when component moves"""
        for wire in self.connected_wires:
            wire.update_line()
            
    def itemChange(self, change, value):
        """Handle item changes, particularly position changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Update connected wires when component is about to move
            # Use QTimer.singleShot to defer the update until after the move
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.update_connected_wires)
        return super().itemChange(change, value)


class Wire(QGraphicsLineItem):
    """Wire connection between component pins"""
    
    def __init__(self, start_pin: ComponentPin, end_pin: Optional[ComponentPin] = None):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.is_temporary = end_pin is None
        
        # Visual appearance
        self.setPen(QPen(QColor(0, 0, 0), 2))  # Black wire, 2px width
        self.setZValue(5)  # Wires above components but below pins
        
        # Make wires selectable and deletable
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Set initial line position
        self.update_line()
        
    def update_line(self, temp_end_pos: Optional[QPointF] = None):
        """Update wire line position"""
        start_pos = self.start_pin.get_connection_point()
        
        if self.end_pin:
            # Permanent wire with end pin
            end_pos = self.end_pin.get_connection_point()
            self.setPen(QPen(QColor(0, 0, 0), 2))  # Black for permanent
        elif temp_end_pos:
            # Temporary wire being drawn
            end_pos = temp_end_pos
            self.setPen(QPen(QColor(255, 0, 0), 2))  # Red for temporary
        else:
            return
            
        # Set line from start to end
        self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
    def complete_wire(self, end_pin: ComponentPin) -> bool:
        """Complete the wire connection"""
        if end_pin == self.start_pin:
            return False  # Can't connect to self
            
        self.end_pin = end_pin
        self.is_temporary = False
        self.update_line()
        return True
        
    def contextMenuEvent(self, event):
        """Handle right-click on wire"""
        menu = QMenu()
        delete_action = menu.addAction("Delete Wire")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            scene = self.scene()
            if scene:
                scene.removeItem(self)


class ComponentScene(QGraphicsScene):
    """Custom scene that handles component placement and wire drawing"""
    
    component_added = Signal(str, str, QPointF)  # name, type, position
    component_removed = Signal(str)  # name
    wire_added = Signal(str, str, str, str)  # start_component, start_pin, end_component, end_pin
    
    def __init__(self):
        super().__init__()
        self.components = []
        self.wires = []
        self.component_counter = 1
        self.current_wire = None  # Wire being drawn
        self.mouse_position = QPointF(0, 0)
        
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
            
            component = ComponentWithPins(name, component_type)
            component.setPos(position.x() - component.rect().width()/2, 
                           position.y() - component.rect().height()/2)
            
            self.addItem(component)
            self.components.append(component)
            self.component_counter += 1
            
            self.component_added.emit(name, component_type, position)
            
    def remove_component(self, component: ComponentWithPins):
        """Remove component from scene"""
        if component in self.components:
            self.components.remove(component)
        self.removeItem(component)
        self.component_removed.emit(component.name)
        
    def start_wire_from_pin(self, pin: ComponentPin):
        """Start drawing a wire from the given pin"""
        if self.current_wire:
            # Complete existing wire or cancel it
            self.removeItem(self.current_wire)
            self.current_wire = None
            
        # Create new temporary wire
        self.current_wire = Wire(pin)
        self.addItem(self.current_wire)
        
        # Update status
        parent = self.parent()
        if parent and hasattr(parent, 'status_updated'):
            parent.status_updated.emit(f"Drawing wire from {pin.parent_component.name}.{pin.pin_id} - Click destination pin")
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self.mouse_position = event.scenePos()
        
        # Update temporary wire if drawing
        if self.current_wire and self.current_wire.is_temporary:
            self.current_wire.update_line(self.mouse_position)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.current_wire:
            # Check if released on a pin by looking at all items at the position
            scene_pos = event.scenePos()
            items = self.items(scene_pos)
            
            target_pin = None
            for item in items:
                if isinstance(item, ComponentPin) and item != self.current_wire.start_pin:
                    target_pin = item
                    break
            
            if target_pin:
                # Complete the wire connection
                if self.current_wire.complete_wire(target_pin):
                    self.wires.append(self.current_wire)
                    
                    # Register wire with both connected components
                    start_component = self.current_wire.start_pin.parent_component
                    end_component = self.current_wire.end_pin.parent_component
                    start_component.add_wire(self.current_wire)
                    end_component.add_wire(self.current_wire)
                    
                    # Emit wire added signal
                    self.wire_added.emit(
                        self.current_wire.start_pin.parent_component.name,
                        self.current_wire.start_pin.pin_id,
                        self.current_wire.end_pin.parent_component.name,
                        self.current_wire.end_pin.pin_id
                    )
                    
                    # Update status
                    parent = self.parent()
                    if parent and hasattr(parent, 'status_updated'):
                        start = f"{self.current_wire.start_pin.parent_component.name}.{self.current_wire.start_pin.pin_id}"
                        end = f"{self.current_wire.end_pin.parent_component.name}.{self.current_wire.end_pin.pin_id}"
                        parent.status_updated.emit(f"Wire connected: {start} → {end}")
                    
                    self.current_wire = None
                else:
                    # Invalid connection
                    self.removeItem(self.current_wire)
                    self.current_wire = None
                    
                    parent = self.parent()
                    if parent and hasattr(parent, 'status_updated'):
                        parent.status_updated.emit("Invalid connection - cannot connect pin to itself")
            else:
                # Released on empty space or invalid target - cancel wire
                self.removeItem(self.current_wire)
                self.current_wire = None
                
                parent = self.parent()
                if parent and hasattr(parent, 'status_updated'):
                    parent.status_updated.emit("Wire cancelled")
        
        super().mouseReleaseEvent(event)


class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom functionality"""
    
    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 10.0
        
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        # Check if Ctrl is pressed
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom functionality
            zoom_in = event.angleDelta().y() > 0
            zoom_speed = 1.15
            
            if zoom_in and self.zoom_factor < self.zoom_max:
                self.scale(zoom_speed, zoom_speed)
                self.zoom_factor *= zoom_speed
            elif not zoom_in and self.zoom_factor > self.zoom_min:
                self.scale(1/zoom_speed, 1/zoom_speed)
                self.zoom_factor /= zoom_speed
                
            # Update status if parent has it
            if hasattr(self.parent(), 'status_updated'):
                self.parent().status_updated.emit(f"Zoom: {self.zoom_factor:.2f}x")
        else:
            # Default behavior for non-Ctrl wheel events
            super().wheelEvent(event)
            
    def reset_zoom(self):
        """Reset zoom to 1.0x"""
        scale_factor = 1.0 / self.zoom_factor
        self.scale(scale_factor, scale_factor)
        self.zoom_factor = 1.0


class VisualBCFManager(QWidget):
    """
    Visual BCF Manager - Phase 2.5 Implementation
    
    This phase fixes core functionality issues:
    - Zoom with Ctrl+Scroll
    - Global delete button
    - Component pins
    - Wire connections between components
    - Enhanced component placement and management
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
        
        self.view = CustomGraphicsView(self.scene)
        self.view.setObjectName("BCFGraphicsView")
        self.view.setMinimumSize(800, 600)
        
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
