from typing import Any, Dict, List

from apps.RBM5.BCF.source.controllers.base_controller import BaseController
from apps.RBM5.BCF.source.models.legacy_bcf.table_model import LegacyTableModel
from apps.RBM5.BCF.gui.source.legacy_bcf.views.table_view import TableView

class TableController(BaseController):
    """Controller for table data"""

    def __init__(self):
        super().__init__(LegacyTableModel())
        self.view = None

    def set_view(self, view: TableView):
        """Set the view for this controller"""
        super().set_view(view)
        self.view.update_view(self.model.get_data())

    def update_table(self, data: Dict[str, Any]):
        """Update the table with new data"""
        self.update_data(data)
        if self.view:
            self.view.update_view(data)

    def get_table_data(self) -> Dict[str, List[Any]]:
        """Get the current table data"""
        return self.model.get_data()

    def update_row(self, index: int, row_data: List[Any]):
        """Update a specific row"""
        self.model.set_row(index, row_data)
        self.data_changed.emit(self.model.get_data())
        if self.view:
            self.view.update_view(self.model.get_data())
