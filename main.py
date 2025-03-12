from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QPushButton,
)
from PySide6.QtCore import Qt
from scene import RFScene
from view import RFView
from chip import Chip
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RF CAD Tool")
        self.resize(1024, 768)

        self.scene = RFScene()
        self.view = RFView(self.scene)
        self.setCentralWidget(self.view)

        self.init_toolbar()

    def init_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setParent(self)
        toolbar.setFloatable(True)
        toolbar.setMovable(True)
        toolbar.setOrientation(Qt.Horizontal)
        toolbar.setFixedHeight(40)
        toolbar.setAllowedAreas(Qt.ToolBarArea.NoToolBarArea)

        # Center toolbar by moving it to the top center
        toolbar.move((self.width() - toolbar.sizeHint().width()) // 2, 0)

        add_chip_button = QPushButton("Add Chip")
        add_chip_button.clicked.connect(self.add_chip)
        toolbar.addWidget(add_chip_button)

        add_rfic_button = QPushButton("Add RFIC")
        add_rfic_button.clicked.connect(self.add_rfic)
        toolbar.addWidget(add_rfic_button)

        add_antenna_button = QPushButton("Add Antenna")
        add_antenna_button.clicked.connect(self.add_antenna)
        toolbar.addWidget(add_antenna_button)

        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.view.zoom_in)
        toolbar.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.view.zoom_out)
        toolbar.addWidget(zoom_out_button)

    def add_chip(self):
        chip = Chip(name="RFIC", pin_names=["IN", "OUT", "GND"])
        chip.setPos(len(self.scene.items()) * 70, 0)
        self.scene.addItem(chip)

    def add_rfic(self):
        print("Add RFIC")  # Placeholder for RFIC component

    def add_antenna(self):
        print("Add Antenna")  # Placeholder for Antenna component


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
