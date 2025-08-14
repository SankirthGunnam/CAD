#!/usr/bin/env python3
"""
Test Application for Visual BCF MVC Architecture

This script creates a working example of the Visual BCF MVC architecture
that can be run to test the functionality.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QSplitter, QGroupBox, QListWidget,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

# Import our MVC components
try:
    from apps.RBM.BCF.src.models.visual_bcf_data_model import VisualBCFDataModel
    from apps.RBM.BCF.src.controllers.visual_bcf_controller import VisualBCFController
    from apps.RBM.BCF.gui.src.visual_bcf.scene import RFScene
    from apps.RBM.BCF.gui.src.visual_bcf.view import RFView
    from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
except ImportError as e:
    logger.error(f"Failed to import MVC components: {e}")
    logger.info("Some imports might fail, creating simplified versions for testing...")


class MockRDBManager:
    """Mock RDB Manager for testing when real one is not available"""
    
    def __init__(self, db_file: str = "test_device_config.json"):
        self.db_file = db_file
        self.data = {
            "config": {
                "visual_bcf": {
                    "components": [],
                    "connections": []
                },
                "device": {
                    "settings": [
                        {
                            "name": "LTE Modem",
                            "function_type": "LTE",
                            "interface_type": "MIPI",
                            "interface": {"mipi": {"channel": 1}},
                            "config": {"usid": "LTE001"}
                        },
                        {
                            "name": "5G Modem", 
                            "function_type": "5G",
                            "interface_type": "MIPI",
                            "interface": {"mipi": {"channel": 2}},
                            "config": {"usid": "5G001"}
                        }
                    ]
                }
            }
        }
        from PySide6.QtCore import QObject, Signal
        
        # Create a simple QObject for signals
        class SignalEmitter(QObject):
            data_changed = Signal(str)
        
        self.signal_emitter = SignalEmitter()
        self.data_changed = self.signal_emitter.data_changed
    
    def get_value(self, path: str):
        """Get value at path"""
        parts = path.split('.')
        current = self.data
        for part in parts:
            current = current.get(part, {})
        return current
    
    def set_value(self, path: str, value):
        """Set value at path"""
        parts = path.split('.')
        current = self.data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        self.data_changed.emit(path)
    
    def get_table(self, path: str):
        """Get table data"""
        value = self.get_value(path)
        return value if isinstance(value, list) else []
    
    def set_table(self, path: str, data: list):
        """Set table data"""
        self.set_value(path, data)


class MockScene:
    """Mock scene for testing"""
    
    def __init__(self):
        from PySide6.QtCore import QObject, Signal
        from PySide6.QtCore import QPointF
        
        class SignalEmitter(QObject):
            add_chip_requested = Signal(QPointF)
            chip_selected = Signal(object)
            selection_changed = Signal(bool)
        
        self.signal_emitter = SignalEmitter()
        self.add_chip_requested = self.signal_emitter.add_chip_requested
        self.chip_selected = self.signal_emitter.chip_selected
        self.selection_changed = self.signal_emitter.selection_changed
        
        self.items_list = []
    
    def addItem(self, item):
        self.items_list.append(item)
        logger.info(f"Added item to scene: {type(item).__name__}")
    
    def removeItem(self, item):
        if item in self.items_list:
            self.items_list.remove(item)
            logger.info(f"Removed item from scene: {type(item).__name__}")
    
    def selectedItems(self):
        return []
    
    def clearSelection(self):
        pass


class MockView:
    """Mock view for testing"""
    
    def __init__(self, scene):
        self.scene = scene
    
    def setSceneRect(self, x, y, width, height):
        pass


class SimplifiedDataModel:
    """Simplified data model for testing"""
    
    def __init__(self, rdb_manager):
        from PySide6.QtCore import QObject, Signal
        
        class SignalEmitter(QObject):
            component_added = Signal(str)
            component_removed = Signal(str)
            component_updated = Signal(str, dict)
            connection_added = Signal(str)
            connection_removed = Signal(str)
            data_synchronized = Signal()
        
        self.signal_emitter = SignalEmitter()
        self.component_added = self.signal_emitter.component_added
        self.component_removed = self.signal_emitter.component_removed
        self.component_updated = self.signal_emitter.component_updated
        self.connection_added = self.signal_emitter.connection_added
        self.connection_removed = self.signal_emitter.connection_removed
        self.data_synchronized = self.signal_emitter.data_synchronized
        
        self.rdb_manager = rdb_manager
        self.components = {}
        self.connections = {}
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from RDB manager"""
        try:
            components_data = self.rdb_manager.get_table("config.visual_bcf.components")
            for comp in components_data:
                self.components[comp.get('id', f'comp_{len(self.components)}')] = comp
            
            connections_data = self.rdb_manager.get_table("config.visual_bcf.connections")
            for conn in connections_data:
                self.connections[conn.get('id', f'conn_{len(self.connections)}')] = conn
                
        except Exception as e:
            logger.info(f"No existing data to load: {e}")
    
    def add_component(self, name: str, component_type: str, position: tuple, properties: Dict = None):
        """Add a component"""
        import uuid
        component_id = str(uuid.uuid4())[:8]  # Short ID for display
        
        component_data = {
            'id': component_id,
            'name': name,
            'component_type': component_type,
            'properties': properties or {},
            'visual_properties': {
                'position': {'x': position[0], 'y': position[1]},
                'size': {'width': 100, 'height': 80}
            }
        }
        
        self.components[component_id] = component_data
        self._save_components()
        self.component_added.emit(component_id)
        
        logger.info(f"Added component: {name} ({component_id})")
        return component_id
    
    def remove_component(self, component_id: str):
        """Remove a component"""
        if component_id in self.components:
            name = self.components[component_id]['name']
            del self.components[component_id]
            self._save_components()
            self.component_removed.emit(component_id)
            logger.info(f"Removed component: {name} ({component_id})")
            return True
        return False
    
    def get_component(self, component_id: str):
        """Get component data"""
        return self.components.get(component_id)
    
    def get_all_components(self):
        """Get all components"""
        return self.components.copy()
    
    def get_statistics(self):
        """Get statistics"""
        return {
            'total_components': len(self.components),
            'total_connections': len(self.connections)
        }
    
    def sync_with_legacy_bcf(self):
        """Sync with Legacy BCF"""
        device_settings = self.rdb_manager.get_table("config.device.settings")
        logger.info(f"Syncing with {len(device_settings)} Legacy BCF devices")
        self.data_synchronized.emit()
    
    def _save_components(self):
        """Save components to RDB"""
        components_list = list(self.components.values())
        self.rdb_manager.set_table("config.visual_bcf.components", components_list)


