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
from PySide6.QtGui import QColor, QIcon, QFont
from typing import Dict, Any, Optional, List, Union


class TreeItem:
    """Internal class to represent tree items"""

    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        self.parent = parent
        self.icon = None
        self.font = QFont()

    def append_child(self, child):
        self.children.append(child)
        child.parent = self

    def child(self, row):
        return self.children[row] if 0 <= row < len(self.children) else None

    def child_count(self):
        return len(self.children)

    def row(self):
        return self.parent.children.index(self) if self.parent else 0


class TreeModel(QAbstractItemModel):
    """Model that takes a dictionary and creates a tree structure"""

    def __init__(self, data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.root = TreeItem("Root")
        self._build_tree(self.root, data)

    def _build_tree(self, parent_node, tree_dict):
        for key, value in tree_dict.items():
            child_node = TreeItem(key)
            # 🎨 Customize font and icon
            font = QFont()
            font.setBold(True if not parent_node.parent else False)
            child_node.font = font
            child_node.icon = (
                QIcon.fromTheme("folder")
                if isinstance(value, dict)
                else QIcon.fromTheme("text-x-generic")
            )
            parent_node.append_child(child_node)

            if isinstance(value, dict):
                self._build_tree(child_node, value)
            if isinstance(value, set):
                for item in value:
                    temp_node = TreeItem(item)
                    temp_node.parent = child_node
                    child_node.append_child(temp_node)

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_node = self.get_node(parent)
        child_node = parent_node.child(row)
        if child_node:
            return self.createIndex(row, column, child_node)
        return QModelIndex()

    def parent(self, index):
        node = self.get_node(index)
        if not node or not node.parent or node.parent == self.root:
            return QModelIndex()
        return self.createIndex(node.parent.row(), 0, node.parent)

    def rowCount(self, parent=QModelIndex()):
        node = self.get_node(parent)
        return node.child_count()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        node = self.get_node(index)
        if not node:
            return None

        if role == Qt.DisplayRole:
            return node.name
        elif role == Qt.FontRole:
            return node.font
        elif role == Qt.DecorationRole:
            return node.icon
        return None

    def setData(self, index, value, role=Qt.EditRole):
        node = self.get_node(index)
        if role == Qt.EditRole:
            node.name = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def get_node(self, index):
        return index.internalPointer() if index.isValid() else self.root


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
            "Animals": {
                "Mammals": {"Dog", "Cat"},
                "Reptiles": {"Snake", "Lizard"},
            },
            "Plants": {
                "Trees": {"Oak", "Pine"},
                "Flowers": {"Rose", "Lily"},
            },
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
                item.parent and item.parent != self.tree_model.root
            ):  # Only handle leaf items
                # Switch to table view
                self.stacked_widget.setCurrentIndex(0)
                self.data_changed.emit({"component": item.name, "type": item.name})
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
