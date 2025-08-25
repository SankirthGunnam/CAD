"""
Component Scene Module - Phase 2.5

Custom scene that handles component placement and wire drawing.
"""
from typing import TYPE_CHECKING
import logging

from PySide6.QtCore import Signal, QPointF, Qt
from PySide6.QtWidgets import QGraphicsScene

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip import ComponentWithPins
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager


class ComponentScene(QGraphicsScene):
    """Custom scene that handles component placement and wire drawing"""

    component_added = Signal(object, str, QPointF)  # component_object, type, position
    component_removed = Signal(object)  # component_object
    wire_added = Signal(object, str, str, str, str)  # wire_object, start_component, start_pin, end_component, end_pin
    wire_removed = Signal(object, str, str, str, str)  # wire_object, start_component, start_pin, end_component, end_pin

    def __init__(self, controller=None):
        super().__init__()
        # Remove duplicate data storage - scene only contains graphics items
        # Business data is managed by the controller and data model
        self.current_wire = None  # Wire being drawn
        self.mouse_position = QPointF(0, 0)
        self.controller = controller  # Controller reference for all operations

    def mousePressEvent(self, event):
        """Handle mouse press for component placement mode"""
        # Check placement mode from controller first, then parent as fallback
        placement_mode = False
        if self.controller and hasattr(self.controller, 'placement_mode'):
            placement_mode = self.controller.placement_mode
        elif hasattr(self.parent(), 'placement_mode'):
            placement_mode = self.parent().placement_mode

        if placement_mode and event.button() == Qt.MouseButton.LeftButton:
            self.add_component_at_position(event.scenePos())

        super().mousePressEvent(event)

    def add_component_at_position(self, position: QPointF):
        """Add component at the specified position"""
        # Get component type from controller first, then parent as fallback
        component_type = "chip"  # default
        if self.controller and hasattr(
                self.controller,
                'selected_component_type'):
            component_type = self.controller.selected_component_type
        elif hasattr(self.parent(), 'selected_component_type'):
            component_type = self.parent().selected_component_type

        # Generate a temporary name for the component
        # The controller will assign the proper name when it's added to the data model
        name = f"{component_type.title()}_temp"

        component = ComponentWithPins(name, component_type)
        component.setPos(position.x() - component.rect().width() / 2,
                         position.y() - component.rect().height() / 2)

        self.addItem(component)

        # Notify controller to add this component to data model and tracking
        if self.controller and hasattr(self.controller, 'add_component_from_scene'):
            component_id = self.controller.add_component_from_scene(component, name, component_type)
            if component_id:
                # Update component name to match what was assigned by controller
                component.name = name
                logger.info("Component added via controller: %s (%s)", component_id, name)
            else:
                logger.warning("Failed to add component via controller: %s", name)
        else:
            logger.warning("No controller available for component tracking")

        # Emit component added signal with the component object
        self.component_added.emit(component, component_type, position)

    def remove_component(self, component: ComponentWithPins):
        """Remove component from scene"""
        # Remove from scene graphics (no need to manage separate lists)
        self.removeItem(component)
        self.component_removed.emit(component)  # Emit the component object, not just the name

    def start_wire_from_pin(self, pin: ComponentPin):
        """Start drawing a wire from the given pin"""
        if self.current_wire:
            # Complete existing wire or cancel it
            self.removeItem(self.current_wire)
            self.current_wire = None

        # Create new temporary wire with scene reference for collision detection
        self.current_wire = Wire(pin, scene=self)
        self.addItem(self.current_wire)

        # Update status
        parent = self.parent()
        if parent and hasattr(parent, 'status_updated'):
            parent.status_updated.emit(
                f"Drawing wire from {pin.parent_component.name}.{pin.pin_id} - Click destination pin")

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self.mouse_position = event.scenePos()

        # Update temporary wire if drawing
        if self.current_wire and self.current_wire.is_temporary:
            self.current_wire.update_path(self.mouse_position)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.current_wire:
            # Check if released on a pin by looking at all items at the
            # position
            scene_pos = event.scenePos()
            items = self.items(scene_pos)

            target_pin = None
            for item in items:
                if isinstance(
                        item,
                        ComponentPin) and item != self.current_wire.start_pin:
                    target_pin = item
                    break

            if target_pin:
                # Complete the wire connection
                if self.current_wire.complete_wire(target_pin):
                    # Register wire with both connected components
                    start_component = self.current_wire.start_pin.parent_component
                    end_component = self.current_wire.end_pin.parent_component
                    start_component.add_wire(self.current_wire)
                    end_component.add_wire(self.current_wire)

                    # Notify controller to add this wire to data model and tracking
                    if self.controller and hasattr(self.controller, 'add_wire_from_scene'):
                        connection_id = self.controller.add_wire_from_scene(
                            self.current_wire,
                            self.current_wire.start_pin.parent_component.name,
                            self.current_wire.start_pin.pin_id,
                            self.current_wire.end_pin.parent_component.name,
                            self.current_wire.end_pin.pin_id
                        )
                        if connection_id:
                            logger.info("Wire added via controller: %s", connection_id)
                        else:
                            logger.warning("Failed to add wire via controller")
                    else:
                        logger.warning("No controller available for wire tracking")

                    # Emit wire added signal with wire object
                    self.wire_added.emit(
                        self.current_wire,  # Emit the wire object first
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
                        parent.status_updated.emit(
                            f"Wire connected: {start} → {end}")

                    self.current_wire = None
                else:
                    # Invalid connection
                    self.removeItem(self.current_wire)
                    self.current_wire = None

                    parent = self.parent()
                    if parent and hasattr(parent, 'status_updated'):
                        parent.status_updated.emit(
                            "Invalid connection - cannot connect pin to itself")
            else:
                # Released on empty space or invalid target - cancel wire
                self.removeItem(self.current_wire)
                self.current_wire = None

                parent = self.parent()
                if parent and hasattr(parent, 'status_updated'):
                    parent.status_updated.emit("Wire cancelled")

        super().mouseReleaseEvent(event)

    # Scene Serialization Methods
    def serialize_scene(self) -> dict:
        """Serialize scene components and connections to dictionary - delegates to controller"""
        if hasattr(self, 'controller') and self.controller:
            # Delegate serialization to controller which has access to data model
            try:
                return self.controller.serialize_scene_data()
            except Exception as e:
                logger.warning("Controller serialization failed: %s", e)
                # Fallback to basic scene serialization
        
        # Basic fallback serialization using scene items
        scene_data = {
            "components": [],
            "connections": []
        }

        # Get all items from the scene
        all_items = self.items()
        
        # Serialize components
        for item in all_items:
            if isinstance(item, ComponentWithPins):
                component_data = {
                    "name": getattr(item, 'name', 'Unknown'),
                    "type": getattr(item, 'component_type', 'unknown'),
                    "position": {
                        "x": item.pos().x(),
                        "y": item.pos().y()
                    },
                    "properties": getattr(item, 'properties', {}),
                    "pins": []
                }

                # Serialize pins if available
                if hasattr(item, 'pins'):
                    for pin in item.pins:
                        if hasattr(pin, 'pin_id'):
                            pin_data = {
                                "pin_id": pin.pin_id,
                                "position": {
                                    "x": pin.pos().x(),
                                    "y": pin.pos().y()
                                }
                            }
                            component_data["pins"].append(pin_data)

                scene_data["components"].append(component_data)

        # Serialize connections/wires
        for item in all_items:
            if isinstance(item, Wire) and hasattr(item, 'start_pin') and hasattr(item, 'end_pin'):
                if item.start_pin and item.end_pin:
                    connection_data = {
                        "start_component": item.start_pin.parent_component.name,
                        "start_pin": item.start_pin.pin_id,
                        "end_component": item.end_pin.parent_component.name,
                        "end_pin": item.end_pin.pin_id,
                        "properties": getattr(item, 'properties', {})
                    }
                    scene_data["connections"].append(connection_data)

        logger.info("Scene serialization: %s components, %s connections", len(scene_data['components']), len(scene_data['connections']))
        return scene_data

    def load_scene(self, scene_data: dict):
        """Load scene from serialized data

        Args:
            scene_data (dict): Scene data containing components and connections
        """
        # Clear existing scene
        self.clear_scene()

        # Load components
        component_map = {}  # Map component names to component objects

        for comp_data in scene_data.get("components", []):
            component_name = comp_data.get("name")
            component_type = comp_data.get("type")
            position = comp_data.get("position", {"x": 0, "y": 0})

            if component_name and component_type:
                # Create component
                component = ComponentWithPins(component_name, component_type)
                component.setPos(position["x"], position["y"])

                # Set properties if available
                if "properties" in comp_data:
                    component.properties = comp_data["properties"]

                # Add to scene
                self.addItem(component)
                self.components.append(component)
                component_map[component_name] = component

        # Load connections
        for conn_data in scene_data.get("connections", []):
            start_comp_name = conn_data.get("start_component")
            start_pin_id = conn_data.get("start_pin")
            end_comp_name = conn_data.get("end_component")
            end_pin_id = conn_data.get("end_pin")

            if all([start_comp_name, start_pin_id, end_comp_name, end_pin_id]):
                start_component = component_map.get(start_comp_name)
                end_component = component_map.get(end_comp_name)

                if start_component and end_component:
                    # Find the pins
                    start_pin = self._find_pin(start_component, start_pin_id)
                    end_pin = self._find_pin(end_component, end_pin_id)

                    if start_pin and end_pin:
                        # Create wire connection
                        wire = Wire(start_pin)
                        if wire.complete_wire(end_pin):
                            self.addItem(wire)

                            # Register wire with components
                            start_component.add_wire(wire)
                            end_component.add_wire(wire)

    def clear_scene(self):
        """Clear all components and connections from scene"""
        print("🧹 Clearing scene...")
        
        # Use controller's clear method if available, otherwise fall back to local clearing
        if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'clear_scene'):
            try:
                # Use controller's comprehensive clear method
                self.controller.clear_scene(show_confirmation=False)
                print(f"🧹 Scene cleared via controller")
            except Exception as e:
                print(f"⚠️  Controller clear failed, using local clear: {e}")
                self._local_clear_scene()
        else:
            # Fall back to local clearing if no controller
            self._local_clear_scene()
    
    def _local_clear_scene(self):
        """Local fallback method for clearing scene"""
        # Remove all items from the scene
        self.clear()
        
        # Reset current wire
        self.current_wire = None
        
        print("🧹 Scene cleared using local method")
        


    def remove_wire(self, wire):
        """Remove a wire from the scene and clean up properly"""
        try:
            # Get wire information before removal
            if hasattr(wire, 'start_pin') and wire.start_pin and hasattr(wire, 'end_pin') and wire.end_pin:
                start_component_name = wire.start_pin.parent_component.name
                start_pin_id = wire.start_pin.pin_id
                end_component_name = wire.end_pin.parent_component.name
                end_pin_id = wire.end_pin.pin_id
                
                # Remove wire from components' connected_wires lists
                if hasattr(wire.start_pin.parent_component, 'remove_wire'):
                    wire.start_pin.parent_component.remove_wire(wire)
                if hasattr(wire.end_pin.parent_component, 'remove_wire'):
                    wire.end_pin.parent_component.remove_wire(wire)
                
                # Remove from scene graphics
                self.removeItem(wire)
                
                # Emit wire removed signal with wire object
                self.wire_removed.emit(
                    wire,  # Emit the wire object first
                    start_component_name, start_pin_id,
                    end_component_name, end_pin_id
                )
                
                print(f"Wire removed: {start_component_name}.{start_pin_id} -> {end_component_name}.{end_pin_id}")
            else:
                # Just remove from scene if wire info is incomplete
                self.removeItem(wire)
                
        except Exception as e:
            print(f"Error removing wire: {e}")
            # Fallback - just remove from scene
            self.removeItem(wire)

    def _find_pin(self, component, pin_id: str):
        """Find a pin on a component by its ID"""
        if hasattr(component, 'pins'):
            for pin in component.pins:
                if hasattr(pin, 'pin_id') and pin.pin_id == pin_id:
                    return pin
        return None
