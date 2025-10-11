#!/usr/bin/env python3
"""
Simple test to check which imports are causing the hang
"""

import sys
from pathlib import Path

print("Starting import test...")

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("✓ Path setup complete")

try:
    print("Testing RDBManager import...")
    from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
    print("✓ RDBManager imported successfully")
except ImportError as e:
    print(f"✗ RDBManager import failed: {e}")
    sys.exit(1)

try:
    print("Testing VisualBCFDataModel import...")
    from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
    print("✓ VisualBCFDataModel imported successfully")
except ImportError as e:
    print(f"✗ VisualBCFDataModel import failed: {e}")
    sys.exit(1)

try:
    print("Testing DeviceSettingsModel import...")
    from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import DeviceSettingsModel
    print("✓ DeviceSettingsModel imported successfully")
except ImportError as e:
    print(f"✗ DeviceSettingsModel import failed: {e}")
    sys.exit(1)

try:
    print("Testing IOConnectModel import...")
    from apps.RBM5.BCF.source.models.visual_bcf.io_connect_model import IOConnectModel
    print("✓ IOConnectModel imported successfully")
except ImportError as e:
    print(f"✗ IOConnectModel import failed: {e}")
    sys.exit(1)

print("✓ All imports successful!")
print("Testing basic functionality...")

try:
    # Create RDB manager
    rdb_manager = RDBManager("test_device_config.json")
    print("✓ RDB manager created")

    # Initialize data model
    data_model = VisualBCFDataModel(rdb_manager)
    print("✓ Data model initialized")

    # Test adding a component
    component_id = data_model.add_component(
        name="Test Component",
        component_type="test",
        position=(100, 100)
    )
    print(f"✓ Component added: {component_id}")

    # Test getting table data
    available_devices = data_model.get_available_devices_for_table()
    print(f"✓ Available devices: {len(available_devices)}")

    io_connections = data_model.get_io_connections_for_table()
    print(f"✓ IO connections: {len(io_connections)}")

    print("🎉 All tests passed!")

except Exception as e:
    print(f"✗ Error during testing: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Test complete")
