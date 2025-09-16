#!/usr/bin/env python3
"""
Test script for the new clean architecture.
This script tests the new scene-controller-model integration.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'RBM5', 'BCF'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

from source.controllers.visual_bcf.visual_bcf_controller import VisualBCFController
from source.models.visual_bcf.visual_bcf_data_model import VisualBCFDataModel
from source.RDB.rdb_manager import RDBManager
from gui.source.visual_bcf.artifacts.chip import ComponentWithPins
from gui.source.visual_bcf.artifacts.connection import Wire
from gui.source.visual_bcf.artifacts.pin import ComponentPin

def test_new_architecture():
    """Test the new clean architecture"""
    print("🧪 Testing new clean architecture...")

    # Create QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("New Architecture Test")
    main_window.resize(800, 600)

    # Create data model with RDB manager
    rdb_manager = RDBManager("test_device_config.json")
    data_model = VisualBCFDataModel(rdb_manager)

    # Create controller
    controller = VisualBCFController(main_window, data_model)

    # Create central widget and layout
    central_widget = QWidget()
    main_window.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)

    # Add the view to the layout
    layout.addWidget(controller.get_view())

    # Test 1: Add component via scene
    print("\n✅ Test 1: Adding component via scene...")
    scene = controller.get_scene()

    # Simulate adding a component at position (100, 100)
    component = ComponentWithPins("TestChip", "chip")
    component.setPos(100, 100)

    # Add to scene
    scene.addItem(component)

    # Call the new controller method
    component_id = controller.add_component_from_scene(component, "TestChip", "chip")

    if component_id:
        print(f"✅ Component added successfully: {component_id}")
        print(f"✅ Component tracked in controller: {component_id in controller._component_graphics_items}")
        print(f"✅ Component in data model: {data_model.get_component(component_id) is not None}")
    else:
        print("❌ Failed to add component")
        return False

    # Test 2: Add wire via scene
    print("\n✅ Test 2: Adding wire via scene...")

    # Create a second component for the wire
    component2 = ComponentWithPins("TestResistor", "resistor")
    component2.setPos(300, 100)
    scene.addItem(component2)

    component2_id = controller.add_component_from_scene(component2, "TestResistor", "resistor")

    if not component2_id:
        print("❌ Failed to add second component")
        return False

    # Create a wire between the components
    # Find pins on the components
    start_pin = None
    end_pin = None

    print(f"🔍 Debug: Component 1 has {len(component.pins)} pins")
    for i, pin in enumerate(component.pins):
        print(f"  Pin {i}: {pin.pin_id} (edge: {getattr(pin, 'edge', 'unknown')})")

    print(f"🔍 Debug: Component 2 has {len(component2.pins)} pins")
    for i, pin in enumerate(component2.pins):
        print(f"  Pin {i}: {pin.pin_id} (edge: {getattr(pin, 'edge', 'unknown')})")

    for pin in component.pins:
        if pin.pin_id == "R1":  # Use right edge pin
            start_pin = pin
            break

    for pin in component2.pins:
        if pin.pin_id == "A":  # Use left edge pin
            end_pin = pin
            break

    if start_pin and end_pin:
        # Create wire
        wire = Wire(start_pin, scene=scene)
        if wire.complete_wire(end_pin):
            scene.addItem(wire)

            # Call the new controller method
            connection_id = controller.add_wire_from_scene(
                wire,
                component.name,
                start_pin.pin_id,
                component2.name,
                end_pin.pin_id
            )

            if connection_id:
                print(f"✅ Wire added successfully: {connection_id}")
                print(f"✅ Wire tracked in controller: {connection_id in controller._connection_graphics_items}")
                print(f"✅ Connection in data model: {data_model.get_connection(connection_id) is not None}")
            else:
                print("❌ Failed to add wire")
                return False
        else:
            print("❌ Failed to complete wire")
            return False
    else:
        print("❌ Could not find pins for wire creation")
        return False

    # Test 3: Serialize scene data
    print("\n✅ Test 3: Serializing scene data...")

    try:
        scene_data = controller.serialize_scene_data()
        print(f"✅ Scene data serialized: {len(scene_data['components'])} components, {len(scene_data['connections'])} connections")

        # Verify the data
        if len(scene_data['components']) == 2:
            print("✅ Correct number of components serialized")
        else:
            print(f"❌ Expected 2 components, got {len(scene_data['components'])}")
            return False

        if len(scene_data['connections']) == 1:
            print("✅ Correct number of connections serialized")
        else:
            print(f"❌ Expected 1 connection, got {len(scene_data['connections'])}")
            return False

    except Exception as e:
        print(f"❌ Failed to serialize scene data: {e}")
        return False

    # Test 4: Clear scene
    print("\n✅ Test 4: Clearing scene...")

    try:
        controller.clear_scene()

        # Verify scene is cleared
        scene_items = scene.items()
        if len(scene_items) == 0:
            print("✅ Scene cleared successfully")
        else:
            print(f"❌ Scene not cleared, {len(scene_items)} items remain")
            return False

        # Verify controller tracking is cleared
        if len(controller._component_graphics_items) == 0:
            print("✅ Component tracking cleared")
        else:
            print(f"❌ Component tracking not cleared, {len(controller._component_graphics_items)} items remain")
            return False

        if len(controller._connection_graphics_items) == 0:
            print("✅ Connection tracking cleared")
        else:
            print(f"❌ Connection tracking not cleared, {len(controller._connection_graphics_items)} items remain")
            return False

    except Exception as e:
        print(f"❌ Failed to clear scene: {e}")
        return False

    print("\n🎉 All tests passed! New architecture is working correctly.")

    # Show the window
    main_window.show()

    return True

if __name__ == "__main__":
    success = test_new_architecture()
    if success:
        print("\n🚀 Starting GUI for manual testing...")
        print("You can now interact with the scene to test the new architecture.")
        print("Press Ctrl+C to exit.")

        try:
            # Start the event loop
            app.exec()
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
    else:
        print("\n💥 Tests failed. Please check the implementation.")
        sys.exit(1)
