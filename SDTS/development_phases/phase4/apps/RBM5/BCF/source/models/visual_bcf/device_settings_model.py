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

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        nid = int(index.internalId())
        # Parent rows: allow editing of label (column 0)
        if nid in self._parent_id_to_row:
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if index.column() == 0:
                flags |= Qt.ItemIsEditable
            return flags
        # Child rows: allow editing of value (column 1)
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:  # type: ignore[override]
        if not index.isValid() or role != Qt.EditRole:
            return False
        nid = int(index.internalId())
        if nid in self._parent_id_to_row:
            # Edit parent label field
            if index.column() != 0:
                return False
            row = self._parent_id_to_row[nid]
            try:
                self._records[row][self._parent_label_key] = str(value)
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
            except Exception:
                return False
        info = self._child_id_to_info.get(nid)
        if info is None:
            return False
        if index.column() != 1:
            return False
        prow, key = info
        try:
            self._records[prow][key] = str(value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        except Exception:
            return False

    def add_record(self, defaults: Optional[Dict] = None) -> int:
        """Append a new parent record and return its parent_id."""
        rec: Dict[str, str] = {}
        # Ensure label key exists
        rec[self._parent_label_key] = "New Device"
        if defaults:
            rec.update(defaults)
        self.beginResetModel()
        self._records.append(rec)
        self._rebuild_ids()
        self.endResetModel()
        # Return last parent id
        return self._parent_ids[-1] if self._parent_ids else -1

    def index_for_id(self, node_id: int, column: int = 0) -> QModelIndex:
        if node_id in self._parent_id_to_row:
            row = self._parent_id_to_row[node_id]
            return self.createIndex(row, column, node_id)
        info = self._child_id_to_info.get(node_id)
        if info is not None:
            prow, _ = info
            pid = self._parent_ids[prow]
            parent_index = self.createIndex(prow, 0, pid)
            child_ids = self._child_ids_by_row.get(prow, [])
            try:
                crow = child_ids.index(node_id)
            except ValueError:
                return parent_index
            return self.createIndex(crow, column, node_id)
        return QModelIndex()

    def get_record_by_parent_id(self, parent_id: int):
        """Return the underlying record dict for a given parent node id, or None."""
        row = self._parent_id_to_row.get(parent_id)
        if row is None:
            return None
        try:
            return self._records[row]
        except Exception:
            return None

    def find_parent_id_by_key_value(self, key: str, value) -> int:
        """Find the parent_id of the first record where rec[key] == value. Returns -1 if not found."""
        target = str(value)
        for row, rec in enumerate(self._records):
            try:
                if str(rec.get(key)) == target:
                    return self._parent_ids[row]
            except Exception:
                continue
        return -1

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
        nid = int(index.internalId())
        # Parent row (device): make label (column 0) editable; column 1 is info tag
        if nid in self._parent_id_to_row:
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            if index.column() == 0:
                flags |= Qt.ItemIsEditable
            return flags
        # Child row (property/value): allow editing only in Value column
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:  # type: ignore[override]
        if not index.isValid() or role != Qt.EditRole:
            return False
        nid = int(index.internalId())
        # Parent label edit
        if nid in self._parent_id_to_row:
            if index.column() != 0:
                return False
            row = self._parent_id_to_row[nid]
            try:
                self._records[row][self._parent_label_key] = str(value)
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
            except Exception:
                return False
        # Child value edit
        info = self._child_id_to_info.get(nid)
        if info is None or index.column() != 1:
            return False
        prow, key = info
        try:
            self._records[prow][key] = str(value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        except Exception:
            return False

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
        # Removed mipi_devices_model and gpio_devices_model; operate directly on tree models

        # Tree models directly over raw records (no id/parent keys required)
        self.all_devices_tree_model = RecordsTreeModel(
            self.rdb[paths.DCF_DEVICES],
            parent_label_key=TabsDeviceSettings.AllDevicesTable.DEVICE_NAME(),
            parent_info_label="Device",
        )
        self.mipi_devices_tree_model = RecordsTreeModel(
            self.rdb[paths.BCF_DEV_MIPI(self.current_revision)],
            parent_label_key=TabsDeviceSettings.MipiDevicesTable.NAME(),
            parent_info_label="Device",
        )
        self.gpio_devices_tree_model = RecordsTreeModel(
            self.rdb[paths.BCF_DEV_GPIO(self.current_revision)],
            parent_label_key=TabsDeviceSettings.GpioDevicesTable.NAME(),
            parent_info_label="Device",
        )

    # --------- Public API to add devices directly to tree models ---------
    def add_mipi_device_defaults(self, data: Dict = None) -> int:
        import uuid
        m = TabsDeviceSettings.MipiDevicesTable
        defaults = {
            m.ID(): str(uuid.uuid4()),
            m.DCF(): data.get(m.DCF(), ""),
            m.NAME(): data.get(m.NAME(), "New Device"),
            m.USID(): data.get(m.USID(), ""),
            m.MODULE(): data.get(m.MODULE(), ""),
            m.MIPI_TYPE(): data.get(m.MIPI_TYPE(), ""),
            m.MIPI_CHANNEL(): data.get(m.MIPI_CHANNEL(), ""),
            m.DEFAULT_USID(): data.get(m.DEFAULT_USID(), ""),
            m.USER_USID(): data.get(m.USER_USID(), ""),
            m.PID(): data.get(m.PID(), ""),
            m.EXT_PID(): data.get(m.EXT_PID(), ""),
        }
        return self.mipi_devices_tree_model.add_record(defaults)

    def add_gpio_device_defaults(self, data: Dict = None) -> int:
        import uuid
        g = TabsDeviceSettings.GpioDevicesTable
        defaults = {
            g.ID(): str(uuid.uuid4()),
            g.DCF(): data.get(g.DCF(), ""),
            g.NAME(): data.get(g.NAME(), "New Device"),
            g.CTRL_TYPE(): data.get(g.CTRL_TYPE(), ""),
            g.BOARD(): data.get(g.BOARD(), ""),
        }
        return self.gpio_devices_tree_model.add_record(defaults)

    def refresh_from_data_model(self) -> bool:
        """Refresh all table models from the data model"""
        try:
            # Rebuild tree models only (no table models)
            self.all_devices_tree_model = RecordsTreeModel(
                self.rdb[paths.DCF_DEVICES],
                parent_label_key=TabsDeviceSettings.AllDevicesTable.DEVICE_NAME(),
                parent_info_label="Device",
            )
            self.mipi_devices_tree_model = RecordsTreeModel(
                self.rdb[paths.BCF_DEV_MIPI(self.current_revision)],
                parent_label_key=TabsDeviceSettings.MipiDevicesTable.NAME(),
                parent_info_label="Device",
            )
            self.gpio_devices_tree_model = RecordsTreeModel(
                self.rdb[paths.BCF_DEV_GPIO(self.current_revision)],
                parent_label_key=TabsDeviceSettings.GpioDevicesTable.NAME(),
                parent_info_label="Device",
            )
            return True
        except Exception as e:
            print(f"✗ Error refreshing device settings tables: {e}")
            return False
