from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt


class RFView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(self.renderHints().Antialiasing)
        self.setRenderHint(self.renderHints().TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setInteractive(True)

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