class SimplifiedController:
    """Simplified controller for testing"""
    
    def __init__(self, scene, view, data_model):
        from PySide6.QtCore import QObject, Signal
        
        class SignalEmitter(QObject):
            component_selected = Signal(str)
            operation_completed = Signal(str, str)
            error_occurred = Signal(str)
        
        self.signal_emitter = SignalEmitter()
        self.component_selected = self.signal_emitter.component_selected
        self.operation_completed = self.signal_emitter.operation_completed
        self.error_occurred = self.signal_emitter.error_occurred
        
        self.scene = scene
        self.view = view
        self.data_model = data_model
        
        # Connect signals
        self.scene.add_chip_requested.connect(self._on_add_chip_requested)
        self.data_model.component_added.connect(self._on_component_added)
        self.data_model.component_removed.connect(self._on_component_removed)
    
    def _on_add_chip_requested(self, position):
        """Handle add chip request"""
        self.add_component(
            name=f"Chip_{len(self.data_model.get_all_components()) + 1}",
            component_type="chip",
            position=(position.x(), position.y())
        )
    
    def _on_component_added(self, component_id):
        """Handle component added to model"""
        logger.info(f"Controller: Component added to model: {component_id}")
        # In real implementation, create graphics item here
        self.operation_completed.emit("add_component", f"Added component: {component_id}")
    
    def _on_component_removed(self, component_id):
        """Handle component removed from model"""
        logger.info(f"Controller: Component removed from model: {component_id}")
        self.operation_completed.emit("remove_component", f"Removed component: {component_id}")
    
    def add_component(self, name: str, component_type: str, position: tuple, properties: Dict = None):
        """Add a component"""
        return self.data_model.add_component(name, component_type, position, properties)
    
    def remove_component(self, component_id: str):
        """Remove a component"""
        return self.data_model.remove_component(component_id)
    
    def get_statistics(self):
        """Get statistics"""
        return self.data_model.get_statistics()
    
    def sync_with_legacy_bcf(self):
        """Sync with Legacy BCF"""
        self.data_model.sync_with_legacy_bcf()


