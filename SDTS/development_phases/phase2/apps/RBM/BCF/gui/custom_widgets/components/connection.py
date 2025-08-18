from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtCore import Qt, QPointF

from apps.RBM.BCF.source.models.connection import Connection as ConnectionModel
from .pin import Pin


class Connection(QGraphicsPathItem):
    """GUI representation of a connection"""

    def __init__(self, model_or_pin, parent=None):
        super().__init__(parent)
        if isinstance(model_or_pin, Pin):
            self.model = ConnectionModel(model_or_pin.model)
            self.start_pin = model_or_pin
        else:
            self.model = model_or_pin
            self.start_pin = None
        self.setZValue(-1)  # Draw connections below components
        self.setPen(QPen(QColor(0, 0, 0), 2))
        self.update_path()

    def update_path(self) -> None:
        """Update the connection path between pins"""
        if not self.model.start_pin:
            return

        path = QPainterPath()

        # Get the scene position of the start pin
        if self.start_pin:
            # Use the actual widget position in the scene
            start_pos = self.start_pin.scenePos()
        else:
            # Fallback to model coordinates
            start_pin = self.model.start_pin
            start_pos = QPointF(start_pin.x, start_pin.y)

        path.moveTo(start_pos)

        if self.model.end_pin:
            # If we have an end pin, connect to it
            end_pin = self.model.end_pin
            # Try to find the corresponding widget
            scene = self.scene()
            if scene:
                for item in scene.items():
                    if isinstance(item, Pin) and item.model == end_pin:
                        end_pos = item.scenePos()
                        break
                else:
                    # Fallback to model coordinates
                    end_pos = QPointF(end_pin.x, end_pin.y)
            else:
                # Fallback to model coordinates
                end_pos = QPointF(end_pin.x, end_pin.y)

            # Calculate control points for a smooth curve
            control_points = self._calculate_control_points(start_pos, end_pos)
            path.cubicTo(control_points[0], control_points[1], end_pos)
        else:
            # If we're still drawing the connection, use the scene mouse position
            scene = self.scene()
            if scene and hasattr(scene, "_mouse_pos"):
                # Draw a temporary line to the mouse position
                path.lineTo(scene._mouse_pos)

        self.setPath(path)

    def _calculate_control_points(
        self, start: QPointF, end: QPointF
    ) -> tuple[QPointF, QPointF]:
        """Calculate control points for a smooth curve between two points"""
        dx = end.x() - start.x()
        dy = end.y() - start.y()

        # Control points are placed at 1/3 and 2/3 of the distance
        ctrl1 = QPointF(start.x() + dx / 3, start.y())
        ctrl2 = QPointF(end.x() - dx / 3, end.y())

        return ctrl1, ctrl2

    def paint(self, painter, option, widget) -> None:
        """Override paint to add selection highlighting"""
        if self.isSelected():
            pen = self.pen()
            pen.setColor(Qt.red)
            painter.setPen(pen)
        super().paint(painter, option, widget)
