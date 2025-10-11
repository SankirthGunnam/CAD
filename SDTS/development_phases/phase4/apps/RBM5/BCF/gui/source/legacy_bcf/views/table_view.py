from typing import Any, Dict

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout

from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView

class TableView(BaseView):
    """View for displaying data in a table format"""

    def __init__(self, parent=None):
        # BaseView will call the subclass setup_ui() once
        super().__init__()

    def setup_ui(self):
        """Setup the UI components"""
        # Guard against duplicate layout creation
        if self.layout() is not None:
            return
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Type", "Status"])

        layout.addWidget(self.table)

    def update_view(self, data: Dict[str, Any]):
        """Update the table with new data"""
        if not data:
            return

        # Clear existing items
        self.table.clear()

        # Set table dimensions
        rows = len(data)
        cols = len(next(iter(data.values()))) if data else 0
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)

        # Fill table
        for row, (key, values) in enumerate(data.items()):
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                self.table.setItem(row, col, item)

    def get_data(self) -> Dict[str, Any]:
        """Get the current data from the table"""
        data = {}
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data[f"row_{row}"] = row_data
        return data
