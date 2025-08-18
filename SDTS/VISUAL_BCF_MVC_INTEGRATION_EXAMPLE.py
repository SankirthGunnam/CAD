"""
Example: Visual BCF MVC Integration

This file shows how to integrate the new MVC architecture into the Visual BCF Manager.
This is an example of how the VisualBCFManager would be updated to use the new architecture.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Signal, QPointF
from typing import Dict, Any, Optional

# Import the new MVC components
from apps.RBM.BCF.source.models.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM.BCF.source.controllers.visual_bcf_controller import VisualBCFController
from apps.RBM.BCF.gui.source.visual_bcf.scene import RFScene
from apps.RBM.BCF.gui.source.visual_bcf.view import RFView
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager


class VisualBCFManagerMVC(QWidget):
    """
    Updated Visual BCF Manager using MVC architecture.
    
    This manager now follows proper MVC pattern:
    - Model: VisualBCFDataModel (handles all data operations)
    - View: RFScene + RFView (handles graphics display)  
    - Controller: VisualBCFController (handles user interactions)
    """
    
    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    component_selected = Signal(str)  # component_id
    operation_completed = Signal(str, str)  # operation, message
    
    def __init__(self, rdb_manager: RDBManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Visual BCF Manager (MVC)")
        
        # Store RDB manager reference
        self.rdb_manager = rdb_manager
        
        # Initialize MVC components
        self._setup_mvc_components()
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize with some default data (optional)
        self._initialize_default_data()
    
    def _setup_mvc_components(self):
        """Initialize the MVC components"""
        
        # Model: Handles all data operations and persistence
        self.data_model = VisualBCFDataModel(self.rdb_manager)
        
        # View: Graphics scene and view for visualization
        self.scene = RFScene()
        self.view = RFView(self.scene)
        
        # Controller: Coordinates between Model and View
        self.controller = VisualBCFController(self.scene, self.view, self.data_model)
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add the graphics view (this is the main visual component)
        main_layout.addWidget(self.view)
        
        # Set scene rectangle
        self.view.setSceneRect(-1000, -1000, 2000, 2000)
    
    def _connect_signals(self):
        """Connect signals between MVC components"""
        
        # Connect controller signals to manager signals
        self.controller.component_selected.connect(self.component_selected.emit)
        self.controller.operation_completed.connect(self.operation_completed.emit)
        self.controller.error_occurred.connect(self.error_occurred.emit)
        
        # Connect data model signals
        self.data_model.component_added.connect(self._on_component_added)
        self.data_model.component_removed.connect(self._on_component_removed)
        self.data_model.data_synchronized.connect(self._on_data_synchronized)
        
        # Connect controller operation signals to emit data_changed
        self.controller.operation_completed.connect(self._on_operation_completed)
    
    def _initialize_default_data(self):
        """Initialize with some default components (optional)"""
        # You can add some default components here if needed
        pass
    
    # Signal handlers
    
    def _on_component_added(self, component_id: str):
        """Handle component added"""
        component_data = self.data_model.get_component(component_id)
        if component_data:
            self.data_changed.emit({
                "action": "component_added",
                "component_id": component_id,
                "component_data": component_data.to_dict()
            })
    
    def _on_component_removed(self, component_id: str):
        """Handle component removed"""
        self.data_changed.emit({
            "action": "component_removed", 
            "component_id": component_id
        })
    
    def _on_data_synchronized(self):
        """Handle data synchronization"""
        self.data_changed.emit({
            "action": "data_synchronized",
            "statistics": self.data_model.get_statistics()
        })
    
    def _on_operation_completed(self, operation_type: str, message: str):
        """Handle operation completed"""
        self.data_changed.emit({
            "action": "operation_completed",
            "operation": operation_type,
            "message": message,
            "statistics": self.data_model.get_statistics()
        })
    
    # Public interface methods (these are what other parts of the application call)
    
    def add_component(self, name: str, component_type: str, position: tuple, 
                     properties: Dict[str, Any] = None) -> str:
        """Add a component through the controller"""
        return self.controller.add_component(name, component_type, position, properties)
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component through the controller"""
        return self.controller.remove_component(component_id)
    
    def get_selected_components(self):
        """Get selected components"""
        return self.controller.get_selected_components()
    
    def copy_selected_components(self):
        """Copy selected components"""
        self.controller.copy_selected_components()
    
    def paste_components(self, position: tuple = None):
        """Paste components"""
        self.controller.paste_components(position)
    
    def delete_selected_components(self):
        """Delete selected components"""
        self.controller.delete_selected_components()
    
    def clear_scene(self):
        """Clear all components"""
        self.controller.clear_scene()
    
    def sync_with_legacy_bcf(self):
        """Synchronize with Legacy BCF data"""
        self.controller.sync_with_legacy_bcf()
    
    def export_to_legacy_bcf(self):
        """Export to Legacy BCF format"""
        self.controller.export_to_legacy_bcf()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.controller.get_statistics()
    
    def set_interaction_mode(self, mode: str):
        """Set interaction mode (select, connect, etc.)"""
        self.controller.set_mode(mode)
    
    def get_interaction_mode(self) -> str:
        """Get current interaction mode"""
        return self.controller.get_mode()
    
    # Legacy interface methods (for compatibility)
    
    def update_scene(self, data: dict):
        """Update scene with new data (for compatibility with legacy interface)"""
        # This could trigger a sync with legacy BCF data
        self.sync_with_legacy_bcf()
    
    def refresh(self):
        """Refresh the scene (reload data from model)"""
        # The controller automatically handles this through model signals
        self.data_model.sync_with_legacy_bcf()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Clear all data
            self.controller.clear_scene()
            
            # Disconnect signals
            self.controller.disconnect()
            self.data_model.disconnect()
            
        except Exception as e:
            self.error_occurred.emit(f"Error during cleanup: {str(e)}")
    
    # Toolbar integration methods
    
    def show_rf_toolbar(self):
        """Show RF toolbar (if applicable)"""
        # This would show any floating toolbars
        pass
    
    def hide_rf_toolbar(self):
        """Hide RF toolbar (if applicable)"""
        # This would hide any floating toolbars  
        pass


