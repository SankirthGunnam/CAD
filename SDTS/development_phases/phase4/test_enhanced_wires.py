#!/usr/bin/env python3
"""
Test Enhanced Wires - Phase 3

This script demonstrates the enhanced wire functionality:
1. Perpendicular (right-angle) routing
2. Collision avoidance with components
3. Intersection bumps for wire crossings
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

from apps.RBM5.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager


class EnhancedWireTestWindow(QMainWindow):
    """Test window for enhanced wire functionality"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTS - Phase 3: Enhanced Wire Test")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)

        # Create button layout
        button_layout = QHBoxLayout()

        # Add test buttons
        self.add_component_btn = QPushButton("Add Component")
        self.add_component_btn.clicked.connect(self.add_test_component)
        button_layout.addWidget(self.add_component_btn)

        self.test_wire_routing_btn = QPushButton("Test Wire Routing")
        self.test_wire_routing_btn.clicked.connect(self.test_wire_routing)
        button_layout.addWidget(self.test_wire_routing_btn)

        self.test_collision_avoidance_btn = QPushButton("Test Collision Avoidance")
        self.test_collision_avoidance_btn.clicked.connect(self.test_collision_avoidance)
        button_layout.addWidget(self.test_collision_avoidance_btn)

        self.test_intersections_btn = QPushButton("Test Wire Intersections")
        self.test_intersections_btn.clicked.connect(self.test_wire_intersections)
        button_layout.addWidget(self.test_intersections_btn)

        self.clear_scene_btn = QPushButton("Clear Scene")
        self.clear_scene_btn.clicked.connect(self.clear_scene)
        button_layout.addWidget(self.clear_scene_btn)

        layout.addLayout(button_layout)

        # Create BCF manager
        self.bcf_manager = VisualBCFManager()
        self.bcf_manager.setParent(self)

        # Add the view to the layout
        layout.addWidget(self.bcf_manager.get_view())

        # Status bar
        self.statusBar().showMessage("Enhanced Wire Test Ready")

        # Connect status updates
        if hasattr(self.bcf_manager, 'status_updated'):
            self.bcf_manager.status_updated.connect(self.statusBar().showMessage)

    def add_test_component(self):
        """Add a test component to the scene"""
        print("🔄 Adding test component...")

        # Enable component placement mode
        self.bcf_manager.controller.placement_mode = True
        self.bcf_manager.controller.selected_component_type = "chip"

        # Simulate component placement at center
        scene = self.bcf_manager.controller.get_scene()
        center_pos = scene.sceneRect().center()
        scene.add_component_at_position(center_pos)

        print("✅ Test component added")
        self.statusBar().showMessage("Test component added - click to place more")

    def test_wire_routing(self):
        """Test perpendicular wire routing"""
        print("🔄 Testing perpendicular wire routing...")

        scene = self.bcf_manager.controller.get_scene()

        # Get components
        if len(scene.components) < 2:
            print("❌ Need at least 2 components to test wire routing")
            self.statusBar().showMessage("Add at least 2 components first")
            return

        # Get first two components
        comp1 = scene.components[0]
        comp2 = scene.components[1]

        # Get pins
        pins1 = [pin for pin in comp1.childItems() if hasattr(pin, 'pin_id')]
        pins2 = [pin for pin in comp2.childItems() if hasattr(pin, 'pin_id')]

        if not pins1 or not pins2:
            print("❌ Components don't have pins")
            return

        # Start wire from first pin
        scene.start_wire_from_pin(pins1[0])

        # Complete wire to second pin
        if scene.current_wire and scene.current_wire.complete_wire(pins2[0]):
            scene.wires.append(scene.current_wire)

            # Register wire with components
            comp1.add_wire(scene.current_wire)
            comp2.add_wire(scene.current_wire)

            scene.current_wire = None
            print("✅ Perpendicular wire routing test completed")
            self.statusBar().showMessage("Perpendicular wire routing test completed")
        else:
            print("❌ Wire routing test failed")

    def test_collision_avoidance(self):
        """Test collision avoidance with components"""
        print("🔄 Testing collision avoidance...")

        scene = self.bcf_manager.controller.get_scene()

        # Need at least 3 components for collision test
        if len(scene.components) < 3:
            print("❌ Need at least 3 components to test collision avoidance")
            self.statusBar().showMessage("Add at least 3 components first")
            return

        # Place components in a way that would cause collision
        comp1 = scene.components[0]
        comp2 = scene.components[1]
        comp3 = scene.components[2]

        # Position components to create collision scenario
        comp1.setPos(100, 100)
        comp2.setPos(300, 100)
        comp3.setPos(200, 200)  # In the middle, blocking direct path

        # Get pins
        pins1 = [pin for pin in comp1.childItems() if hasattr(pin, 'pin_id')]
        pins2 = [pin for pin in comp2.childItems() if hasattr(pin, 'pin_id')]

        if not pins1 or not pins2:
            print("❌ Components don't have pins")
            return

        # Create wire that should avoid the middle component
        scene.start_wire_from_pin(pins1[0])

        if scene.current_wire and scene.current_wire.complete_wire(pins2[0]):
            scene.wires.append(scene.current_wire)

            # Register wire with components
            comp1.add_wire(scene.current_wire)
            comp2.add_wire(scene.current_wire)

            scene.current_wire = None
            print("✅ Collision avoidance test completed")
            self.statusBar().showMessage("Collision avoidance test completed - wire should route around middle component")
        else:
            print("❌ Collision avoidance test failed")

    def test_wire_intersections(self):
        """Test wire intersection handling with bumps"""
        print("🔄 Testing wire intersections...")

        scene = self.bcf_manager.controller.get_scene()

        # Need at least 4 components for intersection test
        if len(scene.components) < 4:
            print("❌ Need at least 4 components to test wire intersections")
            self.statusBar().showMessage("Add at least 4 components first")
            return

        # Position components to create crossing wires
        comp1 = scene.components[0]
        comp2 = scene.components[1]
        comp3 = scene.components[2]
        comp4 = scene.components[3]

        # Position in a cross pattern
        comp1.setPos(100, 100)
        comp2.setPos(300, 100)
        comp3.setPos(200, 50)
        comp4.setPos(200, 250)

        # Get pins
        pins1 = [pin for pin in comp1.childItems() if hasattr(pin, 'pin_id')]
        pins2 = [pin for pin in comp2.childItems() if hasattr(pin, 'pin_id')]
        pins3 = [pin for pin in comp3.childItems() if hasattr(pin, 'pin_id')]
        pins4 = [pin for pin in comp4.childItems() if hasattr(pin, 'pin_id')]

        if not all([pins1, pins2, pins3, pins4]):
            print("❌ Components don't have pins")
            return

        # Create first wire (horizontal)
        scene.start_wire_from_pin(pins1[0])
        if scene.current_wire and scene.current_wire.complete_wire(pins2[0]):
            scene.wires.append(scene.current_wire)
            comp1.add_wire(scene.current_wire)
            comp2.add_wire(scene.current_wire)
            scene.current_wire = None

        # Create second wire (vertical) that should intersect
        scene.start_wire_from_pin(pins3[0])
        if scene.current_wire and scene.current_wire.complete_wire(pins4[0]):
            scene.wires.append(scene.current_wire)
            comp3.add_wire(scene.current_wire)
            comp4.add_wire(scene.current_wire)
            scene.current_wire = None

            print("✅ Wire intersection test completed")
            self.statusBar().showMessage("Wire intersection test completed - check for intersection bumps")
        else:
            print("❌ Wire intersection test failed")

    def clear_scene(self):
        """Clear all components and wires from the scene"""
        print("🔄 Clearing scene...")

        scene = self.bcf_manager.controller.get_scene()

        # Clear wires
        for wire in scene.wires[:]:
            scene.removeItem(wire)
        scene.wires.clear()

        # Clear components
        for component in scene.components[:]:
            scene.remove_component(component)

        print("✅ Scene cleared")
        self.statusBar().showMessage("Scene cleared")


def main():
    """Main test function"""
    print("=== Enhanced Wire Test - Phase 3 ===")
    print("Testing enhanced wire functionality:")
    print("1. Perpendicular (right-angle) routing")
    print("2. Collision avoidance with components")
    print("3. Intersection bumps for wire crossings")
    print()

    app = QApplication(sys.argv)

    # Create test window
    test_window = EnhancedWireTestWindow()
    test_window.show()

    print("✅ Test window created and displayed")
    print("📋 Instructions:")
    print("   - Click 'Add Component' to add components to the scene")
    print("   - Click 'Test Wire Routing' to test perpendicular routing")
    print("   - Click 'Test Collision Avoidance' to test component avoidance")
    print("   - Click 'Test Wire Intersections' to test intersection bumps")
    print("   - Click 'Clear Scene' to start over")
    print()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
