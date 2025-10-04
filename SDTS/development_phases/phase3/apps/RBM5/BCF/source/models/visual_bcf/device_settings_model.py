# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel
from apps.RBM5.BCF.gui.source.visual_bcf.device_settings import DeviceSettings
from apps.RBM5.BCF.config.constants.tabs import DeviceSettings as TabsDeviceSettings
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QFont, QColor
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Two-column hierarchical model for QTreeView (moved from demo)
# -----------------------------


class FlatTreeItemModel(QAbstractItemModel):
    def __init__(
        self,
        rows: List[Dict],
        columns: List[Tuple[str, str]] | None = None,
        id_key: str = "id",
        parent_key: str = "parent_id",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rows: List[Dict] = list(rows)
        self._id_key = id_key
        self._parent_key = parent_key
        self._id_to_row_index: Dict[int, int] = {}
        self._columns: List[Tuple[str, str]] = columns or [("Property", "label"), ("Value", "info")]
        self._reindex()

    def _reindex(self) -> None:
        self._id_to_row_index = {int(r[self._id_key]): i for i, r in enumerate(self._rows)}

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

    # Qt model API
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self._columns)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        if not parent.isValid():
            parent_id: Optional[int] = None
        else:
            parent_id = int(parent.internalId())
        return len(self._children_ids(parent_id))

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:  # type: ignore[override]
        if row < 0 or column < 0 or column >= self.columnCount():
            return QModelIndex()
        if not parent.isValid():
            parent_id: Optional[int] = None
        else:
            parent_id = int(parent.internalId())
        children = self._children_ids(parent_id)
        if row >= len(children):
            return QModelIndex()
        node_id = children[row]
        return self.createIndex(row, column, node_id)

    def parent(self, index: QModelIndex) -> QModelIndex:  # type: ignore[override]
        if not index.isValid():
            return QModelIndex()
        node_id = int(index.internalId())
        parent_id = self._parent_id_of(node_id)
        if parent_id is None:
            return QModelIndex()
        row_in_grandparent = self._row_in_parent(parent_id)
        return self.createIndex(row_in_grandparent, 0, parent_id)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        node_id = int(index.internalId())
        row_idx = self._id_to_row_index.get(node_id)
        if row_idx is None:
            return None
        row = self._rows[row_idx]
        header, key = self._columns[index.column()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            if key == self._id_key:
                return str(int(row[self._id_key]))
            value = row.get(key)
            return "" if value is None else str(value)
        if role == Qt.FontRole and index.column() == 0:
            is_top = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
            if is_top:
                f = QFont()
                f.setBold(True)
                return f
        if role == Qt.ToolTipRole:
            if index.column() == 0:
                is_top = row.get(self._parent_key) is None or str(row.get("info", "")) == "Device"
                return ("Device: " if is_top else "Property: ") + str(row.get("label", ""))
            if index.column() == 1:
                return "Value: " + str(row.get("info", ""))
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[override]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self._columns):
                return self._columns[section][0]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        header, key = self._columns[index.column()]
        editable = key not in (self._id_key, self._parent_key)
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if editable:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:  # type: ignore[override]
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

    # Convenience ops
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
        self._rows = [r for r in self._rows if int(r[self._id_key]) not in to_remove]
        self._reindex()
        self.endResetModel()

    def index_for_id(self, node_id: int, column: int = 0) -> QModelIndex:
        chain: List[int] = []
        cur: Optional[int] = node_id
        while cur is not None:
            chain.append(cur)
            cur = self._parent_id_of(cur)
        chain.reverse()
        parent = QModelIndex()
        for i, nid in enumerate(chain):
            if i == 0:
                row = self._row_in_parent(nid)
                parent = self.index(row, 0, QModelIndex())
            else:
                row = self._row_in_parent(nid)
                parent = self.index(row, 0, parent)
        return parent.sibling(parent.row(), column)


