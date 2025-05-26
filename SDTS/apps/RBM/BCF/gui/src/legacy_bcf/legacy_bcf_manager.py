from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDockWidget,
    QTreeView,
    QStackedWidget,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QColor, QIcon
from typing import Dict, Any, Optional, List, Union


class TreeItem:
    """Internal class to represent tree items"""

    def __init__(self, key: str, value: Any, parent=None):
        self.parent_item = parent
        self.key = key
        self.value = value
        self.child_items = []


class TreeModel(QAbstractItemModel):
    """Model that takes a dictionary and creates a tree structure"""

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.root_item = TreeItem("Root", None)
        self.setup_model_data(data)

    def setup_model_data(self, data: Dict[str, Any]):
        """Initialize the model with data"""
        for key, value in data.items():
            if isinstance(value, dict):
                # Create parent item
                parent_item = TreeItem(key, None, self.root_item)
                self.root_item.child_items.append(parent_item)

                # Add children
                for child_key, child_value in value.items():
                    child_item = TreeItem(child_key, child_value, parent_item)
                    parent_item.child_items.append(child_item)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        """Create an index for the given row and column under the parent"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child_items[row]
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Return the parent of the given index"""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent_item

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(
            parent_item.child_items.index(child_item), 0, parent_item
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows under the given parent"""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return len(parent_item.child_items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns"""
        return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return the data for the given role and index"""
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            return item.key

        elif role == Qt.BackgroundRole:
            if item.value:
                colors = {
                    "Band": QColor(200, 230, 255),  # Light blue
                    "Board": QColor(255, 230, 200),  # Light orange
                    "RCC": QColor(230, 255, 200),  # Light green
                }
                return colors.get(item.value, QColor(255, 255, 255))

        elif role == Qt.UserRole:
            return item.value

        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """Set the data for the given role and index"""
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            item = index.internalPointer()
            item.value = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """Return the header data"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "Components"
        return None


class LegacyBCFManager(QWidget):
    """Legacy BCF Manager that provides a table-based interface"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Legacy BCF Manager")

        # Create main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tree view dock
        self.tree_dock = QDockWidget("Components", self)
        self.tree_dock.setFeatures(
            QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable
        )
        self.tree_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)

        # Define component structure
        self.component_structure = {
            "Bands": {"Band 1": "Band", "Band 2": "Band", "Band 3": "Band"},
            "Boards": {"Board 1": "Board", "Board 2": "Board", "Board 3": "Board"},
            "RCCs": {"RCC 1": "RCC", "RCC 2": "RCC", "RCC 3": "RCC"},
        }

        # Create and set model
        self.tree_model = TreeModel(self.component_structure)
        self.tree_view.setModel(self.tree_model)
        self.tree_dock.setWidget(self.tree_view)

        # Create stacked widget for center area
        self.stacked_widget = QStackedWidget()

        # Create table widget for the first page
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Status"])
        self._populate_table()  # Add initial data
        self.stacked_widget.addWidget(self.table)

        # Add a placeholder page
        placeholder = QLabel("Select a component from the tree view")
        placeholder.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(placeholder)

        # Add widgets to layout
        layout.addWidget(self.tree_dock)
        layout.addWidget(self.stacked_widget)

        # Set initial state
        self.stacked_widget.setCurrentIndex(1)  # Show placeholder

        # Connect signals
        self.tree_view.clicked.connect(self._on_tree_item_clicked)

    def _populate_table(self):
        """Populate table with initial data"""
        # Add sample data
        self.table.setRowCount(3)

        # Sample data
        data = [
            ("001", "Sample Band", "Band", "Active"),
            ("002", "Sample Board", "Board", "Inactive"),
            ("003", "Sample RCC", "RCC", "Active"),
        ]

        for row, (id_, name, type_, status) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(id_))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(type_))
            self.table.setItem(row, 3, QTableWidgetItem(status))

    def _on_tree_item_clicked(self, index: QModelIndex):
        """Handle tree item click"""
        try:
            item = index.internalPointer()
            if (
                item.parent_item and item.parent_item != self.tree_model.root_item
            ):  # Only handle leaf items
                # Switch to table view
                self.stacked_widget.setCurrentIndex(0)
                self.data_changed.emit({"component": item.key, "type": item.value})
            else:
                # Switch to placeholder for group items
                self.stacked_widget.setCurrentIndex(1)
        except Exception as e:
            self.error_occurred.emit(f"Error handling tree item click: {str(e)}")

    def update_table(self, data: dict):
        """Update table with new data"""
        try:
            # Clear existing items
            self.table.clear()

            # Set table dimensions
            if data:
                rows = len(data)
                cols = len(next(iter(data.values()))) if data else 0
                self.table.setRowCount(rows)
                self.table.setColumnCount(cols)

                # Fill table
                for row, (key, values) in enumerate(data.items()):
                    for col, value in enumerate(values):
                        item = QTableWidgetItem(str(value))
                        self.table.setItem(row, col, item)

            self.data_changed.emit(data)
        except Exception as e:
            self.error_occurred.emit(f"Error updating table: {str(e)}")