class VisualBCFTestApp(QMainWindow):
    """Test application for Visual BCF MVC"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual BCF MVC Test Application")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize MVC components
        self.setup_mvc()
        
        # Setup UI
        self.setup_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Add some test data
        self.add_test_data()
    
    def setup_mvc(self):
        """Setup MVC components"""
        logger.info("Setting up MVC components...")
        
        # Use mock components for testing
        self.rdb_manager = MockRDBManager()
        self.data_model = SimplifiedDataModel(self.rdb_manager)
        self.scene = MockScene()
        self.view = MockView(self.scene)
        self.controller = SimplifiedController(self.scene, self.view, self.data_model)
        
        logger.info("MVC components initialized")
    
    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        controls_widget = self.create_controls_panel()
        main_layout.addWidget(controls_widget, 1)
        
        # Right panel - Information
        info_widget = self.create_info_panel()
        main_layout.addWidget(info_widget, 1)
    
    def create_controls_panel(self):
        """Create controls panel"""
        group = QGroupBox("MVC Test Controls")
        layout = QVBoxLayout(group)
        
        # Component operations
        layout.addWidget(QLabel("Component Operations:"))
        
        add_lte_btn = QPushButton("Add LTE Modem")
        add_lte_btn.clicked.connect(self.add_lte_modem)
        layout.addWidget(add_lte_btn)
        
        add_5g_btn = QPushButton("Add 5G Modem")
        add_5g_btn.clicked.connect(self.add_5g_modem)
        layout.addWidget(add_5g_btn)
        
        add_generic_btn = QPushButton("Add Generic Chip")
        add_generic_btn.clicked.connect(self.add_generic_chip)
        layout.addWidget(add_generic_btn)
        
        # List of components
        layout.addWidget(QLabel("Components:"))
        self.components_list = QListWidget()
        layout.addWidget(self.components_list)
        
        # Remove selected component
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_component)
        layout.addWidget(remove_btn)
        
        # Sync operations
        layout.addWidget(QLabel("Sync Operations:"))
        
        sync_btn = QPushButton("Sync with Legacy BCF")
        sync_btn.clicked.connect(self.sync_with_legacy)
        layout.addWidget(sync_btn)
        
        clear_btn = QPushButton("Clear All Components")
        clear_btn.clicked.connect(self.clear_all_components)
        layout.addWidget(clear_btn)
        
        return group
    
    def create_info_panel(self):
        """Create information panel"""
        group = QGroupBox("System Information")
        layout = QVBoxLayout(group)
        
        # Statistics
        layout.addWidget(QLabel("Statistics:"))
        self.stats_label = QLabel("Components: 0")
        layout.addWidget(self.stats_label)
        
        # Log output
        layout.addWidget(QLabel("Activity Log:"))
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Database content
        layout.addWidget(QLabel("Database Content:"))
        self.db_text = QTextEdit()
        self.db_text.setReadOnly(True)
        layout.addWidget(self.db_text)
        
        # Auto-refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_display)
        self.refresh_timer.start(2000)  # Update every 2 seconds
        
        return group
    
    def connect_signals(self):
        """Connect MVC signals to UI updates"""
        self.controller.operation_completed.connect(self.on_operation_completed)
        self.controller.error_occurred.connect(self.on_error_occurred)
        self.data_model.data_synchronized.connect(self.on_data_synchronized)
    
    def add_test_data(self):
        """Add some initial test data"""
        QTimer.singleShot(1000, self.add_initial_components)
    
    def add_initial_components(self):
        """Add initial components for testing"""
        logger.info("Adding initial test components...")
        self.add_lte_modem()
        
    # Button handlers
    
    def add_lte_modem(self):
        """Add LTE modem component"""
        import random
        position = (random.randint(50, 300), random.randint(50, 200))
        self.controller.add_component(
            name="LTE Modem",
            component_type="modem",
            position=position,
            properties={"function_type": "LTE", "interface_type": "MIPI"}
        )
    
    def add_5g_modem(self):
        """Add 5G modem component"""
        import random
        position = (random.randint(50, 300), random.randint(50, 200))
        self.controller.add_component(
            name="5G Modem",
            component_type="modem", 
            position=position,
            properties={"function_type": "5G", "interface_type": "MIPI"}
        )
    
    def add_generic_chip(self):
        """Add generic chip component"""
        import random
        position = (random.randint(50, 300), random.randint(50, 200))
        chip_num = len(self.data_model.get_all_components()) + 1
        self.controller.add_component(
            name=f"Generic Chip {chip_num}",
            component_type="chip",
            position=position,
            properties={"function_type": "generic"}
        )
    
    def remove_selected_component(self):
        """Remove selected component"""
        current_item = self.components_list.currentItem()
        if current_item:
            component_id = current_item.data(Qt.UserRole)
            self.controller.remove_component(component_id)
    
    def sync_with_legacy(self):
        """Sync with Legacy BCF"""
        self.controller.sync_with_legacy_bcf()
    
    def clear_all_components(self):
        """Clear all components"""
        components = list(self.data_model.get_all_components().keys())
        for comp_id in components:
            self.controller.remove_component(comp_id)
    
    # Signal handlers
    
    def on_operation_completed(self, operation: str, message: str):
        """Handle operation completed"""
        log_message = f"✅ {operation}: {message}"
        self.log_text.append(log_message)
        logger.info(log_message)
        self.update_display()
    
    def on_error_occurred(self, error_message: str):
        """Handle error occurred"""
        log_message = f"❌ Error: {error_message}"
        self.log_text.append(log_message)
        logger.error(error_message)
    
    def on_data_synchronized(self):
        """Handle data synchronized"""
        log_message = "🔄 Data synchronized with Legacy BCF"
        self.log_text.append(log_message)
        logger.info("Data synchronized")
        self.update_display()
    
    def update_display(self):
        """Update the display with current data"""
        # Update statistics
        stats = self.controller.get_statistics()
        self.stats_label.setText(f"Components: {stats['total_components']}")
        
        # Update components list
        self.components_list.clear()
        components = self.data_model.get_all_components()
        for comp_id, comp_data in components.items():
            name = comp_data['name']
            comp_type = comp_data['component_type']
            item_text = f"{name} ({comp_type}) - {comp_id}"
            item = self.components_list.addItem(item_text)
            # Store component ID in item data
            if hasattr(self.components_list.item(self.components_list.count() - 1), 'setData'):
                self.components_list.item(self.components_list.count() - 1).setData(Qt.UserRole, comp_id)
        
        # Update database content
        import json
        db_content = json.dumps(self.rdb_manager.data, indent=2)
        self.db_text.setPlainText(db_content)


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Create and show test application
    test_app = VisualBCFTestApp()
    test_app.show()
    
    # Log startup message
    logger.info("Visual BCF MVC Test Application started")
    logger.info("Use the controls to test MVC functionality:")
    logger.info("- Add components to see Model-Controller interaction")
    logger.info("- Sync with Legacy BCF to test data integration") 
    logger.info("- Watch the activity log and database content")
    
    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
