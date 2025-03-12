from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import QRectF

from chip import Chip

item_map = {
    "Chip": Chip,
}


class RFView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setRenderHint(self.renderHints().TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setInteractive(True)
        self.setAcceptDrops(True)
        self.placeholder_item = None

    def dragEnterEvent(self, event):
        item_text = event.mimeData().text()
        event.acceptProposedAction()
        if not self.placeholder_item:
            pos = self.mapToScene(event.position().toPoint())
            self.placeholder_item = Chip(item_text, pos, pin_names=["IN", "OUT", "ANT"])
            self.scene().addItem(self.placeholder_item)

    def dragMoveEvent(self, event):
        if self.placeholder_item:
            pos = self.mapToScene(event.position().toPoint())
            self.placeholder_item.setPos(pos)

    def dragLeaveEvent(self, event):
        if self.placeholder_item:
            self.scene().removeItem(self.placeholder_item)
            self.placeholder_item = None

    def dropEvent(self, event):
        event.acceptProposedAction()
        self.placeholder_item = None

    def zoom_in(self, pos):
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(1.2, 1.2)

    def zoom_out(self, pos):
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(0.8, 0.8)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in(event.position())
        else:
            self.zoom_out(event.position())
