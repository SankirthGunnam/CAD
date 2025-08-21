from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal

class BaseController(QObject):
    """Base class for all controllers in the legacy BCF manager"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, model=None):
        super().__init__()
        self.model = model
        self.view = None

    def set_view(self, view):
        """Set the view for this controller"""
        self.view = view
        self.view.set_controller(self)

    def set_model(self, model):
        """Set the model for this controller"""
        self.model = model

    def update_data(self, data: Dict[str, Any]):
        """Update the model with new data"""
        if self.model:
            self.model.update_data(data)
            self.data_changed.emit(data)

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get data from the model"""
        if self.model:
            return self.model.get_data()
        return None
