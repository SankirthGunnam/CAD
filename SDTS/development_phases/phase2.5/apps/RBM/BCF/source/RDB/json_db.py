import json
import os
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QObject, Signal
from apps.RBM.BCF.source.RDB.database_interface import DatabaseInterface


class JSONDatabase(QObject):
    """JSON database manager that implements DatabaseInterface"""

    data_changed = Signal(str)  # Signal emits the path that changed

    def __init__(self, db_file: str = "device_config.json"):
        super().__init__()
        self.db_file = db_file
        self.data: Dict[str, Any] = {}
        self.connected = False

    def connect(self) -> None:
        """Connect to the database"""
        if not self.connected:
            self._load_db()
            self.connected = True

    def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.connected:
            self._save_db()
            self.connected = False

    def _load_db(self) -> None:
        """Load database from file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, "r") as f:
                    self.data = json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            self.data = {}

    def _save_db(self) -> None:
        """Save database to file"""
        try:
            with open(self.db_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")

    def _get_path_parts(self, path: str) -> List[str]:
        """Split path into parts, handling both dot and slash notation"""
        return path.replace("/", ".").split(".")

    def _get_node(self, path: str) -> Any:
        """Get node at specified path"""
        if not self.connected:
            return None

        parts = self._get_path_parts(path)
        current = self.data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, {})
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    def _set_node(self, path: str, value: Any) -> bool:
        """Set node at specified path"""
        if not self.connected:
            return False

        parts = self._get_path_parts(path)
        if not parts:
            return False

        current = self.data
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict):
                if part not in current:
                    current[part] = {}
                current = current[part]
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    if idx >= len(current):
                        current.extend([{}] * (idx - len(current) + 1))
                    current = current[idx]
                except ValueError:
                    return False
            else:
                return False

        last_part = parts[-1]
        if isinstance(current, dict):
            current[last_part] = value
        elif isinstance(current, list):
            try:
                idx = int(last_part)
                if idx >= len(current):
                    current.extend([None] * (idx - len(current) + 1))
                current[idx] = value
            except ValueError:
                return False
        else:
            return False

        self._save_db()
        self.data_changed.emit(path)
        return True

    def get_value(self, path: str) -> Any:
        """Get value at specified path"""
        return self._get_node(path)

    def set_value(self, path: str, value: Any) -> bool:
        """Set value at specified path"""
        return self._set_node(path, value)

    def get_table(self, path: str) -> List[Dict]:
        """Get table data at specified path"""
        node = self._get_node(path)
        if isinstance(node, list):
            return node
        return []

    def set_table(self, path: str, rows: List[Dict]) -> bool:
        """Set table data at specified path"""
        return self._set_node(path, rows)

    def get_row(self, path: str, row_index: int) -> Optional[Dict]:
        """Get specific row from table"""
        table = self.get_table(path)
        if 0 <= row_index < len(table):
            return table[row_index]
        return None

    def set_row(self, path: str, row_index: int, row_data: Dict) -> bool:
        """Set specific row in table"""
        table = self.get_table(path)
        if 0 <= row_index < len(table):
            table[row_index] = row_data
            return self.set_table(path, table)
        return False

    def add_row(self, path: str, row_data: Dict) -> bool:
        """Add new row to table"""
        table = self.get_table(path)
        table.append(row_data)
        return self.set_table(path, table)

    def delete_row(self, path: str, row_index: int) -> bool:
        """Delete row from table"""
        table = self.get_table(path)
        if 0 <= row_index < len(table):
            del table[row_index]
            return self.set_table(path, table)
        return False

    def create_tables(self) -> None:
        """Create database tables"""
        # For JSON database, we just need to ensure the basic structure exists
        if not self.data:
            self.data = {
                "config": {
                    "device": {"settings": [], "properties": {}},
                    "band": {"settings": [], "properties": {}},
                    "board": {"settings": [], "properties": {}},
                    "rcc": {"settings": [], "properties": {}},
                }
            }
            self._save_db()

    def rollback(self) -> None:
        """Rollback changes"""
        # For JSON database, we just reload from file
        self._load_db()
