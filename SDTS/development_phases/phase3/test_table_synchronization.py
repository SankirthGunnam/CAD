#!/usr/bin/env python3
"""
Test script to verify that table synchronization is working correctly
and populating the new device settings and IO connect tables with data.
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
    from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
    
    print("✓ All imports successful")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_initial_table_state(data_model):
    """Test the initial state of all tables"""
    print("\n=== Testing Initial Table State ===")
    
    try:
        # Get statistics for all tables
        stats = data_model.get_table_statistics()
        
        print("📊 Table Statistics:")
        print(f"  Visual BCF Components: {stats['component_count']}")
        print(f"  Visual BCF Connections: {stats['connection_count']}")
        print(f"  Available Devices: {stats['available_devices_count']}")
        print(f"  Selected Devices: {stats['selected_devices_count']}")
        print(f"  IO Connections: {stats['io_connections_count']}")
        
        print("\n📋 Table Status:")
        for table_name, status in stats['table_status'].items():
            print(f"  {table_name}: {status}")
        
        return stats
        
    except Exception as e:
        print(f"✗ Error getting table statistics: {e}")
        return None

def test_adding_visual_bcf_data(data_model):
    """Test adding Visual BCF components and connections"""
    print("\n=== Testing Visual BCF Data Addition ===")
    
    try:
        # Add a test component
        component_id = data_model.add_component(
            name="Test Modem",
            component_type="modem",
            position=(100, 100),
            properties={"function_type": "test_modem"}
        )
        
        if component_id:
            print(f"✓ Test component added: {component_id}")
            
            # Add another component
            component2_id = data_model.add_component(
                name="Test RFIC",
                component_type="rfic",
                position=(200, 200),
                properties={"function_type": "test_rfic"}
            )
            
            if component2_id:
                print(f"✓ Test RFIC component added: {component2_id}")
                
                # Add a connection between them
                connection_id = data_model.add_connection(
                    from_component_id=component_id,
                    from_pin_id="TX1",
                    to_component_id=component2_id,
                    to_pin_id="RX1"
                )
                
                if connection_id:
                    print(f"✓ Test connection added: {connection_id}")
                else:
                    print("✗ Failed to add test connection")
            else:
                print("✗ Failed to add test RFIC component")
        else:
            print("✗ Failed to add test component")
            
        return True
        
    except Exception as e:
        print(f"✗ Error adding Visual BCF data: {e}")
        return False

def test_synchronization(data_model):
    """Test the synchronization of data to device tables"""
    print("\n=== Testing Data Synchronization ===")
    
    try:
        # Manually trigger synchronization
        success = data_model.sync_visual_bcf_to_device_tables()
        
        if success:
            print("✓ Manual synchronization completed successfully")
        else:
            print("✗ Manual synchronization failed")
            
        return success
        
    except Exception as e:
        print(f"✗ Error during synchronization: {e}")
        return False

def test_populate_from_existing_data(data_model):
    """Test populating device tables from existing Visual BCF data"""
    print("\n=== Testing Population from Existing Data ===")
    
    try:
        # Populate device tables from existing data
        success = data_model.populate_device_tables_from_existing_data()
        
        if success:
            print("✓ Device tables populated successfully from existing data")
        else:
            print("✗ Failed to populate device tables from existing data")
            
        return success
        
    except Exception as e:
        print(f"✗ Error populating device tables: {e}")
        return False

def test_final_table_state(data_model):
    """Test the final state of all tables after synchronization"""
    print("\n=== Testing Final Table State ===")
    
    try:
        # Get final statistics for all tables
        stats = data_model.get_table_statistics()
        
        print("📊 Final Table Statistics:")
        print(f"  Visual BCF Components: {stats['component_count']}")
        print(f"  Visual BCF Connections: {stats['connection_count']}")
        print(f"  Available Devices: {stats['available_devices_count']}")
        print(f"  Selected Devices: {stats['selected_devices_count']}")
        print(f"  IO Connections: {stats['io_connections_count']}")
        
        print("\n📋 Final Table Status:")
        for table_name, status in stats['table_status'].items():
            print(f"  {table_name}: {status}")
        
        # Check if synchronization worked
        if (stats['component_count'] > 0 and 
            stats['available_devices_count'] > 0 and
            stats['connection_count'] > 0 and
            stats['io_connections_count'] > 0):
            print("\n🎉 SUCCESS: All tables are now populated with data!")
            return True
        else:
            print("\n⚠️  WARNING: Some tables are still empty")
            return False
        
    except Exception as e:
        print(f"✗ Error getting final table statistics: {e}")
        return False

def test_table_data_retrieval(data_model):
    """Test retrieving data from the new tables"""
    print("\n=== Testing Table Data Retrieval ===")
    
    try:
        # Test Available Devices
        available_devices = data_model.get_available_devices()
        print(f"📱 Available Devices ({len(available_devices)}):")
        for device in available_devices:
            print(f"  - {device.get('Device Name', 'Unknown')} ({device.get('Module', 'Unknown')})")
        
        # Test IO Connections
        io_connections = data_model.get_io_connections()
        print(f"\n🔌 IO Connections ({len(io_connections)}):")
        for connection in io_connections:
            print(f"  - {connection.get('Connection ID', 'Unknown')}: "
                  f"{connection.get('Source Device', 'Unknown')} → {connection.get('Dest Device', 'Unknown')}")
        
        # Test Selected Devices (should be empty initially)
        selected_devices = data_model.get_selected_devices(revision=1)
        print(f"\n📋 Selected Devices for Revision 1 ({len(selected_devices)}):")
        for device in selected_devices:
            print(f"  - {device.get('Name', 'Unknown')} ({device.get('DCF', 'Unknown')})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error retrieving table data: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Table Synchronization Test")
    print("=" * 60)
    
    try:
        # Create a test RDB manager
        rdb_manager = RDBManager("test_device_config.json")
        
        # Initialize the data model
        data_model = VisualBCFDataModel(rdb_manager)
        print("✓ Data model initialized successfully")
        
        # Test initial state
        initial_stats = test_initial_table_state(data_model)
        if not initial_stats:
            return
        
        # Test adding Visual BCF data
        if not test_adding_visual_bcf_data(data_model):
            print("⚠️  Skipping synchronization test due to data addition failure")
            return
        
        # Test manual synchronization
        if not test_synchronization(data_model):
            print("⚠️  Manual synchronization failed")
        
        # Test population from existing data
        if not test_populate_from_existing_data(data_model):
            print("⚠️  Population from existing data failed")
        
        # Test final state
        final_success = test_final_table_state(data_model)
        
        # Test data retrieval
        if final_success:
            test_table_data_retrieval(data_model)
        
        # Clean up and save
        if rdb_manager and hasattr(rdb_manager.db, 'save'):
            rdb_manager.db.save()
            print("\n✓ Test data saved to database")
        
    except Exception as e:
        print(f"✗ Critical error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Table Synchronization Test Complete")

if __name__ == "__main__":
    main()
