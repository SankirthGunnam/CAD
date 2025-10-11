"""
Component with Pins Module - Phase 2.5

Enhanced component with visible pins for connections.
"""

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsTextItem, QMenu, QMessageBox, QGraphicsItem)

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire


class ComponentWithPins(QGraphicsRectItem):
    """Enhanced component with visible pins for connections"""

    def __init__(
            self,
            name: str,
            component_type: str,
            width: float = 100,
            height: float = 60,
            component_config: dict = None):
        height = len(component_config.get('pins', [])) * 10 + 20 if component_config else 60
        super().__init__(0, 0, width, height)

        # Component properties
        self.name = name
        self.component_type = component_type
        self.component_config = component_config or {}
        self.is_selected = False
        self.pins = []  # List of ComponentPin objects
        self.connected_wires = []  # List of wires connected to this component

        # Visual properties
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(self.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

        # Set appearance and create pins based on type or configuration
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
        """Create pins based on component configuration or fallback to type-based creation"""
        width = self.rect().width()
        height = self.rect().height()
        pin_radius = 4  # Pin radius for centering calculations

        # Try to create pins from component configuration first
        if self.component_config and 'pins' in self.component_config:
            self._create_pins_from_config()
            return

        # Fallback to type-based pin creation
        if self.component_type == "chip":
            # Comprehensive chip: 6 pins on each side (24 total)
            side_pins = 6
            top_bottom_pins = 6

            # Vertical spacing for left/right pins
            pin_spacing_vertical = height / (side_pins + 1)
            # Horizontal spacing for top/bottom pins
            pin_spacing_horizontal = width / (top_bottom_pins + 1)

            # Left side pins (inputs) - perfectly centered on left edge
            input_names = ["DATA_IN", "CLK", "RST", "EN", "CS", "WR"]
            for i in range(side_pins):
                pin_name = input_names[i] if i < len(
                    input_names) else f"IN{i + 1}"
                pin = ComponentPin(f"L{i + 1}", pin_name,
                                   "input", self, "left")
                pin.setParentItem(self)
                # Position pin so half extends outside left edge (x=0)
                pin.setPos(0,
                           pin_spacing_vertical * (i + 1) - pin_radius)
                self.pins.append(pin)

            # Right side pins (outputs) - perfectly centered on right edge
            output_names = ["DATA_OUT", "INT", "RDY", "ACK", "ERR", "STAT"]
            for i in range(side_pins):
                pin_name = output_names[i] if i < len(
                    output_names) else f"OUT{i + 1}"
                pin = ComponentPin(f"R{i + 1}", pin_name,
                                   "output", self, "right")
                pin.setParentItem(self)
                # Position pin so half extends outside right edge (x=width)
                pin.setPos(width,
                           pin_spacing_vertical * (i + 1) - pin_radius)
                self.pins.append(pin)

            # Top pins (power/control) - perfectly centered on top edge
            top_names = ["VDD", "VREF", "AVDD", "DVDD", "NC", "TEST"]
            for i in range(top_bottom_pins):
                pin_name = top_names[i] if i < len(
                    top_names) else f"VCC{i + 1}"
                pin_type = "power" if "VDD" in pin_name or "V" in pin_name else "io"
                pin = ComponentPin(f"T{i + 1}", pin_name,
                                   pin_type, self, "top")
                pin.setParentItem(self)
                # Position pin so half extends outside top edge (y=0)
                pin.setPos(pin_spacing_horizontal *
                           (i + 1) - pin_radius, 0)
                self.pins.append(pin)

            # Bottom pins (ground/control) - perfectly centered on bottom edge
            bottom_names = ["GND", "AGND", "DGND", "VSS", "BIAS", "SHDN"]
            for i in range(top_bottom_pins):
                pin_name = bottom_names[i] if i < len(
                    bottom_names) else f"GND{i + 1}"
                pin_type = "gnd" if "GND" in pin_name or "VSS" in pin_name else "io"
                pin = ComponentPin(f"B{i + 1}", pin_name,
                                   pin_type, self, "bottom")
                pin.setParentItem(self)
                # Position pin so half extends outside bottom edge (y=height)
                pin.setPos(pin_spacing_horizontal * (i + 1) -
                           pin_radius, height)
                self.pins.append(pin)

        elif self.component_type == "resistor":
            # Resistor: 2 pins (left and right) - centered on edges
            pin1 = ComponentPin("A", "A", "terminal", self, "left")
            pin1.setParentItem(self)
            pin1.setPos(0, height / 2 - pin_radius)
            self.pins.append(pin1)

            pin2 = ComponentPin("B", "B", "terminal", self, "right")
            pin2.setParentItem(self)
            pin2.setPos(width, height / 2 - pin_radius)
            self.pins.append(pin2)

        elif self.component_type == "capacitor":
            # Capacitor: 2 pins (left and right) - centered on edges
            pin1 = ComponentPin("POS", "+", "positive", self, "left")
            pin1.setParentItem(self)
            pin1.setPos(0, height / 2 - pin_radius)
            self.pins.append(pin1)

            pin2 = ComponentPin("NEG", "-", "negative", self, "right")
            pin2.setParentItem(self)
            pin2.setPos(width, height / 2 - pin_radius)
            self.pins.append(pin2)

    def _get_pin_type(self, pin_name: str):
        for pin in self.component_config.get('pins', []):
            if pin.get('id', '') == pin_name:
                return pin.get('type', 'io')
        return 'io'

    def _create_pins_from_config(self):
        """Create pins from component configuration"""
        width = self.rect().width()
        height = self.rect().height()
        pin_radius = 4  # Pin radius for centering calculations

        try:
            pins_config = self.component_config.get('pins', [])
            print(f"Creating pins from config for {self.name}: {len(pins_config)} pins")
            
            for pin_config in pins_config:
                # Get pin information from configuration
                pin_id = pin_config.get('pin_id', pin_config.get('id', ''))
                pin_name = pin_config.get('pin_name', pin_config.get('name', pin_id))
                pin_side = pin_config.get('side', 'right')
                pin_position = pin_config.get('position', 0.5)  # Position as fraction (0.0 to 1.0)
                pin_type = pin_config.get('type', 'digital')
                
                if not pin_id:
                    print(f"Warning: Pin missing ID in config: {pin_config}")
                    continue
                
                # Create the pin
                pin = ComponentPin(
                    pin_id,
                    pin_name,
                    pin_type,
                    self,
                    pin_side
                )
                
                pin.setParentItem(self)
                
                # Position the pin based on side and position
                if pin_side == 'left':
                    pin.setPos(0, height * pin_position - pin_radius)
                elif pin_side == 'right':
                    pin.setPos(width, height * pin_position - pin_radius)
                elif pin_side == 'top':
                    pin.setPos(width * pin_position - pin_radius, 0)
                elif pin_side == 'bottom':
                    pin.setPos(width * pin_position - pin_radius, height)
                else:
                    # Default to right side
                    pin.setPos(width, height * pin_position - pin_radius)
                
                self.pins.append(pin)
                print(f"  Created pin: {pin_id} ({pin_name}) on {pin_side} at position {pin_position}")
                
        except Exception as e:
            print(f"Error creating pins from configuration: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to creating a basic pin
            pin = ComponentPin("PIN1", "PIN", "io", self, "right")
            pin.setParentItem(self)
            pin.setPos(self.rect().width(), self.rect().height() / 2)
            self.pins.append(pin)

    def _setup_appearance(self):
        """Set visual appearance based on component configuration or type"""
        # Try to use visual properties from configuration first
        if self.component_config and 'visual_properties' in self.component_config:
            visual_props = self.component_config['visual_properties']
            color = visual_props.get('color', '#4CAF50')
            
            # Convert hex color to QColor
            try:
                if color.startswith('#'):
                    color = color[1:]  # Remove #
                qcolor = QColor(f"#{color}")
                self.setBrush(QBrush(qcolor))
                # Create a darker version for the border
                border_color = qcolor.darker(120)
                self.setPen(QPen(border_color, 2))
            except:
                # Fallback to default colors
                self.setBrush(QBrush(QColor(100, 150, 200)))
                self.setPen(QPen(QColor(50, 100, 150), 2))
        else:
            # Fallback to type-based appearance
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
            if hasattr(wire, 'update_wire_position_dragging'):
                # Use dragging-aware update for better performance
                wire.update_wire_position_dragging()
            elif hasattr(wire, 'update_wire_position_lightweight'):
                # Fallback to lightweight update
                wire.update_wire_position_lightweight()
            elif hasattr(wire, 'update_path'):
                wire.update_path()
            elif hasattr(wire, 'update_line'):
                wire.update_line()  # Fallback for old wire types

        # Also update any other wires intersecting this moved component
        self._update_intersecting_wires(final=False)

    def update_connected_wires_full(self):
        """Force full update of all connected wires (use after placement is complete)"""
        for wire in self.connected_wires:
            if hasattr(wire, 'update_wire_position_final'):
                # Use final position update for complete recalculation
                wire.update_wire_position_final()
            elif hasattr(wire, 'update_path'):
                wire.update_path()
            elif hasattr(wire, 'update_line'):
                wire.update_line()  # Fallback for old wire types

        # And recalc any other wires intersecting this component
        self._update_intersecting_wires(final=True)

    def itemChange(self, change, value):
        """Handle item changes, particularly position changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Don't update wires during dragging - only update on final position
            # This prevents performance issues during mouse movement
            pass

        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update connected wires only after the move is complete
            # Use QTimer.singleShot to defer the update
            QTimer.singleShot(0, self.update_connected_wires)

            # Defer intersecting wires update in the same tick
            QTimer.singleShot(0, lambda: self._update_intersecting_wires(final=False))

            # Notify controller to sync model position (deferred)
            try:
                scene = self.scene()
                if scene and hasattr(scene, 'controller'):
                    controller = scene.controller
                    if (controller and
                        hasattr(controller, 'on_graphics_component_moved') and
                            callable(getattr(controller, 'on_graphics_component_moved', None))):

                        QTimer.singleShot(
                            0, lambda: self._notify_controller_position_change(controller))

            except Exception as e:
                print(f"Warning: Could not notify controller of position change: {e}")

        return super().itemChange(change, value)

    def _notify_controller_position_change(self, controller):
        """Safely notify controller of position change"""
        try:
            if controller and hasattr(
                    controller, 'on_graphics_component_moved'):
                controller.on_graphics_component_moved(self)
        except Exception as e:
            print(f"Error notifying controller of position change: {e}")

    def mouseReleaseEvent(self, event):
        """Handle mouse release to trigger full wire updates after dragging"""
        super().mouseReleaseEvent(event)

        # After dragging is complete, do a full wire update
        # This ensures proper collision detection and routing
        QTimer.singleShot(100, self.update_connected_wires_full)
        # And finalize intersecting wire updates
        QTimer.singleShot(120, lambda: self._update_intersecting_wires(final=True))

    def _update_intersecting_wires(self, final: bool = False):
        """Find wires whose paths intersect this component's expanded scene rect and update them.

        We use the scene's spatial index via items(rect) with a modest padding to catch near misses.
        """
        scene = self.scene()
        if not scene:
            return
        try:
            comp_rect = self.mapRectToScene(self.boundingRect())
            padding = 30.0
            expanded = comp_rect.adjusted(-padding, -padding, padding, padding)

            candidates = scene.items(expanded)
            for item in candidates:
                if not isinstance(item, Wire):
                    continue

                # Quick bounding check using wire's scene bounds
                try:
                    wire_bounds = item.mapRectToScene(item.boundingRect())
                except Exception:
                    continue
                if not wire_bounds.intersects(expanded):
                    continue

                # Trigger appropriate update
                if final and hasattr(item, 'update_wire_position_final'):
                    item.update_wire_position_final()
                elif hasattr(item, 'update_wire_position_dragging'):
                    item.update_wire_position_dragging()
                elif hasattr(item, 'update_path'):
                    item.update_path()
        except Exception as e:
            # Non-fatal; best effort only
            print(f"Warning: intersecting wire update failed: {e}")
