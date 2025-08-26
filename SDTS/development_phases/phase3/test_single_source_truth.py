#!/usr/bin/env python3
"""
Test script to demonstrate the single source of truth approach:
- Components and connections stored as lists of dictionaries
- Each dictionary contains ALL related information
- Tables display specific fields from the same data
- No synchronization needed
"""

import sys
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

def test_single_source_truth():
    """Test the single source of truth approach"""
    print("🚀 Testing Single Source of Truth Approach")
    print("=" * 60)
    
    try:
        # Create RDB manager
        rdb_manager = RDBManager("test_device_config.json")
        
        # Initialize data model
        data_model = VisualBCFDataModel(rdb_manager)
        print("✓ Data model initialized")
        
        # Test 1: Add a component with all information
        print("\n📱 Test 1: Adding Component with Complete Information")
        component_id = data_model.add_component(
            name="Test Modem",
            component_type="modem",
            position=(100, 100),
            properties={"custom_prop": "custom_value"}
        )
        
        if component_id:
            print(f"✓ Component added with ID: {component_id}")
            
            # Show the complete component data
            component = data_model.get_component(component_id)
            print("\n📋 Complete Component Data:")
            for key, value in component.items():
                print(f"  {key}: {value}")
            
            # Test 2: Add another component
            print("\n📱 Test 2: Adding Another Component")
            component2_id = data_model.add_component(
                name="Test RFIC",
                component_type="rfic",
                position=(200, 200)
            )
            
            if component2_id:
                print(f"✓ RFIC component added with ID: {component2_id}")
                
                # Test 3: Add connection between components
                print("\n🔌 Test 3: Adding Connection")
                connection_id = data_model.add_connection(
                    from_component_id=component_id,
                    from_pin_id="TX1",
                    to_component_id=component2_id,
                    to_pin_id="RX1"
                )
                
                if connection_id:
                    print(f"✓ Connection added with ID: {connection_id}")
                    
                    # Show the complete connection data
                    connection = data_model.get_connection(connection_id)
                    print("\n📋 Complete Connection Data:")
                    for key, value in connection.items():
                        print(f"  {key}: {value}")
                    
                    # Test 4: Demonstrate table views from same data
                    print("\n📊 Test 4: Table Views from Same Data")
                    
                    # Available Devices table view
                    available_devices = data_model.get_available_devices_for_table()
                    print(f"\n📋 Available Devices Table View ({len(available_devices)} devices):")
                    for device in available_devices:
                        print(f"  Device: {device['Device Name']}")
                        print(f"    Type: {device['Control Type\\n(MIPI / GPIO)']}")
                        print(f"    Module: {device['Module']}")
                        print(f"    USID: {device['USID\\n(Default)']}")
                        print(f"    MID: {device['MID\\n(MSB)']}/{device['MID\\n(LSB)']}")
                        print(f"    PID: {device['PID']}")
                        print(f"    DCF Type: {device['DCF Type']}")
                    
                    # IO Connections table view
                    io_connections = data_model.get_io_connections_for_table()
                    print(f"\n🔌 IO Connections Table View ({len(io_connections)} connections):")
                    for conn in io_connections:
                        print(f"  Connection: {conn['Connection ID']}")
                        print(f"    Source: {conn['Source Device']} ({conn['Source Pin']})")
                        print(f"    Dest: {conn['Dest Device']} ({conn['Dest Pin']})")
                        print(f"    Type: {conn['Connection Type']}")
                        print(f"    Status: {conn['Status']}")
                    
                    # Test 5: Demonstrate Legacy BCF compatibility
                    print("\n🔄 Test 5: Legacy BCF Compatibility")
                    legacy_devices = data_model.get_legacy_bcf_devices()
                    print(f"Legacy BCF Devices ({len(legacy_devices)}):")
                    for device in legacy_devices:
                        print(f"  {device['name']}: {device['function_type']} ({device['interface_type']})")
                        print(f"    USID: {device['usid']}, PID: {device['pid']}")
                    
                    # Test 6: Show statistics
                    print("\n📊 Test 6: Comprehensive Statistics")
                    stats = data_model.get_table_statistics()
                    print("Table Statistics:")
                    for key, value in stats.items():
                        if key == 'table_status':
                            print(f"  {key}:")
                            for status_key, status_value in value.items():
                                print(f"    {status_key}: {status_value}")
                        elif key == 'compatibility':
                            print(f"  {key}:")
                            for compat_key, compat_value in value.items():
                                print(f"    {compat_key}: {compat_value}")
                        else:
                            print(f"  {key}: {value}")
                    
                    # Test 7: Demonstrate data consistency
                    print("\n✅ Test 7: Data Consistency Verification")
                    print("All data comes from the same source:")
                    print(f"  - Visual BCF Components: {stats['component_count']}")
                    print(f"  - Available Devices Table View: {stats['available_devices_count']}")
                    print(f"  - Legacy BCF Devices: {len(legacy_devices)}")
                    print(f"  - Visual BCF Connections: {stats['connection_count']}")
                    print(f"  - IO Connections Table View: {stats['io_connections_count']}")
                    
                    if (stats['component_count'] == stats['available_devices_count'] and 
                        stats['connection_count'] == stats['io_connections_count']):
                        print("🎉 SUCCESS: Data consistency verified! All views show the same data.")
                    else:
                        print("⚠️  WARNING: Data inconsistency detected!")
                    
                else:
                    print("✗ Failed to add connection")
            else:
                print("✗ Failed to add RFIC component")
        else:
            print("✗ Failed to add component")
        
        # Save data
        if rdb_manager and hasattr(rdb_manager.db, 'save'):
            rdb_manager.db.save()
            print("\n✓ Test data saved to database")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Single Source of Truth Test Complete")

def main():
    """Main function"""
    test_single_source_truth()

if __name__ == "__main__":
    main()
