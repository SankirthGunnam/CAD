from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter

from .scene import RFScene


class RFView(QGraphicsView):
    """View class for displaying the RF circuit"""
    
    # Signals
    resizeSignal = Signal()

    def __init__(self, scene: RFScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Set up the view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

    def wheelEvent(self, event) -> None:
        """Handle mouse wheel events for zooming"""
        zoom_factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)

    def fitInView(
        self, rect: QRectF, aspectRatioMode: Qt.AspectRatioMode = Qt.KeepAspectRatio
    ) -> None:
        """Override to ensure proper scaling"""
        super().fitInView(rect, aspectRatioMode)
        # Ensure we don't zoom out too far
        if self.transform().m11() < 0.1:
            self.resetTransform()

    def resetTransform(self) -> None:
        """Reset the view transformation"""
        super().resetTransform()
        # Set a reasonable initial scale
        self.scale(1.0, 1.0)

    def keyPressEvent(self, event) -> None:
        """Handle keyboard events"""
        if event.key() == Qt.Key_Delete:
            # Delete selected items
            for item in self.scene().selectedItems():
                if hasattr(item, "model") and hasattr(item.model, "remove"):
                    item.model.remove()
        super().keyPressEvent(event)
        
    def resizeEvent(self, event) -> None:
        """Handle resize events and emit signal"""
        super().resizeEvent(event)
        self.resizeSignal.emit()
