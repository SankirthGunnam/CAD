from PySide6.QtWidgets import (

from apps.RBM5.BCF.source.models.base_model import BaseModel
from apps.RBM5.BCF.source.controllers.base_controller import BaseController
from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView

    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QTreeView,
    QTabWidget,
    QLabel,
)
from PySide6.QtCore import Qt, Signal, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QColor, QIcon, QFont
from typing import Dict, Any, Optional, List, Union
import importlib
import os
import sys

# Add the necessary paths to sys.path
sys.path.append(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class TreeItem:
    """Internal class to represent tree items"""

    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        self.parent = parent
        self.icon = None
        self.font = QFont()
        self.view_type = None  # Store the type of view to load

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
            # Set view type based on the value
            if isinstance(value, dict):
                child_node.view_type = "table"  # Default view type
            else:
                child_node.view_type = value  # Use the value as view type

            # Customize font and icon
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
        elif role == Qt.UserRole:
            return node.view_type
        return None

    def get_node(self, index):
        return index.internalPointer() if index.isValid() else self.root


class LegacyBCFManager(QWidget):
    """Legacy BCF Manager that provides a dynamic tab-based interface"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Legacy BCF Manager")
        self.setup_ui()
        self.load_views()
        self.setup_tree()

    def setup_ui(self):
        """Setup the main UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tree view dock
        self.tree_dock = QDockWidget("Components", self)
        self.tree_dock.setFeatures(
            QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable
        )
        self.tree_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_dock.setWidget(self.tree_view)

        # Create tab widget for center area
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Add widgets to layout
        layout.addWidget(self.tree_dock)
        layout.addWidget(self.tab_widget)

        # Connect signals
        self.tree_view.clicked.connect(self._on_tree_item_clicked)

    def load_views(self):
        """Load available views from the views directory"""
        self.views = {}
        views_dir = os.path.join(os.path.dirname(__file__), "views")

        for file in os.listdir(views_dir):
            if file.endswith("_view.py"):
                view_name = file[:-8]  # Remove '_view.py'
                try:
                    module = importlib.import_module(
                        f".views.{view_name}_view", package=__package__
                    )
                    view_class = getattr(module, f"{view_name.title()}View")
                    self.views[view_name] = view_class
                except Exception as e:
                    self.error_occurred.emit(
                        f"Error loading view {view_name}: {str(e)}"
                    )

    def setup_tree(self):
        """Setup the tree structure"""
        self.component_structure = {
            "Bands": {
                "Band 1": "table",
                "Band 2": "table",
                "Band 3": "table",
            },
            "Boards": {
                "Board 1": "table",
                "Board 2": "table",
                "Board 3": "table",
            },
            "RCCs": {
                "RCC 1": "table",
                "RCC 2": "table",
                "RCC 3": "table",
            },
        }

        self.tree_model = TreeModel(self.component_structure)
        self.tree_view.setModel(self.tree_model)

    def _on_tree_item_clicked(self, index: QModelIndex):
        """Handle tree item click"""
        try:
            item = index.internalPointer()
            if (
                item.parent and item.parent != self.tree_model.root
            ):  # Only handle leaf items
                self.open_tab(item.name, item.view_type)
        except Exception as e:
            self.error_occurred.emit(
                f"Error handling tree item click: {str(e)}")

    def open_tab(self, name: str, view_type: str):
        """Open a new tab with the specified view"""
        try:
            # Check if tab already exists
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == name:
                    self.tab_widget.setCurrentIndex(i)
                    return

            # Create new view
            if view_type in self.views:
                view = self.views[view_type]()

                # Create and set up controller
                controller_module = importlib.import_module(
                    f"controllers.{view_type}_controller", package="src"
                )
                controller_class = getattr(
                    controller_module, f"{view_type.title()}Controller"
                )
                controller = controller_class()
                controller.set_view(view)

                # Add tab
                self.tab_widget.addTab(view, name)
                self.tab_widget.setCurrentWidget(view)
            else:
                self.error_occurred.emit(f"View type {view_type} not found")
        except Exception as e:
            self.error_occurred.emit(f"Error opening tab: {str(e)}")

    def close_tab(self, index: int):
        """Close the tab at the specified index"""
        self.tab_widget.removeTab(index)

    def update_table(self, data: dict):
        """Update table with new data"""
        try:
            # Emit data changed signal
            self.data_changed.emit(data)
        except Exception as e:
            self.error_occurred.emit(f"Error updating table: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        try:
            # Close all tabs
            self.tab_widget.clear()
            # Clear tree model
            if hasattr(self, 'tree_model'):
                self.tree_model = None
        except Exception as e:
            self.error_occurred.emit(f"Error during cleanup: {str(e)}")
