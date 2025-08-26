# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel
from apps.RBM5.BCF.source.RDB.paths import BCF_DB_IO_CONNECT_ENHANCED

class IOConnectModel:
    def __init__(self, parent, rdb: "RDBManager"):
        self.parent = parent
        self.rdb = rdb

        # Enhanced table for IO connections with new Source/Dest Sub Block columns
        self.connections_model = RDBTableModel(
            db=rdb,
            table_path=str(BCF_DB_IO_CONNECT_ENHANCED) + ".io_connects",
            columns=[
                {"name": "Connection ID", "key": "Connection ID", "editable": False},
                {"name": "Source Device", "key": "Source Device", "editable": True},
                {"name": "Source Pin", "key": "Source Pin", "editable": True},
                {"name": "Source Sub Block", "key": "Source Sub Block", "editable": True},
                {"name": "Dest Device", "key": "Dest Device", "editable": True},
                {"name": "Dest Pin", "key": "Dest Pin", "editable": True},
                {"name": "Dest Sub Block", "key": "Dest Sub Block", "editable": True},
                {"name": "Connection Type", "key": "Connection Type", "editable": True},
                {"name": "Status", "key": "Status", "editable": True}
            ],
            parent=parent
        )

    def change_model_data(self):
        """Update model data based on current revision"""
        # This method would update the model when data changes
        # Implementation depends on your RDB structure
        pass
