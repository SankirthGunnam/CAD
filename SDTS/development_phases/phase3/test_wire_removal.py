#!/usr/bin/env python3
"""
Test script to verify wire removal functionality.
"""

import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5/BCF'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5'))

from PySide6.QtWidgets import QApplication
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController

def test_wire_removal():
    """Test wire removal functionality"""
    print("🧪 Testing Wire Removal...")
    
    try:
        # Create application (needed for Qt)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create RDB manager
        rdb_manager = RDBManager("test_wire_removal.json")
        
        # Create data model
        data_model = VisualBCFDataModel(rdb_manager)
        print("✅ Data model created")
        
        # Create controller
        controller = VisualBCFController(None, data_model)
        print("✅ Controller created")
        
        # Test 1: Add components to the data model
        component1_id = data_model.add_component("TestChip", "chip", (100, 100))
        component2_id = data_model.add_component("TestResistor", "resistor", (200, 200))
        print(f"✅ Components added: {component1_id}, {component2_id}")
        
        # Test 2: Add a connection
        connection_id = data_model.add_connection(component1_id, "R1", component2_id, "A")
        print(f"✅ Connection added: {connection_id}")
        
        # Test 3: Check if controller can find the connection
        connection_data = data_model.get_connection(connection_id)
        if connection_data:
            print(f"✅ Connection data found: {connection_data}")
        else:
            print("❌ Connection data not found")
            return False
        
        # Test 4: Test wire removal
        print("\n🔄 Testing Wire Removal...")
        success = controller.remove_connection(connection_id)
        
        if success:
            print("✅ Wire removal successful!")
            
            # Check if connection was removed from data model
            connection_data_after = data_model.get_connection(connection_id)
            if not connection_data_after:
                print("✅ Connection removed from data model")
            else:
                print("❌ Connection still exists in data model")
                return False
                
            return True
        else:
            print("❌ Wire removal failed")
            return False
        
    except Exception as e:
        print(f"❌ Wire removal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wire_removal()
    sys.exit(0 if success else 1)
