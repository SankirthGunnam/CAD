from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Optional, Type, Protocol
import json
import logging
from .database_interface import DatabaseInterface
from .json_db import JSONDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseInterface(Protocol):
    """Protocol defining the interface for database operations"""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def create_tables(self) -> None: ...
    def add_chip(self, chip_data: Dict[str, Any]) -> Optional[int]: ...
    def get_chip(self, chip_id: int) -> Optional[Dict[str, Any]]: ...
    def get_all_chips(self) -> List[Dict[str, Any]]: ...
    def update_chip(self, chip_id: int, chip_data: Dict[str, Any]) -> bool: ...
    def delete_chip(self, chip_id: int) -> bool: ...
    def add_pin(self, chip_id: int, pin_data: Dict[str, Any]) -> Optional[int]: ...
    def get_chip_pins(self, chip_id: int) -> List[Dict[str, Any]]: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class RDBManager(QObject):
    """Manager class that provides a clean interface for database operations"""

    # Signals for database events
    data_changed = Signal(str)  # Signal emits the path that changed
    error_occurred = Signal(str)  # Signal when error occurs (error_message)

    def __init__(self, db_file: str = "device_config.json"):
        super().__init__()
        self.db: DatabaseInterface = JSONDatabase(db_file)
        self.db.data_changed.connect(self._on_data_changed)
        self._connect()

    def _connect(self) -> None:
        """Connect to the database"""
        try:
            self.db.connect()
            self._initialize_database()
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.error_occurred.emit(str(e))

    def _initialize_database(self) -> None:
        """Initialize database structure and default data"""
        try:
            # Create tables
            self.db.create_tables()

            # Initialize default data if needed
            self._initialize_default_data()
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()

    def _initialize_default_data(self) -> None:
        """Initialize database with default values"""
        try:
            # Check if default data already exists
            chips = self.db.get_all_chips()
            if not chips:
                # Add default chip
                default_chip = {
                    "name": "Default Chip",
                    "width": 100.0,
                    "height": 100.0,
                    "parameters": {"material": "Silicon", "thickness": 0.5},
                }
                self._add_chip(default_chip)
        except Exception as e:
            logger.error(f"Default data initialization error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()

    def reset_database(self) -> None:
        """Reset the database to initial state"""
        try:
            self.db.disconnect()
            self._connect()
        except Exception as e:
            logger.error(f"Database reset error: {str(e)}")
            self.error_occurred.emit(str(e))

    # Model Interface Methods
    def get_chip(self, chip_id: int) -> Optional[Dict[str, Any]]:
        """Get a chip by ID"""
        try:
            return self.db.get_chip(chip_id)
        except Exception as e:
            logger.error(f"Get chip error: {str(e)}")
            self.error_occurred.emit(str(e))
            return None

    def get_all_chips(self) -> List[Dict[str, Any]]:
        """Get all chips"""
        try:
            return self.db.get_all_chips()
        except Exception as e:
            logger.error(f"Get all chips error: {str(e)}")
            self.error_occurred.emit(str(e))
            return []

    def _add_chip(self, chip_data: Dict[str, Any]) -> Optional[int]:
        """Add a new chip to the database"""
        try:
            chip_id = self.db.add_chip(chip_data)
            if chip_id:
                self.db.commit()
                self.data_changed.emit("chips")
            return chip_id
        except Exception as e:
            logger.error(f"Add chip error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()
            return None

    def update_chip(self, chip_id: int, chip_data: Dict[str, Any]) -> bool:
        """Update an existing chip"""
        try:
            success = self.db.update_chip(chip_id, chip_data)
            if success:
                self.db.commit()
                self.data_changed.emit("chips")
            return success
        except Exception as e:
            logger.error(f"Update chip error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()
            return False

    def delete_chip(self, chip_id: int) -> bool:
        """Delete a chip and its associated pins"""
        try:
            success = self.db.delete_chip(chip_id)
            if success:
                self.db.commit()
                self.data_changed.emit("chips")
            return success
        except Exception as e:
            logger.error(f"Delete chip error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()
            return False

    # Pin Management
    def add_pin(self, chip_id: int, pin_data: Dict[str, Any]) -> Optional[int]:
        """Add a pin to a chip"""
        try:
            pin_id = self.db.add_pin(chip_id, pin_data)
            if pin_id:
                self.db.commit()
                self.data_changed.emit("pins")
            return pin_id
        except Exception as e:
            logger.error(f"Add pin error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()
            return None

    def get_chip_pins(self, chip_id: int) -> List[Dict[str, Any]]:
        """Get all pins for a chip"""
        try:
            return self.db.get_chip_pins(chip_id)
        except Exception as e:
            logger.error(f"Get chip pins error: {str(e)}")
            self.error_occurred.emit(str(e))
            return []

    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.db.disconnect()

    def _on_data_changed(self, path: str) -> None:
        """Handle database changes"""
        self.data_changed.emit(path)

    def get_value(self, path: str) -> Any:
        """Get value at specified path"""
        return self.db.get_value(path)

    def set_value(self, path: str, value: Any) -> bool:
        """Set value at specified path"""
        return self.db.set_value(path, value)

    def get_table(self, path: str) -> List[Dict]:
        """Get table data at specified path"""
        return self.db.get_table(path)

    def set_table(self, path: str, rows: List[Dict]) -> bool:
        """Set table data at specified path"""
        return self.db.set_table(path, rows)

    def get_row(self, path: str, row_index: int) -> Optional[Dict]:
        """Get specific row from table"""
        return self.db.get_row(path, row_index)

    def set_row(self, path: str, row_index: int, row_data: Dict) -> bool:
        """Set specific row in table"""
        return self.db.set_row(path, row_index, row_data)

    def add_row(self, path: str, row_data: Dict) -> bool:
        """Add new row to table"""
        return self.db.add_row(path, row_data)

    def delete_row(self, path: str, row_index: int) -> bool:
        """Delete row from table"""
        return self.db.delete_row(path, row_index)

    def get_model(self, path: str, columns: List[Dict[str, str]]) -> "RDBTableModel":
        """Create a Qt model for the specified table"""
        from ..models.rdb_table_model import RDBTableModel

        return RDBTableModel(self, path, columns)
