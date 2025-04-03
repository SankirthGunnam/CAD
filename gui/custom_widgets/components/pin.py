from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QRectF, QPointF

from src.models.pin import Pin as PinModel


class Pin(QGraphicsItem):
    """GUI representation of a pin"""

    SIZE = 6  # Pin size in pixels

    def __init__(self, model: PinModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setAcceptHoverEvents(True)
        self._hover = False

    @property
    def connections(self):
        return self.model.connections

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the pin"""
        return QRectF(-self.SIZE / 2, -self.SIZE / 2, self.SIZE, self.SIZE)

    def paint(self, painter: QPainter, option, widget) -> None:
        """Paint the pin"""
        pen = QPen(Qt.black if not self._hover else Qt.red)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 255, 0))  # Yellow fill
        painter.drawEllipse(self.boundingRect())

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter events"""
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave events"""
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events for starting connections"""
        if event.button() == Qt.LeftButton:
            # Emit signal or notify scene to start connection
            scene = self.scene()
            if scene:
                scene.start_connection(self)
        super().mousePressEvent(event)
