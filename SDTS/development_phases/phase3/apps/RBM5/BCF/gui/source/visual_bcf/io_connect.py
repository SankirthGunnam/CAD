"""
IO Connect View for Visual BCF MVC Pattern

This module provides the IOConnectView class with a simple layout
containing just a single connections table.
"""

import typing
from PySide6.QtWidgets import (
    QVBoxLayout,
    QTreeView,
    QHBoxLayout,
    QToolButton,
    QFrame,
    QMenu,
    QMessageBox,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from apps.RBM5.BCF.config.constants.tabs import IOConnect

from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView
if typing.TYPE_CHECKING:
    from apps.RBM5.BCF.source.models.visual_bcf.io_connect_model import (
        IOConnectModel,
    )


class IOConnectTree(QTreeView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("IOConnectTree")
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)
        self.setAnimated(True)
        self.setIndentation(18)
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
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


class View(BaseView):
    def __init__(self, controller, model: "IOConnectModel"):
        super().__init__(controller, model)
        self.tree = IOConnectTree(self, model.tree_model)
        base_layout = QVBoxLayout(self)
        base_layout.setSpacing(8)
        base_layout.addWidget(self._make_section(self.tree))
        self.setLayout(base_layout)

    def _make_header_bar(self, tree: QTreeView):
        bar = QHBoxLayout()
        # No title label; section title is implied by context
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

    def _make_section(self, tree: QTreeView) -> QFrame:
        container = QFrame(self)
        container.setFrameShape(QFrame.StyledPanel)
        container.setStyleSheet(
            """
            QFrame {
                border: 1px solid #d9e2ef;
                border-radius: 6px;
                background: #ffffff;
            }
            """
        )
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addLayout(self._make_header_bar(tree))
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(tree)
        return container
