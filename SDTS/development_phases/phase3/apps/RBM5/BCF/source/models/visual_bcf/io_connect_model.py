# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel
import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.gui.source.visual_bcf.io_connect import IOConnect


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
