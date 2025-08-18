"""
Wire Connection Module - Phase 2.5

Wire connection between component pins.
"""

from typing import Optional
from PySide6.QtWidgets import QGraphicsLineItem, QMenu
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPen, QColor

try:
    from .pin import ComponentPin
except ImportError:
    from pin import ComponentPin


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
