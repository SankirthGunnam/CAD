from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import QRectF, QPointF, Qt

from src.models.chip import ChipModel
from .pin import Pin


class Chip(QGraphicsItem):
    """GUI representation of a chip"""

    def __init__(self, model: ChipModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        # Create visual rectangle
        self._rect = QGraphicsRectItem(0, 0, model.width, model.height, self)
        self._rect.setBrush(QBrush(QColor(100, 100, 255)))
        self._rect.setPen(QPen(QColor(0, 0, 0)))

        # Create name label
        self._name_item = QGraphicsTextItem(model.name, self)
        self._update_name_position()

        # Create pin widgets
        self._pins = []
        self._create_pins()

    def _create_pins(self) -> None:
        """Create pin widgets for each pin in the model"""
        for pin in self.model.pins:
            pin_widget = Pin(pin, self)
            pin_widget.setPos(pin.x, pin.y)
            self._pins.append(pin_widget)

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

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move events"""
        super().mouseMoveEvent(event)
        # Update pin positions
        for pin in self._pins:
            pin.update()
