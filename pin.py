# pin.py
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt

class Pin(QGraphicsEllipseItem):
    def __init__(self, name, x, y, radius=6):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.name = name
        self.connected_pins = []
        self.setBrush(QBrush(QColor('red')))
        self.setPos(x, y)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)

        # Add text for pin name
        # self.text_item = QGraphicsTextItem(name, self)
        # self.text_item.setDefaultTextColor(Qt.black)
        # self.text_item.setPos(-radius, -radius - 12)

    def add_connection(self, pin):
        if pin not in self.connected_pins:
            self.connected_pins.append(pin)
