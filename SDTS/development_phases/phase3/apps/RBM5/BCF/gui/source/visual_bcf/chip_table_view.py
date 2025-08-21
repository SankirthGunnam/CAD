from PySide6.QtWidgets import QTableView, QHeaderView, QMenu, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, QModelIndex

from apps.RBM5.BCF.source.models.visual_bcf.chip_table_model import ChipTableModel
from apps.RBM5.BCF.gui.source.visual_bcf.chip_dialog import ChipDialog

class ChipTableView(QTableView):
    """View for displaying and managing chips in a table"""

    def __init__(self, model: ChipTableModel):
        super().__init__()
        self.model = model
        self.setModel(model)
        # self.setup_ui()

    def setup_ui(self):
        """Setup the table view appearance and behavior"""
        # Configure headers
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

        # Enable sorting
        self.setSortingEnabled(True)

        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Add button for new chips
        self.add_button = QPushButton("Add New Chip")
        self.add_button.clicked.connect(self.add_chip)

        # Create main layout
        layout = QVBoxLayout()
        layout.addWidget(self.add_button)
        layout.addWidget(self)
        self.setLayout(layout)

    def show_context_menu(self, position):
        """Show context menu for selected row"""
        index = self.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        edit_action = menu.addAction("Edit Chip")
        delete_action = menu.addAction("Delete Chip")

        action = menu.exec_(self.viewport().mapToGlobal(position))

        if action == edit_action:
            self.edit_chip(index)
        elif action == delete_action:
            self.delete_chip(index)

    def add_chip(self):
        """Add a new chip"""
        dialog = ChipDialog(self.model)
        dialog.exec()

    def edit_chip(self, index: QModelIndex):
        """Edit the selected chip"""
        chip_id = self.model.chips[index.row()]["id"]
        dialog = ChipDialog(self.model, chip_id)
        dialog.exec()

    def delete_chip(self, index: QModelIndex):
        """Delete the selected chip"""
        chip_id = self.model.chips[index.row()]["id"]
        self.model.delete_chip(chip_id)
