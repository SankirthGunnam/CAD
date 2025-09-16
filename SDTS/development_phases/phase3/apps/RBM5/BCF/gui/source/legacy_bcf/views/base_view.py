from typing import Any, Dict

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QWidget

class BaseView(QWidget):
    """Base class for all views in the legacy BCF manager"""

    def __init__(self, controller=None, model=None):
        super().__init__()  # Don't pass controller as parent - it's not a QWidget
        self.controller = controller
        self.model = model
        self.setup_ui()

    def set_controller(self, controller):
        """Set the controller for this view"""
        self.controller = controller

    def setup_ui(self):
        if hasattr(self, "setupUi"):
            self.setupUi()
            
    def update_view(self, data: Dict[str, Any]):
        """Update the view with new data"""
        raise NotImplementedError("Subclasses must implement update_view")

    def get_data(self) -> Dict[str, Any]:
        """Get the current data from the view"""
        raise NotImplementedError("Subclasses must implement get_data")

    def set_data(self, widget: str, index: QModelIndex, data: Any):
        """Set the data for a specific widget and index"""
        raise NotImplementedError("Subclasses must implement set_data")