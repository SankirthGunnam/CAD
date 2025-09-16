# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel


class IOConnectModel:
    def __init__(self, parent, rdb: "RDBManager"):
        self.parent = parent
        self.rdb = rdb

        # Single table for IO connections
        self.connections_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.io_connections",
            columns=[
                {"name": "Connection ID", "key": "id", "editable": False},
                {"name": "Source Device", "key": "source_device", "editable": True},
                {"name": "Source Pin", "key": "source_pin", "editable": True},
                {"name": "Dest Device", "key": "dest_device", "editable": True},
                {"name": "Dest Pin", "key": "dest_pin", "editable": True},
                {"name": "Connection Type", "key": "type", "editable": True},
                {"name": "Status", "key": "status", "editable": True}
            ],
            parent=parent
        )

    def change_model_data(self):
        """Update model data based on current revision"""
        # This method would update the model when data changes
        # Implementation depends on your RDB structure
        pass
