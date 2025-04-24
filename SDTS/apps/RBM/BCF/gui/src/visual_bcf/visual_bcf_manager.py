from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPen, QBrush, QColor
from typing import Dict, Any, Optional

from .scene import RFScene
from .view import RFView
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.src.models.chip import ChipModel


class VisualBCFManager(QWidget):
    """Manager for the visual BCF interface with graphics scene and view"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Visual BCF Manager")

        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create graphics scene and view
        self.scene = RFScene()
        self.view = RFView(self.scene)
        self.view.setSceneRect(-1000, -1000, 2000, 2000)  # Set a large scene rect
        self.view.setBackgroundBrush(Qt.darkGray)  # Set background color
        layout.addWidget(self.view)

        # Create control panel dock
        self.control_dock = QDockWidget("Controls")
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Add zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_in_button = QPushButton("+")
        self.zoom_out_button = QPushButton("-")
        self.reset_zoom_button = QPushButton("Reset")
        zoom_layout.addWidget(self.zoom_in_button)
        zoom_layout.addWidget(self.zoom_out_button)
        zoom_layout.addWidget(self.reset_zoom_button)
        control_layout.addLayout(zoom_layout)

        # Add component buttons
        self.add_band_button = QPushButton("Add Band")
        self.add_board_button = QPushButton("Add Board")
        self.add_rcc_button = QPushButton("Add RCC")

        control_layout.addWidget(self.add_band_button)
        control_layout.addWidget(self.add_board_button)
        control_layout.addWidget(self.add_rcc_button)

        self.control_dock.setWidget(control_widget)

        # Connect signals
        self.zoom_in_button.clicked.connect(self._on_zoom_in)
        self.zoom_out_button.clicked.connect(self._on_zoom_out)
        self.reset_zoom_button.clicked.connect(self._on_reset_zoom)
        self.add_band_button.clicked.connect(self._on_add_band)
        self.add_board_button.clicked.connect(self._on_add_board)
        self.add_rcc_button.clicked.connect(self._on_add_rcc)

    def _on_zoom_in(self):
        """Handle zoom in button click"""
        self.view.scale(1.2, 1.2)

    def _on_zoom_out(self):
        """Handle zoom out button click"""
        self.view.scale(1 / 1.2, 1 / 1.2)

    def _on_reset_zoom(self):
        """Handle reset zoom button click"""
        self.view.resetTransform()

    def _on_add_band(self):
        """Handle add band button click"""
        try:
            # Create band model and component
            band_model = ChipModel(name="Band", width=200, height=100)
            band_model.add_pin(0, 50, "Input")
            band_model.add_pin(200, 50, "Output")

            band_component = Chip(band_model)
            self.scene.add_component(band_component)
            self.data_changed.emit({"action": "add_band"})
        except Exception as e:
            self.error_occurred.emit(f"Error adding band: {str(e)}")

    def _on_add_board(self):
        """Handle add board button click"""
        try:
            # Create board model and component
            board_model = ChipModel(name="Board", width=150, height=150)
            board_model.add_pin(75, 0, "Input")
            board_model.add_pin(75, 150, "Output")

            board_component = Chip(board_model)
            self.scene.add_component(board_component)
            self.data_changed.emit({"action": "add_board"})
        except Exception as e:
            self.error_occurred.emit(f"Error adding board: {str(e)}")

    def _on_add_rcc(self):
        """Handle add RCC button click"""
        try:
            # Create RCC model and component
            rcc_model = ChipModel(name="RCC", width=100, height=100)
            rcc_model.add_pin(0, 50, "Input")
            rcc_model.add_pin(100, 50, "Output")

            rcc_component = Chip(rcc_model)
            self.scene.add_component(rcc_component)
            self.data_changed.emit({"action": "add_rcc"})
        except Exception as e:
            self.error_occurred.emit(f"Error adding RCC: {str(e)}")

    def update_scene(self, data: Dict[str, Any]):
        """Update the scene with new data"""
        try:
            # Clear existing items
            for component in self.scene.get_components():
                self.scene.remove_component(component)

            # TODO: Add items based on data
            pass
        except Exception as e:
            self.error_occurred.emit(f"Error updating scene: {str(e)}")
