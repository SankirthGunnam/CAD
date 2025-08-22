#!/usr/bin/env python3
"""
Test script to verify save/load cycle works correctly.
"""

import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5/BCF'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5'))

from PySide6.QtWidgets import QApplication

from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel

def test_save_load_cycle():
    """Test the save/load cycle"""
    print("🧪 Testing Save/Load Cycle...")
    
    try:
        # Create application (needed for Qt)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create RDB manager
        rdb_manager = RDBManager("test_device_config.json")
        
        # Create data model
        data_model = VisualBCFDataModel(rdb_manager)
        print("✅ Data model created")
        
        # Test 1: Add components to the data model
        component1_id = data_model.add_component("TestChip", "chip", (100, 100))
        component2_id = data_model.add_component("TestResistor", "resistor", (200, 200))
        print(f"✅ Components added: {component1_id}, {component2_id}")
        
        # Test 2: Add a connection
        connection_id = data_model.add_connection(component1_id, "R1", component2_id, "A")
        print(f"✅ Connection added: {connection_id}")
        
        # Test 3: Save scene data to RDB tables
        scene_data = {
            "components": [
                {
                    "id": component1_id,
                    "name": "TestChip",
                    "type": "chip",
                    "position": {"x": 100, "y": 100},
                    "properties": {},
                    "visual_properties": {"position": {"x": 100, "y": 100}}
                },
                {
                    "id": component2_id,
                    "name": "TestResistor", 
                    "type": "resistor",
                    "position": {"x": 200, "y": 200},
                    "properties": {},
                    "visual_properties": {"position": {"x": 200, "y": 200}}
                }
            ],
            "connections": [
                {
                    "id": connection_id,
                    "start_component": "TestChip",
                    "end_component": "TestResistor",
                    "start_pin": "R1",
                    "end_pin": "A",
                    "properties": {}
                }
            ]
        }
        
        save_success = data_model.save_scene_data(scene_data)
        print(f"✅ Scene data saved to RDB: {save_success}")
        
        # Test 4: Load scene data from RDB tables
        loaded_scene = data_model.load_scene_data()
        if loaded_scene:
            components = loaded_scene.get("components", [])
            connections = loaded_scene.get("connections", [])
            print(f"✅ Scene loaded from RDB: {len(components)} components, {len(connections)} connections")
            
            # Verify the data
            if len(components) == 2 and len(connections) == 1:
                print("✅ Save/Load cycle working correctly!")
                return True
            else:
                print(f"❌ Data mismatch: Expected 2 components, 1 connection, got {len(components)} components, {len(connections)} connections")
                return False
        else:
            print("❌ Failed to load scene data from RDB")
            return False
        
    except Exception as e:
        print(f"❌ Save/Load cycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_save_load_cycle()
    sys.exit(0 if success else 1)
