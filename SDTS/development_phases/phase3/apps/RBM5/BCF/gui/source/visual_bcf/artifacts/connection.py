"""
Enhanced Wire Connection Module - Phase 3

Wire connection between component pins with advanced routing:
- Perpendicular (right-angle) routing
- Collision avoidance with components
- Intersection bumps for wire crossings
"""

from typing import Optional, List, Tuple
import math

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsPathItem, QMenu, QGraphicsItem

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin


class WirePath:
    """Represents a wire path with multiple segments and routing logic"""
    
    def __init__(self, start_point: QPointF, end_point: QPointF):
        self.start_point = start_point
        self.end_point = end_point
        self.segments = []
        self.intersection_bumps = []
        self._calculate_path()
    
    def _calculate_path(self):
        """Calculate the optimal perpendicular path between two points"""
        dx = abs(self.end_point.x() - self.start_point.x())
        dy = abs(self.end_point.y() - self.start_point.y())
        
        # Determine routing strategy based on distance
        if dx > dy:
            # Horizontal first, then vertical
            self._route_horizontal_first()
        else:
            # Vertical first, then horizontal
            self._route_vertical_first()
    
    def _route_horizontal_first(self):
        """Route wire horizontally first, then vertically"""
        mid_x = self.start_point.x() + (self.end_point.x() - self.start_point.x()) / 2
        
        # First segment: horizontal from start to midpoint
        self.segments.append((
            self.start_point,
            QPointF(mid_x, self.start_point.y())
        ))
        
        # Second segment: vertical from midpoint to end y-level
        self.segments.append((
            QPointF(mid_x, self.start_point.y()),
            QPointF(mid_x, self.end_point.y())
        ))
        
        # Third segment: horizontal from midpoint to end
        self.segments.append((
            QPointF(mid_x, self.end_point.y()),
            self.end_point
        ))
    
    def _route_vertical_first(self):
        """Route wire vertically first, then horizontally"""
        mid_y = self.start_point.y() + (self.end_point.y() - self.start_point.y()) / 2
        
        # First segment: vertical from start to midpoint
        self.segments.append((
            self.start_point,
            QPointF(self.start_point.x(), mid_y)
        ))
        
        # Second segment: horizontal from midpoint to end x-level
        self.segments.append((
            QPointF(self.start_point.x(), mid_y),
            QPointF(self.end_point.x(), mid_y)
        ))
        
        # Third segment: vertical from midpoint to end
        self.segments.append((
            QPointF(self.end_point.x(), mid_y),
            self.end_point
        ))
    
    def add_intersection_bump(self, intersection_point: QPointF, direction: str):
        """Add a bump at wire intersection point"""
        # Store bump as tuple: (intersection_point, direction)
        # The actual bump drawing is now integrated into the wire path
        self.intersection_bumps.append((intersection_point, direction))
    
    def get_path(self) -> QPainterPath:
        """Get the complete wire path as a QPainterPath with integrated bumps"""
        path = QPainterPath()
        
        if not self.segments:
            return path
        
        # Start at the beginning
        path.moveTo(self.segments[0][0])
        
        # Process segments and integrate bumps
        current_pos = self.segments[0][0]
        
        for i, (segment_start, segment_end) in enumerate(self.segments):
            # Check if this segment has any bumps
            segment_bumps = self._get_bumps_for_segment(i, segment_start, segment_end)
            
            if not segment_bumps:
                # No bumps, just draw the segment normally
                path.lineTo(segment_end)
                current_pos = segment_end
            else:
                # This segment has bumps, need to break it up
                self._draw_segment_with_bumps(path, segment_start, segment_end, segment_bumps, current_pos)
                current_pos = segment_end
        
        return path
    
    def _get_bumps_for_segment(self, segment_index: int, segment_start: QPointF, segment_end: QPointF) -> List[Tuple[QPointF, str]]:
        """Get bumps that intersect with a specific segment"""
        segment_bumps = []
        
        for bump_data in self.intersection_bumps:
            if len(bump_data) == 2:  # New simplified format: (intersection_point, direction)
                intersection_point, direction = bump_data
                # Check if this intersection point is along this segment
                if self._point_is_along_segment(intersection_point, segment_start, segment_end):
                    segment_bumps.append((intersection_point, direction))
            elif len(bump_data) == 5:  # Old format compatibility
                intersection_point, _, _, _, direction = bump_data
                # Check if this intersection point is along this segment
                if self._point_is_along_segment(intersection_point, segment_start, segment_end):
                    segment_bumps.append((intersection_point, direction))
        
        # Sort bumps by distance from segment start
        segment_bumps.sort(key=lambda x: self._distance_to_point(x[0], segment_start))
        return segment_bumps
    
    def _point_is_along_segment(self, point: QPointF, seg_start: QPointF, seg_end: QPointF) -> bool:
        """Check if a point lies along a line segment"""
        # Calculate distances
        d1 = self._distance_to_point(point, seg_start)
        d2 = self._distance_to_point(point, seg_end)
        segment_length = self._distance_to_point(seg_end, seg_start)
        
        # Point is along segment if sum of distances equals segment length (within tolerance)
        tolerance = 0.1
        return abs(d1 + d2 - segment_length) < tolerance
    
    def _distance_to_point(self, p1: QPointF, p2: QPointF) -> float:
        """Calculate distance between two points"""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        return math.sqrt(dx*dx + dy*dy)
    
    def _draw_segment_with_bumps(self, path: QPainterPath, segment_start: QPointF, segment_end: QPointF, 
                                bumps: List[Tuple[QPointF, str]], current_pos: QPointF):
        """Draw a segment with integrated bumps"""
        if not bumps:
            path.lineTo(segment_end)
            return
        
        # Start from current position
        current = current_pos
        
        for bump_point, bump_direction in bumps:
            # Draw line to just before the bump
            path.lineTo(bump_point)
            
            # Create the semi-circle bump
            self._draw_bump_integrated(path, bump_point, bump_direction)
            
            # Update current position to the end of the bump
            current = self._get_bump_end_point(bump_point, bump_direction)
        
        # Draw final line to segment end
        path.lineTo(segment_end)
    
    def _draw_bump_integrated(self, path: QPainterPath, intersection_point: QPointF, direction: str):
        """Draw a bump that's integrated into the wire path"""
        bump_size = 8
        
        if direction == "horizontal":
            # Vertical bump - wire goes up and over
            # Start at intersection point
            # Go up to create semi-circle
            top_point = QPointF(intersection_point.x(), intersection_point.y() - bump_size)
            # Control points for smooth curve
            control1 = QPointF(intersection_point.x() - bump_size/2, intersection_point.y() - bump_size/2)
            control2 = QPointF(intersection_point.x() + bump_size/2, intersection_point.y() - bump_size/2)
            
            # Draw the semi-circle
            path.quadTo(control1, top_point)
            path.quadTo(control2, QPointF(intersection_point.x(), intersection_point.y() - bump_size))
            
        else:  # vertical
            # Horizontal bump - wire goes left and over
            # Start at intersection point
            # Go left to create semi-circle
            left_point = QPointF(intersection_point.x() - bump_size, intersection_point.y())
            # Control points for smooth curve
            control1 = QPointF(intersection_point.x() - bump_size/2, intersection_point.y() - bump_size/2)
            control2 = QPointF(intersection_point.x() - bump_size/2, intersection_point.y() + bump_size/2)
            
            # Draw the semi-circle
            path.quadTo(control1, left_point)
            path.quadTo(control2, QPointF(intersection_point.x() - bump_size, intersection_point.y()))
    
    def _get_bump_end_point(self, intersection_point: QPointF, direction: str) -> QPointF:
        """Get the end point of a bump (where the wire continues)"""
        bump_size = 8
        
        if direction == "horizontal":
            # Vertical bump ends at the same x, but y is back to intersection level
            return QPointF(intersection_point.x(), intersection_point.y())
        else:  # vertical
            # Horizontal bump ends at the same y, but x is back to intersection level
            return QPointF(intersection_point.x(), intersection_point.y())


