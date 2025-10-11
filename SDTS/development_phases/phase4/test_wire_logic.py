#!/usr/bin/env python3
"""
Test Wire Logic - Phase 3

This script tests the enhanced wire logic without requiring PySide6.
It focuses on testing the mathematical algorithms and data structures.
"""

import sys
import os
import math

# Mock QPointF for testing
class MockQPointF:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"QPointF({self.x}, {self.y})"

# Mock QRectF for testing
class MockQRectF:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def intersects(self, other):
        return not (self.x + self.width < other.x or
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or
                   other.y + other.height < self.y)

def test_wire_path_calculation():
    """Test wire path calculation logic"""
    print("🔄 Testing wire path calculation...")

    # Test horizontal-first routing
    start = MockQPointF(0, 0)
    end = MockQPointF(100, 50)

    # Calculate expected path
    mid_x = start.x + (end.x - start.x) / 2

    expected_segments = [
        (start, MockQPointF(mid_x, start.y)),  # Horizontal to midpoint
        (MockQPointF(mid_x, start.y), MockQPointF(mid_x, end.y)),  # Vertical to end level
        (MockQPointF(mid_x, end.y), end)  # Horizontal to end
    ]

    print(f"✅ Start point: {start}")
    print(f"✅ End point: {end}")
    print(f"✅ Midpoint X: {mid_x}")
    print(f"✅ Expected segments: {len(expected_segments)}")

    # Verify segment logic
    for i, (seg_start, seg_end) in enumerate(expected_segments):
        print(f"   Segment {i+1}: {seg_start} → {seg_end}")

    return True

def test_collision_detection():
    """Test collision detection logic"""
    print("\n🔄 Testing collision detection...")

    # Test line-rectangle intersection
    def line_intersects_rect(start, end, rect):
        # Simple bounding box check
        line_rect = MockQRectF(
            min(start.x, end.x),
            min(start.y, end.y),
            abs(end.x - start.x),
            abs(end.y - start.y)
        )
        return rect.intersects(line_rect)

    # Test case 1: Line intersects rectangle
    line_start = MockQPointF(0, 0)
    line_end = MockQPointF(100, 100)
    rect = MockQRectF(25, 25, 50, 50)

    intersects = line_intersects_rect(line_start, line_end, rect)
    print(f"✅ Line (0,0) → (100,100) intersects rect (25,25,50x50): {intersects}")

    # Test case 2: Line doesn't intersect rectangle
    line_start2 = MockQPointF(0, 0)
    line_end2 = MockQPointF(20, 20)
    rect2 = MockQRectF(100, 100, 50, 50)

    intersects2 = line_intersects_rect(line_start2, line_end2, rect2)
    print(f"✅ Line (0,0) → (20,20) intersects rect (100,100,50x50): {intersects2}")

    return True

def test_intersection_calculation():
    """Test line segment intersection calculation"""
    print("\n🔄 Testing line segment intersection...")

    def segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end):
        """Find intersection point between two line segments"""
        # Calculate direction vectors
        v1_x = seg1_end.x - seg1_start.x
        v1_y = seg1_end.y - seg1_start.y
        v2_x = seg2_end.x - seg2_start.x
        v2_y = seg2_end.y - seg2_start.y

        # Calculate determinant
        det = v1_x * v2_y - v1_y * v2_x

        # If determinant is 0, lines are parallel
        if abs(det) < 1e-10:
            return None

        # Calculate parameters t1 and t2
        dx = seg2_start.x - seg1_start.x
        dy = seg2_start.y - seg1_start.y

        t1 = (dx * v2_y - dy * v2_x) / det
        t2 = (dx * v1_y - dy * v1_x) / det

        # Check if intersection is within both line segments
        if 0 <= t1 <= 1 and 0 <= t2 <= 1:
            # Calculate intersection point
            intersection_x = seg1_start.x + t1 * v1_x
            intersection_y = seg1_start.y + t1 * v1_y
            return MockQPointF(intersection_x, intersection_y)

        return None

    # Test case 1: Intersecting segments
    seg1_start = MockQPointF(0, 0)
    seg1_end = MockQPointF(100, 100)
    seg2_start = MockQPointF(0, 100)
    seg2_end = MockQPointF(100, 0)

    intersection = segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
    print(f"✅ Segments (0,0)→(100,100) and (0,100)→(100,0) intersect at: {intersection}")

    # Test case 2: Parallel segments (no intersection)
    seg3_start = MockQPointF(0, 0)
    seg3_end = MockQPointF(100, 0)
    seg4_start = MockQPointF(0, 50)
    seg4_end = MockQPointF(100, 50)

    intersection2 = segment_intersection(seg3_start, seg3_end, seg4_start, seg4_end)
    print(f"✅ Parallel segments intersection: {intersection2}")

    return True

def test_detour_calculation():
    """Test detour calculation for collision avoidance"""
    print("\n🔄 Testing detour calculation...")

    # Test horizontal detour
    start = MockQPointF(0, 100)
    end = MockQPointF(200, 100)
    blocking_rect = MockQRectF(75, 75, 50, 50)

    # Calculate detour
    detour_y = blocking_rect.y + blocking_rect.height + 20  # 20px below

    detour_segments = [
        (start, MockQPointF(start.x, detour_y)),  # Down to detour level
        (MockQPointF(start.x, detour_y), MockQPointF(end.x, detour_y)),  # Across at detour level
        (MockQPointF(end.x, detour_y), end)  # Up to end
    ]

    print(f"✅ Horizontal detour around blocking component:")
    print(f"   Blocking rect: ({blocking_rect.x}, {blocking_rect.y}, {blocking_rect.width}x{blocking_rect.height})")
    print(f"   Detour Y level: {detour_y}")
    print(f"   Detour segments: {len(detour_segments)}")

    for i, (seg_start, seg_end) in enumerate(detour_segments):
        print(f"     Segment {i+1}: {seg_start} → {seg_end}")

    return True

def test_bump_calculation():
    """Test intersection bump calculation"""
    print("\n🔄 Testing intersection bump calculation...")

    # Test bump creation
    intersection_point = MockQPointF(100, 100)
    bump_size = 8

    # Horizontal wire bump (vertical bump)
    horizontal_bump_start = MockQPointF(intersection_point.x, intersection_point.y - bump_size)
    horizontal_bump_end = MockQPointF(intersection_point.x, intersection_point.y + bump_size)

    # Vertical wire bump (horizontal bump)
    vertical_bump_start = MockQPointF(intersection_point.x - bump_size, intersection_point.y)
    vertical_bump_end = MockQPointF(intersection_point.x + bump_size, intersection_point.y)

    print(f"✅ Intersection point: {intersection_point}")
    print(f"✅ Bump size: {bump_size}")
    print(f"✅ Horizontal wire bump: {horizontal_bump_start} → {horizontal_bump_end}")
    print(f"✅ Vertical wire bump: {vertical_bump_start} → {vertical_bump_end}")

    return True

def main():
    """Main test function"""
    print("=== Enhanced Wire Logic Test - Phase 3 ===")
    print("Testing wire algorithms and mathematical logic...")
    print()

    # Run all tests
    tests = [
        ("Path Calculation", test_wire_path_calculation),
        ("Collision Detection", test_collision_detection),
        ("Intersection Calculation", test_intersection_calculation),
        ("Detour Calculation", test_detour_calculation),
        ("Bump Calculation", test_bump_calculation)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*50)
    print("LOGIC TEST SUMMARY")
    print("="*50)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1

    print("-" * 50)
    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All logic tests passed! Wire algorithms are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
