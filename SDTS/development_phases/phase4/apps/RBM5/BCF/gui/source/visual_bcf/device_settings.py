"""
Device Settings View for Visual BCF MVC Pattern

This module provides the DeviceSettingsView class with a simple vertical layout
containing two tables: All Devices and Selected Devices.
"""

import typing
from PySide6.QtWidgets import (
    QVBoxLayout,
    QTreeView,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QFrame,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
    QMenu,
    QMessageBox,
    QWidget,
    QInputDialog,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from apps.RBM5.BCF.config.constants.tabs import DeviceSettings

from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView
if typing.TYPE_CHECKING:
    from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import (
        DeviceSettingsModel,
    )


class AllDevicesTree(QTreeView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("AllDevicesTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(200)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._model = model
        
        print(f"✓ All Devices tree initialized with parent: {parent}")
        print(f"✓ All Devices tree model before setting: {model}")
        print('tree model type', type(model), model)
        if model is not None:
            self.setModel(model)
            self.expandAll()
            print(f"✓ All Devices tree initialized with model: {model}")
        else:
            print("❌ All Devices tree model is None - not setting model")

    def _show_context_menu(self, position):
        """Show context menu for table row operations"""
        if not self.selectionModel().hasSelection():
            return
            
        menu = QMenu(self)
        
        add_action = QAction("Add Child", self)
        add_action.triggered.connect(self._add_child)
        menu.addAction(add_action)

        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
        # Editing handled via delegate, no direct menu edit needed
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(position))

    def _delete_selected_row(self):
        """Delete the selected node after confirmation"""
        if not self.selectionModel().hasSelection():
            return
        idx = self.currentIndex()
        if not idx.isValid():
            return
        model = self.model()
        if not model:
            return
        label = model.data(idx.sibling(idx.row(), 0))
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Node",
            f"Are you sure you want to delete '{label}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            pass
            # Remove the subtree
           # self.expandAll()

    def _add_child(self):
        model = self.model()
        if not model:
            return
        idx = self.currentIndex()
        parent_id = int(idx.internalId()) if idx.isValid() else None
        try:
            new_id = model.add_child(parent_id)
            self.expandAll()
            sel = model.index_for_id(new_id, 1) if hasattr(model, 'index_for_id') else QModelIndex()
            if sel.isValid():
                self.setCurrentIndex(sel)
                self.edit(sel)
        except Exception:
            pass

    # Editing is handled via an item delegate installed by the parent view

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self._delete_selected_row()
        else:
            super().keyPressEvent(event)

    def column_headers(self):
        return ["Property", "Value"]


class MipiDevicesTree(QTreeView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self._parent = parent
        self.setObjectName("MipiDevicesTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(200)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._model = model
        
        if model is not None:
            self.setModel(model)
            self.expandAll()

    def _show_context_menu(self, position):
        """Show context menu for table row operations"""
        if not self.selectionModel().hasSelection():
            return
            
        menu = QMenu(self)
        
        add_action = QAction("Add Child", self)
        add_action.triggered.connect(self._add_child)
        menu.addAction(add_action)

        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
        # Editing handled via delegate
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(position))

    def _delete_selected_row(self):
        """Delete the selected node after confirmation"""
        if not self.selectionModel().hasSelection():
            return
        idx = self.currentIndex()
        if not idx.isValid():
            return
        model = self.model()
        if not model:
            return
        label = model.data(idx.sibling(idx.row(), 0))
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Node",
            f"Are you sure you want to delete '{label}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            controller = getattr(self._parent, 'controller', None)
            if controller and hasattr(controller, 'delete_row'):
                controller.delete_row(int(idx.internalId()), tree='mipi')

    def _add_child(self):
        model = self.model()
        if not model:
            return
        idx = self.currentIndex()
        parent_id = int(idx.internalId()) if idx.isValid() else None
        try:
            new_id = model.add_child(parent_id)
            self.expandAll()
            sel = model.index_for_id(new_id, 1) if hasattr(model, 'index_for_id') else QModelIndex()
            if sel.isValid():
                self.setCurrentIndex(sel)
                self.edit(sel)
        except Exception:
            pass

    # Editing is handled via an item delegate

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self._delete_selected_row()
        else:
            super().keyPressEvent(event)

    def column_headers(self):
        return ["Property", "Value"]


class GpioDevicesTree(QTreeView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self._parent = parent
        self.setObjectName("GpioDevicesTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(200)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._model = model
        
        if model is not None:
            self.setModel(model)
            self.expandAll()

    def _show_context_menu(self, position):
        """Show context menu for table row operations"""
        if not self.selectionModel().hasSelection():
            return
            
        menu = QMenu(self)
        
        add_action = QAction("Add Child", self)
        add_action.triggered.connect(self._add_child)
        menu.addAction(add_action)

        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
        # Editing handled via delegate
        
        # Show menu at cursor position
        menu.exec(self.mapToGlobal(position))

    def _delete_selected_row(self):
        """Delete the selected node after confirmation"""
        if not self.selectionModel().hasSelection():
            return
        idx = self.currentIndex()
        if not idx.isValid():
            return
        model = self.model()
        if not model:
            return
        label = model.data(idx.sibling(idx.row(), 0))
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Node",
            f"Are you sure you want to delete '{label}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            controller = getattr(self._parent, 'controller', None)
            if controller and hasattr(controller, 'delete_row'):
                controller.delete_row(int(idx.internalId()), tree='gpio')

    def _add_child(self):
        model = self.model()
        if not model:
            return
        idx = self.currentIndex()
        parent_id = int(idx.internalId()) if idx.isValid() else None
        try:
            new_id = model.add_child(parent_id)
            self.expandAll()
            sel = model.index_for_id(new_id, 1) if hasattr(model, 'index_for_id') else QModelIndex()
            if sel.isValid():
                self.setCurrentIndex(sel)
                self.edit(sel)
        except Exception:
            pass

    # Editing is handled via an item delegate

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self._delete_selected_row()
        else:
            super().keyPressEvent(event)

    def column_headers(self):
        return ["Property", "Value"]


class SectionAccordion(QTreeWidget):
    def __init__(self, parent: QWidget, sections: list[tuple[str, QTreeView]]):
        super().__init__(parent)
        self._parent = parent
        self.setColumnCount(1)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(12)
        self.setAnimated(True)
        self.setVerticalScrollMode(QTreeView.ScrollPerPixel)
        # Build sections
        self._sections: list[dict] = []
        self._top_items: list[QTreeWidgetItem] = []
        for title, tree in sections:
            top = QTreeWidgetItem([title])
            self.addTopLevelItem(top)
            child = QTreeWidgetItem([""])
            top.addChild(child)
            child.setFirstColumnSpanned(True)
            section_widget = self._make_section_widget(title, tree)
            self.setItemWidget(child, 0, section_widget)
            self._sections.append({"top": top, "child": child, "widget": section_widget, "tree": tree})
            self._top_items.append(top)
        # Only one open at a time
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)
        # Start with first expanded
        if self._top_items:
            self.expandItem(self._top_items[0])
        self._reflow()


    def _on_item_expanded(self, item: QTreeWidgetItem):
        if item.parent() is not None:
            return
        for other in self._top_items:
            if other is not item and other.isExpanded():
                self.collapseItem(other)
        self._reflow()

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        if item.parent() is not None:
            return
        self._reflow()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self) -> None:
        # Allocate available viewport height to the expanded section's content row
        viewport_h = self.viewport().height()
        header_h = 0
        for top in self._top_items:
            header_h += max(0, self.visualItemRect(top).height())
        available = max(120, viewport_h - header_h - 8)
        expanded_top = None
        for top in self._top_items:
            if top.isExpanded():
                expanded_top = top
                break
        for sec in self._sections:
            child: QTreeWidgetItem = sec["child"]
            if sec["top"] is expanded_top:
                sec["widget"].setMinimumHeight(available)
                sec["widget"].setMaximumHeight(available)
                child.setSizeHint(0, QSize(0, available))
            else:
                sec["widget"].setMinimumHeight(0)
                sec["widget"].setMaximumHeight(0)
                child.setSizeHint(0, QSize(0, 0))
        self.doItemsLayout()

    def _make_section_widget(self, title: str, tree: QTreeView) -> QWidget:
        container = QFrame(self)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        header = self._make_header_bar(title, tree)
        layout.addLayout(header)
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(tree)
        return container

    def _make_header_bar(self, title: str, tree: QTreeView):
        bar = QHBoxLayout()
        # No title label; section title is shown on the accordion item
        btn_expand = QToolButton(self)
        btn_expand.setText("Expand All")
        btn_expand.clicked.connect(tree.expandAll)
        btn_collapse = QToolButton(self)
        btn_collapse.setText("Collapse All")
        btn_collapse.clicked.connect(tree.collapseAll)
        # Add New Device button for MIPI and GPIO sections only
        btn_add = None
        if isinstance(tree, (MipiDevicesTree, GpioDevicesTree)):
            btn_add = QToolButton(self)
            btn_add.setText("Add Device")
            def _on_add_device():
                try:
                    # Show ChipSelectionDialog and send result via controller signal
                    from apps.RBM5.BCF.gui.source.visual_bcf.chip_selection_dialog import ChipSelectionDialog
                    import apps.RBM5.BCF.source.RDB.paths as paths
                    # Use controller's model to fetch all devices table
                    dm = self._parent.model
                    all_devices = dm.rdb[paths.DCF_DEVICES]
                    dialog = ChipSelectionDialog(all_devices, self)
                    def _emit_selected(data):
                        # Call controller.add_row to add to the appropriate tree; scene will update via signals
                        controller = getattr(self._parent, 'controller', None)
                        if controller and hasattr(controller, 'add_row'):
                            device_name = data.get('Name') or data.get('name') or "New Device"
                            component_type = data.get('Component Type', 'chip')
                            tree_key = 'mipi' if isinstance(tree, MipiDevicesTree) else ('gpio' if isinstance(tree, GpioDevicesTree) else 'mipi')
                            try:
                                controller.add_row(device_name, component_type, tree=tree_key)
                            except Exception:
                                pass
                    dialog.component_selected.connect(_emit_selected)
                    dialog.exec()
                except Exception:
                    print("❌ Error adding device")
                    import traceback
                    traceback.print_exc()

            btn_add.clicked.connect(_on_add_device)
        bar.addStretch(1)
        bar.addWidget(btn_expand)
        bar.addWidget(btn_collapse)
        if btn_add is not None:
            bar.addWidget(btn_add)
        return bar


class View(BaseView):
    def __init__(self, controller, model: "DeviceSettingsModel"):
        super().__init__(controller, model)
        print(f"✓ Device Settings view initialized with controller: {controller}")
        print(f"✓ Device Settings view initialized with model: {model}")
        self.all_devices_tree = AllDevicesTree(self, model.all_devices_tree_model)
        print(f"✓ Device Settings view initialized with all_devices_tree: {self.all_devices_tree}")
        self.mipi_devices_tree = MipiDevicesTree(self, model.mipi_devices_tree_model)
        self.gpio_devices_tree = GpioDevicesTree(self, model.gpio_devices_tree_model)
        base_layout = QVBoxLayout(self)
        print(f"✓ Device Settings view initialized with all_devices_tree: {self.all_devices_tree}")
        print(f"✓ Device Settings view initialized with mipi_devices_tree: {self.mipi_devices_tree}")
        print(f"✓ Device Settings view initialized with gpio_devices_tree: {self.gpio_devices_tree}")
        base_layout.setSpacing(6)
        # Accordion that holds all three trees as collapsible sections
        accordion = SectionAccordion(self, [
            ("All Devices", self.all_devices_tree),
            ("MIPI Devices", self.mipi_devices_tree),
            ("GPIO Devices", self.gpio_devices_tree),
        ])
        base_layout.addWidget(accordion)
        # Install an editing delegate for the Value column across all trees
        delegate = _ValueEditDelegate(self)
        self.all_devices_tree.setItemDelegateForColumn(1, delegate)
        self.mipi_devices_tree.setItemDelegateForColumn(1, delegate)
        self.gpio_devices_tree.setItemDelegateForColumn(1, delegate)
        # Allow editing on click via delegate
        for tree in (self.all_devices_tree, self.mipi_devices_tree, self.gpio_devices_tree):
            tree.setEditTriggers(QTreeView.DoubleClicked | QTreeView.SelectedClicked | QTreeView.EditKeyPressed)
        print(f"✓ Device Settings view initialized with base_layout: {base_layout}")
        self.setLayout(base_layout)

    # Public API for external callers (e.g., VisualBCFController/Manager)
    def add_mipi_device(self):
        try:
            dm = self.model
            new_id = dm.add_mipi_device_defaults()
            self.mipi_devices_tree.setModel(dm.mipi_devices_tree_model)
            self.mipi_devices_tree.expandAll()
            sel = dm.mipi_devices_tree_model.index_for_id(new_id, 1)
            if sel.isValid():
                self.mipi_devices_tree.setCurrentIndex(sel)
                self.mipi_devices_tree.edit(sel)
        except Exception:
            pass

    def add_gpio_device(self):
        try:
            dm = self.model
            new_id = dm.add_gpio_device_defaults()
            self.gpio_devices_tree.setModel(dm.gpio_devices_tree_model)
            self.gpio_devices_tree.expandAll()
            sel = dm.gpio_devices_tree_model.index_for_id(new_id, 1)
            if sel.isValid():
                self.gpio_devices_tree.setCurrentIndex(sel)
                self.gpio_devices_tree.edit(sel)
        except Exception:
            pass


from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit


class _ValueEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value is None:
            value = index.model().data(index, Qt.DisplayRole)
        editor.setText("" if value is None else str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text(), Qt.EditRole)
