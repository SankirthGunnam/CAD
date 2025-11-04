"""
Example usage of JsonTreeModel.

This demonstrates how to use JsonTreeModel to display and edit
a list of dictionaries in a QTreeView.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeView, QMenuBar, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from json_tree_model import JsonTreeModel
# from apps.RBM.BCF.source.models.json_tree_model import JsonTreeModel


class JsonTreeViewWindow(QMainWindow):
    """Example window showing JsonTreeModel in action"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON Tree Model Example")
        self.resize(800, 600)

        # Create model
        self.model = JsonTreeModel(self)
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setRootIsDecorated(True)
        self.tree_view.setExpandsOnDoubleClick(True)
        # Enable editing - double-click or F2 to edit
        self.tree_view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.SelectedClicked | QTreeView.EditTrigger.EditKeyPressed)
        self.setCentralWidget(self.tree_view)

        # Create menu bar
        self._create_menu_bar()

        # Load example data
        self._load_example_data()

    def _create_menu_bar(self):
        """Create menu bar with file operations"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        load_action = file_menu.addAction("&Load JSON...")
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_json)
        
        save_action = file_menu.addAction("&Save JSON...")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_json)
        
        save_as_action = file_menu.addAction("Save &As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_json_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        add_item_action = edit_menu.addAction("&Add Item")
        add_item_action.setShortcut("Ctrl+A")
        add_item_action.triggered.connect(self.add_item)
        
        remove_item_action = edit_menu.addAction("&Remove Item")
        remove_item_action.setShortcut("Ctrl+R")
        remove_item_action.triggered.connect(self.remove_item)

    def _load_example_data(self):
        """Load example data"""
        example_data = [
            {"id": "1001", "type": "Regular"},
            {"id": "1002", "type": "Chocolate"},
            {"id": "1003", "type": "Blueberry"},
            {"id": "1004", "type": "Devil's Food"}
        ]
        self.model.load_data(example_data)
        self.tree_view.expandAll()

    def load_json(self):
        """Load JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                self.model.load_from_json(file_path)
                self.tree_view.expandAll()
                QMessageBox.information(self, "Success", f"Loaded JSON file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load JSON file:\n{str(e)}")

    def save_json(self):
        """Save JSON file"""
        try:
            if self.model.save_to_json():
                QMessageBox.information(self, "Success", "JSON file saved successfully")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save JSON file")
        except ValueError as e:
            # No file path available, ask for one
            self.save_json_as()

    def save_json_as(self):
        """Save JSON file with new name"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                if self.model.save_to_json(file_path):
                    QMessageBox.information(self, "Success", f"Saved JSON file: {file_path}")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to save JSON file")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save JSON file:\n{str(e)}")

    def add_item(self):
        """Add a new item"""
        new_item = {"id": "NEW", "type": "New Type"}
        if self.model.add_item(new_item):
            # Expand to show new item
            index = self.model.index(self.model.rowCount() - 1, 0)
            self.tree_view.expand(index)
            self.tree_view.setCurrentIndex(index)

    def remove_item(self):
        """Remove selected item"""
        current_index = self.tree_view.currentIndex()
        if current_index.isValid():
            # Get the top-level item row
            top_level_index = current_index
            while top_level_index.parent().isValid():
                top_level_index = top_level_index.parent()
            
            row = top_level_index.row()
            if self.model.remove_item(row):
                QMessageBox.information(self, "Success", "Item removed")


def main():
    """Main function to run the example"""
    app = QApplication(sys.argv)
    
    window = JsonTreeViewWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

