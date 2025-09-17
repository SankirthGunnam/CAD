"""
IO Connect View for Visual BCF MVC Pattern

This module provides the IOConnectView class with a simple layout
containing just a single connections table.
"""

import typing
from PySide6.QtWidgets import (
    QVBoxLayout,
    QTableView,
    QScrollArea,
    QMenu,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from apps.RBM5.BCF.config.constants.tabs import IOConnect

from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView
if typing.TYPE_CHECKING:
    from apps.RBM5.BCF.source.models.visual_bcf.io_connect_model import (
        IOConnectModel,
    )


class IOConnectTable(QTableView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("IOConnectTable")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setMinimumHeight(400)
        
        # Enable context menu and keyboard shortcuts
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        self.setModel(model)

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
        """Delete the selected row after confirmation"""
        if not self.selectionModel().hasSelection():
            return
            
        current_row = self.currentIndex().row()
        if current_row < 0:
            return
            
        # Get row data for confirmation
        model = self.model()
        if not model:
            return
            
        source_device = model.data(model.index(current_row, 0))  # Source Device column
        dest_device = model.data(model.index(current_row, 2))    # Dest Device column
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Connection",
            f"Are you sure you want to delete connection from '{source_device}' to '{dest_device}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove the row
            model.removeRow(current_row)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Delete:
            self._delete_selected_row()
        else:
            super().keyPressEvent(event)

    def column_headers(self):
        return [
            IOConnect.IOConnectTable.SOURCE_DEVICE(),
            IOConnect.IOConnectTable.SOURCE_PIN(),
            IOConnect.IOConnectTable.DEST_DEVICE(),
            IOConnect.IOConnectTable.DEST_PIN(),
        ]


class View(BaseView):
    def __init__(self, controller, model: "IOConnectModel"):
        super().__init__(controller, model)
        self.table = IOConnectTable(self, model.table)
        base_layout = QVBoxLayout(self)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)
        base_layout.addWidget(scroll_area)
        self.setLayout(base_layout)
