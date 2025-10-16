"""
Custom Graphics View Module - Phase 2.5

Custom QGraphicsView with zoom functionality.
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QPen, QColor

class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView with zoom functionality"""

    def __init__(self, scene):
        super().__init__(scene)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 10.0
        self.view_transform_changed = Signal()
        self._mode = 'select'

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
            try:
                # Notify listeners (e.g., minimap) that transform changed
                self.view_transform_changed.emit()
            except Exception:
                pass
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
        try:
            self.view_transform_changed.emit()
        except Exception:
            pass

    def set_zoom_factor(self, factor: float):
        """Set absolute zoom factor (relative to 1.0)."""
        if factor <= 0:
            return
        scale_factor = factor / self.zoom_factor
        self.scale(scale_factor, scale_factor)
        self.zoom_factor = factor
        try:
            self.view_transform_changed.emit()
        except Exception:
            pass

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
            try:
                self.view_transform_changed.emit()
            except Exception:
                pass

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
            try:
                self.view_transform_changed.emit()
            except Exception:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.view_transform_changed.emit()
        except Exception:
            pass

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == 'move':
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(Qt.OpenHandCursor)
        elif mode == 'select':
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.setCursor(Qt.ArrowCursor)
        elif mode == 'connection':
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    def mousePressEvent(self, event):
        if self._mode == 'move' and event.button() == Qt.LeftButton:
            try:
                self.setCursor(Qt.ClosedHandCursor)
            except Exception:
                pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._mode == 'move':
            try:
                self.setCursor(Qt.OpenHandCursor)
            except Exception:
                pass


class MiniMapView(QGraphicsView):
    """A miniature view of the same scene that overlays a red rectangle to indicate
    the current viewport of the main view.
    """

    def __init__(self, scene, main_view: QGraphicsView, parent=None):
        super().__init__(scene)
        self._main_view = main_view
        self.setParent(parent)
        self.setFixedSize(200, 150)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setInteractive(False)
        self.setStyleSheet("background: #f8f9fb; border: 1px solid #d1d5db; border-radius: 4px;")
        # Always show content area (items bounding rect) in minimap
        try:
            self.fitInView(self._content_rect(), Qt.KeepAspectRatio)
        except Exception:
            pass

    def _content_rect(self) -> QRectF:
        try:
            rect = self.scene().itemsBoundingRect()
            if rect.isEmpty():
                rect = self.scene().sceneRect()
            # Add small margin so content isn't flush to edges
            return rect.adjusted(-50, -50, 50, 50)
        except Exception:
            return QRectF(-100, -100, 200, 200)

    def paintEvent(self, event):
        # Always keep content area fitted
        try:
            self.fitInView(self._content_rect(), Qt.KeepAspectRatio)
        except Exception:
            pass
        super().paintEvent(event)
        try:
            # Get main view scene rect of visible area
            vp_rect = self._main_view.viewport().rect()
            if vp_rect.isEmpty():
                return
            # Map main viewport rect to scene, then to our viewport coords
            scene_poly = self._main_view.mapToScene(vp_rect)
            if not scene_poly:
                return
            scene_rect = scene_poly.boundingRect()
            # Map that rect into this view's viewport
            top_left = self.mapFromScene(scene_rect.topLeft())
            bottom_right = self.mapFromScene(scene_rect.bottomRight())
            vis_rect = QRectF(top_left, bottom_right)
            painter = QPainter(self.viewport())
            pen = QPen(QColor(220, 38, 38))  # red
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(vis_rect)
            painter.end()
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self.fitInView(self._content_rect(), Qt.KeepAspectRatio)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self.fitInView(self._content_rect(), Qt.KeepAspectRatio)
        except Exception:
            pass
