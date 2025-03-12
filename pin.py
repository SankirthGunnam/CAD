from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsLineItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import QPointF


class Pin(QGraphicsItem):
    def __init__(self, parent=None, name="Pin", pos=QPointF(0, 0)):
        super().__init__(parent)
        self.name = name
        self.setPos(pos)
        self.connected_pins = []

        # Pin Appearance
        self.pad_size = 10
        self.pin_length = 20

        self.pad = QGraphicsRectItem(
            0, -self.pad_size / 2, self.pad_size, self.pad_size, self
        )
        self.pad.setBrush(QBrush(QColor(255, 100, 100)))
        self.pad.setPen(QPen(QColor(0, 0, 0)))

        self.line = QGraphicsLineItem(
            self.pad_size / 2, 0, self.pad_size / 2, self.pin_length, self
        )
        self.line.setPen(QPen(QColor(0, 0, 0)))

    def add_connection(self, pin):
        if pin not in self.connected_pins:
            self.connected_pins.append(pin)

    def remove_connection(self, pin):
        if pin in self.connected_pins:
            self.connected_pins.remove(pin)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        pass
