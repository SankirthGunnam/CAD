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
)

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
        self.setModel(model)

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
