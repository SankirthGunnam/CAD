# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel

class DeviceSettingsModel:
    def __init__(self, parent, rdb: "RDBManager"):
        self.parent = parent
        self.rdb = rdb

        # Two tables for device settings - available devices and selected
        # devices
        self.all_devices_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.all_devices",
            columns=[
                {"name": "Device Name", "key": "name", "editable": True},
                {"name": "Type", "key": "type", "editable": True},
                {"name": "Function", "key": "function", "editable": True},
                {"name": "Status", "key": "status", "editable": True}
            ],
            parent=parent
        )

        self.selected_devices_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.selected_devices",
            columns=[
                {"name": "Device Name", "key": "name", "editable": False},
                {"name": "Pin Count", "key": "pin_count", "editable": True},
                {"name": "Configuration", "key": "config", "editable": True},
                {"name": "Priority", "key": "priority", "editable": True}
            ],
            parent=parent
        )

    def change_model_data(self):
        """Update model data based on current revision"""
        # This method would update the models when data changes
        # Implementation depends on your RDB structure
        pass
