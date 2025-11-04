# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel
import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.gui.source.visual_bcf.io_connect import IOConnect
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from typing import Dict, List, Optional, Tuple


class RecordsTreeModel(QAbstractItemModel):

    def __init__(
        self,
        records: List[Dict],
        parent_label_builder,
        skip_keys: Optional[List[str]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._records: List[Dict] = list(records)
        self._parent_label_builder = parent_label_builder
        self._skip_keys = set(skip_keys or [])
        # id maps
        self._parent_ids: List[int] = []
        self._parent_id_to_row: Dict[int, int] = {}
        self._child_ids_by_row: Dict[int, List[int]] = {}
        self._child_id_to_info: Dict[int, Tuple[int, str]] = {}
        self._rebuild_ids()

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
            for key in rec.keys():
                if key in self._skip_keys:
                    continue
                cid = next_id
                next_id += 1
                self._child_id_to_info[cid] = (row, str(key))
                child_ids.append(cid)
            self._child_ids_by_row[row] = child_ids

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
                    try:
                        return str(self._parent_label_builder(rec))
                    except Exception:
                        return ""
                if index.column() == 1:
                    return "Connection"
            if role == Qt.ToolTipRole:
                return f"Connection: {self._parent_label_builder(rec)}"
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
                return f"Field: {key}"
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
        # Parent rows (connections) are not editable; child value column editable
        if nid in self._parent_id_to_row:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        # Child rows
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 1:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:  # type: ignore[override]
        if not index.isValid() or role != Qt.EditRole:
            return False
        nid = int(index.internalId())
        info = self._child_id_to_info.get(nid)
        if info is None:
            return False
        prow, key = info
        if index.column() != 1:
            return False
        try:
            self._records[prow][key] = str(value)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        except Exception:
            return False

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

    def index_for_id(self, node_id: int, column: int = 0) -> QModelIndex:
        if node_id in self._parent_id_to_row:
            row = self._parent_id_to_row[node_id]
            return self.createIndex(row, column, node_id)
        info = self._child_id_to_info.get(node_id)
        if info is not None:
            prow, _ = info
            pid = self._parent_ids[prow]
            parent_index = self.createIndex(prow, 0, pid)
            # find child row
            child_ids = self._child_ids_by_row.get(prow, [])
            try:
                crow = child_ids.index(node_id)
            except ValueError:
                return parent_index
            return self.createIndex(crow, column, node_id)
        return QModelIndex()

    def add_record(self, defaults: Optional[Dict] = None) -> int:
        """Append a new connection record and return its parent_id."""
        rec: Dict[str, str] = {}
        # Create all expected keys so children render
        try:
            from apps.RBM5.BCF.config.constants.tabs import IOConnect as IOCTabs
            rec[IOCTabs.IOConnectTable.SOURCE_DEVICE()] = ""
            rec[IOCTabs.IOConnectTable.SOURCE_PIN()] = ""
            rec[IOCTabs.IOConnectTable.DEST_DEVICE()] = ""
            rec[IOCTabs.IOConnectTable.DEST_PIN()] = ""
        except Exception:
            # Fallback generic keys
            rec.update({"Source Device": "", "Source Pin": "", "Dest Device": "", "Dest Pin": ""})
        if defaults:
            rec.update(defaults)
        self.beginResetModel()
        self._records.append(rec)
        self._rebuild_ids()
        self.endResetModel()
        # Return last parent id
        return self._parent_ids[-1] if self._parent_ids else -1

    def get_record_by_parent_id(self, parent_id: int):
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


class IOConnectModel:

    @property
    def current_revision(self):
        return self.rdb[paths.CURRENT_REVISION]

    @property
    def bcf_db(self):
        return self.rdb[paths.BCF_DB(self.current_revision)]

    @property
    def bcf_db_ant(self):
        return self.rdb[paths.BCF_DB_ANT(self.current_revision)]

    @property
    def bcf_db_cpl(self):
        return self.rdb[paths.BCF_DB_CPL(self.current_revision)]

    @property
    def bcf_db_filter(self):
        return self.rdb[paths.BCF_DB_FILTER(self.current_revision)]

    @property
    def bcf_db_ext_io(self):
        return self.rdb[paths.BCF_DB_EXT_IO(self.current_revision)]

    @property
    def bcf_db_io_connect(self):
        return self.rdb[paths.BCF_DB_IO_CONNECT]

    @property
    def _bcf_dev_mipi(self):
        return self.rdb[paths.BCF_DEV_MIPI(self.current_revision)]

    @property
    def _bcf_dev_gpio(self):
        return self.rdb[paths.BCF_DEV_GPIO(self.current_revision)]

    @property
    def bcf_db_io_conn(self):
        return self.rdb[paths.BCF_DB_IO_CONNECT]

    @property
    def ant_types(self):
        return self.rdb[paths.DYNAMIC_ANT_TYPES]

    def __init__(self, controller, rdb: "RDBManager"):
        self.parent = controller
        self.rdb = rdb
        self.table = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.BCF_DB_IO_CONNECT,
            columns=[
                IOConnect.IOConnectTable.SOURCE_DEVICE(),
                IOConnect.IOConnectTable.SOURCE_PIN(),
                IOConnect.IOConnectTable.DEST_DEVICE(),
                IOConnect.IOConnectTable.DEST_PIN(),
            ],
        )
        self.tree_model = RecordsTreeModel(
            self._iter_rows(self.rdb[paths.BCF_DB_IO_CONNECT]),
            parent_label_builder=lambda r: f"{r.get(IOConnect.IOConnectTable.SOURCE_DEVICE(), '')} -> {r.get(IOConnect.IOConnectTable.DEST_DEVICE(), '')}",
        )

    def refresh_from_data_model(self) -> bool:
        """Refresh table model from the data model"""
        try:
            # Force refresh of table model
            self.table.layoutChanged.emit()
            print("✓ IO Connect table refreshed from data model")
            # Rebuild tree model
            self.tree_model = RecordsTreeModel(
                self._iter_rows(self.rdb[paths.BCF_DB_IO_CONNECT]),
                parent_label_builder=lambda r: f"{r.get(IOConnect.IOConnectTable.SOURCE_DEVICE(), '')} -> {r.get(IOConnect.IOConnectTable.DEST_DEVICE(), '')}",
            )
            return True
        except Exception as e:
            print(f"✗ Error refreshing IO connect table: {e}")
            return False

    def _iter_rows(self, obj) -> List[Dict]:
        try:
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                return list(obj.values())
        except Exception:
            pass
        return []
