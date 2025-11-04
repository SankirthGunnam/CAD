from __future__ import annotations

import sys
import os
from typing import Dict, List, Optional, Tuple

# Add the apps path to sys.path to import from the BCF module
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'RBM5', 'BCF'))

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QSize
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QTreeView,
    QHeaderView,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMenu,
    QStyle,
)

from config.constants.tabs import DeviceSettings


# -----------------------------
# Model
# -----------------------------

ROLE_LEVEL = Qt.UserRole + 1
ROLE_LINES = Qt.UserRole + 2
ROLE_HAS_CHILDREN = Qt.UserRole + 3
ROLE_EXPANDED = Qt.UserRole + 4
ROLE_ID = Qt.UserRole + 5

# -----------------------------
# Two-column hierarchical model for QTreeView
# -----------------------------


class FlatTreeItemModel(QAbstractItemModel):
    """Hierarchical model over a flat list-of-dicts with two columns.

    Column mapping is provided via (header, key) pairs. Example:
      columns=[("Name", "label"), ("Info", "id")]
    """

    def __init__(
        self,
        rows: List[Dict],
        columns: List[Tuple[str, str]] | None = None,
        id_key: str = "id",
        parent_key: str = "parent_id",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._rows: List[Dict] = list(rows)
        self._id_key = id_key
        self._parent_key = parent_key
        self._id_to_row_index: Dict[int, int] = {}
        self._columns: List[Tuple[str, str]] = columns or [
            ("Name", "label"), ("Info", "id")]
        self._reindex()

    # ---------- Helpers ----------
    def _reindex(self) -> None:
        self._id_to_row_index = {
            int(r[self._id_key]): i for i, r in enumerate(self._rows)}

    def _children_ids(self, parent_id: Optional[int]) -> List[int]:
        ids: List[int] = []
        for r in self._rows:
            if r.get(self._parent_key) == parent_id:
                ids.append(int(r[self._id_key]))
        return ids

    def _parent_id_of(self, node_id: int) -> Optional[int]:
        row_idx = self._id_to_row_index.get(node_id)
        if row_idx is None:
            return None
        parent_val = self._rows[row_idx].get(self._parent_key)
        return int(parent_val) if parent_val is not None else None

    def _row_in_parent(self, node_id: int) -> int:
        parent_id = self._parent_id_of(node_id)
        siblings = self._children_ids(parent_id)
        try:
            return siblings.index(node_id)
        except ValueError:
            return -1

    # ---------- Qt model API ----------
    # type: ignore[override]
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    # type: ignore[override]
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        parent_id: Optional[int]
        if not parent.isValid():
            parent_id = None
        else:
            parent_id = int(parent.internalId())
        return len(self._children_ids(parent_id))

    # type: ignore[override]
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if row < 0 or column < 0 or column >= self.columnCount():
            return QModelIndex()
        parent_id: Optional[int]
        if not parent.isValid():
            parent_id = None
        else:
            parent_id = int(parent.internalId())
        children = self._children_ids(parent_id)
        if row >= len(children):
            return QModelIndex()
        node_id = children[row]
        return self.createIndex(row, column, node_id)

    # type: ignore[override]
    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node_id = int(index.internalId())
        parent_id = self._parent_id_of(node_id)
        if parent_id is None:
            return QModelIndex()
        grandparent_id = self._parent_id_of(parent_id)
        row_in_grandparent = self._row_in_parent(parent_id)
        return self.createIndex(row_in_grandparent, 0, parent_id)

    # type: ignore[override]
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        node_id = int(index.internalId())
        row_idx = self._id_to_row_index.get(node_id)
        if row_idx is None:
            return None
        row = self._rows[row_idx]
        header, key = self._columns[index.column()]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if key == self._id_key:
                return str(int(row[self._id_key]))
            value = row.get(key)
            return "" if value is None else str(value)
        # Decoration: show different icons for devices vs properties on first column
        # if role == Qt.DecorationRole and index.column() == 0:
        #     is_device = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
        #     icon = QApplication.style().standardIcon(
        #         QStyle.SP_DirIcon if is_device else QStyle.SP_FileIcon
        #     )
        #     return icon
        # Font: bold for device (top-level) rows on first column
        if role == Qt.FontRole and index.column() == 0:
            is_device = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
            if is_device:
                font = QFont()
                font.setBold(True)
                return font
        # Foreground: subtle color difference for devices
        if role == Qt.ForegroundRole and index.column() == 0:
            is_device = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
            if is_device:
                return QColor("#1a4a8e")
        # Tooltips: helpful hints for both columns
        if role == Qt.ToolTipRole:
            if index.column() == 0:
                is_device = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
                if is_device:
                    return f"Device: {row.get('label', '')}"
                return f"Property: {row.get('label', '')}"
            if index.column() == 1:
                return f"Value: {row.get('info', '')}"
        if role == ROLE_ID and index.column() == 0:
            return node_id
        return None

    # type: ignore[override]
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._columns):
                return self._columns[section][0]
        return None

    # type: ignore[override]
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        header, key = self._columns[index.column()]
        editable = key not in (self._id_key, self._parent_key)
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if editable:
            flags |= Qt.ItemIsEditable
        return flags

    # type: ignore[override]
    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or role != Qt.EditRole:
            return False
        node_id = int(index.internalId())
        row_idx = self._id_to_row_index.get(node_id)
        if row_idx is None:
            return False
        header, key = self._columns[index.column()]
        if key in (self._id_key, self._parent_key):
            return False
        self._rows[row_idx][key] = str(value)
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    # ---------- Convenience ops (reset-based for simplicity) ----------
    def add_child(self, parent_id: Optional[int], values: Optional[Dict] = None) -> int:
        new_id = 1
        if self._rows:
            new_id = max(int(r[self._id_key]) for r in self._rows) + 1
        new_row = {self._id_key: new_id, self._parent_key: parent_id}
        for _, key in self._columns:
            if key not in (self._id_key, self._parent_key):
                new_row[key] = None
        if values:
            new_row.update(values)
        self.beginResetModel()
        self._rows.append(new_row)
        self._reindex()
        self.endResetModel()
        return new_id

    def remove_subtree(self, node_id: int) -> None:
        to_remove: set[int] = set()
        stack: List[int] = [node_id]
        while stack:
            cur = stack.pop()
            if cur in to_remove:
                continue
            to_remove.add(cur)
            stack.extend(self._children_ids(cur))
        self.beginResetModel()
        self._rows = [r for r in self._rows if int(
            r[self._id_key]) not in to_remove]
        self._reindex()
        self.endResetModel()

    def index_for_id(self, node_id: int, column: int = 0) -> QModelIndex:
        # Build chain from root to node
        chain: List[int] = []
        cur: Optional[int] = node_id
        while cur is not None:
            chain.append(cur)
            cur = self._parent_id_of(cur)
        chain.reverse()  # [root, ..., node]
        parent = QModelIndex()
        for i, nid in enumerate(chain):
            if i == 0:
                # root child under None parent
                row = self._row_in_parent(nid)
                parent = self.index(row, 0, QModelIndex())
            else:
                # child under previous parent
                row = self._row_in_parent(nid)
                parent = self.index(row, 0, parent)
        return parent.sibling(parent.row(), column)


