# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel

class DeviceSettingsModel:
    def __init__(self, parent, rdb: "RDBManager", data_model=None):
        self.parent = parent
        self.rdb = rdb
        self.data_model = data_model  # Reference to Visual BCF data model

        # Use single source of truth - get data from Visual BCF data model
        # The tables will display data from the same source as the graphics scene
        self.all_devices_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.components",  # This will be the actual data source
            columns=[
                {"name": "Device Name", "key": "name", "editable": True},
                {"name": "Control Type\n(MIPI / GPIO)", "key": "interface_type", "editable": True},
                {"name": "Module", "key": "component_type", "editable": True},
                {"name": "USID\n(Default)", "key": "usid", "editable": True},
                {"name": "MID\n(MSB)", "key": "mid_msb", "editable": True},
                {"name": "MID\n(LSB)", "key": "mid_lsb", "editable": True},
                {"name": "PID", "key": "pid", "editable": True},
                {"name": "EXT PID", "key": "ext_pid", "editable": True},
                {"name": "REV ID", "key": "rev_id", "editable": True},
                {"name": "DCF Type", "key": "dcf_type", "editable": True}
            ],
            parent=parent
        )

        self.selected_devices_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.components",  # This will be the actual data source
            columns=[
                {"name": "Device Name", "key": "name", "editable": False},
                {"name": "Function Type", "key": "function_type", "editable": True},
                {"name": "Interface Type", "key": "interface_type", "editable": True},
                {"name": "Pin Count", "key": "pin_count", "editable": True}
            ],
            parent=parent
        )

    def refresh_from_data_model(self):
        """Refresh the table data from the Visual BCF data model (single source of truth)"""
        if self.data_model:
            try:
                # Get available devices in table format from the data model
                available_devices = self.data_model.get_available_devices_for_table()
                print(available_devices)
                # Update the all devices table model with the data
                if hasattr(self.all_devices_model, 'set_data'):
                    self.all_devices_model.set_data(available_devices)
                
                # For selected devices, we could filter or show a subset
                # For now, show the same data
                if hasattr(self.selected_devices_model, 'set_data'):
                    self.selected_devices_model.set_data(available_devices)
                
                return True
            except Exception as e:
                print(f"Error refreshing from data model: {e}")
                return False
        return False

    def get_available_devices_data(self):
        """Get available devices data from the single source of truth"""
        if self.data_model:
            return self.data_model.get_available_devices_for_table()
        return []

    def get_selected_devices_data(self):
        """Get selected devices data from the single source of truth"""
        if self.data_model:
            # For now, return the same data as available devices
            # This could be extended to show only selected/filtered devices
            return self.data_model.get_available_devices_for_table()
        return []

    def change_model_data(self):
        """Update model data based on current revision - now uses single source of truth"""
        if self.data_model:
            # Refresh from the data model (single source of truth)
            self.refresh_from_data_model()
        else:
            # Fallback to old method if no data model reference
            pass
