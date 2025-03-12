from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import Qt


from connection import Connection
from chip import Chip
from pin import Pin


class RFScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.selected_pin = None

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, Pin):
            if self.selected_pin is None:
                self.selected_pin = item
            else:
                obstacles = [chip for chip in self.items() if isinstance(chip, Chip)]
                connection = Connection(self.selected_pin, item, obstacles)
                self.addItem(connection)
                self.selected_pin.add_connection(item)
                item.add_connection(self.selected_pin)
                self.selected_pin = None
        else:
            self.selected_pin = None
        super().mousePressEvent(event)

    def addComponent(self, component_type, pos):
        item = QGraphicsRectItem(0, 0, 60, 40)
        item.setPos(pos)
        item.setFlags(
            QGraphicsRectItem.ItemIsMovable | QGraphicsRectItem.ItemIsSelectable
        )
        self.addItem(item)
        text = QGraphicsTextItem(component_type, item)
        text.setDefaultTextColor(Qt.white)
        text.setPos(10, 10)