class RecordsTreeModel(QAbstractItemModel):
    """Two-level tree over raw records (no id/parent in input), with stable internalIds.

    Parents: one per record (column 0 shows a selected label field; column 1 shows a tag like "Device").
    Children: all other fields except skip_keys.
    """

    def __init__(
        self,
        records: List[Dict],
        parent_label_key: str,
        parent_info_label: str = "Device",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._records: List[Dict] = list(records)
        self._parent_label_key = parent_label_key
        self._parent_info_label = parent_info_label
        # id maps
        self._parent_ids: List[int] = []             # row -> parent_id
        self._parent_id_to_row: Dict[int, int] = {}  # parent_id -> row
        self._child_ids_by_row: Dict[int, List[int]] = {}  # row -> [child_id]
        self._child_id_to_info: Dict[int, Tuple[int, str]] = {}  # child_id -> (row, key)
        self._rebuild_ids()

    def _child_keys(self, rec: Dict) -> List[str]:
        keys: List[str] = []
        for k in rec.keys():
            # exclude the field used for parent label to avoid duplication
            if k == self._parent_label_key:
                continue
            keys.append(str(k))
        return keys

    def _rebuild_ids(self) -> None:
        self._parent_ids.clear()
        self._parent_id_to_row.clear()
        self._child_ids_by_row.clear()
        self._child_id_to_info.clear()
        next_id = 1
        for row, rec in enumerate(self._records):
            pid = next_id
            next_id += 1
            self._parent_ids.append(pid)
            self._parent_id_to_row[pid] = row
            child_ids: List[int] = []
            for key in self._child_keys(rec):
                cid = next_id
                next_id += 1
                self._child_id_to_info[cid] = (row, key)
                child_ids.append(cid)
            self._child_ids_by_row[row] = child_ids

    # Qt model API
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 2

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        if not parent.isValid():
            return len(self._records)
        pid = int(parent.internalId())
        prow = self._parent_id_to_row.get(pid)
        if prow is None:
            return 0
        return len(self._child_ids_by_row.get(prow, []))

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:  # type: ignore[override]
        if row < 0 or column < 0 or column >= self.columnCount():
            return QModelIndex()
        if not parent.isValid():
            if 0 <= row < len(self._parent_ids):
                return self.createIndex(row, column, self._parent_ids[row])
            return QModelIndex()
        pid = int(parent.internalId())
        prow = self._parent_id_to_row.get(pid)
        if prow is None:
            return QModelIndex()
        child_ids = self._child_ids_by_row.get(prow, [])
        if 0 <= row < len(child_ids):
            return self.createIndex(row, column, child_ids[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:  # type: ignore[override]
        if not index.isValid():
            return QModelIndex()
        nid = int(index.internalId())
        info = self._child_id_to_info.get(nid)
        if info is None:
            return QModelIndex()
        prow, _ = info
        pid = self._parent_ids[prow]
        return self.createIndex(prow, 0, pid)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        nid = int(index.internalId())
        if nid in self._parent_id_to_row:
            rec = self._records[self._parent_id_to_row[nid]]
            if role in (Qt.DisplayRole, Qt.EditRole):
                if index.column() == 0:
                    return str(rec.get(self._parent_label_key, ""))
                if index.column() == 1:
                    return self._parent_info_label
            if role == Qt.FontRole and index.column() == 0:
                f = QFont()
                f.setBold(True)
                return f
            if role == Qt.ToolTipRole:
                return f"Device: {rec.get(self._parent_label_key, '')}"
            return None
        info = self._child_id_to_info.get(nid)
        if info is None:
            return None
        prow, key = info
        rec = self._records[prow]
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return key
            if index.column() == 1:
                val = rec.get(key)
                return "" if val is None else str(val)
        if role == Qt.ToolTipRole:
            if index.column() == 0:
                return f"Property: {key}"
            if index.column() == 1:
                return f"Value: {rec.get(key)}"
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # type: ignore[override]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "Property" if section == 0 else "Value"
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # Convenience ops compatible with views calling remove_subtree(node_id)
    def remove_subtree(self, node_id: int) -> None:
        self.beginResetModel()
        if node_id in self._parent_id_to_row:
            row = self._parent_id_to_row[node_id]
            if 0 <= row < len(self._records):
                del self._records[row]
        else:
            info = self._child_id_to_info.get(node_id)
            if info is not None:
                prow, key = info
                try:
                    if key in self._records[prow]:
                        del self._records[prow][key]
                except Exception:
                    pass
        self._rebuild_ids()
        self.endResetModel()


class DeviceSettingsModel(AbstractModel):

    @property
    def device_selection(self):
        return self.rdb[paths.DEVICE_SELECTION]

    @property
    def static_mipi_channels(self):
        return self.rdb[paths.STATIC_MIPI_CHANNELS]

    @property
    def bcf_data(self):
        return self.rdb[paths.BCF_CONFIG]

    @property
    def bcf_db(self):
        return self.rdb[paths.BCF_DB(self.current_revision)]

    @property
    def dcf_for_bcf(self):
        return self.rdb[paths.BCF_DCF_FOR_BCF]

    @property
    def mipi_version(self):
        return self.rdb[paths.DYNAMIC_MIPI_VERSION]

    def __init__(self, controller, rdb: "RDBManager"):
        print(f"✓ Device Settings model initialized with controller: {controller}")
        super().__init__(controller=controller, rdb=rdb)
        print(f"✓ Device Settings model initialized with rdb: {rdb}")
        print(f"✓ bcf_db type: {type(self.bcf_db)}, value: {self.bcf_db}")
        self.all_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.DCF_DEVICES,
            columns=[
                DeviceSettings.AllDevicesTable.DEVICE_ID(),
                DeviceSettings.AllDevicesTable.DEVICE_NAME(),
                DeviceSettings.AllDevicesTable.CONTROL_TYPE(),
                DeviceSettings.AllDevicesTable.MODULE(),
            ],
        )
        print(f"✓ Device Settings model initialized with all_devices_model: {self.all_devices_model}")
        self.mipi_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.BCF_DEV_MIPI(self.current_revision),
            columns=[
                DeviceSettings.MipiDevicesTable.ID(),
                DeviceSettings.MipiDevicesTable.DCF(),
                DeviceSettings.MipiDevicesTable.NAME(),
                DeviceSettings.MipiDevicesTable.USID(),
                DeviceSettings.MipiDevicesTable.MODULE(),
                DeviceSettings.MipiDevicesTable.MIPI_TYPE(),
                DeviceSettings.MipiDevicesTable.MIPI_CHANNEL(),
                DeviceSettings.MipiDevicesTable.DEFAULT_USID(),
                DeviceSettings.MipiDevicesTable.USER_USID(),
                DeviceSettings.MipiDevicesTable.PID(),
                DeviceSettings.MipiDevicesTable.EXT_PID(),
            ],
        )
        print(f"✓ Device Settings model initialized with mipi_devices_model: {self.mipi_devices_model}")
        self.gpio_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.BCF_DEV_GPIO(self.current_revision),
            columns=[
                DeviceSettings.GpioDevicesTable.ID(),
                DeviceSettings.GpioDevicesTable.DCF(),
                DeviceSettings.GpioDevicesTable.NAME(),
                DeviceSettings.GpioDevicesTable.CTRL_TYPE(),
                DeviceSettings.GpioDevicesTable.BOARD(),
            ],
        )
        print(f"✓ Device Settings model initialized with gpio_devices_model: {self.gpio_devices_model}")

        # Tree models directly over raw records (no id/parent keys required)
        self.all_devices_tree_model = RecordsTreeModel(
            self._iter_rows(self.rdb[paths.DCF_DEVICES]),
            parent_label_key=TabsDeviceSettings.AllDevicesTable.DEVICE_NAME(),
            parent_info_label="Device",
        )
        self.mipi_devices_tree_model = RecordsTreeModel(
            self._iter_rows(self.rdb[paths.BCF_DEV_MIPI(self.current_revision)]),
            parent_label_key=TabsDeviceSettings.MipiDevicesTable.NAME(),
            parent_info_label="Device",
        )
        self.gpio_devices_tree_model = RecordsTreeModel(
            self._iter_rows(self.rdb[paths.BCF_DEV_GPIO(self.current_revision)]),
            parent_label_key=TabsDeviceSettings.GpioDevicesTable.NAME(),
            parent_info_label="Device",
        )

    def refresh_from_data_model(self) -> bool:
        """Refresh all table models from the data model"""
        try:
            # Force refresh of all table models
            self.mipi_devices_model.layoutChanged.emit()
            self.gpio_devices_model.layoutChanged.emit()
            print("✓ Device Settings tables refreshed from data model")
            # Rebuild tree models
            self.all_devices_tree_model = RecordsTreeModel(
                self._iter_rows(self.rdb[paths.DCF_DEVICES]),
                parent_label_key=TabsDeviceSettings.AllDevicesTable.DEVICE_NAME(),
                parent_info_label="Device",
            )
            self.mipi_devices_tree_model = RecordsTreeModel(
                self._iter_rows(self.rdb[paths.BCF_DEV_MIPI(self.current_revision)]),
                parent_label_key=TabsDeviceSettings.MipiDevicesTable.NAME(),
                parent_info_label="Device",
            )
            self.gpio_devices_tree_model = RecordsTreeModel(
                self._iter_rows(self.rdb[paths.BCF_DEV_GPIO(self.current_revision)]),
                parent_label_key=TabsDeviceSettings.GpioDevicesTable.NAME(),
                parent_info_label="Device",
            )
            return True
        except Exception as e:
            print(f"✗ Error refreshing device settings tables: {e}")
            return False

    # --------- Tree builders ---------
    def _iter_rows(self, obj) -> List[Dict]:
        try:
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                return list(obj.values())
        except Exception:
            pass
        return []
