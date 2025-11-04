# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations

import json
import sys
from typing import Any

from PySide6.QtWidgets import QTreeView, QApplication, QHeaderView, QMainWindow
from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt, QFileInfo
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
    def load(
        cls, value: list | dict, parent: "TreeItem" = None, sort=True
    ) -> "TreeItem":
        """Create a 'root' TreeItem from a nested list or a nested dictonary

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

            for key, value in items:
                child = cls.load(value, rootItem)
                child.key = key
                child.value_type = type(value)
                rootItem.appendChild(child)

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
                return item.value

        elif role == Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                return item.value

    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole):
        """Override from QAbstractItemModel

        Set json item according index and role.
        Directly modifies self.document for efficient saves.

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
                    # This is a key-value pair, find its parent dict
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


class JsonTreeViewWindow(QMainWindow):
    """Window with autosave functionality on close"""
    
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
        self.setCentralWidget(self.view)
        
        self.setWindowTitle("JSON Tree View" + (f" - {file_path}" if file_path else ""))
        self.resize(500, 300)
    
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

    json_path = QFileInfo(__file__).absoluteDir().filePath("example.json")

    with open(json_path, encoding='utf-8') as file:
        document = json.load(file)
        model.load(document, json_path)

    window = JsonTreeViewWindow(model, json_path)
    window.show()
    app.exec()
