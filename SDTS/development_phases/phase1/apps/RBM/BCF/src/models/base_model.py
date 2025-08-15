from typing import Any, Dict, Optional
from PySide6.QtCore import QObject


class BaseModel(QObject):
    """Base class for all models in the legacy BCF manager"""

    def __init__(self):
        super().__init__()
        self._data: Dict[str, Any] = {}

    def update_data(self, data: Dict[str, Any]):
        """Update the model's data"""
        self._data = data

    def get_data(self) -> Dict[str, Any]:
        """Get the model's data"""
        return self._data

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a specific value from the model's data"""
        return self._data.get(key, default)

    def set_value(self, key: str, value: Any):
        """Set a specific value in the model's data"""
        self._data[key] = value
