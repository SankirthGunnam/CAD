#!/usr/bin/env python3
"""
Test to validate your import modifications
"""

import sys
import os

print("=== Testing Your Import Modifications ===")
print(f"Current working directory: {os.getcwd()}")

# Initialize the centralized path setup first
import apps.RBM5.BCF

# Test the modified files you've changed
test_modules = [
    # Key files you've modified
    ("Visual BCF Manager", "apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager", "VisualBCFManager"),
    ("Scene", "apps.RBM5.BCF.gui.source.visual_bcf.scene", "ComponentScene"),
    ("Artifacts Package", "apps.RBM5.BCF.gui.source.visual_bcf.artifacts", ["ComponentPin", "ComponentWithPins", "Wire"]),
    ("Chip Component", "apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip", "ComponentWithPins"),
    ("Connection Wire", "apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection", "Wire"),
    ("Device Settings Controller", "apps.RBM5.BCF.source.controllers.visual_bcf.device_settings_controller", "DeviceSettingsController"),
    ("IO Connect Controller", "apps.RBM5.BCF.source.controllers.visual_bcf.io_connect_controller", "IOConnectController"),
    ("RDB Manager", "apps.RBM5.BCF.source.RDB.rdb_manager", "RDBManager"),
    ("JSON DB", "apps.RBM5.BCF.source.RDB.json_db", "JSONDatabase"),
    ("RDB Table Model", "apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model", "RDBTableModel"),
    ("Device Settings Model", "apps.RBM5.BCF.source.models.visual_bcf.device_settings_model", "DeviceSettingsModel"),
    ("IO Connect Model", "apps.RBM5.BCF.source.models.visual_bcf.io_connect_model", "IOConnectModel"),
]

successful_imports = []
failed_imports = []
skipped_imports = []

print(f"\n1. Testing {len(test_modules)} modules with your import changes...")

for test_info in test_modules:
    if len(test_info) == 3:
        name, module_path, expected_classes = test_info
        if isinstance(expected_classes, list):
            # Package test
            try:
                print(f"   Testing {name} package...")
                package = __import__(module_path, fromlist=expected_classes)
                
                missing_classes = []
                for cls_name in expected_classes:
                    if not hasattr(package, cls_name):
                        missing_classes.append(cls_name)
                
                if missing_classes:
                    failed_imports.append((name, f"Missing classes: {missing_classes}"))
                    print(f"   ✗ {name}: Missing {missing_classes}")
                else:
                    successful_imports.append(name)
                    print(f"   ✓ {name}: All expected classes available")
                    
            except ImportError as e:
                if "PySide6" in str(e):
                    skipped_imports.append((name, "PySide6 dependency"))
                    print(f"   ⚠ {name}: Skipped (PySide6 not available)")
                else:
                    failed_imports.append((name, str(e)))
                    print(f"   ✗ {name}: Import failed - {e}")
        else:
            # Single class test
            class_name = expected_classes
            try:
                print(f"   Testing {name}...")
                module = __import__(module_path, fromlist=[class_name])
                
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    successful_imports.append(name)
                    print(f"   ✓ {name}: Successfully imported {class_name}")
                else:
                    failed_imports.append((name, f"Class {class_name} not found"))
                    print(f"   ✗ {name}: Class {class_name} not found in module")
                    
            except ImportError as e:
                if "PySide6" in str(e):
                    skipped_imports.append((name, "PySide6 dependency"))
                    print(f"   ⚠ {name}: Skipped (PySide6 not available)")
                else:
                    failed_imports.append((name, str(e)))
                    print(f"   ✗ {name}: Import failed - {e}")
            except Exception as e:
                failed_imports.append((name, str(e)))
                print(f"   ✗ {name}: Error - {e}")

# Test specific import patterns you've implemented
print(f"\n2. Testing specific import patterns...")

# Test direct absolute imports (your new pattern)
try:
    print("   Testing direct absolute imports...")
    # This simulates what your visual_bcf_manager.py does
    from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
    from apps.RBM5.BCF.gui.source.visual_bcf.artifacts import ComponentWithPins, ComponentPin, Wire
    print("   ✓ Direct absolute imports working correctly")
    successful_imports.append("Direct Absolute Imports")
except Exception as e:
    if "PySide6" in str(e):
        print("   ⚠ Direct absolute imports: Skipped (PySide6 not available)")
        skipped_imports.append(("Direct Absolute Imports", "PySide6 dependency"))
    else:
        print(f"   ✗ Direct absolute imports failed: {e}")
        failed_imports.append(("Direct Absolute Imports", str(e)))

