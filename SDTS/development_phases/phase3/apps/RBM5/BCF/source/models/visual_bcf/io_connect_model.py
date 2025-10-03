# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel
import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.gui.source.visual_bcf.io_connect import IOConnect
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from typing import Dict, List, Optional, Tuple


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

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return len(self._columns)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        parent_id: Optional[int]
        if not parent.isValid():
            parent_id = None
        else:
            parent_id = int(parent.internalId())
        return len(self._children_ids(parent_id))

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:  # type: ignore[override]
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

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if key == self._id_key:
                return str(int(row[self._id_key]))
            value = row.get(key)
            return "" if value is None else str(value)
        if role == Qt.ToolTipRole:
            if index.column() == 0:
                is_top = row.get(self._parent_key) is None or str(row.get("info", "")) == "Connection"
                return ("Connection: " if is_top else "Field: ") + str(row.get("label", ""))
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
            self.rdb,
            paths.BCF_DB_IO_CONNECT,
            columns=[
                IOConnect.IOConnectTable.SOURCE_DEVICE(),
                IOConnect.IOConnectTable.SOURCE_PIN(),
                IOConnect.IOConnectTable.DEST_DEVICE(),
                IOConnect.IOConnectTable.DEST_PIN(),
            ],
        )
        self.tree_model = FlatTreeItemModel(
            self._build_tree_rows(), columns=[("Property", "label"), ("Value", "info")]
        )

    def refresh_from_data_model(self) -> bool:
        """Refresh table model from the data model"""
        try:
            # Force refresh of table model
            self.table.layoutChanged.emit()
            print("✓ IO Connect table refreshed from data model")
            # Rebuild tree model
            self.tree_model = FlatTreeItemModel(
                self._build_tree_rows(), columns=[("Property", "label"), ("Value", "info")]
            )
            return True
        except Exception as e:
            print(f"✗ Error refreshing IO connect table: {e}")
            return False

    def _build_tree_rows(self) -> List[Dict]:
        rows: List[Dict] = []
        try:
            data = self.rdb[paths.BCF_DB_IO_CONNECT]
            if isinstance(data, list):
                iterable = data
            elif isinstance(data, dict):
                iterable = list(data.values())
            else:
                iterable = []
        except Exception:
            iterable = []
        next_id = 1
        for record in iterable:
            title = f"{record.get(IOConnect.IOConnectTable.SOURCE_DEVICE(), '')} -> {record.get(IOConnect.IOConnectTable.DEST_DEVICE(), '')}"
            parent_id = next_id
            rows.append({"id": parent_id, "parent_id": None, "label": title, "info": "Connection"})
            next_id += 1
            child_base = parent_id * 100
            for key, value in record.items():
                rows.append({"id": child_base, "parent_id": parent_id, "label": str(key), "info": str(value)})
                child_base += 1
        return rows
