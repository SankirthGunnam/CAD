"""
Component Pin Module - Phase 2.5

Enhanced connection pin for components with proper names and smart positioning.
"""

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPen, QBrush, QColor, QFont


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