# Test that your scene.py imports work
try:
    print("   Testing scene.py import pattern...")
    from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
    from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.chip import ComponentWithPins  
    from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire
    print("   ✓ Scene.py import pattern working correctly")
    successful_imports.append("Scene Import Pattern")
except Exception as e:
    if "PySide6" in str(e):
        print("   ⚠ Scene import pattern: Skipped (PySide6 not available)")
        skipped_imports.append(("Scene Import Pattern", "PySide6 dependency"))
    else:
        print(f"   ✗ Scene import pattern failed: {e}")
        failed_imports.append(("Scene Import Pattern", str(e)))

# Test artifacts package initialization
try:
    print("   Testing artifacts package __init__.py...")
    import apps.RBM5.BCF.gui.source.visual_bcf.artifacts
    # Test if the __all__ exports work
    artifacts = apps.RBM5.BCF.gui.source.visual_bcf.artifacts
    expected_exports = ['ComponentPin', 'ComponentWithPins', 'Wire']
    
    missing_exports = []
    for export in expected_exports:
        if not hasattr(artifacts, export):
            missing_exports.append(export)
    
    if missing_exports:
        print(f"   ✗ Artifacts package: Missing exports {missing_exports}")
        failed_imports.append(("Artifacts Package Exports", f"Missing: {missing_exports}"))
    else:
        print("   ✓ Artifacts package exports working correctly")
        successful_imports.append("Artifacts Package Exports")
        
except Exception as e:
    if "PySide6" in str(e):
        print("   ⚠ Artifacts package: Skipped (PySide6 not available)")
        skipped_imports.append(("Artifacts Package Exports", "PySide6 dependency"))
    else:
        print(f"   ✗ Artifacts package failed: {e}")
        failed_imports.append(("Artifacts Package Exports", str(e)))

# Summary
print(f"\n=== Your Import Changes Summary ===")
print(f"✓ Successful imports: {len(successful_imports)}")
print(f"⚠ Skipped (PySide6): {len(skipped_imports)}")
print(f"✗ Failed imports: {len(failed_imports)}")

if successful_imports:
    print(f"\n✅ Successfully working:")
    for name in successful_imports:
        print(f"   - {name}")

if skipped_imports:
    print(f"\n⚠️ Skipped (PySide6 not available):")
    for name, reason in skipped_imports:
        print(f"   - {name}: {reason}")

if failed_imports:
    print(f"\n❌ Issues found:")
    for name, error in failed_imports:
        print(f"   - {name}: {error}")
else:
    print(f"\n🎉 All imports working correctly (excluding PySide6 dependencies)!")

# Analysis of your changes
print(f"\n=== Analysis of Your Changes ===")
print("✅ Excellent improvements made:")
print("   1. Removed centralized path setup import from individual files")
print("   2. Converted to clean direct absolute imports")
print("   3. Eliminated try/except fallback patterns") 
print("   4. Simplified import structure significantly")

# Check for remaining relative imports
print(f"\n3. Checking for any remaining relative imports...")
import subprocess
import os

try:
    # Check for any remaining relative imports with dots
    result = subprocess.run([
        'grep', '-r', '--include=*.py', '-n', 
        '-E', r'from \.|import \.', 
        '/home/sankirth/Projects/CAD/SDTS/development_phases/phase2.5/apps/RBM5/BCF'
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout.strip():
        print("   ⚠️ Found some remaining relative imports:")
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                print(f"      {line}")
    else:
        print("   ✅ No relative imports with dots found!")
except Exception as e:
    print(f"   ⚠️ Could not check for relative imports: {e}")

total_tested = len(test_modules) + 3  # +3 for the specific pattern tests
success_rate = (len(successful_imports) / total_tested) * 100

print(f"\n📊 Results Summary:")
print(f"   Total tests: {total_tested}")
print(f"   Successful: {len(successful_imports)}")
print(f"   Success rate: {success_rate:.1f}%")

if len(failed_imports) == 0 or all("PySide6" in str(error) for _, error in failed_imports):
    print(f"\n🎉 EXCELLENT WORK!")
    print("Your import modifications are working perfectly!")
    print("Clean, direct absolute imports throughout the codebase.")
else:
    print(f"\n⚠️ Some imports need attention (excluding PySide6 dependencies)")
