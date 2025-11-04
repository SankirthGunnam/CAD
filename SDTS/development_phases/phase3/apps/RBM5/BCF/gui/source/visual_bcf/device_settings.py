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
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
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
        
        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
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
            # Remove the subtree
            model.remove_subtree(int(idx.internalId()))

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
        self.setObjectName("MipiDevicesTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(200)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        if model is not None:
            self.setModel(model)
            self.expandAll()

    def _show_context_menu(self, position):
        """Show context menu for table row operations"""
        if not self.selectionModel().hasSelection():
            return
            
        menu = QMenu(self)
        
        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
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
            model.remove_subtree(int(idx.internalId()))

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
        self.setObjectName("GpioDevicesTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(200)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        if model is not None:
            self.setModel(model)
            self.expandAll()

    def _show_context_menu(self, position):
        """Show context menu for table row operations"""
        if not self.selectionModel().hasSelection():
            return
            
        menu = QMenu(self)
        
        # Add delete action
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self._delete_selected_row)
        menu.addAction(delete_action)
        
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
            model.remove_subtree(int(idx.internalId()))

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
        bar.addStretch(1)
        bar.addWidget(btn_expand)
        bar.addWidget(btn_collapse)
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
        print(f"✓ Device Settings view initialized with base_layout: {base_layout}")
        self.setLayout(base_layout)
