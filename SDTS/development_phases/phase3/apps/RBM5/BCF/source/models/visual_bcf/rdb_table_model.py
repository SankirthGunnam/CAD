from typing import Any, Dict, List, Optional

# Use centralized path setup from BCF package
import apps.RBM5.BCF  # This automatically sets up the path

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager


class TableModel(QAbstractTableModel):
    """Qt model for displaying and editing database tables with nested structures"""

    def __init__(
        self,
        db: RDBManager,
        table_path: str,
        columns: List[Dict[str, str]],
        parent=None,
    ):
        super().__init__(parent)
        self.db = db
        self.table_path = table_path
        self.columns = columns
        print(f"✓ TableModel initialized with db type: {type(db)}, table_path: {table_path}")

        # Only connect signal if db is not None
        if self.db is not None and hasattr(self.db, 'data_changed'):
            self.db.data_changed.connect(self._on_data_changed)

    # Note: TableModel inherits from QAbstractTableModel, not QWidget
    # It doesn't have a setModel method - this was causing segfault
    # The model is set on the view widget, not the model itself

    def _on_data_changed(self, changed_path: str) -> None:
        """Handle database changes"""
        if changed_path == self.table_path:
            self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows in the table"""
        if self.db is None:
            return 0
        try:
            table_data = self.db.get_table(self.table_path)
            return len(table_data) if table_data else 0
        except Exception as e:
            print(f"Error getting table {self.table_path}: {e}")
            return 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns in the table"""
        return len(self.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for the given index and role"""
        if not index.isValid() or self.db is None:
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            try:
                row = index.row()
                print('table data', self.db[self.table_path][row], self.columns[index.column()])
                return self.db[self.table_path][row][self.columns[index.column()]]
            except Exception as e:
                print(f"Error getting data for row {index.row()}: {e}")
                return None
        return None

    def setData(
            self,
            index: QModelIndex,
            value: Any,
            role: int = Qt.EditRole) -> bool:
        """Set data at the given index"""
        if not index.isValid() or role != Qt.EditRole or self.db is None:
            return False

        try:
            row = self.db.get_row(self.table_path, index.row())
            if row:
                column_key = self.columns[index.column()]["key"]
                # Handle nested paths in column keys
                if "." in column_key:
                    parts = column_key.split(".")
                    current = row
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    row[column_key] = value

                return self.db.set_row(self.table_path, index.row(), row)
        except Exception as e:
            print(f"Error setting data: {e}")
            return False
        return False

    def headerData(
            self,
            section: int,
            orientation: Qt.Orientation,
            role: int = Qt.DisplayRole) -> Any:
        """Return header data"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return item flags"""
        if not index.isValid():
            return Qt.NoItemFlags

        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if (
            "editable" not in self.columns[index.column()]
            or self.columns[index.column()]["editable"]
        ):
            flags |= Qt.ItemIsEditable
        return flags

    def insertRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Insert a new row"""
        if self.db is None:
            return False
        try:
            self.beginInsertRows(parent, row, row)
            new_row = {
                col["key"].split(".")[0]: ""
                for col in self.columns
                if "." not in col["key"]
            }
            self.db.add_row(self.table_path, new_row)
            self.endInsertRows()
            return True
        except Exception as e:
            print(f"Error inserting row: {e}")
            return False

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Remove a row"""
        if self.db is None:
            return False
        try:
            self.beginRemoveRows(parent, row, row)
            self.db.delete_row(self.table_path, row)
            self.endRemoveRows()
            return True
        except Exception as e:
            print(f"Error removing row: {e}")
            return False
