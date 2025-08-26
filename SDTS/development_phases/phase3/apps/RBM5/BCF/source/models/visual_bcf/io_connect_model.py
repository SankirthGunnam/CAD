# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path

from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel

class IOConnectModel:
    def __init__(self, parent, rdb: "RDBManager", data_model=None):
        self.parent = parent
        self.rdb = rdb
        self.data_model = data_model  # Reference to Visual BCF data model

        # Use single source of truth - get data from Visual BCF data model
        # The table will display data from the same source as the graphics scene
        self.connections_model = RDBTableModel(
            db=rdb,
            table_path="visual_bcf.connections",  # This will be the actual data source
            columns=[
                {"name": "Connection ID", "key": "id", "editable": False},
                {"name": "Source Device", "key": "source_device", "editable": True},
                {"name": "Source Pin", "key": "source_pin", "editable": True},
                {"name": "Source Sub Block", "key": "source_sub_block", "editable": True},
                {"name": "Dest Device", "key": "dest_device", "editable": True},
                {"name": "Dest Pin", "key": "dest_pin", "editable": True},
                {"name": "Dest Sub Block", "key": "dest_sub_block", "editable": True},
                {"name": "Connection Type", "key": "connection_type", "editable": True},
                {"name": "Status", "key": "status", "editable": True}
            ],
            parent=parent
        )

    def refresh_from_data_model(self):
        """Refresh the table data from the Visual BCF data model (single source of truth)"""
        if self.data_model:
            try:
                # Get IO connections in table format from the data model
                io_connections = self.data_model.get_io_connections_for_table()
                
                # Update the table model with the data
                if hasattr(self.connections_model, 'set_data'):
                    self.connections_model.set_data(io_connections)
                
                return True
            except Exception as e:
                print(f"Error refreshing from data model: {e}")
                return False
        return False

    def get_connection_data(self):
        """Get connection data from the single source of truth"""
        if self.data_model:
            return self.data_model.get_io_connections_for_table()
        return []

    def update_connection(self, connection_id: str, updated_data: dict):
        """Update a connection in the single source of truth"""
        if self.data_model:
            # This would update the Visual BCF connection, which automatically
            # updates all table views since they use the same data source
            try:
                # Get the current connection
                connection = self.data_model.get_connection(connection_id)
                if connection:
                    # Update the connection properties
                    success = self.data_model.update_component_properties(connection_id, updated_data)
                    if success:
                        # Refresh the table view
                        self.refresh_from_data_model()
                        return True
            except Exception as e:
                print(f"Error updating connection: {e}")
        return False

    def delete_connection(self, connection_id: str):
        """Delete a connection from the single source of truth"""
        if self.data_model:
            try:
                success = self.data_model.remove_connection(connection_id)
                if success:
                    # Refresh the table view
                    self.refresh_from_data_model()
                    return True
            except Exception as e:
                print(f"Error deleting connection: {e}")
        return False

    def change_model_data(self):
        """Update model data based on current revision - now uses single source of truth"""
        if self.data_model:
            # Refresh from the data model (single source of truth)
            self.refresh_from_data_model()
        else:
            # Fallback to old method if no data model reference
            pass