# Example of how to use the new MVC architecture
def example_usage():
    """Example of how to use the new Visual BCF MVC architecture"""
    
    from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager
    from PySide6.QtWidgets import QApplication
    import sys
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create RDB Manager
    rdb_manager = RDBManager("device_config.json")
    
    # Create the MVC Visual BCF Manager
    visual_bcf = VisualBCFManagerMVC(rdb_manager)
    
    # Connect to signals (optional)
    visual_bcf.component_selected.connect(
        lambda comp_id: print(f"Component selected: {comp_id}")
    )
    
    visual_bcf.operation_completed.connect(
        lambda op, msg: print(f"Operation {op} completed: {msg}")
    )
    
    visual_bcf.data_changed.connect(
        lambda data: print(f"Data changed: {data}")
    )
    
    # Show the widget
    visual_bcf.show()
    
    # Add some components programmatically
    comp1_id = visual_bcf.add_component(
        name="LTE Modem", 
        component_type="modem",
        position=(100, 100),
        properties={"function_type": "LTE", "interface_type": "MIPI"}
    )
    
    comp2_id = visual_bcf.add_component(
        name="5G Modem",
        component_type="modem", 
        position=(300, 200),
        properties={"function_type": "5G", "interface_type": "MIPI"}
    )
    
    # Sync with Legacy BCF
    visual_bcf.sync_with_legacy_bcf()
    
    # Print statistics
    stats = visual_bcf.get_statistics()
    print(f"Current statistics: {stats}")
    
    # Start the event loop
    return app.exec()


if __name__ == "__main__":
    example_usage()
