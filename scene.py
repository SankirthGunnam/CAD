from PySide6.QtWidgets import QGraphicsScene

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
