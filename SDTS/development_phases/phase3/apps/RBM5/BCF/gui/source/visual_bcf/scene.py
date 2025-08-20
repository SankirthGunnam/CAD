"""
Component Scene Module - Phase 2.5

Custom scene that handles component placement and wire drawing.
"""
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Signal, QPointF, Qt

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip import ComponentWithPins
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire

if TYPE_CHECKING:
    from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager


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
    
    # Scene Serialization Methods
    def serialize_scene(self) -> dict:
        """Serialize scene components and connections to dictionary
        
        Returns:
            dict: Scene data containing:
                - components: List of component data with positions
                - connections: List of wire/connection data
        """
        scene_data = {
            "components": [],
            "connections": []
        }
        
        # Serialize components
        for component in self.components:
            if hasattr(component, 'name') and hasattr(component, 'component_type'):
                component_data = {
                    "name": component.name,
                    "type": component.component_type,
                    "position": {
                        "x": component.pos().x(),
                        "y": component.pos().y()
                    },
                    "properties": getattr(component, 'properties', {}),
                    "pins": []
                }
                
                # Serialize pins if available
                if hasattr(component, 'pins'):
                    for pin in component.pins:
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
        for wire in self.wires:
            if hasattr(wire, 'start_pin') and hasattr(wire, 'end_pin'):
                if wire.start_pin and wire.end_pin:
                    connection_data = {
                        "start_component": wire.start_pin.parent_component.name,
                        "start_pin": wire.start_pin.pin_id,
                        "end_component": wire.end_pin.parent_component.name,
                        "end_pin": wire.end_pin.pin_id,
                        "properties": getattr(wire, 'properties', {})
                    }
                    scene_data["connections"].append(connection_data)
        
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
                            self.wires.append(wire)
                            
                            # Register wire with components
                            start_component.add_wire(wire)
                            end_component.add_wire(wire)
    
    def clear_scene(self):
        """Clear all components and connections from scene"""
        # Remove all items
        self.clear()
        
        # Clear lists
        self.components.clear()
        self.wires.clear()
        
        # Reset counter
        self.component_counter = 1
        self.current_wire = None
    
    def _find_pin(self, component, pin_id: str):
        """Find a pin on a component by its ID"""
        if hasattr(component, 'pins'):
            for pin in component.pins:
                if hasattr(pin, 'pin_id') and pin.pin_id == pin_id:
                    return pin
        return None
