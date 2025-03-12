from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import QRectF, QPointF

from pin import Pin


class Chip(QGraphicsRectItem):
    def __init__(
        self, name="Chip", pos=QPointF(0, 0), width=50, height=50, pin_names=None
    ):
        super().__init__(0, 0, width, height)
        self.setPos(pos)
        self.setBrush(QBrush(QColor(100, 100, 255)))
        self.setPen(QPen(QColor(0, 0, 0)))
        self.setFlag(QGraphicsItem.ItemIsMovable)

        self.name = name
        self.name_item = QGraphicsTextItem(name, self)
        text_rect = self.name_item.boundingRect()
        self.name_item.setPos(
            (width - text_rect.width()) / 2, (height - text_rect.height()) / 2
        )

        # Create pins
        self.pins = []
        self.add_pin(QPointF(width / 2, 0))  # Top pin
        self.add_pin(QPointF(width / 2, height))  # Bottom pin
        self.add_pin(QPointF(0, height / 2))  # Left pin
        self.add_pin(QPointF(width, height / 2))  # Right pin

    def add_pin(self, pos):
        pin = Pin(self, pos=pos)
        self.pins.append(pin)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for pin in self.pins:
            pin.update()  # Update pin positions if needed
