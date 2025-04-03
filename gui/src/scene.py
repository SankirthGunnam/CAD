from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from typing import Optional, List, Dict

from src.models.connection import Connection
from src.models.pin import Pin
from gui.custom_widgets.components.chip import Chip
from gui.custom_widgets.components.pin import Pin as PinComponent
from gui.custom_widgets.components.connection import Connection as ConnectionComponent


class RFScene(QGraphicsScene):
    """Scene for RF circuit components"""

    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(Qt.white)
        self.temp_connection = None
        self.start_pin = None
        self._mouse_pos = QPointF(0, 0)
        self._pins: Dict[Pin, PinComponent] = {}  # Map model pins to their widgets

    @property
    def mouse_pos(self) -> QPointF:
        return self._mouse_pos

    def add_component(self, component):
        """Add a component to the scene"""
        self.addItem(component)
        # Create pin widgets for the component
        if isinstance(component, Chip):
            for pin in component.model.pins:
                if pin not in self._pins:
                    pin_widget = PinComponent(pin, self)
                    self._pins[pin] = pin_widget

    def remove_component(self, component) -> None:
        """Remove a component and its connections from the scene"""
        # Remove all connections and pin widgets
        if isinstance(component, Chip):
            for pin in component.model.pins:
                # Remove connections
                for connection in pin.connections[
                    :
                ]:  # Create a copy to avoid modification during iteration
                    connection.remove()
                # Remove pin widget
                if pin in self._pins:
                    self.removeItem(self._pins[pin])
                    del self._pins[pin]
        self.removeItem(component)

    def get_components(self) -> List[Chip]:
        """Get all components in the scene"""
        return [item for item in self.items() if isinstance(item, Chip)]

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, PinComponent):
                self.start_pin = item
                # Create a connection starting from this pin widget
                self.temp_connection = ConnectionComponent(item)
                self.addItem(self.temp_connection)
                # Update the path to start from the pin's position
                self.temp_connection.update_path()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self._mouse_pos = event.scenePos()
        if self.temp_connection:
            self.temp_connection.update_path()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton and self.temp_connection:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, PinComponent) and item != self.start_pin:
                # Only allow connections between pins
                if self.temp_connection.model.finish_connection(item.model):
                    self.temp_connection = None
                else:
                    self.temp_connection.model.remove()
                    self.removeItem(self.temp_connection)
                    self.temp_connection = None
            else:
                # If not released on a valid pin, remove the temporary connection
                self.temp_connection.model.remove()
                self.removeItem(self.temp_connection)
                self.temp_connection = None
            self.start_pin = None
        else:
            super().mouseReleaseEvent(event)
