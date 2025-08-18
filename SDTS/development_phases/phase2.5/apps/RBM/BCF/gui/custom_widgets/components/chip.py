from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import QRectF, QPointF, Qt

from apps.RBM.BCF.src.models.chip import ChipModel


class Chip(QGraphicsItem):
    """GUI representation of a chip"""

    def __init__(self, model: ChipModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

        # Create visual rectangle
        self._rect = QGraphicsRectItem(0, 0, model.width, model.height, self)
        self._rect.setBrush(QBrush(QColor(100, 100, 255)))
        self._rect.setPen(QPen(QColor(0, 0, 0)))

        # Create name label
        self._name_item = QGraphicsTextItem(model.name, self)
        self._update_name_position()

    def _update_name_position(self) -> None:
        """Update the position of the name label"""
        text_rect = self._name_item.boundingRect()
        self._name_item.setPos(
            (self.model.width - text_rect.width()) / 2,
            (self.model.height - text_rect.height()) / 2,
        )

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the chip"""
        return QRectF(0, 0, self.model.width, self.model.height)

    def paint(self, painter, option, widget) -> None:
        """Paint method required by QGraphicsItem"""
        pass  # Actual painting is done by child items

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update model position when chip moves
            new_pos = value
            self.model.position = (new_pos.x(), new_pos.y())

            # Update connections when chip moves
            self._update_connections()

            # Update scene if available
            if self.scene():
                self.scene().update()

        return super().itemChange(change, value)
    
    def _update_connections(self):
        """Update all connections associated with this chip's pins"""
        # Get the scene to find connection components
        scene = self.scene()
        if not scene:
            return
        
        # Find all connection components in the scene and update them
        from apps.RBM.BCF.gui.custom_widgets.components.connection import Connection as ConnectionComponent
        for item in scene.items():
            if isinstance(item, ConnectionComponent):
                # Check if this connection involves our chip's pins
                if self._connection_involves_our_pins(item):
                    item.update_path()
                    
    def _connection_involves_our_pins(self, connection_component):
        """Check if a connection involves any of this chip's pins"""
        if not connection_component.model.start_pin and not connection_component.model.end_pin:
            return False
            
        # Check if any of our pins match the connection's pins
        for pin in self.model.pins:
            if (connection_component.model.start_pin == pin or 
                connection_component.model.end_pin == pin):
                return True
        return False
