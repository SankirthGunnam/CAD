# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import json
import re
import sys
from typing import Any

from PySide6.QtWidgets import QTreeView, QApplication, QHeaderView, QMainWindow, QMessageBox
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt, QFileInfo, Slot
from PySide6.QtGui import QCloseEvent


class TreeItem:
    """A Json item corresponding to a line in QTreeView"""

    def __init__(self, parent: "TreeItem" = None):
        self._parent = parent
        self._key = ""
        self._value = ""
        self._value_type = None
        self._children = []

    def appendChild(self, item: "TreeItem"):
        """Add item as a child"""
        self._children.append(item)

    def child(self, row: int) -> "TreeItem":
        """Return the child of the current item from the given row"""
        return self._children[row]

    def parent(self) -> "TreeItem":
        """Return the parent of the current item"""
        return self._parent

    def childCount(self) -> int:
        """Return the number of children of the current item"""
        return len(self._children)

    def row(self) -> int:
        """Return the row where the current item occupies in the parent"""
        return self._parent._children.index(self) if self._parent else 0

    @property
    def key(self) -> str:
        """Return the key name"""
        return self._key

    @key.setter
    def key(self, key: str):
        """Set key name of the current item"""
        self._key = key

    @property
    def value(self) -> str:
        """Return the value name of the current item"""
        return self._value

    @value.setter
    def value(self, value: str):
        """Set value name of the current item"""
        self._value = value

    @property
    def value_type(self):
        """Return the python type of the item's value."""
        return self._value_type

    @value_type.setter
    def value_type(self, value):
        """Set the python type of the item's value."""
        self._value_type = value

    @classmethod
    def _extract_group_name(cls, key: str) -> tuple[str, str | None]:
        """Extract group name from key if it has a group suffix.
        
        Returns:
            tuple: (base_key, group_name) or (key, None) if no group
        Examples:
            'id group1' -> ('id', 'group1')
            'type group2' -> ('type', 'group2')
            'id' -> ('id', None)
        """
        # Check for pattern: "key groupN" or "keygroupN"
        parts = key.rsplit(' ', 1)  # Split from right, max 1 split
        if len(parts) == 2:
            base_key, group_part = parts
            # Check if group_part starts with 'group' followed by digits
            if group_part.lower().startswith('group') and group_part[5:].isdigit():
                return base_key, group_part
            elif group_part.lower().startswith('group'):
                return base_key, group_part
        
        # Check for pattern: "keygroupN" (no space)
        if key.lower().endswith('group') or 'group' in key.lower():
            # Try to find 'group' in the key
            match = re.search(r'(.+?)(group\d+)$', key.lower())
            if match:
                base_key = key[:match.start(2)]  # Original case
                group_name = match.group(2)
                return base_key.rstrip(), group_name
        
        return key, None

    @classmethod
    def load(
        cls, value: list | dict, parent: "TreeItem" = None, sort=True
    ) -> "TreeItem":
        """Create a 'root' TreeItem from a nested list or a nested dictonary
        with grouping support for keys with group suffixes.

        Examples:
            with open("file.json") as file:
                data = json.dump(file)
                root = TreeItem.load(data)

        This method is a recursive function that calls itself.

        Returns:
            TreeItem: TreeItem
        """
        rootItem = TreeItem(parent)
        rootItem.key = "root"

        if isinstance(value, dict):
            items = sorted(value.items()) if sort else value.items()
            
            # Separate grouped and non-grouped keys
            grouped_keys = {}  # {group_name: {base_key: value}}
            non_grouped_items = []
            
            for key, val in items:
                base_key, group_name = cls._extract_group_name(key)
                if group_name:
                    # This key belongs to a group
                    if group_name not in grouped_keys:
                        grouped_keys[group_name] = {}
                    grouped_keys[group_name][base_key] = val
                else:
                    # Regular key-value pair
                    non_grouped_items.append((key, val))
            
            # Add non-grouped items first
            for key, val in non_grouped_items:
                child = cls.load(val, rootItem)
                child.key = key
                child.value_type = type(val)
                rootItem.appendChild(child)
            
            # Add grouped items
            for group_name in sorted(grouped_keys.keys()):
                # Create a group node
                group_item = TreeItem(rootItem)
                group_item.key = group_name
                group_item.value_type = dict
                group_item.value = ""  # Group nodes don't have values
                
                # Add grouped key-value pairs as children of the group node
                for base_key, val in sorted(grouped_keys[group_name].items()):
                    child = cls.load(val, group_item)
                    child.key = base_key
                    child.value_type = type(val)
                    group_item.appendChild(child)
                
                rootItem.appendChild(group_item)

        elif isinstance(value, list):
            for index, value in enumerate(value):
                child = cls.load(value, rootItem)
                child.key = value.get('id', index)
                child.value_type = type(value)
                rootItem.appendChild(child)

        else:
            rootItem.value = value
            rootItem.value_type = type(value)

        return rootItem


