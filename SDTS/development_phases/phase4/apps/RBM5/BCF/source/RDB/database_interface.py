from typing import Protocol, Dict, List, Any, Optional

class DatabaseInterface(Protocol):
    """Protocol defining the interface for database operations"""
    # Note: Qt signals should be defined in the actual implementation, not in
    # the Protocol

    def connect(self) -> None:
        """Connect to the database"""
        ...

    def disconnect(self) -> None:
        """Disconnect from the database"""
        ...

    def get_value(self, path: str) -> Any:
        """Get value at specified path"""
        ...

    def set_value(self, path: str, value: Any) -> bool:
        """Set value at specified path"""
        ...

    def get_table(self, path: str) -> List[Dict]:
        """Get table data at specified path"""
        ...

    def set_table(self, path: str, rows: List[Dict]) -> bool:
        """Set table data at specified path"""
        ...

    def get_row(self, path: str, row_index: int) -> Optional[Dict]:
        """Get specific row from table"""
        ...

    def set_row(self, path: str, row_index: int, row_data: Dict) -> bool:
        """Set specific row in table"""
        ...

    def add_row(self, path: str, row_data: Dict) -> bool:
        """Add new row to table"""
        ...

    def delete_row(self, path: str, row_index: int) -> bool:
        """Delete row from table"""
        ...
