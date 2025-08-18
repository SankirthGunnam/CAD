"""
RFIC chip visual component.
Extends the base Chip component with RFIC-specific styling and visual elements.
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsRectItem
from PySide6.QtGui import QBrush, QColor, QPen, QFont
from PySide6.QtCore import QRectF, QPointF, Qt

from apps.RBM.BCF.source.models.rfic_chip import RFICChipModel
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip


class RFICChip(Chip):
    """GUI representation of an RFIC chip with RF-specific styling"""
    
    def __init__(self, model: RFICChipModel, parent=None):
        super().__init__(model, parent)
        
        # Override the visual styling for RFIC
        self._setup_rfic_styling()
        
        # Add RFIC-specific visual elements
        self._add_rfic_indicators()
    
    def _setup_rfic_styling(self) -> None:
        """Setup RFIC-specific visual styling"""
        # Use RF-themed colors
        rf_color = QColor(255, 140, 0)  # Orange for RF components
        border_color = QColor(139, 69, 19)  # Brown border
        
        # Update the main rectangle styling
        self._rect.setBrush(QBrush(rf_color))
        self._rect.setPen(QPen(border_color, 2))
        
        # Update name label with bold font and white color
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self._name_item.setFont(font)
        self._name_item.setDefaultTextColor(Qt.white)
        
        # Update the text to show it's an RFIC
        self._name_item.setPlainText(f"{self.model.name} (RFIC)")
        self._update_name_position()
    
    def _add_rfic_indicators(self) -> None:
        """Add RFIC-specific visual indicators"""
        # Add frequency range indicator
        freq_text = QGraphicsTextItem(self.model.get_frequency_range(), self)
        freq_font = QFont()
        freq_font.setPointSize(7)
        freq_text.setFont(freq_font)
        freq_text.setDefaultTextColor(Qt.white)
        
        # Position frequency text below the main name
        name_rect = self._name_item.boundingRect()
        freq_text.setPos(
            (self.model.width - freq_text.boundingRect().width()) / 2,
            name_rect.bottom() + 5
        )
        
        # Add MIMO indicator
        mimo_text = QGraphicsTextItem(f"MIMO: {self.model.get_mimo_support()}", self)
        mimo_font = QFont()
        mimo_font.setPointSize(7)
        mimo_text.setFont(mimo_font)
        mimo_text.setDefaultTextColor(Qt.white)
        
        # Position MIMO text below frequency
        freq_rect = freq_text.boundingRect()
        mimo_text.setPos(
            (self.model.width - mimo_text.boundingRect().width()) / 2,
            freq_text.pos().y() + freq_rect.height() + 2
        )
        
        # Add TX/RX indicators on the sides
        self._add_port_indicators()
    
    def _add_port_indicators(self) -> None:
        """Add TX/RX port indicators"""
        # TX indicator (left side)
        tx_text = QGraphicsTextItem("TX", self)
        tx_font = QFont()
        tx_font.setBold(True)
        tx_font.setPointSize(8)
        tx_text.setFont(tx_font)
        tx_text.setDefaultTextColor(Qt.red)  # Red for TX
        tx_text.setPos(-25, self.model.height / 2 - 10)
        
        # RX indicator (right side)
        rx_text = QGraphicsTextItem("RX", self)
        rx_font = QFont()
        rx_font.setBold(True)
        rx_font.setPointSize(8)
        rx_text.setFont(rx_font)
        rx_text.setDefaultTextColor(Qt.blue)  # Blue for RX
        rx_text.setPos(self.model.width + 5, self.model.height / 2 - 10)
        
        # Control indicator (top)
        ctrl_text = QGraphicsTextItem("CTRL", self)
        ctrl_font = QFont()
        ctrl_font.setPointSize(6)
        ctrl_text.setFont(ctrl_font)
        ctrl_text.setDefaultTextColor(Qt.green)  # Green for control
        ctrl_text.setPos(self.model.width / 2 - 15, -15)
        
        # Power indicator (bottom)
        pwr_text = QGraphicsTextItem("PWR", self)
        pwr_font = QFont()
        pwr_font.setPointSize(6)
        pwr_text.setFont(pwr_font)
        pwr_text.setDefaultTextColor(Qt.yellow)  # Yellow for power
        pwr_text.setPos(self.model.width / 2 - 10, self.model.height + 5)
    
    def _update_name_position(self) -> None:
        """Update the position of the name label for RFIC"""
        text_rect = self._name_item.boundingRect()
        # Position higher to make room for additional info
        self._name_item.setPos(
            (self.model.width - text_rect.width()) / 2,
            self.model.height / 2 - text_rect.height() - 15
        )
    
    def get_rfic_model(self) -> RFICChipModel:
        """Get the RFIC model (typed return)"""
        return self.model
    
    def update_rfic_info(self) -> None:
        """Update RFIC-specific visual information"""
        # This can be called when RFIC properties change
        # to refresh the visual display
        self._setup_rfic_styling()
        self._add_rfic_indicators()
