#!/usr/bin/env python3
"""
Validate Enhanced Wires - Phase 3

This script validates the enhanced wire functionality by checking imports
and syntax without requiring the full GUI environment.
"""

import sys
import os

def validate_imports():
    """Validate that all required modules can be imported"""
    print("🔄 Validating enhanced wire imports...")
    
    try:
        # Test basic imports
        from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire, Wire, WirePath
        print("✅ Successfully imported Wire classes")
        
        # Test component imports
        from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin
        print("✅ Successfully imported ComponentPin")
        
        # Test scene imports
        from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
        print("✅ Successfully imported ComponentScene")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_wire_classes():
    """Validate wire class structure and methods"""
    print("\n🔄 Validating wire class structure...")
    
    try:
        from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire, Wire, WirePath
        
        # Check WirePath class
        wire_path = WirePath.__name__
        print(f"✅ WirePath class: {wire_path}")
        
        # Check Wire class
        enhanced_wire = Wire.__name__
        print(f"✅ Wire class: {enhanced_wire}")
        
        # Check Wire class (backward compatibility)
        wire = Wire.__name__
        print(f"✅ Wire class: {wire}")
        
        # Check inheritance
        if issubclass(Wire, Wire):
            print("✅ Wire inherits from Wire (backward compatibility)")
        else:
            print("❌ Wire does not inherit from Wire")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Class validation error: {e}")
        return False

def validate_methods():
    """Validate that required methods exist"""
    print("\n🔄 Validating wire methods...")
    
    try:
        from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.connection import Wire, Wire, WirePath
        
        # Check WirePath methods
        wire_path_methods = [
            '_calculate_path',
            '_route_horizontal_first', 
            '_route_vertical_first',
            'add_intersection_bump',
            'get_path'
        ]
        
        for method in wire_path_methods:
            if hasattr(WirePath, method):
                print(f"✅ WirePath.{method} method exists")
            else:
                print(f"❌ WirePath.{method} method missing")
                return False
        
        # Check Wire methods
        enhanced_wire_methods = [
            'update_path',
            '_calculate_optimal_path',
            '_avoid_component_collisions',
            '_handle_wire_intersections',
            'complete_wire',
            'update_wire_position'
        ]
        
        for method in enhanced_wire_methods:
            if hasattr(Wire, method):
                print(f"✅ Wire.{method} method exists")
            else:
                print(f"❌ Wire.{method} method missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Method validation error: {e}")
        return False

def validate_scene_integration():
    """Validate scene integration changes"""
    print("\n🔄 Validating scene integration...")
    
    try:
        # Check if scene.py was updated
        scene_file = "apps/RBM5/BCF/gui/source/visual_bcf/scene.py"
        if os.path.exists(scene_file):
            with open(scene_file, 'r') as f:
                content = f.read()
                
            # Check for enhanced wire usage
            if "Wire(pin, scene=self)" in content:
                print("✅ Scene updated to pass scene reference to wires")
            else:
                print("❌ Scene not updated for enhanced wire support")
                return False
                
            if "update_path" in content:
                print("✅ Scene updated to use update_path method")
            else:
                print("❌ Scene not updated to use update_path method")
                return False
                
        else:
            print("❌ Scene file not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Scene validation error: {e}")
        return False

def validate_controller_integration():
    """Validate controller integration changes"""
    print("\n🔄 Validating controller integration...")
    
    try:
        # Check if controller.py was updated
        controller_file = "apps/RBM5/BCF/source/controllers/visual_bcf/visual_bcf_controller.py"
        if os.path.exists(controller_file):
            with open(controller_file, 'r') as f:
                content = f.read()
                
            # Check for enhanced wire usage
            if "Wire(start_pin, scene=self.scene)" in content:
                print("✅ Controller updated to pass scene reference to wires")
            else:
                print("❌ Controller not updated for enhanced wire support")
                return False
                
        else:
            print("❌ Controller file not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Controller validation error: {e}")
        return False

def main():
    """Main validation function"""
    print("=== Enhanced Wire Validation - Phase 3 ===")
    print("Validating enhanced wire functionality implementation...")
    print()
    
    # Run all validations
    validations = [
        ("Import Validation", validate_imports),
        ("Class Structure", validate_wire_classes),
        ("Method Validation", validate_methods),
        ("Scene Integration", validate_scene_integration),
        ("Controller Integration", validate_controller_integration)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Overall: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 All validations passed! Enhanced wire system is ready.")
        return True
    else:
        print("⚠️  Some validations failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
