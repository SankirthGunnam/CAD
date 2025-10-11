from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QTreeView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide6.QtCore import Qt, Signal, QAbstractItemModel, QModelIndex
from PySide6.QtGui import QColor, QIcon, QFont, QStandardItemModel, QStandardItem
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.controllers.base_controller import BaseController
from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView
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
                # This node is a group with children; do not mark as table
                child_node.view_type = "group"
            else:
                child_node.view_type = value  # e.g., "table"

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
    # Emitted when a top-level parent node is clicked in the tree
    # Args: parent_name, children_map (child_name -> view_type)
    parent_node_selected = Signal(str, dict)

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

        # Create content tree in place of tabs: parent nodes -> children; expanding child shows content widget
        self.content_tree = QTreeWidget()
        self.content_tree.setHeaderHidden(True)
        # Allow rows to grow based on embedded widgets
        self.content_tree.setUniformRowHeights(False)
        self.content_tree.itemExpanded.connect(self._on_content_item_expanded)
        self.content_tree.itemCollapsed.connect(self._on_content_item_collapsed)
        self.content_tree.itemClicked.connect(self._on_content_item_clicked)

        # Create breadcrumbs label above the tab widget
        self.breadcrumbs_label = QLabel("")
        self.breadcrumbs_label.setObjectName("legacyBreadcrumbs")
        self.breadcrumbs_label.setStyleSheet(
            "#legacyBreadcrumbs { padding: 6px 8px; font-weight: bold; color: #444; }"
        )

        # Right container holds breadcrumbs + tabs vertically
        self.right_container = QWidget()
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.breadcrumbs_label)
        # Single-child container (used when a leaf is selected on the left tree)
        self.single_child_container = QWidget()
        _single_layout = QVBoxLayout(self.single_child_container)
        _single_layout.setContentsMargins(4, 4, 4, 4)
        _single_layout.setSpacing(4)
        self.single_child_container.setVisible(False)
        right_layout.addWidget(self.single_child_container)
        right_layout.addWidget(self.content_tree)

        # Add widgets to layout (left: tree, right: breadcrumbs+tabs)
        layout.addWidget(self.tree_dock)
        layout.addWidget(self.right_container)

        # Connect signals
        self.tree_view.clicked.connect(self._on_tree_item_clicked)
        # content tree drives view

    def _update_breadcrumbs(self, parts):
        try:
            text = " > ".join([p for p in parts if p])
            self.breadcrumbs_label.setText(text)
        except Exception:
            pass

    def _find_path_to_key(self, target_name: str) -> List[str]:
        """Return hierarchical path list from top-level to the key matching target_name."""
        print(f"[_find_path_to_key] target={target_name}")
        def recurse(tree: Dict[str, Any], path: List[str]) -> Optional[List[str]]:
            for key, value in tree.items():
                new_path = path + [key]
                # Debug current step
                # print(f"  visiting key={key}, path={new_path}")
                if key == target_name:
                    return new_path
                if isinstance(value, dict):
                    found = recurse(value, new_path)
                    if found:
                        return found
            return None

        found_path = recurse(self.component_structure, [])
        print(f"[_find_path_to_key] found_path={found_path}")
        return found_path or []

    def _breadcrumbs_from_content_item(self, item: QTreeWidgetItem) -> List[str]:
        """Build full breadcrumbs path based on the current content-tree item and global structure."""
        # Collect names from the content tree item up to its top-level
        names: List[str] = []
        cur = item
        while cur is not None:
            names.append(cur.text(0))
            cur = cur.parent()
        names.reverse()  # Now from selected-parent -> ... -> current item

        # Prepend any higher-level ancestors from component_structure
        if names:
            selected_parent_name = names[0]
            prefix = self._find_path_to_key(selected_parent_name)
            if prefix and prefix[-1] == selected_parent_name:
                # Avoid duplicating the selected parent name
                crumbs = ["Legacy"] + prefix + names[1:]
                print(f"[_breadcrumbs_from_content_item in ] names={names}, prefix={prefix}, crumbs={crumbs}")
                return crumbs
        crumbs = ["Legacy"] + names
        print(f"[_breadcrumbs_from_content_item] names={names}, crumbs={crumbs}")
        return crumbs

    def _find_parent_of_child(self, child_name: str) -> Optional[str]:
        for parent_name, children in self.component_structure.items():
            if isinstance(children, dict) and child_name in children:
                return parent_name
        return None

    def _get_children_for_parent_name(self, parent_name: str) -> Dict[str, Any]:
        """Return the children dict for a parent, searching recursively in component_structure."""
        def recurse(tree: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            for key, value in tree.items():
                if key == parent_name and isinstance(value, dict):
                    return value
                if isinstance(value, dict):
                    found = recurse(value)
                    if found is not None:
                        return found
            return None

        result = recurse(self.component_structure)
        return result if isinstance(result, dict) else {}

    # Tabs removed; content tree manages selection and embedded views

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
                "Band Group A": {  # sub-parent with sub-children
                    "Band 1": "table",
                    "Band 2": "table",
                },
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
        # Initialize right-pane content tree with default parent
        self._populate_content_tree("Bands")

    def _populate_content_tree(self, selected_parent: Optional[str] = None, selected_child: Optional[str] = None):
        try:
            self.content_tree.clear()
            # Show only the selected parent (default to Bands) and its children
            parent_name = selected_parent or "Bands"
            parent_children = self._get_children_for_parent_name(parent_name)
            parent_item = QTreeWidgetItem([parent_name])
            parent_item.setData(0, Qt.UserRole, {"type": "parent"})
            print('parent_children', parent_children)
            if isinstance(parent_children, dict):
                for child_name, view_val in parent_children.items():
                    child_item = QTreeWidgetItem([child_name])
                    if isinstance(view_val, dict):
                        # This is a group node, not a table leaf
                        child_item.setData(0, Qt.UserRole, {"type": "group"})
                        # Add its own children as leaf nodes
                        for grandchild_name, grandchild_view in view_val.items():
                            grandchild_item = QTreeWidgetItem([grandchild_name])
                            grandchild_item.setData(0, Qt.UserRole, {"type": "child", "view_type": grandchild_view})
                            child_item.addChild(grandchild_item)
                            # Pre-embed table for grandchild
                            if grandchild_item.childCount() == 0 and grandchild_view == "table":
                                self._embed_child_view(grandchild_item, grandchild_name, grandchild_view, update_breadcrumbs=False)
                    else:
                        # Leaf node
                        child_item.setData(0, Qt.UserRole, {"type": "child", "view_type": view_val})
                        # Pre-embed the child's widget as a grandchild so it's ready by default
                        if child_item.childCount() == 0 and view_val == "table":
                            self._embed_child_view(child_item, child_name, view_val, update_breadcrumbs=False)
                    parent_item.addChild(child_item)

            self.content_tree.addTopLevelItem(parent_item)
            self.content_tree.expandAll()
            # Set breadcrumbs to Legacy > parent
            self._update_breadcrumbs(["Legacy", parent_name])

            # If a specific child is requested, expand and embed it once
            if selected_child:
                for j in range(parent_item.childCount()):
                    child_item = parent_item.child(j)
                    if child_item.text(0) == selected_child:
                        self.content_tree.expandItem(parent_item)
                        if child_item.childCount() == 0:
                            view_type = child_item.data(0, Qt.UserRole).get("view_type")
                            self._embed_child_view(child_item, selected_child, view_type)
                        self.content_tree.setCurrentItem(child_item)
                        self._update_breadcrumbs(["Legacy", parent_name, selected_child])
                        break
        except Exception as e:
            self.error_occurred.emit(f"Error populating content tree: {str(e)}")

    def _on_content_item_expanded(self, item: QTreeWidgetItem):
        try:
            node_info = item.data(0, Qt.UserRole) or {}
            name = item.text(0)
            if node_info.get("type") == "parent":
                # Update breadcrumbs for parent with full hierarchy
                crumbs = self._breadcrumbs_from_content_item(item)
                self._update_breadcrumbs(crumbs)
            elif node_info.get("type") == "child":
                # For child expansion, embed the corresponding view as a grandchild row
                view_type = node_info.get("view_type")
                # Only embed if not already embedded (no grandchild yet)
                if item.childCount() == 0:
                    self._embed_child_view(item, name, view_type)
                # Update breadcrumbs with full hierarchy
                crumbs = self._breadcrumbs_from_content_item(item)
                self._update_breadcrumbs(crumbs)
        except Exception as e:
            self.error_occurred.emit(f"Error handling item expansion: {str(e)}")

    def _on_content_item_collapsed(self, item: QTreeWidgetItem):
        try:
            node_info = item.data(0, Qt.UserRole) or {}
            name = item.text(0)
            if node_info.get("type") == "child":
                # Remove embedded widget if any by removing grandchild
                while item.childCount() > 0:
                    grandchild = item.child(0)
                    self.content_tree.removeItemWidget(grandchild, 0)
                    item.removeChild(grandchild)
                # Update breadcrumbs back to parent
                parent_item = item.parent()
                parent_name = parent_item.text(0) if parent_item else ""
                self._update_breadcrumbs(["Legacy", parent_name])
        except Exception as e:
            self.error_occurred.emit(f"Error handling item collapse: {str(e)}")

    def _embed_child_view(self, item: QTreeWidgetItem, name: str, view_type: str, update_breadcrumbs: bool = True):
        try:
            # Create the view and set controller similar to open_tab logic
            if view_type in self.views:
                print(f"Embedding view for {name}")
                view = self.views[view_type]()
                if view_type == "table":
                    controller_module = importlib.import_module(
                        "apps.RBM5.BCF.source.controllers.table_controller"
                    )
                    controller_class = getattr(controller_module, "TableController")
                else:
                    controller_module = importlib.import_module(
                        f"apps.RBM5.BCF.source.controllers.{view_type}_controller"
                    )
                    controller_class = getattr(
                        controller_module, f"{view_type.title()}Controller"
                    )
                controller = controller_class()
                controller.set_view(view)

                # Put the view as the widget for this child item
                table_item = QTreeWidgetItem(item)
                item.addChild(table_item)
                self.content_tree.setItemWidget(table_item, 0, view)
                # Ensure the row height accommodates the widget
                try:
                    table_item.setSizeHint(0, view.sizeHint())
                except Exception:
                    import traceback
                    traceback.print_exc()

                if update_breadcrumbs:
                    parent_item = item.parent()
                    parent_name = parent_item.text(0) if parent_item else ""
                    self._update_breadcrumbs(["Legacy", parent_name, name])
                print(f"Embedded view for {name}")
            else:
                self.error_occurred.emit(f"View type {view_type} not found for {name}")
        except Exception as e:
            self.error_occurred.emit(f"Error embedding child view: {str(e)}")

    def _on_content_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        try:
            node_info = item.data(0, Qt.UserRole) or {}
            name = item.text(0)
            if node_info.get("type") == "parent":
                # Select and expand parent; update breadcrumbs
                self.content_tree.expandItem(item)
                self._update_breadcrumbs(["Legacy", name])
            elif node_info.get("type") == "child":
                # Ensure parent is expanded and embed view once; update breadcrumbs
                parent_item = item.parent()
                parent_name = parent_item.text(0) if parent_item else ""
                if parent_item is not None:
                    self.content_tree.expandItem(parent_item)
                # Avoid duplicate embedding: only embed if no grandchild exists
                if item.childCount() == 0:
                    view_type = node_info.get("view_type")
                    self._embed_child_view(item, name, view_type)
                self._update_breadcrumbs(["Legacy", parent_name, name])
            elif node_info.get("type") == "group":
                # Group nodes should expand/collapse to show their children
                self.content_tree.expandItem(item)
                parent_item = item.parent()
                parent_name = parent_item.text(0) if parent_item else ""
                self._update_breadcrumbs(["Legacy", parent_name, name])
        except Exception as e:
            self.error_occurred.emit(f"Error handling item click: {str(e)}")

    def _on_tree_item_clicked(self, index: QModelIndex):
        """Handle tree item click"""
        try:
            item = index.internalPointer()
            if not item:
                return

            # If a top-level parent (direct child of root) is clicked, rebuild right pane for that parent
            if item.parent == self.tree_model.root:
                # Show tree; hide single child
                self.single_child_container.setVisible(False)
                self.content_tree.setVisible(True)
                print(f"Tree item clicked parent: {item.name}")
                self._populate_content_tree(item.name)
                return

            # Only handle leaf items (no sub-children): show only the selected child's widget
            if item.parent and item.parent != self.tree_model.root:
                parent_name = item.parent.name
                # Check if this child has sub-children in the component structure (search nested)
                child_map = self._get_children_for_parent_name(parent_name)
                child_value = child_map.get(item.name)
                if isinstance(child_value, dict):
                    # It has sub-children: rebuild right pane for this child as a new parent
                    self.single_child_container.setVisible(False)
                    self.content_tree.setVisible(True)
                    self._populate_content_tree(item.name)
                else:
                    # Leaf: show only widget
                    self.content_tree.setVisible(False)
                    self.single_child_container.setVisible(True)
                    self._clear_single_child_container()
                    self._add_single_child_widget(parent_name, item.name, item.view_type)
                return
        except Exception as e:
            self.error_occurred.emit(
                f"Error handling tree item click: {str(e)}")

    def _select_parent_in_content_tree(self, parent_name: str) -> None:
        try:
            for i in range(self.content_tree.topLevelItemCount()):
                parent_item = self.content_tree.topLevelItem(i)
                if parent_item and parent_item.text(0) == parent_name:
                    self.content_tree.setCurrentItem(parent_item)
                    self.content_tree.expandItem(parent_item)
                    self._update_breadcrumbs(["Legacy", parent_name])
                    return
        except Exception as e:
            self.error_occurred.emit(f"Error selecting parent in content tree: {str(e)}")

    def open_tab(self, name: str, view_type: str):
        """Select the child under its parent in the content tree and embed its view."""
        try:
            parent_name = self._find_parent_of_child(name) or ""
            if not parent_name:
                self.error_occurred.emit(f"Parent not found for child '{name}'")
                return
            # Locate parent and child in content tree
            for i in range(self.content_tree.topLevelItemCount()):
                parent_item = self.content_tree.topLevelItem(i)
                if not parent_item or parent_item.text(0) != parent_name:
                    continue
                # Expand/select parent
                self.content_tree.expandItem(parent_item)
                # Find child item
                for j in range(parent_item.childCount()):
                    child_item = parent_item.child(j)
                    if child_item and child_item.text(0) == name:
                        self.content_tree.setCurrentItem(child_item)
                        # Embed view on demand
                        self._embed_child_view(child_item, name, view_type)
                        return
            self.error_occurred.emit(f"Child '{name}' not found under parent '{parent_name}'")
        except Exception as e:
            self.error_occurred.emit(f"Error selecting child in content tree: {str(e)}")

    # Tabs removed; no close_tab

    def _clear_single_child_container(self) -> None:
        try:
            layout = self.single_child_container.layout()
            if not layout:
                return
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
        except Exception as e:
            self.error_occurred.emit(f"Error clearing single child container: {str(e)}")

    def _add_single_child_widget(self, parent_name: str, child_name: str, view_type: str) -> None:
        try:
            if view_type in self.views:
                view = self.views[view_type]()
                # Map view_type to controller
                if view_type == "table":
                    controller_module = importlib.import_module(
                        "apps.RBM5.BCF.source.controllers.table_controller"
                    )
                    controller_class = getattr(controller_module, "TableController")
                else:
                    controller_module = importlib.import_module(
                        f"apps.RBM5.BCF.source.controllers.{view_type}_controller"
                    )
                    controller_class = getattr(
                        controller_module, f"{view_type.title()}Controller"
                    )
                controller = controller_class()
                controller.set_view(view)

                # Add to container and update breadcrumbs
                self.single_child_container.layout().addWidget(view)
                self._update_breadcrumbs(["Legacy", parent_name, child_name])
            else:
                self.error_occurred.emit(
                    f"View type {view_type} not found for {child_name}")
        except Exception as e:
            self.error_occurred.emit(
                f"Error adding single child widget: {str(e)}")

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
            # Clear content tree
            self.content_tree.clear()
            # Clear tree model
            if hasattr(self, 'tree_model'):
                self.tree_model = None
        except Exception as e:
            self.error_occurred.emit(f"Error during cleanup: {str(e)}")
