#!/usr/bin/env python3
"""
Visual Scene Serialization Test - Phase 3

This script shows the scene serialization functionality with a live UI
so you can see the components being created, saved, and loaded visually.
"""

import sys
import json
import tempfile
import os
from pathlib import Path

# Add the current project to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel, QMessageBox
from PySide6.QtCore import Qt, QTimer

# Import from phase3 directory structure
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip import ComponentWithPins
from apps.RBM5.BCF.source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController
from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager


class VisualSerializationTestWindow(QMainWindow):
    """Test window showing scene serialization with visual components"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Scene Serialization Test - Phase 3")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize temporary database
        # self.temp_db = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        # self.temp_db_path = self.temp_db.name
        # self.temp_db.close()
        self.temp_db_path = os.path.join(os.path.dirname(__file__), "sample.json")
        
        # Initialize RDB manager
        self.rdb_manager = RDBManager(self.temp_db_path)
        
        # Create manager with proper MVC architecture
        self.bcf_manager = VisualBCFManager(
            parent=self,
            rdb_manager=self.rdb_manager
        )
        
        # Access MVC components through manager
        self.data_model = self.bcf_manager.data_model
        
        # Controller is created by the manager and owns the view/scene
        self.controller = self.bcf_manager.visual_bcf_controller
        if self.controller:
            # Get view and scene from controller
            self.view = self.controller.get_view()
            self.scene = self.controller.get_scene()
            print("✅ VisualBCFController obtained from manager")
            print(f"✅ View obtained from controller: {self.view}")
            print(f"✅ Scene obtained from controller: {self.scene}")
        else:
            print("❌ No controller available from manager")
            self.view = None
            self.scene = None
        
        # Setup UI
        self.setup_ui()
        
        # Connect to controller signals for better status updates
        if self.controller:
            self.controller.operation_completed.connect(self.on_controller_operation)
            self.controller.error_occurred.connect(self.on_controller_error)
        
        # Don't auto-add test components - let user add them manually
        # self.add_test_components()
        
    def setup_ui(self):
        """Setup the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("🧪 Visual Scene Serialization Test - Phase 3")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # Info label
        self.info_label = QLabel("Components and connections shown below. Test save/load functionality with buttons.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("margin: 10px; color: #666;")
        main_layout.addWidget(self.info_label)
        
        # Graphics view (main area) - using the manager as central widget
        main_layout.addWidget(self.bcf_manager, 1)
        
        # Button panel
        button_layout = QHBoxLayout()
        
        # Add more components (using controller if available)
        add_chip_btn = QPushButton("➕ Add Chip")
        add_chip_btn.clicked.connect(self.add_chip)
        button_layout.addWidget(add_chip_btn)
        
        add_resistor_btn = QPushButton("➕ Add Resistor")
        add_resistor_btn.clicked.connect(self.add_resistor)
        button_layout.addWidget(add_resistor_btn)
        
        add_capacitor_btn = QPushButton("➕ Add Capacitor")
        add_capacitor_btn.clicked.connect(self.add_capacitor)
        button_layout.addWidget(add_capacitor_btn)
        
        button_layout.addStretch()
        
        # Serialization test buttons
        serialize_btn = QPushButton("💾 Serialize Scene")
        serialize_btn.clicked.connect(self.test_serialize)
        button_layout.addWidget(serialize_btn)
        
        save_btn = QPushButton("💾 Save Scene")
        save_btn.clicked.connect(self.test_save_scene)
        button_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🧹 Clear Scene")
        clear_btn.clicked.connect(self.test_clear_scene)
        button_layout.addWidget(clear_btn)
        
        load_btn = QPushButton("📂 Load Scene")
        load_btn.clicked.connect(self.test_load_scene)
        button_layout.addWidget(load_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready - Scene initialized with test components")
        self.status_label.setStyleSheet("background: #f0f0f0; padding: 8px; border: 1px solid #ccc;")
        main_layout.addWidget(self.status_label)
        
        # Initialize scene storage
        self.saved_scene_data = None
        
    def add_test_components(self):
        """Add some test components via the controller"""
        try:
            if not self.controller:
                self.update_status("❌ No controller available for adding components")
                return
                
            # Add components through controller
            self.controller.add_component("TestChip1", "chip", (100, 100), {"function_type": "generic"})
            self.controller.add_component("TestResistor1", "resistor", (300, 100), {"function_type": "passive"})
            self.controller.add_component("TestCapacitor1", "capacitor", (200, 250), {"function_type": "passive"})
            
            self.update_status("✅ Added 3 test components via controller")
            
        except Exception as e:
            self.update_status(f"❌ Error adding test components: {e}")
            
    def add_chip(self):
        """Add a new chip component via controller"""
        try:
            if self.controller:
                # Use controller to add component
                stats = self.controller.get_statistics()
                comp_count = stats.get('component_count', 0)
                name = f"Chip{comp_count + 1}"
                position = (50 + (comp_count * 40), 150 + (comp_count * 30))
                self.controller.add_component(name, "chip", position, {"function_type": "generic"})
                self.update_status(f"✅ Added {name} via controller")
            else:
                self.update_status("❌ No controller available")
        except Exception as e:
            self.update_status(f"❌ Error adding chip: {e}")
            
    def add_resistor(self):
        """Add a new resistor component via controller"""
        try:
            if self.controller:
                # Use controller to add component
                stats = self.controller.get_statistics()
                comp_count = stats.get('component_count', 0)
                name = f"Resistor{comp_count + 1}"
                position = (150 + (comp_count * 40), 200 + (comp_count * 30))
                self.controller.add_component(name, "resistor", position, {"function_type": "passive"})
                self.update_status(f"✅ Added {name} via controller")
            else:
                self.update_status("❌ No controller available")
        except Exception as e:
            self.update_status(f"❌ Error adding resistor: {e}")
            
    def add_capacitor(self):
        """Add a new capacitor component via controller"""
        try:
            if self.controller:
                # Use controller to add component
                stats = self.controller.get_statistics()
                comp_count = stats.get('component_count', 0)
                name = f"Capacitor{comp_count + 1}"
                position = (250 + (comp_count * 40), 100 + (comp_count * 30))
                self.controller.add_component(name, "capacitor", position, {"function_type": "passive"})
                self.update_status(f"✅ Added {name} via controller")
            else:
                self.update_status("❌ No controller available")
        except Exception as e:
            self.update_status(f"❌ Error adding capacitor: {e}")
            
    def test_serialize(self):
        """Test scene serialization via controller"""
        try:
            if not self.controller:
                self.update_status("❌ No controller available for serialization")
                return
                
            # Get statistics from controller (which includes component/connection counts)
            stats = self.controller.get_statistics()
            components_count = stats.get('component_count', 0)
            connections_count = stats.get('connection_count', 0)
            
            # Show serialization result
            msg = f"📊 Controller Statistics:\n"
            msg += f"• Components: {components_count}\n"
            msg += f"• Connections: {connections_count}\n\n"
            
            if 'components' in stats:
                msg += "Component Details:\n"
                components = list(stats.get('components', {}).values())[:3]  # Show first 3
                for i, comp in enumerate(components):
                    pos = comp.visual_properties.get('position', {}) if hasattr(comp, 'visual_properties') else {}
                    msg += f"  {i+1}. {getattr(comp, 'name', 'Unknown')} ({getattr(comp, 'component_type', 'unknown')})\n"
                if components_count > 3:
                    msg += f"  ... and {components_count - 3} more\n"
            
            QMessageBox.information(self, "Controller Statistics", msg)
            self.update_status(f"✅ Controller has {components_count} components, {connections_count} connections")
            
        except Exception as e:
            self.update_status(f"❌ Statistics error: {e}")
            QMessageBox.warning(self, "Error", f"Statistics failed: {e}")
    
    def test_save_scene(self):
        """Test saving scene data via controller"""
        try:
            if not self.controller:
                self.update_status("❌ No controller available for saving")
                return
                
            # Save scene through controller
            success = self.controller.save_scene(self.temp_db_path)
            if not success:
                self.update_status("❌ Controller save failed")
                return
                
            # Get scene statistics 
            stats = self.controller.get_statistics()
            components_count = stats.get('component_count', 0)
            connections_count = stats.get('connection_count', 0)
            
            self.update_status(f"💾 Scene saved to {Path(self.temp_db_path).name}! ({components_count} components)")
            
            # Show success message with file path
            msg = f"Scene saved successfully via controller!\n"
            msg += f"• File: {Path(self.temp_db_path).name}\n"
            msg += f"• Components: {components_count}\n"
            msg += f"• Connections: {connections_count}\n\n"
            msg += f"Full path: {self.temp_db_path}"
            
            QMessageBox.information(self, "Save Scene", msg)
            
        except Exception as e:
            self.update_status(f"❌ Save error: {e}")
            QMessageBox.warning(self, "Error", f"Save failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _convert_scene_to_model_format(self, scene_data):
        """Convert scene data to the format expected by the data model"""
        model_components = []
        
        for comp in scene_data.get('components', []):
            model_comp = {
                'id': f"comp_{len(model_components) + 1}",
                'name': comp.get('name', ''),
                'component_type': comp.get('type', 'chip'),
                'function_type': comp.get('properties', {}).get('function_type', comp.get('type', 'chip')),
                'properties': comp.get('properties', {}),
                'visual_properties': {
                    'position': comp.get('position', {'x': 0, 'y': 0}),
                    'size': {'width': 100, 'height': 80},
                    'rotation': 0
                },
                'pins': comp.get('pins', [])
            }
            model_components.append(model_comp)
        
        return model_components
            
            
    def test_clear_scene(self):
        """Test clearing the scene via controller"""
        try:
            if not self.controller:
                self.update_status("❌ No controller available for clearing")
                return
                
            # Clear scene through controller
            self.controller.clear_scene(show_confirmation=False)  # Skip confirmation dialog in test
            self.update_status("🧹 Scene cleared via controller")
            QMessageBox.information(self, "Clear Scene", "Scene cleared successfully via controller!")
        except Exception as e:
            self.update_status(f"❌ Clear error: {e}")
            QMessageBox.warning(self, "Error", f"Clear failed: {e}")
            
    def test_load_scene(self):
        """Test loading scene data via controller"""
        try:
            if not self.controller:
                self.update_status("❌ No controller available for loading")
                return
                
            # Load scene through controller
            if os.path.exists(self.temp_db_path):
                success = self.controller.load_scene(self.temp_db_path)
            else:
                success = self.controller.load_scene()  # Load from default location
            
            if not success:
                QMessageBox.warning(self, "Load Scene", 
                    f"No saved scene data found!\n\nTried:\n• JSON file: {Path(self.temp_db_path).name}\n• Default database location\n\nPlease save the scene first.")
                return
                
            # Get updated statistics after load
            stats = self.controller.get_statistics()
            components_count = stats.get('component_count', 0)
            connections_count = stats.get('connection_count', 0)
            
            self.update_status(f"📂 Scene loaded via controller! ({components_count} components, {connections_count} connections)")
            
            # Show success message
            msg = f"Scene loaded successfully via controller!\n"
            msg += f"• Components: {components_count}\n"
            msg += f"• Connections: {connections_count}\n\n"
            msg += f"Source: {Path(self.temp_db_path).name if os.path.exists(self.temp_db_path) else 'Default database'}"
            
            QMessageBox.information(self, "Load Scene", msg)
            
        except Exception as e:
            self.update_status(f"❌ Load error: {e}")
            QMessageBox.warning(self, "Error", f"Load failed: {e}")
            import traceback
            traceback.print_exc()
            
    def update_status(self, message):
        """Update the status label"""
        self.status_label.setText(message)
        print(f"Status: {message}")  # Also print to console
    
    def on_controller_operation(self, operation_type: str, message: str):
        """Handle controller operation completion signals"""
        try:
            # Get current statistics for comprehensive status update
            stats = self.controller.get_statistics() if self.controller else {}
            components_count = stats.get('component_count', 0)
            connections_count = stats.get('connection_count', 0)
            
            # Format status message with statistics
            detailed_message = f"{message} | Components: {components_count}, Connections: {connections_count}"
            self.update_status(detailed_message)
            
            # Log the operation for debugging
            print(f"Controller Operation: {operation_type} -> {detailed_message}")
            
        except Exception as e:
            print(f"Error handling controller operation signal: {e}")
            self.update_status(f"Operation completed but status update failed: {e}")
    
    def on_controller_error(self, error_message: str):
        """Handle controller error signals"""
        error_status = f"❌ Controller Error: {error_message}"
        self.update_status(error_status)
        print(f"Controller Error: {error_message}")
        
    def auto_save_on_close(self):
        """Auto-save scene when closing the application via controller"""
        try:
            if not self.controller:
                print("❌ No controller available for auto-save")
                return False
                
            # Get current statistics
            stats = self.controller.get_statistics()
            components_count = stats.get('component_count', 0)
            
            if components_count > 0:
                # Auto-save through controller
                success = self.controller.save_scene(self.temp_db_path)
                if success:
                    print(f"🔄 Auto-saved {components_count} components to {Path(self.temp_db_path).name}")
                    return True
                else:
                    print("❌ Controller auto-save failed")
                    return False
            else:
                print("ℹ️ No components to auto-save")
                return False
                
        except Exception as e:
            print(f"❌ Auto-save failed: {e}")
            return False
    
    def closeEvent(self, event):
        """Handle application close with auto-save"""
        try:
            # Auto-save the current scene
            saved = self.auto_save_on_close()
            
            # Show confirmation if there were components to save
            stats = self.controller.get_statistics() if self.controller else {}
            components_count = stats.get('component_count', 0)
            
            if components_count > 0:
                msg = f"Application closing...\n\n"
                if saved:
                    msg += f"✅ Auto-saved {components_count} components to:\n{Path(self.temp_db_path).name}\n\n"
                    msg += "Your scene has been preserved!"
                else:
                    msg += f"⚠️ Failed to auto-save {components_count} components\n\n"
                    msg += "You may want to manually save before closing."
                
                # Show non-blocking notification
                print(msg.replace('\n', ' '))
            
            # Cleanup database connection
            if hasattr(self, 'rdb_manager'):
                self.rdb_manager.db.disconnect()
                
        except Exception as e:
            print(f"❌ Error during close: {e}")
        
        # Accept the close event
        event.accept()


def main():
    """Main function to run the visual test"""
    
    # Create Qt Application
    app = QApplication(sys.argv)
    
    try:
        # Create and show the test window
        window = VisualSerializationTestWindow()
        window.show()
        
        print("🎬 Visual Scene Serialization Test Started!")
        print("=" * 50)
        print("• You should see a window with test components")
        print("• Try the buttons to test serialization functionality")
        print("• Add more components and test save/load")
        print("• Check the status bar for feedback")
        print()
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Error starting visual test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
