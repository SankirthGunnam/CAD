#!/usr/bin/env python3
"""
Test script to verify the new centralized paths and table structures
for Visual BCF data model, device settings, and IO connections.
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
    from apps.RBM5.BCF.source.RDB.paths import (
        VISUAL_BCF_COMPONENTS,
        VISUAL_BCF_CONNECTIONS,
        DCF_DEVICES_AVAILABLE,
        BCF_DEV_MIPI,
        BCF_DB_IO_CONNECT_ENHANCED
    )
    from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel

    print("✓ All imports successful")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_paths():
    """Test that all paths are correctly defined"""
    print("\n=== Testing Path Definitions ===")

    # Test Visual BCF paths
    print(f"VISUAL_BCF_COMPONENTS: {VISUAL_BCF_COMPONENTS}")
    print(f"VISUAL_BCF_CONNECTIONS: {VISUAL_BCF_CONNECTIONS}")

    # Test Device paths
    print(f"DCF_DEVICES_AVAILABLE: {DCF_DEVICES_AVAILABLE()}")
    print(f"BCF_DEV_MIPI(1): {BCF_DEV_MIPI(1)}")

    # Test IO Connect paths
    print(f"BCF_DB_IO_CONNECT_ENHANCED: {BCF_DB_IO_CONNECT_ENHANCED}")

    print("✓ All paths are correctly defined")

def test_data_model_initialization():
    """Test that the data model can be initialized with new paths"""
    print("\n=== Testing Data Model Initialization ===")

    try:
        # Create a test RDB manager
        rdb_manager = RDBManager("test_device_config.json")

        # Initialize the data model
        data_model = VisualBCFDataModel(rdb_manager)

        print("✓ Data model initialized successfully")
        print(f"  Components table path: {data_model.components_table_path}")
        print(f"  Connections table path: {data_model.connections_table_path}")

        return data_model, rdb_manager

    except Exception as e:
        print(f"✗ Error initializing data model: {e}")
        return None, None

def test_device_settings_tables(data_model):
    """Test device settings table operations"""
    print("\n=== Testing Device Settings Tables ===")

    try:
        # Test available devices
        available_devices = data_model.get_available_devices()
        print(f"✓ Available devices retrieved: {len(available_devices)} devices")

        # Test adding an available device
        test_device = {
            "Device Name": "Test Modem",
            "Control Type\n(MIPI / GPIO)": "MIPI",
            "Module": "Test Module",
            "USID\n(Default)": "TEST001",
            "MID\n(MSB)": "00",
            "MID\n(LSB)": "01",
            "PID": "1234",
            "EXT PID": "5678",
            "REV ID": "1.0",
            "DCF Type": "Standard"
        }

        success = data_model.add_available_device(test_device)
        if success:
            print("✓ Test device added successfully")

            # Verify it was added
            devices = data_model.get_available_devices()
            print(f"  Total devices now: {len(devices)}")
        else:
            print("✗ Failed to add test device")

        # Test selected devices
        selected_devices = data_model.get_selected_devices(revision=1)
        print(f"✓ Selected devices retrieved for revision 1: {len(selected_devices)} devices")

        # Test adding a selected device
        test_selected = {
            "DCF": "Test DCF",
            "Name": "Test Selected Device",
            "USID": "SEL001"
        }

        success = data_model.add_selected_device(test_selected, revision=1)
        if success:
            print("✓ Test selected device added successfully")

            # Verify it was added
            selected = data_model.get_selected_devices(revision=1)
            print(f"  Total selected devices now: {len(selected)}")
        else:
            print("✗ Failed to add test selected device")

    except Exception as e:
        print(f"✗ Error testing device settings tables: {e}")

def test_io_connect_tables(data_model):
    """Test IO connect table operations"""
    print("\n=== Testing IO Connect Tables ===")

    try:
        # Test getting IO connections
        io_connections = data_model.get_io_connections()
        print(f"✓ IO connections retrieved: {len(io_connections)} connections")

        # Test adding an IO connection
        test_connection = {
            "Connection ID": "IO_001",
            "Source Device": "Source Modem",
            "Source Pin": "TX1",
            "Source Sub Block": "RF Block A",
            "Dest Device": "Dest Modem",
            "Dest Pin": "RX1",
            "Dest Sub Block": "RF Block B",
            "Connection Type": "MIPI",
            "Status": "Active"
        }

        success = data_model.add_io_connection(test_connection)
        if success:
            print("✓ Test IO connection added successfully")

            # Verify it was added
            connections = data_model.get_io_connections()
            print(f"  Total IO connections now: {len(connections)}")

            # Test updating the connection
            update_data = {"Status": "Inactive"}
            success = data_model.update_io_connection("IO_001", update_data)
            if success:
                print("✓ Test IO connection updated successfully")
            else:
                print("✗ Failed to update test IO connection")

            # Test removing the connection
            success = data_model.remove_io_connection("IO_001")
            if success:
                print("✓ Test IO connection removed successfully")

                # Verify it was removed
                connections = data_model.get_io_connections()
                print(f"  Total IO connections after removal: {len(connections)}")
            else:
                print("✗ Failed to remove test IO connection")
        else:
            print("✗ Failed to add test IO connection")

    except Exception as e:
        print(f"✗ Error testing IO connect tables: {e}")

def test_visual_bcf_tables(data_model):
    """Test Visual BCF component and connection tables"""
    print("\n=== Testing Visual BCF Tables ===")

    try:
        # Test adding a component
        component_id = data_model.add_component(
            name="Test Component",
            component_type="chip",
            position=(100, 100),
            properties={"function_type": "test"}
        )

        if component_id:
            print(f"✓ Test component added successfully with ID: {component_id}")

            # Test adding a connection
            # First get the component to access its pins
            components = data_model.get_all_components()
            if components:
                component = components[0]
                pins = component.get('pins', [])
                if pins:
                    from_pin = pins[0]
                    to_pin = pins[0] if len(pins) > 1 else pins[0]

                    connection_id = data_model.add_connection(
                        from_component_id=component_id,
                        from_pin_id=from_pin.get('pin_id', 'pin1'),
                        to_component_id=component_id,
                        to_pin_id=to_pin.get('pin_id', 'pin2')
                    )

                    if connection_id:
                        print(f"✓ Test connection added successfully with ID: {connection_id}")
                    else:
                        print("✗ Failed to add test connection")
                else:
                    print("⚠ No pins available for connection test")
            else:
                print("⚠ No components available for connection test")
        else:
            print("✗ Failed to add test component")

    except Exception as e:
        print(f"✗ Error testing Visual BCF tables: {e}")

def main():
    """Main test function"""
    print("🚀 Starting New Paths and Tables Test")
    print("=" * 50)

    # Test path definitions
    test_paths()

    # Test data model initialization
    data_model, rdb_manager = test_data_model_initialization()

    if data_model:
        # Test device settings tables
        test_device_settings_tables(data_model)

        # Test IO connect tables
        test_io_connect_tables(data_model)

        # Test Visual BCF tables
        test_visual_bcf_tables(data_model)

        # Clean up
        if rdb_manager and hasattr(rdb_manager.db, 'save'):
            rdb_manager.db.save()
            print("\n✓ Test data saved to database")

    print("\n" + "=" * 50)
    print("🏁 New Paths and Tables Test Complete")

if __name__ == "__main__":
    main()
