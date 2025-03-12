
# chip.py
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtGui import QBrush, QColor
from PySide6.QtCore import Qt
from pin import Pin

class Chip(QGraphicsRectItem):
    def __init__(self, name, width=100, height=60, pin_names=None):
        super().__init__(0, 0, width, height)
        self.setBrush(QBrush(QColor('lightgray')))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        
        # Centered name
        self.name_item = QGraphicsTextItem(name, self)
        self.name_item.setDefaultTextColor(Qt.black)
        text_rect = self.name_item.boundingRect()
        self.name_item.setPos((width - text_rect.width()) / 2, (height - text_rect.height()) / 2)
        
        # Create pins
        self.pins = []
        if pin_names:
            spacing = width / (len(pin_names) + 1)
            for i, pin_name in enumerate(pin_names):
                pin = Pin(pin_name, (i + 1) * spacing, height)
                self.pins.append(pin)
                pin.setParentItem(self)  # Ensures pins move with the chip

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for pin in self.pins:
            pin.update()  # Update pin positions if needed