class JsonModel(QAbstractItemModel):
    """ An editable model of Json data """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._rootItem = TreeItem()
        self._headers = ("key", "value")
        self.document = []
        self._file_path = None  # Track the file path for autosave

    def clear(self):
        """ Clear data from the model """
        self.load({})

    def load(self, document: dict, file_path: str = None):
        """Load model from a nested dictionary returned by json.loads()

        Arguments:
            document (dict): JSON-compatible dictionary
            file_path (str): Optional file path for autosave
        """
        self.document = document
        self._file_path = file_path
        assert isinstance(
            document, (dict, list, tuple)
        ), "`document` must be of dict, list or tuple, " f"not {type(document)}"

        self.beginResetModel()

        self._rootItem = TreeItem.load(document)
        self._rootItem.value_type = type(document)

        self.endResetModel()

        return True

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        """Override from QAbstractItemModel

        Return data from a json item according index and role

        """
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return item.key

            if index.column() == 1:
                # For dictionary items in a list (parent is root), show group type values
                if item.parent() == self._rootItem and item.value_type == dict:
                    # This is a top-level dict item in a list
                    # Collect all type values from group nodes
                    group_type_values = []
                    for i in range(item.childCount()):
                        child = item.child(i)
                        # Check if this is a group node (value_type is dict and value is empty)
                        if child.value_type == dict and child.value == "":
                            # This is a group node, find the "type" child
                            for j in range(child.childCount()):
                                group_child = child.child(j)
                                if group_child.key == "type":
                                    group_type_values.append(str(group_child.value))
                    
                    if group_type_values:
                        return ", ".join(group_type_values)
                
                return item.value

        elif role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                return item.value

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole):
        """Override from QAbstractItemModel

        Set json item according index and role.
        Directly modifies self.document for efficient saves.
        Handles grouped keys by reconstructing the full key name.

        Args:
            index (QModelIndex)
            value (Any)
            role (Qt.ItemDataRole)

        """
        if role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                item = index.internalPointer()
                
                # Update the tree item for display
                item.value = str(value)
                
                # Directly update self.document for efficient saves
                # Find the parent dict item and its row number
                parent_item = item.parent()
                
                # Skip if parent is root (can't edit root level items)
                if parent_item != self._rootItem:
                    # Check if parent is a group node
                    if parent_item.value_type == dict and parent_item.value == "":
                        # This is a grouped item - parent is a group node
                        group_name = parent_item.key
                        base_key = item.key
                        # Reconstruct the full key name: "base_key group_name"
                        full_key = f"{base_key} {group_name}"
                        
                        # Find the dict item in the list (grandparent)
                        dict_item = parent_item.parent()
                        if dict_item and dict_item.parent() == self._rootItem:
                            dict_row = dict_item.row()
                            
                            if isinstance(self.document, list) and dict_row < len(self.document):
                                if isinstance(self.document[dict_row], dict):
                                    original_value = self.document[dict_row].get(full_key)
                                    
                                    if original_value is not None:
                                        converted_value = self._convert_value(value, original_value)
                                        self.document[dict_row][full_key] = converted_value
                                    else:
                                        self.document[dict_row][full_key] = str(value)
                                    
                                    item.value = str(self.document[dict_row][full_key])
                    
                    else:
                        # Regular (non-grouped) item
                        dict_item = parent_item
                        
                        # Find the row of the dict item in the root
                        if dict_item.parent() == self._rootItem:
                            # This is a dict item in a list
                            dict_row = dict_item.row()
                            
                            # Check if document is a list
                            if isinstance(self.document, list) and dict_row < len(self.document):
                                if isinstance(self.document[dict_row], dict):
                                    # Update directly: document[dict_row][item.key] = value
                                    original_value = self.document[dict_row].get(item.key)
                                    
                                    # Try to preserve original type if possible
                                    if original_value is not None:
                                        converted_value = self._convert_value(value, original_value)
                                        self.document[dict_row][item.key] = converted_value
                                    else:
                                        # New key, store as string
                                        self.document[dict_row][item.key] = str(value)
                                    
                                    # Update tree item to reflect the change
                                    item.value = str(self.document[dict_row][item.key])
                                    
                                    # Special case: If the key being edited is "id", update the parent dict item's key
                                    if item.key == "id":
                                        # Update the parent dict item's key to show the new id
                                        new_id = self.document[dict_row].get("id", dict_row)
                                        dict_item.key = new_id
                                        
                                        # Emit dataChanged for the parent item (column 0) so it updates the display
                                        parent_index = self.index(dict_row, 0, QModelIndex())
                                        self.dataChanged.emit(parent_index, parent_index, [Qt.ItemDataRole.DisplayRole])

                self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])

                return True

        return False

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ):
        """Override from QAbstractItemModel

        For the JsonModel, it returns only data for columns (orientation = Horizontal)

        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section]

    def index(self, row: int, column: int, parent=QModelIndex()) -> QModelIndex:
        """Override from QAbstractItemModel

        Return index according row, column and parent

        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Override from QAbstractItemModel

        Return parent index of index

        """

        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QModelIndex()):
        """Override from QAbstractItemModel

        Return row count from parent index
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        """Override from QAbstractItemModel

        Return column number. For the model, it always return 2 columns
        """
        return 2

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Override from QAbstractItemModel

        Return flags of index
        """
        flags = super(JsonModel, self).flags(index)

        if index.column() == 1:
            return Qt.ItemFlag.ItemIsEditable | flags
        else:
            return flags

    def _convert_value(self, new_value: Any, original_value: Any) -> Any:
        """Convert new_value to match the type of original_value if possible"""
        try:
            if isinstance(original_value, bool):
                # Handle boolean
                str_val = str(new_value).lower()
                if str_val in ('true', '1', 'yes', 'on'):
                    return True
                elif str_val in ('false', '0', 'no', 'off', ''):
                    return False
                return new_value
            elif isinstance(original_value, int):
                # Try to convert to int
                try:
                    return int(new_value)
                except (ValueError, TypeError):
                    return str(new_value)
            elif isinstance(original_value, float):
                # Try to convert to float
                try:
                    return float(new_value)
                except (ValueError, TypeError):
                    return str(new_value)
            else:
                # Keep as string or original type
                return str(new_value)
        except Exception:
            # Fallback to string
            return str(new_value)

    def to_json(self, item=None):

        if item is None:
            item = self._rootItem

        nchild = item.childCount()

        if item.value_type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                # Check if this is a group node (has dict value_type but empty value)
                if ch.value_type == dict and ch.value == "":
                    # This is a group node - reconstruct grouped keys
                    group_name = ch.key
                    group_children = ch.childCount()
                    for j in range(group_children):
                        group_child = ch.child(j)
                        base_key = group_child.key
                        # Reconstruct full key name: "base_key group_name"
                        full_key = f"{base_key} {group_name}"
                        document[full_key] = self.to_json(group_child)
                else:
                    # Regular key-value pair
                    document[ch.key] = self.to_json(ch)
            return document

        elif item.value_type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.to_json(ch))
            return document

        else:
            return item.value

    def save_to_json(self, file_path: str = None) -> bool:
        """Save the current document to a JSON file.
        
        Args:
            file_path (str): Path to save file. If None, uses the stored file path.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if file_path is None:
            file_path = self._file_path
        
        if file_path is None:
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.document, f, indent=2, ensure_ascii=False)
            self._file_path = file_path
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False

    def set_file_path(self, file_path: str):
        """Set the file path for autosave"""
        self._file_path = file_path

    def get_file_path(self) -> str:
        """Get the current file path"""
        return self._file_path

    def _update_tree_from_document(self):
        """Update the tree structure from the current document"""
        self.beginResetModel()
        self._rootItem = TreeItem.load(self.document)
        self._rootItem.value_type = type(self.document)
        self.endResetModel()

    def insertRow(self, row: int, parent: QModelIndex = QModelIndex(), item_data: dict = None) -> bool:
        """Insert a new row at the specified position.
        
        For a list of dictionaries, inserts a new dictionary at the given row.
        
        Args:
            row: Position to insert the new item
            parent: Parent index (should be invalid for top-level items in a list)
            item_data: Dictionary data for the new item. If None, creates an empty dict.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(self.document, list):
            return False
        
        if row < 0 or row > len(self.document):
            return False
        
        # Prepare new item data
        new_item = item_data.copy() if item_data else {'id': len(self.document), 'type': 'New Item'}
        
        # Insert into document
        self.document.insert(row, new_item)
        
        # Update tree structure
        self._update_tree_from_document()
        
        return True

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Remove a row at the specified position.
        
        For a list of dictionaries, removes the dictionary at the given row.
        
        Args:
            row: Position of the item to remove
            parent: Parent index (should be invalid for top-level items in a list)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(self.document, list):
            return False
        
        if row < 0 or row >= len(self.document):
            return False
        
        # Remove from document
        self.document.pop(row)
        
        # Update tree structure
        self._update_tree_from_document()
        
        return True

    def addItem(self, item_data: dict = None) -> bool:
        """Add a new item to the end of the list.
        
        Convenience method that calls insertRow at the end.
        
        Args:
            item_data: Dictionary data for the new item. If None, creates an empty dict.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not isinstance(self.document, list):
            return False
        
        return self.insertRow(len(self.document), QModelIndex(), item_data)

    def removeItem(self, row: int) -> bool:
        """Remove an item at the specified row.
        
        Convenience method that calls removeRow.
        
        Args:
            row: Position of the item to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.removeRow(row, QModelIndex())


class JsonTreeViewWindow(QMainWindow):
    """Window with autosave functionality on close and insert/delete operations"""
    
    def __init__(self, model: JsonModel, file_path: str = None):
        super().__init__()
        self.model = model
        self._file_path = file_path
        
        # Set file path in model if provided
        if file_path:
            self.model.set_file_path(file_path)
        
        # Create tree view
        self.view = QTreeView()
        self.view.setModel(model)
        self.view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.view.setAlternatingRowColors(True)
        self.view.setEditTriggers(QTreeView.EditTrigger.DoubleClicked | QTreeView.EditTrigger.SelectedClicked | QTreeView.EditTrigger.EditKeyPressed)
        self.setCentralWidget(self.view)
        
        # Create menu bar with actions
        self._create_menu_bar()
        
        self.setWindowTitle("JSON Tree View" + (f" - {file_path}" if file_path else ""))
        self.resize(500, 600)
    
    def _create_menu_bar(self):
        """Create menu bar with file and edit operations"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        save_action = file_menu.addAction("&Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        add_action = edit_menu.addAction("&Add Item")
        add_action.setShortcut("Ctrl+A")
        add_action.triggered.connect(self.add_item)
        
        insert_action = edit_menu.addAction("&Insert Item")
        insert_action.setShortcut("Ctrl+I")
        insert_action.triggered.connect(self.insert_item)
        
        remove_action = edit_menu.addAction("&Remove Item")
        remove_action.setShortcut("Ctrl+R")
        remove_action.triggered.connect(self.remove_item)
    
    @Slot()
    def save_file(self):
        """Save the current document"""
        if self.model.save_to_json():
            QMessageBox.information(self, "Success", "File saved successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to save file")
    
    @Slot()
    def add_item(self):
        """Add a new item at the end of the list"""
        if self.model.addItem():
            # Expand to show new item
            index = self.model.index(self.model.rowCount() - 1, 0)
            self.view.expand(index)
            self.view.setCurrentIndex(index)
            QMessageBox.information(self, "Success", "Item added successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to add item. Document must be a list.")
    
    @Slot()
    def insert_item(self):
        """Insert a new item at the current selection"""
        current_index = self.view.currentIndex()
        if current_index.isValid():
            # Get the top-level row
            top_level_index = current_index
            while top_level_index.parent().isValid():
                top_level_index = top_level_index.parent()
            
            row = top_level_index.row()
            if self.model.insertRow(row):
                # Expand to show new item
                index = self.model.index(row, 0)
                self.view.expand(index)
                self.view.setCurrentIndex(index)
                QMessageBox.information(self, "Success", "Item inserted successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to insert item. Document must be a list.")
        else:
            # No selection, add at the end
            self.add_item()
    
    @Slot()
    def remove_item(self):
        """Remove the selected item"""
        current_index = self.view.currentIndex()
        if current_index.isValid():
            # Get the top-level row
            top_level_index = current_index
            while top_level_index.parent().isValid():
                top_level_index = top_level_index.parent()
            
            row = top_level_index.row()
            reply = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete item at row {row}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.model.removeItem(row):
                    QMessageBox.information(self, "Success", "Item removed successfully")
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove item")
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove")
    
    def closeEvent(self, event: QCloseEvent):
        """Override closeEvent to autosave before closing"""
        if self.model.get_file_path():
            # Autosave if file path is set
            if self.model.save_to_json():
                print(f"Autosaved to: {self.model.get_file_path()}")
            else:
                print(f"Warning: Failed to autosave to {self.model.get_file_path()}")
        else:
            # No file path set, could prompt user here
            print("No file path set, skipping autosave")
        
        event.accept()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    model = JsonModel()

    json_path = QFileInfo(__file__).absoluteDir().filePath("example_grouped.json")

    with open(json_path, encoding='utf-8') as file:
        document = json.load(file)
        model.load(document, json_path)

    window = JsonTreeViewWindow(model, json_path)
    window.show()
    app.exec()
