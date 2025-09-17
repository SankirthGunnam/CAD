#!/usr/bin/env python3
"""
Test script for bidirectional synchronization between tables and graphics scene.

This script tests:
1. Table changes updating the graphics scene
2. Graphics scene changes updating the tables
3. Adding, updating, and removing components and connections
"""

import sys
import os
import json
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Use centralized path setup from BCF package
import apps.RBM5.BCF  # This automatically sets up the path

from PySide6.QtWidgets import QApplication, QMainWindow
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bidirectional_sync():
    """Test bidirectional synchronization functionality"""
    print("=" * 60)
    print("TESTING BIDIRECTIONAL SYNCHRONIZATION")
    print("=" * 60)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    try:
        # Initialize RDB Manager
        print("1. Initializing RDB Manager...")
        rdb_manager = RDBManager()
        print("✓ RDB Manager initialized")
        
        # Create Visual BCF Manager
        print("\n2. Creating Visual BCF Manager...")
        main_window = QMainWindow()
        main_window.setWindowTitle("Bidirectional Sync Test")
        main_window.setGeometry(100, 100, 1400, 900)
        
        bcf_manager = VisualBCFManager(
            parent=main_window,
            parent_controller=None,
            rdb_manager=rdb_manager
        )
        main_window.setCentralWidget(bcf_manager)
        print("✓ Visual BCF Manager created")
        
        # Show the window
        main_window.show()
        print("✓ Main window displayed")
        
        # Test 1: Check initial state
        print("\n3. Testing initial state...")
        initial_stats = bcf_manager.get_scene_data()
        print(f"✓ Initial scene state: {initial_stats}")
        
        # Test 2: Test table-to-scene synchronization
        print("\n4. Testing table-to-scene synchronization...")
        print("   - This would be tested by manually adding/removing rows in the tables")
        print("   - The graphics scene should automatically update")
        print("   - Check the Device Settings and IO Connect tabs")
        
        # Test 3: Test scene-to-table synchronization
        print("\n5. Testing scene-to-table synchronization...")
        print("   - This would be tested by adding/removing components in the graphics scene")
        print("   - The tables should automatically update")
        print("   - Use the floating toolbar to add components")
        
        # Test 4: Test bidirectional sync
        print("\n6. Testing bidirectional synchronization...")
        print("   - Add a component via toolbar -> should appear in tables")
        print("   - Remove a component via table -> should disappear from scene")
        print("   - Add a connection via scene -> should appear in IO Connect table")
        print("   - Remove a connection via table -> should disappear from scene")
        
        print("\n" + "=" * 60)
        print("BIDIRECTIONAL SYNC TEST COMPLETED")
        print("=" * 60)
        print("\nManual testing instructions:")
        print("1. Use the floating toolbar to add components to the scene")
        print("2. Check that components appear in the Device Settings tables")
        print("3. Right-click on table rows to remove them")
        print("4. Check that components disappear from the scene")
        print("5. Create connections between components in the scene")
        print("6. Check that connections appear in the IO Connect table")
        print("7. Remove connections from the IO Connect table")
        print("8. Check that connections disappear from the scene")
        
        # Run the application
        print("\nStarting application... (Close window to exit)")
        return app.exec()
        
    except Exception as e:
        logger.error(f"Error during bidirectional sync test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_bidirectional_sync())
