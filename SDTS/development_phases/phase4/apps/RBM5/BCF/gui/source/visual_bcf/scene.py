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
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.wire_thread_manager import SceneWireThreadManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager


class ComponentScene(QGraphicsScene):
    """Custom scene that handles component placement and wire drawing"""

    wire_removed = Signal(object, str, str, str, str)  # wire_object, start_component, start_pin, end_component, end_pin

    def __init__(self, controller=None):
        super().__init__()
        self.current_wire = None  # Wire being drawn
        self.mouse_position = QPointF(0, 0)
        self.controller = controller  # Controller reference for all operations
        self.preview_component = None  # Preview component that follows mouse
        
        # Initialize wire thread manager for async calculations
        self.wire_thread_manager = SceneWireThreadManager(max_threads=10, parent=self)
        logger.info("Scene initialized with wire thread manager (max 10 threads)")

        # Auto-populate an RFIC testbed if the scene starts empty (for performance testing)
        try:
            self._populate_rfic_test_if_empty()
        except Exception as e:
            logger.debug("RFIC testbed init skipped: %s", e)

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

    def mouseMoveEvent(self, event):
        """Handle mouse move for component preview and wire drawing"""
        self.mouse_position = event.scenePos()
        
        # Check placement mode from controller
        placement_mode = False
        if self.controller and hasattr(self.controller, 'placement_mode'):
            placement_mode = self.controller.placement_mode
        elif hasattr(self.parent(), 'placement_mode'):
            placement_mode = self.parent().placement_mode

        if placement_mode and self.controller and self.controller.selected_component_data:
            self._update_preview_component(event.scenePos())
        
        # Update temporary wire if drawing
        if self.current_wire and self.current_wire.is_temporary:
            self.current_wire.update_path(self.mouse_position)
        
        super().mouseMoveEvent(event)

    def _update_preview_component(self, position: QPointF):
        """Update or create preview component that follows mouse"""
        if not self.controller or not self.controller.selected_component_data:
            return
            
        component_data = self.controller.selected_component_data
        component_type = component_data.get('Component Type', 'chip')
        name = component_data.get('Name', f"{component_type.title()}_preview")
        
        # Remove existing preview component
        if self.preview_component:
            self.removeItem(self.preview_component)
            self.preview_component = None
        
        # Create new preview component
        try:
            # Get component configuration using the actual component name
            component_config = self.controller.data_model.component_dcf(name)
            
            # Create component with configuration
            preview = ComponentWithPins(name, component_type, component_config=component_config)
            preview.setPos(position.x() - preview.rect().width() / 2,
                          position.y() - preview.rect().height() / 2)
            
            # Make it semi-transparent
            preview.setOpacity(0.5)
            
            # Add to scene
            self.addItem(preview)
            self.preview_component = preview
            
        except Exception as e:
            logger.warning("Could not create preview component: %s", e)

    def _clear_preview_component(self):
        """Clear the preview component"""
        if self.preview_component:
            self.removeItem(self.preview_component)
            self.preview_component = None

    def add_component_at_position(self, position: QPointF):
        """Add component at the specified position"""
        logger.info("Component Scene: In Add Component At Position")
        
        # Clear preview component first
        self._clear_preview_component()
        
        # Check if we have selected component data from dialog
        if self.controller.selected_component_data:
            component_data = self.controller.selected_component_data
            print('component_data add_component_at_position', component_data)
            component_type = component_data.get('Component Type', 'chip')
            name = component_data.get('Name', f"{component_type.title()}_temp")
            component_id = component_data.get('ID', '')
            
            # Get component configuration
            component_config = self.controller.data_model.component_dcf(name)
            
            # Create component with configuration
            component = ComponentWithPins(name, component_type, component_config=component_config)
            component.setPos(position.x() - component.rect().width() / 2,
                             position.y() - component.rect().height() / 2)
            component.component_id = component_id
            component.properties = component_data.get('Properties', {})
            
            self.addItem(component)
            
            # Add to data model with the selected component data
            self.controller.add_component(component, component_type)
            
            # Reset placement mode
            self.controller.placement_mode = False
            self.controller.selected_component_data = None
            if self.controller.view:
                self.controller.view.setCursor(Qt.ArrowCursor)
            
            logger.info("Component added to scene: %s (%s) with ID: %s", name, component_type, component_id)
        else:
            # Fallback to old behavior for backward compatibility
            component_type = self.controller.selected_component_type
            name = f"{component_type.title()}_temp"
            component = ComponentWithPins(name, component_type)
            component.setPos(position.x() - component.rect().width() / 2,
                             position.y() - component.rect().height() / 2)
            self.addItem(component)
            self.controller.add_component(component, component_type, (position.x(), position.y()))
            logger.info("Component added to scene: %s (%s)", name, component_type)

    def remove_component(self, component: ComponentWithPins):
        """Remove component from scene"""
        # self.removeItem(component)
        self.controller.remove_component(component)

    def start_wire_from_pin(self, pin: ComponentPin):
        """Start drawing a wire from the given pin"""
        if self.current_wire:
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


    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.current_wire:
            # Check if released on a pin by looking at all items at the
            # position
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
                    # Register wire with both connected components
                    start_component = self.current_wire.start_pin.parent_component
                    end_component = self.current_wire.end_pin.parent_component
                    start_component.add_wire(self.current_wire)
                    end_component.add_wire(self.current_wire)

                    self.controller.add_connection(self.current_wire)

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

    def remove_wire(self, wire: Wire):
        """Remove a wire from the scene and clean up properly"""
        try:
            if hasattr(wire, 'start_pin') and wire.start_pin and hasattr(wire, 'end_pin') and wire.end_pin:
                # Remove from scene graphics
                # self.removeItem(wire)
                wire.start_pin.parent_component.remove_wire(wire)
                wire.end_pin.parent_component.remove_wire(wire)

                # Emit wire removed signal with wire object
                self.controller.remove_connection(wire)
                print(f"Wire removed")
            else:
                # Just remove from scene if wire info is incomplete
                self.removeItem(wire)
        except Exception as e:
            print(f"Error removing wire: {e}")
            # Fallback - just remove from scene
            self.removeItem(wire)
    
    def cleanup(self):
        """Clean up scene resources including thread manager"""
        if hasattr(self, 'wire_thread_manager'):
            self.wire_thread_manager.cleanup()
            logger.info("Scene cleanup completed")

    # ---------------------- RFIC Testbed helpers ----------------------

    def _populate_rfic_test_if_empty(self):
        """Populate a synthetic RFIC testbed (two RFICs + connections) when the scene is empty.

        This aids performance testing of wire routing with many pins/wires.
        """
        if len(self.items()) > 0:
            return
        self.add_rfic_testbed()

    def _build_rfic_config(self, name: str, num_pairs: int = 8) -> dict:
        """Build a config dict for an RFIC with PRX/DRX pins on left/right and misc top/bottom pins."""
        pins = []
        # Distribute pins evenly along edges, avoid extremes
        if num_pairs < 1:
            num_pairs = 1
        step = 1.0 / (num_pairs + 1)
        for i in range(num_pairs):
            pos = (i + 1) * step
            idx = i + 1
            # Left edge: PRX_IN, DRX_IN
            pins.append({
                'pin_id': f'PRX_IN{idx}', 'pin_name': f'PRX_IN{idx}', 'side': 'left', 'position': pos, 'type': 'rf_in'
            })
            pins.append({
                'pin_id': f'DRX_IN{idx}', 'pin_name': f'DRX_IN{idx}', 'side': 'left', 'position': min(pos + step/2.0, 0.98), 'type': 'rf_in'
            })
            # Right edge: PRX_OUT, DRX_OUT
            pins.append({
                'pin_id': f'PRX_OUT{idx}', 'pin_name': f'PRX_OUT{idx}', 'side': 'right', 'position': pos, 'type': 'rf_out'
            })
            pins.append({
                'pin_id': f'DRX_OUT{idx}', 'pin_name': f'DRX_OUT{idx}', 'side': 'right', 'position': min(pos + step/2.0, 0.98), 'type': 'rf_out'
            })

        # A few top/bottom pins
        pins.extend([
            {'pin_id': 'LO_IN', 'pin_name': 'LO_IN', 'side': 'top', 'position': 0.3, 'type': 'rf_lo'},
            {'pin_id': 'REFCLK', 'pin_name': 'REFCLK', 'side': 'top', 'position': 0.7, 'type': 'clock'},
            {'pin_id': 'VDD', 'pin_name': 'VDD', 'side': 'bottom', 'position': 0.25, 'type': 'power'},
            {'pin_id': 'GND', 'pin_name': 'GND', 'side': 'bottom', 'position': 0.75, 'type': 'gnd'},
        ])

        return {
            'visual_properties': {'color': '#2E86DE'},
            'pins': pins,
        }

    def add_rfic_testbed(self, num_pairs: int = 8):
        """Create two RFIC components with many PRX/DRX pins and connect them."""
        try:
            # Build components
            cfg_a = self._build_rfic_config('RFIC_A', num_pairs=num_pairs)
            cfg_b = self._build_rfic_config('RFIC_B', num_pairs=num_pairs)

            rfic_a = ComponentWithPins('RFIC_A', 'rfic', component_config=cfg_a)
            rfic_b = ComponentWithPins('RFIC_B', 'rfic', component_config=cfg_b)

            rfic_a.setPos(100, 120)
            rfic_b.setPos(500, 140)

            # Ensure they have component_id used by collision checks
            rfic_a.component_id = 'RFIC_A'
            rfic_b.component_id = 'RFIC_B'

            self.addItem(rfic_a)
            self.addItem(rfic_b)

            # Register with controller/model if available
            if self.controller and hasattr(self.controller, 'add_component'):
                self.controller.add_component(rfic_a, 'rfic')
                self.controller.add_component(rfic_b, 'rfic')

            # Helper to find pin by id
            def pin(comp, pid):
                for p in getattr(comp, 'pins', []):
                    if getattr(p, 'pin_id', '') == pid:
                        return p
                return None

            # Create connections between A and B for PRX and DRX (both directions)
            for i in range(1, num_pairs + 1):
                # A.PRX_OUTi -> B.PRX_INi
                sp = pin(rfic_a, f'PRX_OUT{i}')
                ep = pin(rfic_b, f'PRX_IN{i}')
                if sp and ep:
                    self._add_wire_between(sp, ep)

                # A.DRX_OUTi -> B.DRX_INi
                sp = pin(rfic_a, f'DRX_OUT{i}')
                ep = pin(rfic_b, f'DRX_IN{i}')
                if sp and ep:
                    self._add_wire_between(sp, ep)

            # Add a few intra-component loops to stress self-avoidance
            for i in range(1, min(4, num_pairs) + 1):
                sp = pin(rfic_a, f'PRX_IN{i}')
                ep = pin(rfic_a, f'PRX_OUT{i}')
                if sp and ep:
                    self._add_wire_between(sp, ep)

                sp = pin(rfic_b, f'DRX_IN{i}')
                ep = pin(rfic_b, f'DRX_OUT{i}')
                if sp and ep:
                    self._add_wire_between(sp, ep)

        except Exception as e:
            logger.warning("Failed to add RFIC testbed: %s", e)

    def _add_wire_between(self, start_pin: ComponentPin, end_pin: ComponentPin):
        """Create and register a wire between two pins."""
        try:
            wire = Wire(start_pin, end_pin=end_pin, scene=self)
            self.addItem(wire)

            # Register with components
            if hasattr(start_pin, 'parent_component'):
                start_pin.parent_component.add_wire(wire)
            if hasattr(end_pin, 'parent_component'):
                end_pin.parent_component.add_wire(wire)

            # Notify controller/model if available
            if self.controller and hasattr(self.controller, 'add_connection'):
                self.controller.add_connection(wire)
        except Exception as e:
            logger.debug("Wire creation failed: %s", e)

    def get_component_at_position(self, position: QPointF) -> ComponentWithPins:
        """Get the component at the specified position"""
        items = self.items(position)
        for item in items:
            if isinstance(item, ComponentWithPins):
                return item
        return None