class EnhancedWire(QGraphicsPathItem):
    """Enhanced wire connection between component pins with advanced routing"""

    def __init__(
            self,
            start_pin: ComponentPin,
            end_pin: Optional[ComponentPin] = None,
            scene=None):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.scene = scene
        self.is_temporary = end_pin is None
        
        # Wire properties
        self.wire_width = 2
        self.wire_color = QColor(0, 0, 0)  # Black
        self.temp_color = QColor(255, 0, 0)  # Red for temporary
        
        # Visual appearance
        self.setPen(QPen(self.wire_color, self.wire_width))
        self.setZValue(5)  # Wires above components but below pins
        
        # Make wires selectable and deletable
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Wire path and routing
        self.wire_path = None
        self.avoided_components = []
        
        # Set initial path
        self.update_path()
    
    def update_path(self, temp_end_pos: Optional[QPointF] = None):
        """Update wire path position and routing"""
        start_pos = self.start_pin.get_connection_point()
        
        if self.end_pin:
            # Permanent wire with end pin
            end_pos = self.end_pin.get_connection_point()
            self.setPen(QPen(self.wire_color, self.wire_width))
        elif temp_end_pos:
            # Temporary wire being drawn
            end_pos = temp_end_pos
            self.setPen(QPen(self.temp_color, self.wire_width))
        else:
            return
        
        # Check if position actually changed to avoid unnecessary recalculations
        if (hasattr(self, '_last_start_pos') and hasattr(self, '_last_end_pos') and
            self._last_start_pos == start_pos and self._last_end_pos == end_pos):
            return  # No change, skip update
        
        # Store current positions for next comparison
        self._last_start_pos = start_pos
        self._last_end_pos = end_pos
        
        # Calculate optimal path avoiding components
        self._calculate_optimal_path(start_pos, end_pos)
        
        # Update the graphics item
        if self.wire_path:
            self.setPath(self.wire_path.get_path())
    
    def _calculate_optimal_path(self, start_pos: QPointF, end_pos: QPointF):
        """Calculate optimal wire path avoiding components and other wires"""
        # Start with basic perpendicular routing
        self.wire_path = WirePath(start_pos, end_pos)
        
        # Clear old intersection bumps before recalculating
        if self.wire_path:
            self.wire_path.intersection_bumps.clear()
        
        # Apply collision avoidance
        self._avoid_component_collisions()
        
        # Handle wire intersections
        self._handle_wire_intersections()
    
    def _avoid_component_collisions(self):
        """Modify wire path to avoid passing over components"""
        if not self.scene:
            return
        
        # Get all components in the scene - look for multiple identifiers
        components = []
        for item in self.scene.items():
            # Check if this is a component (not a wire, not a pin)
            is_component = (
                hasattr(item, 'component_type') or  # ComponentWithPins
                hasattr(item, 'name') and hasattr(item, 'rect') or  # Graphics items with name and rect
                (hasattr(item, 'boundingRect') and not hasattr(item, 'is_temporary'))  # Items with bounding rect but not temporary
            )
            
            # Make sure it's not the current wire's parent component
            if is_component and item != self.start_pin.parent_component:
                components.append(item)
        
        # Debug: Print component detection
        print(f"🔍 Wire collision detection: Found {len(components)} components to avoid")
        for comp in components:
            comp_name = getattr(comp, 'name', 'Unknown')
            comp_type = getattr(comp, 'component_type', 'Unknown')
            print(f"   - {comp_name} ({comp_type})")
        
        # Check each segment for collisions
        new_segments = []
        for i, (segment_start, segment_end) in enumerate(self.wire_path.segments):
            print(f"🔍 Checking segment {i+1}: ({segment_start.x():.1f}, {segment_start.y():.1f}) → ({segment_end.x():.1f}, {segment_end.y():.1f})")
            
            if self._segment_collides_with_components(segment_start, segment_end, components):
                print(f"   ❌ Collision detected! Rerouting segment {i+1}")
                # Reroute this segment to avoid collision
                rerouted_segments = self._reroute_segment_around_components(
                    segment_start, segment_end, components
                )
                new_segments.extend(rerouted_segments)
            else:
                print(f"   ✅ No collision for segment {i+1}")
                new_segments.append((segment_start, segment_end))
        
        # Update wire path with new segments
        self.wire_path.segments = new_segments
        print(f"🔍 Wire path updated: {len(new_segments)} segments")
    
    def _segment_collides_with_components(self, start: QPointF, end: QPointF, components: list) -> bool:
        """Check if a line segment collides with any component"""
        for component in components:
            if hasattr(component, 'boundingRect'):
                rect = component.boundingRect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height()
                )
                
                # Check if line segment intersects with component rectangle
                if self._line_intersects_rect(start, end, component_rect):
                    return True
            elif hasattr(component, 'rect'):
                # Handle QGraphicsRectItem components
                rect = component.rect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height()
                )
                
                if self._line_intersects_rect(start, end, component_rect):
                    return True
        
        return False
    
    def _line_intersects_rect(self, start: QPointF, end: QPointF, rect: QRectF) -> bool:
        """Check if a line segment intersects with a rectangle"""
        # Simple bounding box check - can be enhanced with more sophisticated algorithms
        line_rect = QRectF(
            min(start.x(), end.x()),
            min(start.y(), end.y()),
            abs(end.x() - start.x()),
            abs(end.y() - start.y())
        )
        
        return rect.intersects(line_rect)
    
    def _reroute_segment_around_components(self, start: QPointF, end: QPointF, components: list) -> List[Tuple[QPointF, QPointF]]:
        """Reroute a segment to avoid components by adding perpendicular detours"""
        # Find the component that's blocking this segment
        blocking_component = None
        for component in components:
            if hasattr(component, 'boundingRect'):
                rect = component.boundingRect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height()
                )
                
                if self._line_intersects_rect(start, end, component_rect):
                    blocking_component = component
                    break
        
        if not blocking_component:
            return [(start, end)]
        
        # Calculate detour points around the component
        rect = blocking_component.boundingRect()
        component_rect = QRectF(
            blocking_component.pos().x() + rect.x(),
            blocking_component.pos().y() + rect.y(),
            rect.width(),
            rect.height()
        )
        
        # Determine if this is a horizontal or vertical segment
        is_horizontal = abs(end.y() - start.y()) < 1
        
        if is_horizontal:
            # Horizontal segment - add vertical detour
            detour_y = component_rect.bottom() + 20  # 20px below component
            
            # Create three segments: start to detour, detour across, detour to end
            segments = [
                (start, QPointF(start.x(), detour_y)),
                (QPointF(start.x(), detour_y), QPointF(end.x(), detour_y)),
                (QPointF(end.x(), detour_y), end)
            ]
        else:
            # Vertical segment - add horizontal detour
            detour_x = component_rect.right() + 20  # 20px to the right of component
            
            # Create three segments: start to detour, detour across, detour to end
            segments = [
                (start, QPointF(detour_x, start.y())),
                (QPointF(detour_x, start.y()), QPointF(detour_x, end.y())),
                (QPointF(detour_x, end.y()), end)
            ]
        
        return segments
    
    def _handle_wire_intersections(self):
        """Handle intersections with other wires by adding bumps"""
        if not self.scene:
            print("⚠️  No scene reference for intersection detection")
            return
        
        # Get all other wires in the scene - look for multiple wire types
        other_wires = []
        for item in self.scene.items():
            # Check if this is a wire (not a component, not a pin)
            is_wire = (
                isinstance(item, EnhancedWire) or  # Enhanced wire
                hasattr(item, 'is_temporary') or  # Any item with is_temporary flag
                hasattr(item, 'start_pin') and hasattr(item, 'end_pin')  # Items with pins
            )
            
            if is_wire and item != self:
                other_wires.append(item)
        
        print(f"🔍 Wire intersection detection: Found {len(other_wires)} other wires to check")
        
        # Process intersections with other wires
        intersection_count = 0
        for other_wire in other_wires:
            # Check if the other wire has a path to analyze
            if hasattr(other_wire, 'wire_path') and other_wire.wire_path:
                intersection_data = self._find_wire_intersections_with_angles(other_wire)
                if intersection_data:
                    print(f"   🔍 Found {len(intersection_data)} intersections with enhanced wire")
                    for point, direction in intersection_data:
                        self.wire_path.add_intersection_bump(point, direction)
                        intersection_count += 1
            elif hasattr(other_wire, 'line'):  # Fallback for old wire types
                # Convert old wire line to segments for intersection detection
                old_wire_segments = self._convert_old_wire_to_segments(other_wire)
                if old_wire_segments:
                    intersection_data = self._find_intersections_with_segments_and_angles(old_wire_segments)
                    if intersection_data:
                        print(f"   🔍 Found {len(intersection_data)} intersections with old wire")
                        for point, direction in intersection_data:
                            self.wire_path.add_intersection_bump(point, direction)
                            intersection_count += 1
        
        print(f"🔍 Wire intersection detection complete: Added {intersection_count} bumps")
        
        # Debug: Show final bump count
        if self.wire_path:
            print(f"🔍 Final wire path has {len(self.wire_path.intersection_bumps)} bumps")
            for i, (point, direction) in enumerate(self.wire_path.intersection_bumps):
                print(f"   Bump {i+1}: ({point.x():.1f}, {point.y():.1f}) - {direction}")
    
    def _find_wire_intersections(self, other_wire) -> List[Tuple[QPointF, str]]:
        """Find intersection points between this wire and another wire (legacy method)"""
        intersections = []
        
        if not self.wire_path or not other_wire.wire_path:
            return intersections
        
        # Check each segment of this wire against each segment of the other wire
        for i, (seg1_start, seg1_end) in enumerate(self.wire_path.segments):
            for j, (seg2_start, seg2_end) in enumerate(other_wire.wire_path.segments):
                intersection = self._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
                if intersection:
                    # Determine direction for bump
                    direction = "horizontal" if abs(seg1_end.y() - seg1_start.y()) < 1 else "vertical"
                    intersections.append((intersection, direction))
        
        return intersections
    
    def _find_wire_intersections_with_angles(self, other_wire) -> List[Tuple[QPointF, str]]:
        """Find intersection points between this wire and another wire with angle-based bump logic"""
        intersections = []
        
        if not self.wire_path or not other_wire.wire_path:
            return intersections
        
        # Calculate the overall angle of this wire relative to horizontal
        this_wire_angle = self._calculate_wire_angle()
        
        # Calculate the overall angle of the other wire relative to horizontal
        other_wire_angle = self._calculate_wire_angle_for_wire(other_wire)
        
        # Check each segment of this wire against each segment of the other wire
        for i, (seg1_start, seg1_end) in enumerate(self.wire_path.segments):
            for j, (seg2_start, seg2_end) in enumerate(other_wire.wire_path.segments):
                intersection = self._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
                if intersection:
                    # Determine direction for bump
                    direction = "horizontal" if abs(seg1_end.y() - seg1_start.y()) < 1 else "vertical"
                    
                    # Determine which wire should create the bump based on angle
                    # Wire with smaller angle relative to horizontal creates the bump
                    should_create_bump = abs(this_wire_angle) <= abs(other_wire_angle)
                    
                    if should_create_bump:
                        # Return simplified format: (intersection_point, direction)
                        intersections.append((intersection, direction))
        
        return intersections
    
    def _calculate_wire_angle(self) -> float:
        """Calculate the overall angle of this wire relative to horizontal axis"""
        if not self.wire_path or not self.wire_path.segments:
            return 0.0
        
        # Use the first and last points to determine overall direction
        first_point = self.wire_path.segments[0][0]
        last_point = self.wire_path.segments[-1][1]
        
        dx = last_point.x() - first_point.x()
        dy = last_point.y() - first_point.y()
        
        if abs(dx) < 1e-6:  # Vertical wire
            return 90.0 if dy > 0 else -90.0
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to [-180, 180] degrees
        if angle_deg > 180:
            angle_deg -= 360
        elif angle_deg < -180:
            angle_deg += 360
        
        return angle_deg
    
    def _calculate_wire_angle_for_wire(self, other_wire) -> float:
        """Calculate the overall angle of another wire relative to horizontal axis"""
        if not hasattr(other_wire, 'wire_path') or not other_wire.wire_path or not other_wire.wire_path.segments:
            return 0.0
        
        # Use the first and last points to determine overall direction
        first_point = other_wire.wire_path.segments[0][0]
        last_point = other_wire.wire_path.segments[-1][1]
        
        dx = last_point.x() - first_point.x()
        dy = last_point.y() - first_point.y()
        
        if abs(dx) < 1e-6:  # Vertical wire
            return 90.0 if dy > 0 else -90.0
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # Normalize to [-180, 180] degrees
        if angle_deg > 180:
            angle_deg -= 360
        elif angle_deg < -180:
            angle_deg += 360
        
        return angle_deg
    
    def _segment_intersection(self, seg1_start: QPointF, seg1_end: QPointF, 
                             seg2_start: QPointF, seg2_end: QPointF) -> Optional[QPointF]:
        """Find intersection point between two line segments"""
        # Line segment intersection using parametric equations
        # Line 1: P1 + t1(P2 - P1) = P1 + t1 * v1
        # Line 2: P3 + t2(P4 - P3) = P3 + t2 * v2
        
        # Calculate direction vectors
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
    
    def _convert_old_wire_to_segments(self, old_wire) -> List[Tuple[QPointF, QPointF]]:
        """Convert old wire line to segments for intersection detection"""
        if hasattr(old_wire, 'line'):
            line = old_wire.line()
            start_point = QPointF(line.x1(), line.y1())
            end_point = QPointF(line.x2(), line.y2())
            return [(start_point, end_point)]
        return []
    
    def _find_intersections_with_segments(self, segments: List[Tuple[QPointF, QPointF]]) -> List[Tuple[QPointF, str]]:
        """Find intersections between this wire and a list of segments (legacy method)"""
        intersections = []
        
        if not self.wire_path:
            return intersections
        
        for seg1_start, seg1_end in self.wire_path.segments:
            for seg2_start, seg2_end in segments:
                intersection = self._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
                if intersection:
                    # Determine direction for bump
                    direction = "horizontal" if abs(seg1_end.y() - seg1_start.y()) < 1 else "vertical"
                    intersections.append((intersection, direction))
        
        return intersections
    
    def _find_intersections_with_segments_and_angles(self, segments: List[Tuple[QPointF, QPointF]]) -> List[Tuple[QPointF, str]]:
        """Find intersections between this wire and a list of segments with angle-based bump logic"""
        intersections = []
        
        if not self.wire_path:
            return intersections
        
        # Calculate the overall angle of this wire relative to horizontal
        this_wire_angle = self._calculate_wire_angle()
        
        # Calculate the overall angle of the old wire segments relative to horizontal
        if segments:
            first_point = segments[0][0]
            last_point = segments[-1][1]
            dx = last_point.x() - first_point.x()
            dy = last_point.y() - first_point.y()
            
            if abs(dx) < 1e-6:  # Vertical wire
                other_wire_angle = 90.0 if dy > 0 else -90.0
            else:
                angle_rad = math.atan2(dy, dx)
                other_wire_angle = math.degrees(angle_rad)
                # Normalize to [-180, 180] degrees
                if other_wire_angle > 180:
                    other_wire_angle -= 360
                elif other_wire_angle < -180:
                    other_wire_angle += 360
        else:
            other_wire_angle = 0.0
        
        for seg1_start, seg1_end in self.wire_path.segments:
            for seg2_start, seg2_end in segments:
                intersection = self._segment_intersection(seg1_start, seg1_end, seg2_start, seg2_end)
                if intersection:
                    # Determine direction for bump
                    direction = "horizontal" if abs(seg1_end.y() - seg1_start.y()) < 1 else "vertical"
                    
                    # Determine which wire should create the bump based on angle
                    # Wire with smaller angle relative to horizontal creates the bump
                    should_create_bump = abs(this_wire_angle) <= abs(other_wire_angle)
                    
                    if should_create_bump:
                        # Return simplified format: (intersection_point, direction)
                        intersections.append((intersection, direction))
        
        return intersections
    
    def complete_wire(self, end_pin: ComponentPin) -> bool:
        """Complete the wire connection"""
        if end_pin == self.start_pin:
            return False  # Can't connect to self
        
        self.end_pin = end_pin
        self.is_temporary = False
        self.update_path()
        return True
    
    def update_wire_position(self):
        """Update wire position when pins move"""
        if self.start_pin and self.end_pin:
            self.update_path()
    
    def force_intersection_recalculation(self):
        """Force recalculation of intersections and bumps"""
        if not self.wire_path:
            return
        
        print(f"🔄 Forcing intersection recalculation for wire")
        
        # Clear old bumps
        self.wire_path.intersection_bumps.clear()
        
        # Recalculate intersections
        self._handle_wire_intersections()
        
        # Update the graphics
        self.setPath(self.wire_path.get_path())
        
        print(f"🔄 Intersection recalculation complete")
    
    def update_wire_position_lightweight(self):
        """Lightweight update that only recalculates wire positions without full routing"""
        if not self.start_pin or not self.end_pin or not self.wire_path:
            return
        
        start_pos = self.start_pin.get_connection_point()
        end_pos = self.end_pin.get_connection_point()
        
        # Check if position actually changed
        if (hasattr(self, '_last_start_pos') and hasattr(self, '_last_end_pos') and
            self._last_start_pos == start_pos and self._last_end_pos == end_pos):
            return  # No change, skip update
        
        # Store current positions
        self._last_start_pos = start_pos
        self._last_end_pos = end_pos
        
        # Only update the wire path if it's a simple straight connection
        # For complex routed wires, use the full update_path method
        if len(self.wire_path.segments) <= 3:  # Simple wire
            # Recalculate basic path without collision detection
            self.wire_path = WirePath(start_pos, end_pos)
            self.setPath(self.wire_path.get_path())
        else:
            # Complex wire - use full update
            self.update_path()
    
    def contextMenuEvent(self, event):
        """Handle right-click on wire"""
        menu = QMenu()
        delete_action = menu.addAction("Delete Wire")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            scene = self.scene()
            if scene and hasattr(scene, 'remove_wire'):
                scene.remove_wire(self)
            elif scene:
                # Fallback to direct removal if scene doesn't have remove_wire method
                scene.removeItem(self)

    def itemChange(self, change, value):
        """Handle item state changes, particularly selection"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Change line format based on selection state
            if value:  # Selected
                # Change to dot-dash line when selected
                current_pen = self.pen()
                current_pen.setStyle(Qt.PenStyle.DashDotLine)
                self.setPen(current_pen)
                print(f"🔍 Wire selected: Changed to dot-dash line")
            else:  # Not selected
                # Restore normal line when deselected
                if self.is_temporary:
                    self.setPen(QPen(self.temp_color, self.wire_width))
                else:
                    self.setPen(QPen(self.wire_color, self.wire_width))
                print(f"🔍 Wire deselected: Restored normal line")
        
        return super().itemChange(change, value)
    
    def shape(self):
        """Override shape to make selection more precise - only select when clicking on the actual line"""
        if not self.wire_path:
            return super().shape()
        
        # Create a precise shape that follows the wire path
        path = self.wire_path.get_path()
        if path.isEmpty():
            return super().shape()
        
        # Create a stroked path with a small tolerance for easier clicking
        stroker = QPainterPathStroker()
        stroker.setWidth(max(4, self.wire_width + 2))  # Small tolerance around the line
        return stroker.createStroke(path)

# Keep the old Wire class for backward compatibility
class Wire(EnhancedWire):
    """Backward compatibility wrapper for the old Wire class"""
    pass
