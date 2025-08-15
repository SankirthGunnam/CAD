from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QTransform
from PySide6.QtCore import Qt, QRectF, QPointF

from apps.RBM.BCF.src.models.pin import Pin as PinModel


class Pin(QGraphicsItem):
    """GUI representation of a pin with a hammer-like shape"""

    PAD_SIZE = 8  # Size of the circular pad
    LINE_LENGTH = 20  # Length of the connection line
    LINE_WIDTH = 2  # Width of the connection line

    def __init__(self, model: PinModel, scene=None):
        super().__init__()
        self.model = model
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self._hovered = False

        if scene:
            scene.addItem(self)

    @property
    def connections(self):
        return self.model.connections

    def _calculate_direction(self) -> QPointF:
        """Calculate the direction the pin should point based on its position on the chip"""
        # Get chip dimensions from the model
        chip = self.model.chip
        if not chip:
            return QPointF(1, 0)  # Default direction if no chip

        width = chip.width
        height = chip.height

        # Use model coordinates to determine which edge the pin is on
        x = self.model.x
        y = self.model.y

        # Determine which edge the pin is on and return appropriate direction
        if abs(x) < 1:  # Left edge
            return QPointF(-1, 0)
        elif abs(x - width) < 1:  # Right edge
            return QPointF(1, 0)
        elif abs(y) < 1:  # Top edge
            return QPointF(0, -1)
        elif abs(y - height) < 1:  # Bottom edge
            return QPointF(0, 1)

        return QPointF(1, 0)  # Default direction

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the pin"""
        direction = self._calculate_direction()
        # Make bounding rect account for all possible orientations
        total_length = self.PAD_SIZE * 2 + self.LINE_LENGTH
        return QRectF(
            -total_length / 2,
            -total_length / 2,
            total_length,
            total_length,
        )

    def paint(self, painter: QPainter, option, widget) -> None:
        """Paint the pin"""
        # Update position from model
        if self.model.chip:
            chip_pos = self.model.chip.position
            self.setPos(chip_pos[0] + self.model.x, chip_pos[1] + self.model.y)
        else:
            self.setPos(self.model.x, self.model.y)

        direction = self._calculate_direction()

        # Save current painter state
        painter.save()

        # Draw the connection line
        painter.setPen(QPen(Qt.black, self.LINE_WIDTH))
        line_end = QPointF(
            direction.x() * self.LINE_LENGTH, direction.y() * self.LINE_LENGTH
        )
        painter.drawLine(QPointF(0, 0), line_end)

        # Draw the pad at the end of the line
        pad_color = Qt.yellow if self._hovered else Qt.gray
        painter.setPen(QPen(Qt.black, 1))
        painter.setBrush(QBrush(pad_color))
        painter.drawEllipse(
            line_end.x() - self.PAD_SIZE / 2,
            line_end.y() - self.PAD_SIZE / 2,
            self.PAD_SIZE,
            self.PAD_SIZE,
        )

        # Restore painter state
        painter.restore()

    def get_connection_point(self) -> QPointF:
        """Get the point where connections should attach"""
        direction = self._calculate_direction()
        if self.model.chip:
            chip_pos = self.model.chip.position
            model_pos = QPointF(chip_pos[0] + self.model.x, chip_pos[1] + self.model.y)
        else:
            model_pos = QPointF(self.model.x, self.model.y)

        return model_pos + QPointF(
            direction.x() * self.LINE_LENGTH, direction.y() * self.LINE_LENGTH
        )

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter events"""
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave events"""
        self._hovered = False
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
