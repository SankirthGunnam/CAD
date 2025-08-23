#!/usr/bin/env python3
"""
Simple test script to debug connection bump logic without GUI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'RBM5', 'BCF', 'gui', 'source', 'visual_bcf'))

from PySide6.QtCore import QPointF
from artifacts.connection import WirePath

def test_wire_path_creation():
    """Test basic wire path creation"""
    print("=== TESTING WIRE PATH CREATION ===")
    
    # Create a simple wire path
    start_point = QPointF(100, 100)
    end_point = QPointF(300, 100)
    
    print(f"Creating wire path from {start_point} to {end_point}")
    wire_path = WirePath(start_point, end_point)
    
    print(f"Wire path created with {len(wire_path.segments)} segments")
    for i, (seg_start, seg_end) in enumerate(wire_path.segments):
        print(f"  Segment {i}: {seg_start} -> {seg_end}")
    
    # Test path generation
    path = wire_path.get_path()
    print(f"Generated path: {path}")
    
    return wire_path

def test_intersection_detection():
    """Test intersection detection between two wire paths"""
    print("\n=== TESTING INTERSECTION DETECTION ===")
    
    # Create two wire paths that should intersect
    wire1_path = WirePath(QPointF(100, 100), QPointF(300, 100))  # Horizontal
    wire2_path = WirePath(QPointF(200, 50), QPointF(200, 150))   # Vertical
    
    print(f"Wire 1 segments: {wire1_path.segments}")
    print(f"Wire 2 segments: {wire2_path.segments}")
    
    # Test segment intersection manually
    from artifacts.connection import Wire
    
    # Create a mock wire to test intersection methods
    class MockWire:
        def __init__(self, wire_path):
            self.wire_path = wire_path
        
        def _segment_intersection(self, seg1_start, seg1_end, seg2_start, seg2_end):
            """Find intersection point between two line segments"""
            # Line segment intersection using parametric equations
            v1_x = seg1_end.x() - seg1_start.x()
            v1_y = seg1_end.y() - seg1_start.y()
            v2_x = seg2_end.x() - seg2_start.x()
            v2_y = seg2_end.y() - seg2_start.y()
            
            # Calculate determinant
            det = v1_x * v2_y - v1_y * v2_x
            
            # If determinant is 0, lines are parallel
            if abs(det) < 1e-10:
                return None
            
            # Calculate parameters t1 and t2
            dx = seg2_start.x() - seg1_start.x()
            dy = seg2_start.y() - seg1_start.y()
            
            t1 = (dx * v2_y - dy * v2_x) / det
            t2 = (dx * v1_y - dy * v1_x) / det
            
            # Check if intersection is within both line segments
            if 0 <= t1 <= 1 and 0 <= t2 <= 1:
                # Calculate intersection point
                intersection_x = seg1_start.x() + t1 * v1_x
                intersection_y = seg1_start.y() + t1 * v1_y
                return QPointF(intersection_x, intersection_y)
            
            return None
    
    mock_wire1 = MockWire(wire1_path)
    
    # Test intersection between segments
    intersections = []
    for i, (seg1_start, seg1_end) in enumerate(wire1_path.segments):
        for j, (seg2_start, seg2_end) in enumerate(wire2_path.segments):
            intersection = mock_wire1._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
            if intersection:
                print(f"✅ Found intersection: Wire1 segment {i} intersects Wire2 segment {j} at {intersection}")
                intersections.append((intersection, "horizontal"))
            else:
                print(f"❌ No intersection: Wire1 segment {i} vs Wire2 segment {j}")
    
    return intersections

def test_bump_creation(intersections):
    """Test bump creation on wire paths"""
    print("\n=== TESTING BUMP CREATION ===")
    
    if not intersections:
        print("No intersections found, cannot test bumps")
        return
    
    # Create a wire path and add bumps
    wire_path = WirePath(QPointF(100, 100), QPointF(300, 100))
    
    print(f"Original wire path has {len(wire_path.segments)} segments")
    
    # Add bumps for each intersection
    for intersection_point, direction in intersections:
        print(f"Adding bump at {intersection_point} with direction {direction}")
        wire_path.add_intersection_bump(intersection_point, direction)
    
    print(f"Wire path now has {len(wire_path.intersection_bumps)} intersection bumps")
    
    # Generate the path with bumps
    path_with_bumps = wire_path.get_path()
    print(f"Generated path with bumps: {path_with_bumps}")
    
    return wire_path

def main():
    """Main test function"""
    print("=== CONNECTION BUMP LOGIC TEST ===")
    
    try:
        # Test 1: Wire path creation
        wire_path = test_wire_path_creation()
        
        # Test 2: Intersection detection
        intersections = test_intersection_detection()
        
        # Test 3: Bump creation
        if intersections:
            bump_wire_path = test_bump_creation(intersections)
            print(f"\n✅ SUCCESS: Created wire path with {len(bump_wire_path.intersection_bumps)} bumps")
        else:
            print("\n❌ FAILED: No intersections found to create bumps")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
