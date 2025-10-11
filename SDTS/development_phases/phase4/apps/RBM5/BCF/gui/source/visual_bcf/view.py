"""
Custom Graphics View Module - Phase 2.5

Custom QGraphicsView with zoom functionality.
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt

class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom functionality"""

    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 10.0

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        # Check if Ctrl is pressed
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom functionality
            zoom_in = event.angleDelta().y() > 0
            zoom_speed = 1.15

            if zoom_in and self.zoom_factor < self.zoom_max:
                self.scale(zoom_speed, zoom_speed)
                self.zoom_factor *= zoom_speed
            elif not zoom_in and self.zoom_factor > self.zoom_min:
                self.scale(1 / zoom_speed, 1 / zoom_speed)
                self.zoom_factor /= zoom_speed

            # Update status if parent has it
            if hasattr(self.parent(), 'status_updated'):
                self.parent().status_updated.emit(
                    f"Zoom: {self.zoom_factor:.2f}x")
        else:
            # Default behavior for non-Ctrl wheel events
            super().wheelEvent(event)

    def reset_zoom(self):
        """Reset zoom to 1.0x"""
        scale_factor = 1.0 / self.zoom_factor
        self.scale(scale_factor, scale_factor)
        self.zoom_factor = 1.0

        # Update status if parent has it
        if hasattr(self.parent(), 'status_updated'):
            self.parent().status_updated.emit(
                f"Zoom reset: {self.zoom_factor:.2f}x")

    def set_zoom_factor(self, factor: float):
        """Set absolute zoom factor (relative to 1.0)."""
        if factor <= 0:
            return
        scale_factor = factor / self.zoom_factor
        self.scale(scale_factor, scale_factor)
        self.zoom_factor = factor

    def zoom_in(self):
        """Zoom in by a fixed amount"""
        if self.zoom_factor < self.zoom_max:
            zoom_speed = 1.25
            self.scale(zoom_speed, zoom_speed)
            self.zoom_factor *= zoom_speed

            # Update status if parent has it
            if hasattr(self.parent(), 'status_updated'):
                self.parent().status_updated.emit(
                    f"Zoom in: {self.zoom_factor:.2f}x")

    def zoom_out(self):
        """Zoom out by a fixed amount"""
        if self.zoom_factor > self.zoom_min:
            zoom_speed = 1.25
            self.scale(1 / zoom_speed, 1 / zoom_speed)
            self.zoom_factor /= zoom_speed

            # Update status if parent has it
            if hasattr(self.parent(), 'status_updated'):
                self.parent().status_updated.emit(
                    f"Zoom out: {self.zoom_factor:.2f}x")
