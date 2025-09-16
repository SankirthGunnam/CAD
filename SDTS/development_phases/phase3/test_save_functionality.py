#!/usr/bin/env python3
"""
Test script to verify that save functionality works correctly.
"""

import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5/BCF'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/RBM5'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController
from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins

def test_save_functionality():
    """Test the save functionality specifically"""
    print("🧪 Testing Save Functionality...")

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

        # Test 1: Add a component to the data model
        component_id = data_model.add_component("TestComponent", "chip", (100, 100))
        print(f"✅ Component added to data model: {component_id}")

        # Test 2: Test save_visual_bcf_data()
        save_success = data_model.save_visual_bcf_data()
        print(f"✅ save_visual_bcf_data(): {save_success}")

        # Test 3: Test save_visual_bcf_to_file()
        test_file = "test_save_output.json"
        file_save_success = data_model.save_visual_bcf_to_file(test_file)
        print(f"✅ save_visual_bcf_to_file(): {file_save_success}")

        # Test 4: Verify file was created
        if os.path.exists(test_file):
            print(f"✅ File created successfully: {test_file}")

            # Read file and check content
            import json
            with open(test_file, 'r') as f:
                data = json.load(f)

            components = data.get('config', {}).get('visual_bcf', {}).get('components', [])
            print(f"✅ Components in saved file: {len(components)}")

            # Clean up test file
            os.remove(test_file)
            print("✅ Test file cleaned up")
        else:
            print("❌ Test file was not created")

        print("\n🎉 Save functionality tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Save functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_save_functionality()
    sys.exit(0 if success else 1)
