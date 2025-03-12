from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QGraphicsView,
    QGraphicsScene,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QToolBar,
    QPushButton,
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
import sys

from scene import RFScene
from view import RFView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RF CAD Tool")
        self.resize(1024, 768)

        # Central Graphics View and Scene
        self.scene = RFScene()
        self.view = RFView(self.scene)
        self.setCentralWidget(self.view)

        # Left Dock: Component Palette
        self.init_component_palette()

        # Right Dock: Property Editor
        self.init_property_editor()

        # Top Toolbar
        self.init_toolbar()

    def init_component_palette(self):
        dock = QDockWidget("Components", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        self.component_tree = ComponentTree()
        dock.setWidget(self.component_tree)

    def init_property_editor(self):
        dock = QDockWidget("Properties", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        self.property_table = QTableWidget(4, 2)
        self.property_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.property_table.setVerticalHeaderLabels(
            ["Name", "Type", "Function", "Description"]
        )

        for i in range(4):
            self.property_table.setItem(
                i, 0, QTableWidgetItem(self.property_table.verticalHeaderItem(i).text())
            )
            self.property_table.setItem(i, 1, QTableWidgetItem(""))

        dock.setWidget(self.property_table)

    def init_toolbar(self):
        toolbar = QToolBar("Tools")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(lambda: self.view.scale(1.1, 1.1))
        toolbar.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(lambda: self.view.scale(0.9, 0.9))
        toolbar.addWidget(zoom_out_button)


class ComponentTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)

        components = ["Chip", "RFIC", "Antenna", "Coupler", "Connection"]
        for component in components:
            item = QTreeWidgetItem([component])
            self.addTopLevelItem(item)

    def mousePressEvent(self, event):
        item = self.itemAt(
            self.viewport().mapFromGlobal(event.globalPosition().toPoint())
        )
        if item:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.text(0))
            drag.setMimeData(mime_data)
            drag.exec(Qt.MoveAction)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
