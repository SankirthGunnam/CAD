#!/usr/bin/env python3
"""
Utility script to manually populate device settings and IO connect tables
from existing Visual BCF components and connections data.
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

def main():
    """Main function to populate device tables"""
    print("🚀 Device Tables Population Utility")
    print("=" * 50)

    try:
        # Create RDB manager (use existing config file if available)
        config_file = "device_config.json"
        if not Path(config_file).exists():
            config_file = "test_device_config.json"

        print(f"Using config file: {config_file}")
        rdb_manager = RDBManager(config_file)

        # Initialize the data model
        data_model = VisualBCFDataModel(rdb_manager)
        print("✓ Data model initialized successfully")

        # Get initial statistics
        print("\n📊 Initial Table State:")
        initial_stats = data_model.get_table_statistics()
        for key, value in initial_stats.items():
            if key.startswith('table_status'):
                continue
            if isinstance(value, int):
                print(f"  {key}: {value}")

        # Populate device tables from existing data
        print("\n🔄 Populating device tables from existing Visual BCF data...")
        success = data_model.populate_device_tables_from_existing_data()

        if success:
            print("✓ Device tables populated successfully!")

            # Get final statistics
            print("\n📊 Final Table State:")
            final_stats = data_model.get_table_statistics()
            for key, value in final_stats.items():
                if key.startswith('table_status'):
                    continue
                if isinstance(value, int):
                    print(f"  {key}: {value}")

            # Show table status
            print("\n📋 Table Status:")
            for table_name, status in final_stats['table_status'].items():
                print(f"  {table_name}: {status}")

            # Save changes
            if hasattr(rdb_manager.db, 'save'):
                rdb_manager.db.save()
                print("\n✓ Changes saved to database")

        else:
            print("✗ Failed to populate device tables")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("🏁 Device Tables Population Complete")

if __name__ == "__main__":
    main()
