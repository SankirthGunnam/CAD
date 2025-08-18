from PySide6.QtCore import QAbstractTableModel, Qt, Signal
from typing import Dict, Any, List
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager


class ChipTableModel(QAbstractTableModel):
    """Model for displaying chip data in a TableView"""

    # Column definitions
    COLUMNS = [
        ("ID", "id"),
        ("Name", "name"),
        ("Width", "width"),
        ("Height", "height"),
        ("Material", "parameters.material"),
        ("Thickness", "parameters.thickness"),
    ]

    def __init__(self, rdb_manager: RDBManager):
        super().__init__()
        self.rdb_manager = rdb_manager
        self.chips: List[Dict[str, Any]] = []
        self.load_data()

        # Connect to RDBManager signals
        self.rdb_manager.data_changed.connect(self.on_data_changed)

    def load_data(self):
        """Load data from RDBManager"""
        self.beginResetModel()
        self.chips = self.rdb_manager.get_all_chips()
        self.endResetModel()

    def on_data_changed(self, table_name: str):
        """Handle data changes from RDBManager"""
        if table_name == "chips":
            self.load_data()

    def rowCount(self, parent=None):
        return len(self.chips)

    def columnCount(self, parent=None):
        return len(self.COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            chip = self.chips[index.row()]
            col_name = self.COLUMNS[index.column()][1]

            # Handle nested dictionary access (e.g., parameters.material)
            value = chip
            for key in col_name.split("."):
                value = value.get(key, "")
            return str(value)

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section][0]
        return None

    def add_chip(self, chip_data: Dict[str, Any]):
        """Add a new chip"""
        self.rdb_manager._add_chip(chip_data)

    def update_chip(self, chip_id: int, chip_data: Dict[str, Any]):
        """Update an existing chip"""
        self.rdb_manager.update_chip(chip_id, chip_data)

    def delete_chip(self, chip_id: int):
        """Delete a chip"""
        self.rdb_manager.delete_chip(chip_id)
