from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import QRectF, QPointF, Qt

from apps.RBM.BCF.src.models.chip import ChipModel


class Chip(QGraphicsItem):
    """GUI representation of a chip"""

    def __init__(self, model: ChipModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

        # Create visual rectangle
        self._rect = QGraphicsRectItem(0, 0, model.width, model.height, self)
        self._rect.setBrush(QBrush(QColor(100, 100, 255)))
        self._rect.setPen(QPen(QColor(0, 0, 0)))

        # Create name label
        self._name_item = QGraphicsTextItem(model.name, self)
        self._update_name_position()

    def _update_name_position(self) -> None:
        """Update the position of the name label"""
        text_rect = self._name_item.boundingRect()
        self._name_item.setPos(
            (self.model.width - text_rect.width()) / 2,
            (self.model.height - text_rect.height()) / 2,
        )

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the chip"""
        return QRectF(0, 0, self.model.width, self.model.height)

    def paint(self, painter, option, widget) -> None:
        """Paint method required by QGraphicsItem"""
        pass  # Actual painting is done by child items

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.ItemPositionChange:
            # Update model position when chip moves
            new_pos = value
            self.model.position = (new_pos.x(), new_pos.y())

            # Update scene if available
            if self.scene():
                self.scene().update()

        return super().itemChange(change, value)
