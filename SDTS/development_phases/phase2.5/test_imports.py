#!/usr/bin/env python3
"""
Test script to verify that the centralized path setup works correctly.
"""

import sys
import os

print("=== Testing Centralized Path Setup ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Initial sys.path entries: {len(sys.path)}")

# Test importing apps.RBM5.BCF which should automatically set up the path
try:
    print("\n1. Testing apps.RBM5.BCF import (should auto-configure path)...")
    import apps.RBM5.BCF
    print("✓ Successfully imported apps.RBM5.BCF")
    
    # Check if apps directory was added to sys.path
    apps_dirs = [path for path in sys.path if 'apps' in path]
    print(f"✓ Apps directories in sys.path: {apps_dirs}")
    
except ImportError as e:
    print(f"✗ Failed to import apps.RBM5.BCF: {e}")

# Test importing from the RDB module
try:
    print("\n2. Testing RDB module imports...")
    from apps.RBM5.BCF.source.RDB.database_interface import DatabaseInterface
    print("✓ Successfully imported DatabaseInterface")
    
    from apps.RBM5.BCF.source.RDB.json_db import JSONDatabase
    print("✓ Successfully imported JSONDatabase")
    
    from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
    print("✓ Successfully imported RDBManager")
    
except ImportError as e:
    print(f"✗ Failed to import RDB modules: {e}")

# Test importing model classes (these don't have PySide6 dependencies)
try:
    print("\n3. Testing model imports...")
    from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import RDBTableModel
    print("✓ Successfully imported RDBTableModel")
    
except ImportError as e:
    print(f"✗ Failed to import model classes: {e}")

# Test the setup_paths utility
try:
    print("\n4. Testing setup_paths utility...")
    import setup_paths
    print(f"✓ Project root: {setup_paths.PROJECT_ROOT}")
    print(f"✓ Apps dir: {setup_paths.APPS_DIR}")
    
except ImportError as e:
    print(f"✗ Failed to import setup_paths: {e}")

print("\n=== Path Setup Summary ===")
print("The new centralized approach eliminates redundant os.path.dirname code")
print("by having the path setup handled in one place (apps/RBM5/BCF/__init__.py)")
print("and imported via a single line: 'import apps.RBM5.BCF'")

print(f"\nFinal sys.path entries: {len(sys.path)}")
apps_paths = [p for p in sys.path if 'apps' in p or 'development_phases' in p]
if apps_paths:
    print("✓ Project paths in sys.path:")
    for path in apps_paths:
        print(f"  - {path}")
else:
    print("✗ No project paths found in sys.path")
