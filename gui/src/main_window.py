from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from gui.custom_widgets.components.chip import Chip
from .scene import RFScene
from .view import RFView
from src.models.chip import ChipModel


class MainWindow(QMainWindow):
    """Main window for the RF CAD application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("RF CAD Tool")
        self.resize(1200, 800)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create scene and view
        self.scene = RFScene()
        self.view = RFView(self.scene)
        layout.addWidget(self.view)

        # Create toolbar
        self.create_toolbar()

        # Add a sample chip
        self.add_sample_chip()

    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Add Chip action
        add_chip_action = QAction("Add Chip", self)
        add_chip_action.triggered.connect(self.add_sample_chip)
        toolbar.addAction(add_chip_action)

    def add_sample_chip(self):
        """Add a sample chip to the scene"""
        chip_model = ChipModel(name="Sample Chip", width=100, height=100)
        chip_model.add_pin(0, 50, "Input")
        chip_model.add_pin(100, 50, "Output")

        chip_widget = Chip(chip_model)
        self.scene.add_component(chip_widget)
