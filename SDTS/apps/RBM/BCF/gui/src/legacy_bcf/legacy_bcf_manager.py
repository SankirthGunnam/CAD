from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QDockWidget,
)
from PySide6.QtCore import Signal


class LegacyBCFManager(QWidget):
    """Legacy BCF Manager that provides a table-based interface"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Legacy BCF Manager")

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create table widget
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # Create control dock
        self.control_dock = QDockWidget("Controls")
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        self.control_dock.setWidget(control_widget)

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
