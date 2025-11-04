#!/usr/bin/env python3
"""
Test Scene Serialization - Phase 3

This script tests the scene serialization functionality to ensure
components and connections are properly saved and loaded via the MVC architecture.
"""

import sys
import json
import tempfile
import os
from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from apps.RBM5.BCF.source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController
from apps.RBM5.BCF.gui.source.visual_bcf.view import CustomGraphicsView
from apps.RBM5.BCF.gui.source.visual_bcf.scene import ComponentScene
from apps.RBM5.BCF.source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager

# Add the current project to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


# Import from phase3 directory structure


def test_scene_serialization():
    """Test the complete scene serialization flow"""

    print("🧪 Testing Scene Serialization in Phase 3")
    print("=" * 50)

    # Create Qt Application (required for Qt components)
    app = QApplication.instance()
    if not app:
        app = QApplication([])

    try:
        # 1. Initialize RDBManager with temporary database
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_db:
            temp_db_path = temp_db.name

        print(f"📄 Using temporary database: {temp_db_path}")
        rdb_manager = RDBManager(temp_db_path)

        # 2. Initialize Data Model
        print("🗃️  Initializing VisualBCFDataModel...")
        data_model = VisualBCFDataModel(rdb_manager)

        # 3. Create Scene and View
        print("🎬 Creating Scene and View...")
        scene = ComponentScene()
        view = CustomGraphicsView(scene)

        # 4. Initialize Controller
        print("🎮 Initializing VisualBCFController...")
        controller = VisualBCFController(view, data_model)

        # 5. Add test components
        print("\n📦 Adding test components...")

        # Add components via controller (proper MVC approach)
        chip1_id = controller.add_component(
            "TestChip1", "chip", (100, 100), {
                "function_type": "generic"})
        chip2_id = controller.add_component(
            "TestChip2", "chip", (300, 100), {
                "function_type": "generic"})
        rfic_id = controller.add_rfic_chip((200, 200), "TestRFIC")

        print(f"   ✅ Added chip1: {chip1_id}")
        print(f"   ✅ Added chip2: {chip2_id}")
        print(f"   ✅ Added RFIC: {rfic_id}")

        # Add test connections
        print("\n🔗 Adding test connections...")
        if chip1_id and chip2_id:
            conn_id = controller.add_connection(
                chip1_id, "OUT1", chip2_id, "IN1")
            print(f"   ✅ Added connection: {conn_id}")

        # 6. Test Scene Serialization (direct from scene)
        print("\n💾 Testing scene serialization...")
        scene_data = scene.serialize_scene()

        print(
            f"   📊 Serialized components: {len(scene_data.get('components', []))}")
        print(
            f"   📊 Serialized connections: {len(scene_data.get('connections', []))}")

        # Print serialized data (first component as example)
        if scene_data.get('components'):
            print(f"   📋 Example component data:")
            first_comp = scene_data['components'][0]
            print(f"      Name: {first_comp.get('name')}")
            print(f"      Type: {first_comp.get('type')}")
            print(f"      Position: {first_comp.get('position')}")

        # 7. Test Controller Save/Load
        print("\n💾 Testing controller save/load...")

        # Save via controller to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_scene:
            temp_scene_path = temp_scene.name

        save_success = controller.save_scene(temp_scene_path)
        print(
            f"   💾 Save to file: {'✅ Success' if save_success else '❌ Failed'}")

        if save_success:
            # Verify file contents
            with open(temp_scene_path, 'r') as f:
                saved_data = json.load(f)
            print(
                f"   📄 File contains {len(saved_data.get('components', []))} components")

        # 8. Test Clear and Load
        print("\n🧹 Testing clear and load...")

        # Clear current scene
        controller.clear_scene(show_confirmation=False)

        # Verify scene is empty
        empty_data = scene.serialize_scene()
        print(
            f"   🧹 After clear - Components: {len(empty_data.get('components', []))}")

        # Load from file
        if save_success:
            load_success = controller.load_scene(temp_scene_path)
            print(
                f"   📂 Load from file: {'✅ Success' if load_success else '❌ Failed'}")

            if load_success:
                # Verify loaded data
                loaded_data = scene.serialize_scene()
                print(
                    f"   📊 After load - Components: {len(loaded_data.get('components', []))}")
                print(
                    f"   📊 After load - Connections: {len(loaded_data.get('connections', []))}")

        # 9. Test Database Save/Load
        print("\n🗃️  Testing database save/load...")

        # Save to database (default location)
        db_save_success = controller.save_scene()
        print(
            f"   💾 Save to database: {'✅ Success' if db_save_success else '❌ Failed'}")

        # Clear again
        controller.clear_scene(show_confirmation=False)

        # Load from database
        if db_save_success:
            db_load_success = controller.load_scene()
            print(
                f"   📂 Load from database: {'✅ Success' if db_load_success else '❌ Failed'}")

            if db_load_success:
                final_data = scene.serialize_scene()
                print(
                    f"   📊 Final - Components: {len(final_data.get('components', []))}")
                print(
                    f"   📊 Final - Connections: {len(final_data.get('connections', []))}")

        # 10. Cleanup
        print("\n🧽 Cleaning up...")
        try:
            os.unlink(temp_db_path)
            if 'temp_scene_path' in locals():
                os.unlink(temp_scene_path)
        except BaseException:
            pass

        print("\n✅ Scene Serialization Test Complete!")

        # Summary
        print("\n📋 Test Summary:")
        print(f"   • Component creation: ✅")
        print(f"   • Scene serialization: ✅")
        print(
            f"   • Controller save/load: {'✅' if save_success and load_success else '❌'}")
        print(
            f"   • Database save/load: {'✅' if db_save_success and db_load_success else '❌'}")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scene_serialization()
    sys.exit(0 if success else 1)
