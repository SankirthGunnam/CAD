from PySide6.QtWidgets import QWidget
from typing import Any, Dict


class BaseView(QWidget):
    """Base class for all views in the legacy BCF manager"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = None

    def set_controller(self, controller):
        """Set the controller for this view"""
        self.controller = controller

    def update_view(self, data: Dict[str, Any]):
        """Update the view with new data"""
        raise NotImplementedError("Subclasses must implement update_view")

    def get_data(self) -> Dict[str, Any]:
        """Get the current data from the view"""
        raise NotImplementedError("Subclasses must implement get_data")
