"""
JSON Tree Model for displaying and editing a list of dictionaries in a QTreeView.

This model allows editing a list of dictionaries where:
- Each dictionary becomes a top-level tree item
- Dictionary keys are shown as columns (Key, Value)
- Dictionary key-value pairs are shown as child rows
- Editing updates the actual internal data structure
- Supports saving to JSON file
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal


class JsonTreeItem:
    """Internal item structure for the tree model"""

    def __init__(self, data: Dict[str, Any] = None, parent: 'JsonTreeItem' = None, row_index: int = -1):
        """
        Initialize a tree item.
        
        Args:
            data: Dictionary data for this item (if None, it's a root item)
            parent: Parent tree item
            row_index: Index of this item in the parent's children list
        """
        self.parent_item = parent
        self.data_dict = data if data is not None else {}
        self.children: List['JsonTreeItem'] = []
        self.row_index = row_index  # Index in the parent's children list
        
        # For root items, create children for each dict in the list
        # For dict items, create children for each key-value pair
        if parent is None:
            # Root item - children will be created when data is set
            pass
        elif data is not None:
            # This is a dictionary item - create children for each key-value pair
            for key, value in data.items():
                child_data = {"key": key, "value": value}
                child = JsonTreeItem(child_data, self, len(self.children))
                self.children.append(child)

    def child(self, row: int) -> Optional['JsonTreeItem']:
        """Get child at given row"""
        if 0 <= row < len(self.children):
            return self.children[row]
        return None

    def child_count(self) -> int:
        """Get number of children"""
        return len(self.children)

    def column_count(self) -> int:
        """Get number of columns (always 2: Key and Value)"""
        return 2

    def data(self, column: int) -> Any:
        """
        Get data for a column.
        
        For root item children (dict items): column 0 shows index, column 1 shows dict preview
        For dict item children (key-value pairs): column 0 shows key, column 1 shows value
        """
        if self.parent_item is None:
            # Root item - no data
            return None
        
        # If this is a top-level dict item (child of root)
        if self.parent_item.parent_item is None:
            if column == 0:
                # Show index or first key value
                if self.data_dict:
                    first_key = list(self.data_dict.keys())[0]
                    return f"[{self.row_index}] {first_key}: {self.data_dict.get(first_key, '')}"
                return f"[{self.row_index}]"
            elif column == 1:
                # Show preview of dict
                return f"({len(self.data_dict)} items)"
        
        # If this is a key-value pair (child of dict item)
        if "key" in self.data_dict and "value" in self.data_dict:
            if column == 0:
                return str(self.data_dict["key"])
            elif column == 1:
                value = self.data_dict["value"]
                return str(value)
        
        return None

    def set_data(self, column: int, value: Any) -> bool:
        """
        Set data for a column.
        
        Returns True if successful, False otherwise.
        """
        if self.parent_item is None:
            return False
        
        # Can only edit value column (column 1) for key-value pairs
        if column == 1 and "key" in self.data_dict and "value" in self.data_dict:
            # Update the value
            self.data_dict["value"] = value
            
            # Update the parent dictionary in the actual data structure
            parent_dict_item = self.parent_item
            if parent_dict_item.parent_item is None:
                # Parent is a top-level dict item
                key = self.data_dict["key"]
                parent_dict_item.data_dict[key] = value
                return True
        
        return False

    def row(self) -> int:
        """Get row number in parent"""
        return self.row_index

    def parent(self) -> Optional['JsonTreeItem']:
        """Get parent item"""
        return self.parent_item

    def get_dict(self) -> Dict[str, Any]:
        """Get the dictionary data for this item (if it's a dict item)"""
        return self.data_dict.copy()


class JsonTreeModel(QAbstractItemModel):
    """
    Tree model for displaying and editing a list of dictionaries.
    
    Features:
    - Load from list of dictionaries
    - Display in tree view with each dict as top-level item
    - Edit values and update internal data structure
    - Save to JSON file
    """
    
    # Signal emitted when data is saved
    data_saved = Signal(str)  # Emits file path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = JsonTreeItem()
        self._data: List[Dict[str, Any]] = []
        self._file_path: Optional[Path] = None

    def load_data(self, data: List[Dict[str, Any]]):
        """
        Load data from a list of dictionaries.
        
        Args:
            data: List of dictionaries to display
        """
        self.beginResetModel()
        self._data = [item.copy() for item in data]  # Store a copy
        self.root_item = JsonTreeItem()
        
        # Create children for each dictionary
        for idx, dict_item in enumerate(self._data):
            child = JsonTreeItem(dict_item.copy(), self.root_item, idx)
            self.root_item.children.append(child)
        
        self.endResetModel()

    def load_from_json(self, file_path: str | Path):
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to JSON file
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of dictionaries")
        
        self._file_path = file_path
        self.load_data(data)

    def save_to_json(self, file_path: str | Path = None) -> bool:
        """
        Save current data to JSON file.
        
        Args:
            file_path: Path to save JSON file. If None, uses the original file path.
        
        Returns:
            True if successful, False otherwise
        """
        if file_path is None:
            if self._file_path is None:
                raise ValueError("No file path specified and no original file path available")
            file_path = self._file_path
        else:
            file_path = Path(file_path)
        
        # Update internal data from tree structure
        self._update_data_from_tree()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            self._file_path = file_path
            self.data_saved.emit(str(file_path))
            return True
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return False

    def _update_data_from_tree(self):
        """Update internal data structure from tree items"""
        self._data = []
        for child in self.root_item.children:
            if child.data_dict:
                self._data.append(child.data_dict.copy())

    def get_data(self) -> List[Dict[str, Any]]:
        """
        Get the current data as a list of dictionaries.
        
        Returns:
            List of dictionaries
        """
        self._update_data_from_tree()
        return [item.copy() for item in self._data]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns (always 2: Key and Value)"""
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of rows"""
        if parent.column() > 0:
            return 0
        
        parent_item = self._get_item(parent)
        return parent_item.child_count()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for the given index and role"""
        if not index.isValid():
            return None
        
        item = self._get_item(index)
        
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return item.data(index.column())
        
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        Set data at the given index.
        
        Updates both the tree item and the internal data structure.
        """
        if role != Qt.EditRole:
            return False
        
        if not index.isValid():
            return False
        
        item = self._get_item(index)
        
        # Can only edit value column
        if index.column() != 1:
            return False
        
        if item.set_data(index.column(), value):
            # Emit data changed signal
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            
            # Update internal data structure
            self._update_data_from_tree structure
            
            return True
        
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return item flags"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        # Allow editing of value column (column 1) for key-value pairs
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 1:
            # Check if this is a key-value pair (not a dict item)
            item = self._get_item(index)
            if item.parent_item and item.parent_item.parent_item is None:
                # This is a child of a dict item (key-value pair)
                flags |= Qt.ItemIsEditable
        
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Return header data"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Key"
            elif section == 1:
                return "Value"
        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create and return index for the given row, column, and parent"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        parent_item = self._get_item(parent)
        child_item = parent_item.child(row)
        
        if child_item:
            return self.createIndex(row, column, child_item)
        
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Return parent index for the given index"""
        if not index.isValid():
            return QModelIndex()
        
        child_item = self._get_item(index)
        parent_item = child_item.parent()
        
        if parent_item is None or parent_item == self.root_item:
            return QModelIndex()
        
        return self.createIndex(parent_item.row(), 0, parent_item)

    def _get_item(self, index: QModelIndex) -> JsonTreeItem:
        """Get item from index"""
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.root_item

    def add_item(self, data: Dict[str, Any] = None) -> bool:
        """
        Add a new dictionary item to the model.
        
        Args:
            data: Dictionary to add. If None, adds an empty dict.
        
        Returns:
            True if successful
        """
        if data is None:
            data = {}
        
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        
        new_data = data.copy()
        new_item = JsonTreeItem(new_data, self.root_item, len(self.root_item.children))
        self.root_item.children.append(new_item)
        
        self.endInsertRows()
        
        # Update internal data
        self._update_data_from_tree()
        
        return True

    def remove_item(self, row: int) -> bool:
        """
        Remove a dictionary item from the model.
        
        Args:
            row: Row index of the item to remove
        
        Returns:
            True if successful
        """
        if row < 0 or row >= self.rowCount():
            return False
        
        self.beginRemoveRows(QModelIndex(), row, row)
        self.root_item.children.pop(row)
        # Update row indices
        for idx, child in enumerate(self.root_item.children):
            child.row_index = idx
        self.endRemoveRows()
        
        # Update internal data
        self._update_data_from_tree()
        
        return True

() SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause
from __future__ import annotations


from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel
from treeitem import TreeItem


class TreeModel(QAbstractItemModel):

    def __init__(self, headers: list, data: str, parent=None):
        super().__init__(parent)

        self.root_data = headers
        self.root_item = TreeItem(self.root_data.copy())
        self.setup_model_data(data.split("\n"), self.root_item)

    def columnCount(self, parent: QModelIndex = None) -> int:
        return self.root_item.column_count()

    def data(self, index: QModelIndex, role: int = None):
        if not index.isValid():
            return None

        if role != Qt.ItemDataRole.DisplayRole and role != Qt.ItemDataRole.EditRole:
            return None

        item: TreeItem = self.get_item(index)

        return item.data(index.column())

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsEditable | QAbstractItemModel.flags(self, index)

    def get_item(self, index: QModelIndex = QModelIndex()) -> TreeItem:
        if index.isValid():
            item: TreeItem = index.internalPointer()
            if item:
                return item

        return self.root_item

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.root_item.data(section)

        return None

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return QModelIndex()

        child_item: TreeItem = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def insertColumns(self, position: int, columns: int,
                      parent: QModelIndex = QModelIndex()) -> bool:
        self.beginInsertColumns(parent, position, position + columns - 1)
        success: bool = self.root_item.insert_columns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position: int, rows: int,
                   parent: QModelIndex = QModelIndex()) -> bool:
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return False

        self.beginInsertRows(parent, position, position + rows - 1)
        column_count = self.root_item.column_count()
        success: bool = parent_item.insert_children(position, rows, column_count)
        self.endInsertRows()

        return success

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: TreeItem = self.get_item(index)
        if child_item:
            parent_item: TreeItem = child_item.parent()
        else:
            parent_item = None

        if parent_item == self.root_item or not parent_item:
            return QModelIndex()

        return self.createIndex(parent_item.child_number(), 0, parent_item)

    def removeColumns(self, position: int, columns: int,
                      parent: QModelIndex = QModelIndex()) -> bool:
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success: bool = self.root_item.remove_columns(position, columns)
        self.endRemoveColumns()

        if self.root_item.column_count() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position: int, rows: int,
                   parent: QModelIndex = QModelIndex()) -> bool:
        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return False

        self.beginRemoveRows(parent, position, position + rows - 1)
        success: bool = parent_item.remove_children(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() and parent.column() > 0:
            return 0

        parent_item: TreeItem = self.get_item(parent)
        if not parent_item:
            return 0
        return parent_item.child_count()

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False

        item: TreeItem = self.get_item(index)
        result: bool = item.set_data(index.column(), value)

        if result:
            self.dataChanged.emit(index, index,
                                  [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])

        return result

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value,
                      role: int = None) -> bool:
        if role != Qt.ItemDataRole.EditRole or orientation != Qt.Orientation.Horizontal:
            return False

        result: bool = self.root_item.set_data(section, value)

        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def setup_model_data(self, lines: list, parent: TreeItem):
        parents = [parent]
        indentations = [0]

        for line in lines:
            line = line.rstrip()
            if line and "\t" in line:

                position = 0
                while position < len(line):
                    if line[position] != " ":
                        break
                    position += 1

                column_data = line[position:].split("\t")
                column_data = [string for string in column_data if string]

                if position > indentations[-1]:
                    if parents[-1].child_count() > 0:
                        parents.append(parents[-1].last_child())
                        indentations.append(position)
                else:
                    while position < indentations[-1] and parents:
                        parents.pop()
                        indentations.pop()

                parent: TreeItem = parents[-1]
                col_count = self.root_item.column_count()
                parent.insert_children(parent.child_count(), 1, col_count)

                for column in range(len(column_data)):
                    child = parent.last_child()
                    child.set_data(column, column_data[column])

    def _repr_recursion(self, item: TreeItem, indent: int = 0) -> str:
        result = " " * indent + repr(item) + "\n"
        for child in item.child_items:
            result += self._repr_recursion(child, indent + 2)
        return result

    def __repr__(self) -> str:
        r