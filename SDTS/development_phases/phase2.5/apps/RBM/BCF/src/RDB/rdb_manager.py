from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Optional
import logging
from apps.RBM.BCF.src.RDB.database_interface import DatabaseInterface
from apps.RBM.BCF.src.RDB.json_db import JSONDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RDBManager(QObject):
    """Manager class that provides a clean interface for database operations"""

    # Signals for database events
    data_changed = Signal(str)  # Signal emits the path that changed
    error_occurred = Signal(str)  # Signal when error occurs (error_message)

    def __init__(self, db_file: str = "device_config.json"):
        super().__init__()
        self.db: DatabaseInterface = JSONDatabase(db_file)
        self._connect()
        # Connect signals after database initialization
        # self.db.data_changed.connect(self._on_data_changed)  # Temporarily commented out

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
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.db.rollback()

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
        from apps.RBM.BCF.src.models.rdb_table_model import RDBTableModel

        return RDBTableModel(self, path, columns)
    
    def close(self):
        """Close the database connection and clean up resources"""
        try:
            if hasattr(self.db, 'close'):
                self.db.close()
            logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")
            self.error_occurred.emit(str(e))
