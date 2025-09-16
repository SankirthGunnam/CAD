#!/usr/bin/env python3
"""
Test script to debug connection bump logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'RBM5', 'BCF', 'gui', 'source', 'visual_bcf'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

from artifacts.connection import Wire, WirePath
from artifacts.pin import ComponentPin
from artifacts.chip import ComponentWithPins
from scene import ComponentScene
from view import CustomGraphicsView

class BumpTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connection Bump Logic Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create scene and view
        self.scene = ComponentScene()
        self.view = CustomGraphicsView(self.scene)
        layout.addWidget(self.view)

        # Create test components
        self.create_test_components()

        # Create test wires
        self.create_test_wires()

        # Add debug buttons
        self.add_debug_buttons(layout)

        # Set up the scene
        self.view.setScene(self.scene)
        self.view.setRenderHint(self.view.renderHints().Antialiasing)

        print("=== BUMP TEST WINDOW CREATED ===")
        print(f"Scene items: {len(self.scene.items())}")
        print(f"Components: {[item for item in self.scene.items() if hasattr(item, 'component_type')]}")
        print(f"Wires: {[item for item in self.scene.items() if hasattr(item, 'is_temporary')]}")

    def create_test_components(self):
        """Create test components for intersection testing"""
        print("Creating test components...")

        # Component 1 - Top left
        self.comp1 = ComponentWithPins("TestChip1", "chip")
        self.comp1.setPos(100, 100)
        self.scene.addItem(self.comp1)

        # Component 2 - Top right (closer to create intersection)
        self.comp2 = ComponentWithPins("TestChip2", "chip")
        self.comp2.setPos(200, 100)  # Moved closer
        self.scene.addItem(self.comp2)

        # Component 3 - Bottom left (closer to create intersection)
        self.comp3 = ComponentWithPins("TestChip3", "chip")
        self.comp3.setPos(100, 200)  # Moved closer
        self.scene.addItem(self.comp3)

        # Component 4 - Bottom right (closer to create intersection)
        self.comp4 = ComponentWithPins("TestChip4", "chip")
        self.comp4.setPos(200, 200)  # Moved closer
        self.scene.addItem(self.comp4)

        print(f"Created 4 test components")

    def create_test_wires(self):
        """Create test wires that should intersect"""
        print("Creating test wires...")

        # Wire 1: Horizontal wire from left to right (should have bumps)
        pin1 = self.comp1.pins[0]  # First pin of comp1
        pin2 = self.comp2.pins[0]  # First pin of comp2
        self.wire1 = Wire(pin1, scene=self.scene)
        if self.wire1.complete_wire(pin2):
            print(f"Wire 1 created: {pin1.pin_id} -> {pin2.pin_id}")
            print(f"Wire 1 path segments: {len(self.wire1.wire_path.segments) if self.wire1.wire_path else 0}")
            # Add wire to scene
            self.scene.addItem(self.wire1)
            print(f"Wire 1 added to scene")
        else:
            print("Failed to create Wire 1")

        # Wire 2: Vertical wire from top to bottom (should create bumps)
        pin3 = self.comp1.pins[1]  # Second pin of comp1
        pin4 = self.comp3.pins[1]  # Second pin of comp3
        self.wire2 = Wire(pin3, scene=self.scene)
        if self.wire2.complete_wire(pin4):
            print(f"Wire 2 created: {pin3.pin_id} -> {pin4.pin_id}")
            print(f"Wire 2 path segments: {len(self.wire2.wire_path.segments) if self.wire2.wire_path else 0}")
            # Add wire to scene
            self.scene.addItem(self.wire2)
            print(f"Wire 2 added to scene")
        else:
            print("Failed to create Wire 2")

        # Wire 3: Diagonal wire that should intersect with both
        pin5 = self.comp2.pins[1]  # Second pin of comp2
        pin6 = self.comp3.pins[0]  # First pin of comp3
        self.wire3 = Wire(pin5, scene=self.scene)
        if self.wire3.complete_wire(pin6):
            print(f"Wire 3 created: {pin5.pin_id} -> {pin6.pin_id}")
            print(f"Wire 3 path segments: {len(self.wire3.wire_path.segments) if self.wire3.wire_path else 0}")
            # Add wire to scene
            self.scene.addItem(self.wire3)
            print(f"Wire 3 added to scene")
        else:
            print("Failed to create Wire 3")

        print(f"Created 3 test wires")
        print(f"Total scene items: {len(self.scene.items())}")

        # Debug: Print wire positions to understand why they don't intersect
        print("\n=== WIRE POSITION DEBUG ===")
        if hasattr(self, 'wire1') and self.wire1.wire_path:
            print(f"Wire 1 (Horizontal): {self.wire1.wire_path.segments[0][0]} -> {self.wire1.wire_path.segments[-1][1]}")
        if hasattr(self, 'wire2') and self.wire2.wire_path:
            print(f"Wire 2 (Vertical): {self.wire2.wire_path.segments[0][0]} -> {self.wire2.wire_path.segments[-1][1]}")
        if hasattr(self, 'wire3') and self.wire3.wire_path:
            print(f"Wire 3 (Diagonal): {self.wire3.wire_path.segments[0][0]} -> {self.wire3.wire_path.segments[-1][1]}")

    def add_debug_buttons(self, layout):
        """Add debug buttons to test bump logic"""
        # Test intersection detection button
        test_btn = QPushButton("Test Intersection Detection")
        test_btn.clicked.connect(self.test_intersection_detection)
        layout.addWidget(test_btn)

        # Test bump creation button
        bump_btn = QPushButton("Test Bump Creation")
        bump_btn.clicked.connect(self.test_bump_creation)
        layout.addWidget(bump_btn)

        # Refresh wires button
        refresh_btn = QPushButton("Refresh All Wires")
        refresh_btn.clicked.connect(self.refresh_all_wires)
        layout.addWidget(refresh_btn)

        # Debug info button
        debug_btn = QPushButton("Show Debug Info")
        debug_btn.clicked.connect(self.show_debug_info)
        layout.addWidget(debug_btn)

    def test_intersection_detection(self):
        """Test intersection detection between wires"""
        print("\n=== TESTING INTERSECTION DETECTION ===")

        if not hasattr(self, 'wire1') or not hasattr(self, 'wire2') or not hasattr(self, 'wire3'):
            print("Wires not created yet!")
            return

        # Test intersection between wire1 and wire2
        print(f"Wire 1 segments: {self.wire1.wire_path.segments if self.wire1.wire_path else 'None'}")
        print(f"Wire 2 segments: {self.wire2.wire_path.segments if self.wire2.wire_path else 'None'}")

        if self.wire1.wire_path and self.wire2.wire_path:
            # Test segment intersection
            for i, (seg1_start, seg1_end) in enumerate(self.wire1.wire_path.segments):
                for j, (seg2_start, seg2_end) in enumerate(self.wire2.wire_path.segments):
                    intersection = self.wire1._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
                    if intersection:
                        print(f"✅ Found intersection: Wire1 segment {i} intersects Wire2 segment {j} at {intersection}")
                    else:
                        print(f"❌ No intersection: Wire1 segment {i} vs Wire2 segment {j}")

        # Test wire intersection method
        intersections = self.wire1._find_wire_intersections_with_angles(self.wire2)
        print(f"Wire1 intersection detection result: {len(intersections)} intersections")
        for point, direction in intersections:
            print(f"  - Point: {point}, Direction: {direction}")

    def test_bump_creation(self):
        """Test bump creation on wires"""
        print("\n=== TESTING BUMP CREATION ===")

        if not hasattr(self, 'wire1') or not hasattr(self, 'wire2'):
            print("Wires not created yet!")
            return

        # Force intersection recalculation
        print("Forcing intersection recalculation on Wire 1...")
        self.wire1.force_intersection_recalculation()

        print("Forcing intersection recalculation on Wire 2...")
        self.wire2.force_intersection_recalculation()

        # Check if bumps were added
        if self.wire1.wire_path:
            print(f"Wire 1 intersection bumps: {len(self.wire1.wire_path.intersection_bumps)}")
            for bump in self.wire1.wire_path.intersection_bumps:
                print(f"  - Bump: {bump}")

        if self.wire2.wire_path:
            print(f"Wire 2 intersection bumps: {len(self.wire2.wire_path.intersection_bumps)}")
            for bump in self.wire2.wire_path.intersection_bumps:
                print(f"  - Bump: {bump}")

        # Update wire paths
        self.wire1.update_path()
        self.wire2.update_path()

        print("Wire paths updated with bumps")

    def refresh_all_wires(self):
        """Refresh all wires to show updated paths"""
        print("\n=== REFRESHING ALL WIRES ===")

        for item in self.scene.items():
            if hasattr(item, 'update_path'):
                print(f"Refreshing wire: {item}")
                item.update_path()
                item.update()

        # Force scene update
        self.scene.update()
        print("All wires refreshed")

    def show_debug_info(self):
        """Show debug information about the scene"""
        print("\n=== DEBUG INFORMATION ===")
        print(f"Scene items: {len(self.scene.items())}")

        for i, item in enumerate(self.scene.items()):
            if hasattr(item, 'component_type'):
                print(f"  {i}: Component - {item.component_type} at {item.pos()}")
            elif hasattr(item, 'is_temporary'):
                print(f"  {i}: Wire - temporary={item.is_temporary}, start_pin={item.start_pin.pin_id if item.start_pin else 'None'}")
                if hasattr(item, 'wire_path') and item.wire_path:
                    print(f"    Path segments: {len(item.wire_path.segments)}")
                    print(f"    Intersection bumps: {len(item.wire_path.intersection_bumps)}")
            else:
                print(f"  {i}: Other item - {type(item)}")

def main():
    app = QApplication(sys.argv)

    window = BumpTestWindow()
    window.show()

    print("\n=== BUMP TEST READY ===")
    print("1. You should see 4 components and 3 wires")
    print("2. Click 'Test Intersection Detection' to see if intersections are found")
    print("3. Click 'Test Bump Creation' to create bumps")
    print("4. Click 'Refresh All Wires' to update the display")
    print("5. Look for bumps in the wire paths")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