# -----------------------------
# Demo application
# -----------------------------


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Device Settings Tree View - AllDevicesTable Structure")
        self.resize(640, 480)

        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        # View + model (QTreeView with two columns)
        self._view = QTreeView(central)
        self._view.setAlternatingRowColors(True)
        self._view.setEditTriggers(
            QTreeView.DoubleClicked | QTreeView.EditKeyPressed | QTreeView.SelectedClicked)
        self._view.setSelectionMode(QTreeView.SingleSelection)
        self._view.setUniformRowHeights(True)
        self._view.header().setStretchLastSection(True)
        self._view.header().setSectionResizeMode(QHeaderView.Interactive)
        # View tweaks for aesthetics
        self._view.setAnimated(True)
        self._view.setIndentation(18)
        self._view.setIconSize(QSize(16, 16))
        # Right-click context menu
        self._view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._view.customContextMenuRequested.connect(self._on_context_menu)
        # Subtle stylesheet: lighter selection, padding, and gridless look
        self._view.setStyleSheet(
            """
            QTreeView {
                outline: 0;
                alternate-background-color: #f7f9fc;
                background: #ffffff;
                selection-background-color: #e6f0ff;
                selection-color: #0f3d91;
                show-decoration-selected: 1;
                padding: 2px;
                border: 1px solid #d9e2ef;
                border-radius: 4px;
            }
            QTreeView::item {
                padding: 4px 6px;
            }
            QHeaderView::section {
                background: #f0f4fa;
                border: 1px solid #d9e2ef;
                padding: 4px 6px;
            }
            """
        )
        vbox.addWidget(self._view, 1)

        self.setCentralWidget(central)

        # Device settings data: Flat structure using AllDevicesTable enum values as keys
        self._device_data = [
            {
                DeviceSettings.AllDevicesTable.DEVICE_NAME.value: "Camera Module",
                DeviceSettings.AllDevicesTable.DEVICE_ID.value: "1",
                DeviceSettings.AllDevicesTable.CONTROL_TYPE.value: "I2C",
                DeviceSettings.AllDevicesTable.MODULE.value: "CAM",
                DeviceSettings.AllDevicesTable.USID.value: "0x10",
                DeviceSettings.AllDevicesTable.MID_MSB.value: "0x02",
                DeviceSettings.AllDevicesTable.MID_LSB.value: "0x04",
                DeviceSettings.AllDevicesTable.PID.value: "0x1234",
                DeviceSettings.AllDevicesTable.EXT_PID.value: "0x5678",
                DeviceSettings.AllDevicesTable.REV_ID.value: "0x01",
                DeviceSettings.AllDevicesTable.DCF_TYPE.value: "Camera"
            },
            {
                DeviceSettings.AllDevicesTable.DEVICE_NAME.value: "Sensor Module",
                DeviceSettings.AllDevicesTable.DEVICE_ID.value: "2",
                DeviceSettings.AllDevicesTable.CONTROL_TYPE.value: "SPI",
                DeviceSettings.AllDevicesTable.MODULE.value: "SENS",
                DeviceSettings.AllDevicesTable.USID.value: "0x20",
                DeviceSettings.AllDevicesTable.MID_MSB.value: "0x03",
                DeviceSettings.AllDevicesTable.MID_LSB.value: "0x05",
                DeviceSettings.AllDevicesTable.PID.value: "0x2345",
                DeviceSettings.AllDevicesTable.EXT_PID.value: "0x6789",
                DeviceSettings.AllDevicesTable.REV_ID.value: "0x02",
                DeviceSettings.AllDevicesTable.DCF_TYPE.value: "Sensor"
            },
            {
                DeviceSettings.AllDevicesTable.DEVICE_NAME.value: "Display Module",
                DeviceSettings.AllDevicesTable.DEVICE_ID.value: "3",
                DeviceSettings.AllDevicesTable.CONTROL_TYPE.value: "MIPI",
                DeviceSettings.AllDevicesTable.MODULE.value: "DISP",
                DeviceSettings.AllDevicesTable.USID.value: "0x30",
                DeviceSettings.AllDevicesTable.MID_MSB.value: "0x04",
                DeviceSettings.AllDevicesTable.MID_LSB.value: "0x06",
                DeviceSettings.AllDevicesTable.PID.value: "0x3456",
                DeviceSettings.AllDevicesTable.EXT_PID.value: "0x7890",
                DeviceSettings.AllDevicesTable.REV_ID.value: "0x03",
                DeviceSettings.AllDevicesTable.DCF_TYPE.value: "Display"
            },
        ]
        
        # Convert flat device data to hierarchical tree structure
        self._data = self._convert_device_data_to_tree(self._device_data)

        self._model = FlatTreeItemModel(
            self._data, columns=[("Property", "label"), ("Value", "info")], parent=self)
        self._view.setModel(self._model)
        self._view.expandAll()

        # Print the device data structure for verification
        self._print_device_data()

    def _print_device_data(self) -> None:
        """Print the current device data structure for verification."""
        print("Current Device Data Structure:")
        print("=" * 50)
        for i, device in enumerate(self._device_data, 1):
            print(f"Device {i}:")
            for key, value in device.items():
                print(f"  {key}: {value}")
            print()
        print("=" * 50)

    def _convert_device_data_to_tree(self, device_data: List[Dict]) -> List[Dict]:
        """Convert flat device data to hierarchical tree structure."""
        tree_data = []
        device_id = 1
        
        for device in device_data:
            # Create parent node for the device
            device_node_id = device_id
            device_name = device[DeviceSettings.AllDevicesTable.DEVICE_NAME.value]
            tree_data.append({
                "id": device_node_id,
                "parent_id": None,
                "label": device_name,
                "info": "Device"
            })
            
            # Create child nodes for each property (excluding device name)
            child_id = device_id * 100  # Use large numbers to avoid conflicts
            for key, value in device.items():
                if key != DeviceSettings.AllDevicesTable.DEVICE_NAME.value:  # Skip the device name itself
                    tree_data.append({
                        "id": child_id,
                        "parent_id": device_node_id,
                        "label": key,  # Use the enum value directly as the label
                        "info": str(value)
                    })
                    child_id += 1
            
            device_id += 1
            
        return tree_data

    def _on_add_child(self) -> None:
        idx = self._view.currentIndex()
        parent_id: Optional[int]
        if idx.isValid():
            parent_id = int(idx.data(ROLE_ID) or int(idx.internalId()))
        else:
            parent_id = None
        
        # If adding to a device (parent node), add a new property
        if parent_id is not None:
            new_id = self._model.add_child(parent_id, {"label": "New Property", "info": "New Value"})
        else:
            # If adding at root level, add a new device
            self._add_new_device()
            return
        
        self._view.expandAll()
        sel = self._model.index_for_id(new_id, 0)
        if sel.isValid():
            self._view.setCurrentIndex(sel)
            self._view.edit(sel)

    def _add_new_device(self) -> None:
        """Add a new device to the flat data structure and refresh the tree."""
        # Create new device with default values using AllDevicesTable enum
        new_device = {
            DeviceSettings.AllDevicesTable.DEVICE_NAME.value: "New Device",
            DeviceSettings.AllDevicesTable.DEVICE_ID.value: str(len(self._device_data) + 1),
            DeviceSettings.AllDevicesTable.CONTROL_TYPE.value: "I2C",
            DeviceSettings.AllDevicesTable.MODULE.value: "NEW",
            DeviceSettings.AllDevicesTable.USID.value: "0x00",
            DeviceSettings.AllDevicesTable.MID_MSB.value: "0x00",
            DeviceSettings.AllDevicesTable.MID_LSB.value: "0x00",
            DeviceSettings.AllDevicesTable.PID.value: "0x0000",
            DeviceSettings.AllDevicesTable.EXT_PID.value: "0x0000",
            DeviceSettings.AllDevicesTable.REV_ID.value: "0x00",
            DeviceSettings.AllDevicesTable.DCF_TYPE.value: "Unknown"
        }
        
        # Add to flat data
        self._device_data.append(new_device)
        
        # Regenerate tree data
        self._data = self._convert_device_data_to_tree(self._device_data)
        
        # Update model
        self._model = FlatTreeItemModel(
            self._data, columns=[("Property", "label"), ("Value", "info")], parent=self)
        self._view.setModel(self._model)
        self._view.expandAll()

    def _on_remove(self) -> None:
        idx = self._view.currentIndex()
        if not idx.isValid():
            return
        node_id = int(idx.data(ROLE_ID) or int(idx.internalId()))
        parent = idx.parent()
        parent_id = int(parent.internalId()) if parent.isValid() else None
        self._model.remove_subtree(node_id)
        self._view.expandAll()
        if parent_id is not None:
            sel = self._model.index_for_id(parent_id, 0)
            if sel.isValid():
                self._view.setCurrentIndex(sel)

    def _on_context_menu(self, pos) -> None:
        idx = self._view.indexAt(pos)
        menu = QMenu(self)
        act_add_device = menu.addAction("Add Device")
        act_add_property = None
        act_remove = None
        if idx.isValid():
            act_add_property = menu.addAction("Add Property")
            act_remove = menu.addAction("Remove")
        action = menu.exec(self._view.viewport().mapToGlobal(pos))
        if action is None:
            return
        if action == act_add_device:
            self._add_new_device()
            return
        if act_add_property is not None and action == act_add_property:
            base_idx = idx.sibling(idx.row(), 0)
            parent_idx = base_idx if not base_idx.parent().isValid() else base_idx.parent()
            parent_id = int(parent_idx.data(ROLE_ID) or int(parent_idx.internalId()))
            new_id = self._model.add_child(parent_id, {"label": "New Property", "info": "New Value"})
            self._view.expand(parent_idx)
            sel = self._model.index_for_id(new_id, 0)
            if sel.isValid():
                self._view.setCurrentIndex(sel)
                self._view.edit(sel)
            return
        if act_remove is not None and action == act_remove:
            self._on_remove()


def main() -> None:
    app = QApplication([])
    # High-DPI friendliness
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
