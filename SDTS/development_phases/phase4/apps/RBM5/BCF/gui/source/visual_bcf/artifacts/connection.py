"""
Enhanced Wire Connection Module - Phase 3

Wire connection between component pins with advanced routing:
- Perpendicular (right-angle) routing
- Collision avoidance with components
- Intersection bumps for wire crossings
"""

from typing import Optional, List, Tuple
import math
import time
from datetime import datetime

from PySide6.QtCore import QPointF, Qt, QRectF, QLineF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsPathItem, QMenu, QGraphicsItem

from apps.RBM5.BCF.gui.source.visual_bcf.artifacts.pin import ComponentPin


class WirePath:
    """
    New WirePath class using orthogonal routing with component avoidance

    This class calculates wire paths by:
    1. Creating orthogonal (right-angle) routing between start and end points
    2. Detecting components that would be crossed by the path
    3. Creating intelligent detours around components
    4. Maintaining orthogonal routing throughout the path
    5. Supporting real-time calculation during component movement
    """

    def __init__(
        self,
        start_point: QPointF,
        end_point: QPointF,
        start_pin=None,
        end_pin=None,
        scene=None,
        calculate_now=True,
    ):
        # Ensure connections always flow from left to right
        if start_point.x() > end_point.x():
            # Swap points and pins to maintain left-to-right flow
            self.start_point = end_point
            self.end_point = start_point
            self.start_pin = end_pin
            self.end_pin = start_pin
            self._swapped = True
        else:
            self.start_point = start_point
            self.end_point = end_point
            self.start_pin = start_pin
            self.end_pin = end_pin
            self._swapped = False

        self.get_start_and_end_approach_points()
        self.scene = scene
        self.segments = []
        self.intersection_bumps = []

        # Jog bookkeeping for full-wire offsets (per colinear track)
        self._h_jogs_by_y = {}  # y_value -> vertical offset (dy)
        self._v_jogs_by_x = {}  # x_value -> horizontal offset (dx)
        self._lane_spacing = 10

        # Orthogonal routing properties
        self.clearance = 30  # Minimum clearance from components
        self.grid_size = 10  # Grid alignment for cleaner routing

        # Only calculate path immediately if requested (for sync operations)
        if calculate_now:
            self._calculate_orthogonal_path()

    def get_start_and_end_approach_points(self):
        """Get start and end approach points"""
        self.start_approach_point = self._get_perpendicular_approach_point(self.start_pin, self.start_point)
        self.end_approach_point = self._get_perpendicular_approach_point(self.end_pin, self.end_point)
        # self.start_approach_point = self.start_point
        # self.end_approach_point = self.end_point

    def _get_perpendicular_approach_point(self, pin, pin_point):
        """Get the perpendicular approach point for a pin based on its edge"""
        if not pin or not pin.edge:
            return pin_point

        clearance = 20  # 20px clearance from pin

        if pin.edge == "left":
            # Pin on left edge, approach from left (right to left)
            return QPointF(pin_point.x() - clearance, pin_point.y())
        elif pin.edge == "right":
            # Pin on right edge, approach from right (left to right)
            return QPointF(pin_point.x() + clearance, pin_point.y())
        elif pin.edge == "top":
            # Pin on top edge, approach from top (bottom to top)
            return QPointF(pin_point.x(), pin_point.y() - clearance)
        elif pin.edge == "bottom":
            # Pin on bottom edge, approach from bottom (top to bottom)
            return QPointF(pin_point.x(), pin_point.y() + clearance)
        else:
            return pin_point

    def _calculate_orthogonal_path(self):
        """Calculate orthogonal wire path with component avoidance"""
        # Start with basic orthogonal routing
        path_points = self._calculate_basic_orthogonal_path()
        # Check for component intersections and create detours
        path_points = self._avoid_component_intersections(path_points)
        # Compute and apply jogs in one pass
        path_points = self._compute_and_apply_jogs(path_points)

        # Convert path points to segments
        self.segments = [self.start_point]
        self.segments += path_points
        self.segments.append(self.end_point)

    def _calculate_basic_orthogonal_path(self) -> List[QPointF]:
        """Calculate basic orthogonal path from start to end based on pin positions"""
        path, component, p = self.get_default_detour()
        if path is not None:
            return path
        intersection_point, _, edge = self._line_intersects_rect(
            QLineF(self.start_approach_point, p),
            component.boundingRect())
        points = {
            'left': self.get_left_edge_intersection_detour,
            'right': self.get_right_edge_intersection_detour,
            'top': self.get_top_edge_intersection_detour,
            'bottom': self.get_bottom_edge_intersection_detour,
        }[edge](intersection_point, component)

        # While building, update jog maps for candidate segments
        return points

    def _calculate_simple_l_path(self) -> List[QPointF]:
        """Calculate simple L-shaped path when pin info is not available"""
        # Simple L-shaped path: horizontal first, then vertical
        mid_x = (self.start_approach_point.x() + self.end_approach_point.x()) / 2
        mid_point = QPointF(mid_x, self.start_approach_point.y())
        return [self.start_approach_point, mid_point, self.end_approach_point]

    def get_default_detour(self) -> List[QPointF]:
        component = None
        mid_point = None
        for p in [
            QPointF(self.end_approach_point.x(), self.start_approach_point.y()),
            QPointF(self.start_approach_point.x(), self.end_approach_point.y()),
        ]:
            mid_point = p
            component = self.scene.get_component_at_position(p)
            if component is None:
                return [self.start_approach_point, p, self.end_approach_point], None, mid_point
        return None, component, mid_point

    def get_left_edge_intersection_detour(self, intersection_point: QPointF, component: QRectF) -> List[QPointF]:
        p1 = QPointF(component.boundingRect().left() - self.clearance, intersection_point.y())
        if self.start_approach_point.y() < self.end_approach_point.y():
            p2 = QPointF(p1.x(), component.boundingRect().bottom() + self.clearance)
        else:
            p2 = QPointF(p1.x(), component.boundingRect().top() - self.clearance)
        p3 = QPointF(component.boundingRect().center().x(), p2.y())
        return [self.start_approach_point, p1, p2, p3, self.end_approach_point]

    def get_right_edge_intersection_detour(self, intersection_point: QPointF, component: QRectF) -> List[QPointF]:
        p1 = QPointF(component.boundingRect().right() + self.clearance, intersection_point.y())
        if self.start_approach_point.y() < self.end_approach_point.y():
            p2 = QPointF(p1.x(), component.boundingRect().bottom() + self.clearance)
        else:
            p2 = QPointF(p1.x(), component.boundingRect().top() - self.clearance)
        p3 = QPointF(component.boundingRect().center().x(), p2.y())
        return [self.start_approach_point, p1, p2, p3, self.end_approach_point]

    def get_top_edge_intersection_detour(self, intersection_point: QPointF, component: QRectF) -> List[QPointF]:
        p1 = QPointF(intersection_point.x(), component.boundingRect().top() - self.clearance)
        if self.start_approach_point.x() < self.end_approach_point.x():
            p2 = QPointF(component.boundingRect().right() + self.clearance, p1.y())
        else:
            p2 = QPointF(component.boundingRect().left() - self.clearance, p1.y())
        p3 = QPointF(p2.x(), component.boundingRect().center().y())
        return [self.start_approach_point, p1, p2, p3, self.end_approach_point]

    def get_bottom_edge_intersection_detour(self, intersection_point: QPointF, component: QRectF) -> List[QPointF]:
        p1 = QPointF(intersection_point.x(), component.boundingRect().bottom() + self.clearance)
        if self.start_approach_point.x() < self.end_approach_point.x():
            p2 = QPointF(component.boundingRect().right() + self.clearance, p1.y())
        else:
            p2 = QPointF(component.boundingRect().left() - self.clearance, p1.y())
        p3 = QPointF(p2.x(), component.boundingRect().center().y())
        return [self.start_approach_point, p1, p2, p3, self.end_approach_point]

    def _get_component_rect(self, pin) -> QRectF:
        """Get the bounding rectangle of the component that contains the pin"""
        if not pin or not hasattr(pin, "parent") or not pin.parent:
            # Fallback to a default rectangle around the pin
            return QRectF(
                self.start_approach_point.x() - 50, self.start_approach_point.y() - 50, 100, 100
            )

        # Get the parent component
        component = pin.parent
        if hasattr(component, "boundingRect"):
            # Get component's bounding rectangle in scene coordinates
            component_rect = component.boundingRect()
            if hasattr(component, "mapRectToScene"):
                return component.mapRectToScene(component_rect)
            else:
                # Fallback to component position
                return QRectF(
                    component.pos().x(),
                    component.pos().y(),
                    component_rect.width(),
                    component_rect.height(),
                )

        # Final fallback
        return QRectF(self.start_approach_point.x() - 50, self.start_approach_point.y() - 50, 100, 100)

    def _find_clear_horizontal_level(self) -> float:
        """Find a clear horizontal level for routing"""
        # Start with midpoint Y
        mid_y = (self.start_approach_point.y() + self.end_approach_point.y()) / 2

        # Try different Y levels to find one that doesn't intersect components
        for offset in range(0, 200, self.grid_size):
            for y in [mid_y - offset, mid_y + offset]:
                if self._is_horizontal_level_clear(y):
                    return y

        # Fallback to midpoint
        return mid_y

    def _find_clear_vertical_level(self) -> float:
        """Find a clear vertical level for routing"""
        # Start with midpoint X
        mid_x = (self.start_approach_point.x() + self.end_approach_point.x()) / 2

        # Try different X levels to find one that doesn't intersect components
        for offset in range(0, 200, self.grid_size):
            for x in [mid_x - offset, mid_x + offset]:
                if self._is_vertical_level_clear(x):
                    return x

        # Fallback to midpoint
        return mid_x

    def _is_horizontal_level_clear(self, y: float) -> bool:
        """Check if a horizontal line at Y level is clear of components"""
        if not self.scene:
            return True

        # Create test line for this Y level
        test_line = QLineF(
            min(self.start_approach_point.x(), self.end_approach_point.x()) - self.clearance,
            y,
            max(self.start_approach_point.x(), self.end_approach_point.x()) + self.clearance,
            y,
        )

        return not self._line_intersects_any_component(test_line)

    def _is_vertical_level_clear(self, x: float) -> bool:
        """Check if a vertical line at X level is clear of components"""
        if not self.scene:
            return True

        # Create test line for this X level
        test_line = QLineF(
            x,
            min(self.start_approach_point.y(), self.end_approach_point.y()) - self.clearance,
            x,
            max(self.start_approach_point.y(), self.end_approach_point.y()) + self.clearance,
        )

        return not self._line_intersects_any_component(test_line)

    def _line_intersects_any_component(self, line: QLineF) -> bool:
        """Check if a line intersects any component in the scene using spatial query"""
        if not self.scene:
            return False

        # Build a bounding box around the line with clearance padding
        min_x = min(line.p1().x(), line.p2().x()) - self.clearance
        max_x = max(line.p1().x(), line.p2().x()) + self.clearance
        min_y = min(line.p1().y(), line.p2().y()) - self.clearance
        max_y = max(line.p1().y(), line.p2().y()) + self.clearance
        query_rect = QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y))

        # Query only items within the vicinity of the line
        candidates = self.scene.items(query_rect)
        for item in candidates:
            if not hasattr(item, "component_id"):
                continue
            item_rect = item.mapRectToScene(item.boundingRect())
            expanded_rect = item_rect.adjusted(
                -self.clearance, -self.clearance, self.clearance, self.clearance
            )
            if self._line_intersects_rect(line, expanded_rect):
                return True
        return False

    def _avoid_component_intersections(
        self, path_points: List[QPointF]
    ) -> List[QPointF]:
        """Avoid component intersections by creating detours"""
        if not self.scene:
            return path_points

        # Check each segment for component intersections
        new_path_points = [path_points[0]]  # Start with first point

        for i in range(len(path_points) - 1):
            start_point = path_points[i]
            end_point = path_points[i + 1]

            # Create line segment
            segment_line = QLineF(start_point, end_point)

            # Check if this segment intersects any components
            intersecting_components = self._find_intersecting_components(segment_line)

            if intersecting_components:
                # Create detour around intersecting components (intermediate points only)
                detour_points = self._create_orthogonal_detour(
                    start_point, end_point, intersecting_components
                )
                for p in detour_points:
                    if new_path_points[-1] != p:
                        new_path_points.append(p)
                if new_path_points[-1] != end_point:
                    new_path_points.append(end_point)
            else:
                # No intersections - add the end point directly
                if new_path_points[-1] != end_point:
                    new_path_points.append(end_point)

        return new_path_points

    # ---------------------- Jog calculation and application (merged) ----------------------

    def _preassign_start_track_lane(self, points: List[QPointF]) -> None:
        """Assign an initial lane offset for the first track so sibling wires
        from the same start pin are spaced before they diverge.

        We determine the first segment orientation from the first two points,
        then compute a stable ordering among all wires that originate from the
        same `start_pin` by sorting their `end_pin` positions along the axis
        orthogonal to that first segment. The resulting index maps to a lane
        offset around center.
        """
        try:
            if not self.scene or not self.start_pin or not self.end_pin:
                return
            if not points or len(points) < 2:
                return

            start_p = points[0]
            first_p = points[1]
            is_horizontal = abs(first_p.y() - start_p.y()) < 1.0
            track_key = start_p.y() if is_horizontal else start_p.x()

            # If already has an offset for this track, keep it
            if is_horizontal and track_key in self._h_jogs_by_y:
                return
            if not is_horizontal and track_key in self._v_jogs_by_x:
                return

            # Collect end pins of all wires starting from the same start pin
            end_pins: List[ComponentPin] = []
            for item in self.scene.items():
                if hasattr(item, 'start_pin') and hasattr(item, 'end_pin'):
                    if item.start_pin is self.start_pin and getattr(item, 'end_pin', None) is not None:
                        end_pins.append(item.end_pin)

            if not end_pins:
                return
            if self.end_pin not in end_pins:
                end_pins.append(self.end_pin)
            if len(end_pins) <= 1:
                return

            def pin_pos_x(p):
                try:
                    return float(p.scenePos().x())
                except Exception:
                    return 0.0

            def pin_pos_y(p):
                try:
                    return float(p.scenePos().y())
                except Exception:
                    return 0.0

            # Sort by orthogonal axis; tie-break by id for stability
            if is_horizontal:
                end_pins.sort(key=lambda p: (pin_pos_y(p), id(p)))
            else:
                end_pins.sort(key=lambda p: (pin_pos_x(p), id(p)))

            try:
                idx = end_pins.index(self.end_pin)
            except ValueError:
                idx = 0

            center = (len(end_pins) - 1) / 2.0
            offset = (idx - center) * self._lane_spacing

            if is_horizontal:
                self._h_jogs_by_y.setdefault(track_key, offset)
            else:
                self._v_jogs_by_x.setdefault(track_key, offset)
        except Exception:
            # Fail safe if any scene data is unavailable
            return

    def _compute_and_apply_jogs(self, points: List[QPointF]) -> List[QPointF]:
        """Detect colinear overlaps with other wires and apply jogs in one function.

        - Scans segments to populate jog offsets maps for shared tracks.
        - Applies jogs with orthogonal transitions at endpoints.
        """
        if not self.scene or not points or len(points) < 2:
            return points

        # Reset maps
        self._h_jogs_by_y.clear()
        self._v_jogs_by_x.clear()
        # Pre-space sibling wires from same start pin before divergence
        self._preassign_start_track_lane(points)

        # Phase 1: collect jog offsets for any overlapping colinear segments
        for i in range(len(points) - 1):
            a = points[i]
            b = points[i + 1]
            is_horizontal = abs(b.y() - a.y()) < 1.0
            is_vertical = abs(b.x() - a.x()) < 1.0

            if not (is_horizontal or is_vertical):
                continue

            # Pre-assign lane on this initial track to ensure spacing even if
            # there is no existing overlapping wire yet (e.g., detour corridor)
            if is_horizontal:
                if a.y() not in self._h_jogs_by_y:
                    self._h_jogs_by_y[a.y()] = self._compute_lane_offset_for_edge(axis='y')
            else:
                if a.x() not in self._v_jogs_by_x:
                    self._v_jogs_by_x[a.x()] = self._compute_lane_offset_for_edge(axis='x')

            rect = self._segment_bounding_rect_points(a, b, 1.0)
            if rect is None:
                continue

            candidates = self.scene.items(rect)
            for item in candidates:
                if not hasattr(item, 'wire_path') or not getattr(item, 'wire_path'):
                    continue
                # Skip if same connection
                if hasattr(item, 'start_pin') and hasattr(item, 'end_pin'):
                    if item.start_pin is self.start_pin and item.end_pin is self.end_pin:
                        continue
                other_segments = item.wire_path.get_segments() if hasattr(item.wire_path, 'get_segments') else []
                for (o_s, o_e) in other_segments:
                    if self._segments_colinear_and_overlapping_points(a, b, o_s, o_e, 1.0):
                        if is_horizontal:
                            y = a.y()
                            if y not in self._h_jogs_by_y:
                                self._h_jogs_by_y[y] = self._compute_lane_offset_for_edge(axis='y')
                        else:
                            x = a.x()
                            if x not in self._v_jogs_by_x:
                                self._v_jogs_by_x[x] = self._compute_lane_offset_for_edge(axis='x')
                        break

        # Phase 2: apply jogs with endpoint transitions
        start_edge = getattr(self.start_pin, 'edge', 'left') or 'left'
        end_edge = getattr(self.end_pin, 'edge', 'right') or 'right'

        start_p = points[0]
        end_p = points[-1]

        dx_start = self._v_jogs_by_x.get(start_p.x(), 0.0)
        dy_start = self._h_jogs_by_y.get(start_p.y(), 0.0)
        dx_end = self._v_jogs_by_x.get(end_p.x(), 0.0)
        dy_end = self._h_jogs_by_y.get(end_p.y(), 0.0)

        adjusted: List[QPointF] = []
        adjusted.append(start_p)

        if dx_start != 0.0 or dy_start != 0.0:
            if start_edge in ('left', 'right'):
                if dx_start != 0.0:
                    adjusted.append(QPointF(start_p.x() + dx_start, start_p.y()))
                if dy_start != 0.0:
                    adjusted.append(QPointF(start_p.x() + dx_start, start_p.y() + dy_start))
            else:
                if dy_start != 0.0:
                    adjusted.append(QPointF(start_p.x(), start_p.y() + dy_start))
                if dx_start != 0.0:
                    adjusted.append(QPointF(start_p.x() + dx_start, start_p.y() + dy_start))

        for i in range(1, len(points) - 1):
            p = points[i]
            dx = self._v_jogs_by_x.get(p.x(), 0.0)
            dy = self._h_jogs_by_y.get(p.y(), 0.0)
            adjusted.append(QPointF(p.x() + dx, p.y() + dy))

        if dx_end != 0.0 or dy_end != 0.0:
            if end_edge in ('left', 'right'):
                if dy_end != 0.0:
                    adjusted.append(QPointF(end_p.x() + dx_end, end_p.y() + dy_end))
                if dx_end != 0.0:
                    adjusted.append(QPointF(end_p.x() + dx_end, end_p.y()))
            else:
                if dx_end != 0.0:
                    adjusted.append(QPointF(end_p.x() + dx_end, end_p.y() + dy_end))
                if dy_end != 0.0:
                    adjusted.append(QPointF(end_p.x(), end_p.y() + dy_end))

        adjusted.append(end_p)
        return adjusted
    
    def _compute_lane_offset_for_edge(self, axis: str) -> float:
        """Compute a stable lane offset based on pin order on the respective edges.

        axis='y' is for horizontal segments (shift in Y). axis='x' for vertical segments (shift in X).
        """
        # Determine pin ordering on start/end edges to map to a lane index
        def lane_index(pin) -> float:
            try:
                component = getattr(pin, 'parent_component', None)
                if not component or not hasattr(component, 'pins'):
                    return 0.0
                same = [p for p in component.pins if getattr(p, 'edge', None) == getattr(pin, 'edge', None)]
                if not same:
                    return 0.0
                if pin.edge in ('left', 'right'):
                    same.sort(key=lambda p: p.scenePos().y())
                else:
                    same.sort(key=lambda p: p.scenePos().x())
                idx = same.index(pin)
                center = (len(same) - 1) / 2.0
                return idx - center
            except Exception:
                return 0.0

        idx_start = lane_index(self.start_pin)
        idx_end = lane_index(self.end_pin)
        lane = idx_start if abs(idx_start) >= abs(idx_end) else idx_end
        offset = lane * self._lane_spacing
        # For axis direction, simply return signed offset
        return offset

    def _segment_bounding_rect_points(self, p1: QPointF, p2: QPointF, tol: float) -> Optional[QRectF]:
        """Create a thin rectangle around a segment (defined by two points) for spatial querying."""
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        if abs(y1 - y2) < 1e-6:
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2) - tol
            bottom = max(y1, y2) + tol
            return QRectF(left, top, max(1.0, right - left), max(1.0, bottom - top))
        if abs(x1 - x2) < 1e-6:
            left = min(x1, x2) - tol
            right = max(x1, x2) + tol
            top = min(y1, y2)
            bottom = max(y1, y2)
            return QRectF(left, top, max(1.0, right - left), max(1.0, bottom - top))
        left = min(x1, x2) - tol
        right = max(x1, x2) + tol
        top = min(y1, y2) - tol
        bottom = max(y1, y2) + tol
        return QRectF(left, top, max(1.0, right - left), max(1.0, bottom - top))

    def _segments_overlap_1d_vals(self, a1: float, a2: float, b1: float, b2: float, tol: float = 1.0) -> Optional[Tuple[float, float]]:
        """Return 1D overlap interval [max(mins), min(maxs)] if any, else None."""
        min_a, max_a = (a1, a2) if a1 <= a2 else (a2, a1)
        min_b, max_b = (b1, b2) if b1 <= b2 else (b2, b1)
        start = max(min_a, min_b)
        end = min(max_a, max_b)
        if end + tol >= start:
            return (start, end)
        return None

    def _segments_colinear_and_overlapping_points(self, a1: QPointF, a2: QPointF, b1: QPointF, b2: QPointF, tol: float = 1.0) -> Optional[Tuple[QPointF, QPointF]]:
        """If two axis-aligned segments are colinear and overlapping, return the overlap segment endpoints."""
        # Horizontal?
        if abs(a1.y() - a2.y()) < tol and abs(b1.y() - b2.y()) < tol and abs(a1.y() - b1.y()) < tol and abs(a2.y() - b2.y()) < tol:
            ov = self._segments_overlap_1d_vals(a1.x(), a2.x(), b1.x(), b2.x(), tol)
            if ov:
                y = (a1.y() + a2.y()) / 2.0
                return (QPointF(ov[0], y), QPointF(ov[1], y))
        # Vertical?
        if abs(a1.x() - a2.x()) < tol and abs(b1.x() - b2.x()) < tol and abs(a1.x() - b1.x()) < tol and abs(a2.x() - b2.x()) < tol:
            ov = self._segments_overlap_1d_vals(a1.y(), a2.y(), b1.y(), b2.y(), tol)
            if ov:
                x = (a1.x() + a2.x()) / 2.0
                return (QPointF(x, ov[0]), QPointF(x, ov[1]))
        return None

    def _find_intersecting_components(self, line: QLineF) -> List[QGraphicsItem]:
        """Find components that intersect the given line using spatial query"""
        intersecting_components = []

        if not self.scene:
            return intersecting_components

        # Bounding box around the line for candidate filtering
        min_x = min(line.p1().x(), line.p2().x()) - self.clearance
        max_x = max(line.p1().x(), line.p2().x()) + self.clearance
        min_y = min(line.p1().y(), line.p2().y()) - self.clearance
        max_y = max(line.p1().y(), line.p2().y()) + self.clearance
        query_rect = QRectF(min_x, min_y, max(1.0, max_x - min_x), max(1.0, max_y - min_y))

        for item in self.scene.items(query_rect):
            if not hasattr(item, "component_id"):
                continue
            item_rect = item.mapRectToScene(item.boundingRect())
            expanded_rect = item_rect.adjusted(
                -self.clearance, -self.clearance, self.clearance, self.clearance
            )
            if self._line_intersects_rect(line, expanded_rect):
                intersecting_components.append(item)

        if line.p1().y() == line.p2().y():
            intersecting_components.sort(key=lambda c: c.pos().x())
        else:
            intersecting_components.sort(key=lambda c: c.pos().y())
            if line.p1().y() > line.p2().y():
                intersecting_components.reverse()

        return intersecting_components

    def _create_orthogonal_detour(
        self, start_point: QPointF, end_point: QPointF, components: List[QGraphicsItem]
    ) -> List[QPointF]:
        """Create orthogonal detour around components"""
        if not components:
            return []

        detour_points = []
        for component in components:
            rect = component.boundingRect()
            component_rect = QRectF(
                component.pos().x() + rect.x(),
                component.pos().y() + rect.y(),
                rect.width(),
                rect.height()
            )

            intersection_point, line, edge = self._line_intersects_rect(QLineF(start_point, end_point), component_rect)
            if intersection_point:
                detour_points += self._get_detour_points(start_point, end_point, component_rect, intersection_point, line)
                start_point = detour_points[-1]

        # Return only intermediate detour points; caller handles start/end
        return detour_points

    def _get_detour_points(self,
                         start_point: QPointF,
                            end_point: QPointF, component_rect: QRectF, intersection_point: QPointF, line: QLineF) -> List[QPointF]:
        """Get detour points around components"""
        if end_point.x() - start_point.x() == 0:
            return self._create_vertical_detour(start_point, end_point, component_rect, intersection_point, line)
        else:
            return self._create_horizontal_detour(start_point, end_point, component_rect, intersection_point, line)

    def _create_vertical_detour(
        self, start_point: QPointF, end_point: QPointF, component_rect: QRectF, intersection_point: QPointF, line: QLineF
    ) -> List[QPointF]:
        """Create vertical detour around components"""
        # if line if going from top to bottom, should consider top edge of component
        # if line if going from bottom to top, should consider bottom edge of component
        left_distance = abs(component_rect.left() -  intersection_point.x())
        right_distance = abs(component_rect.right() - intersection_point.x())
        if start_point.y() < end_point.y():
            p1 = QPointF(intersection_point.x(), component_rect.top() - self.clearance)
            if left_distance <= right_distance:
                p2 = QPointF(component_rect.left() - self.clearance, p1.y())
            else:
                p2 = QPointF(component_rect.right() + self.clearance, p1.y())
            p3 = QPointF(p2.x(), component_rect.bottom() + self.clearance)
            p4 = QPointF(p1.x(), p3.y())
            return [p1, p2, p3, p4]
        else:
            p1 = QPointF(intersection_point.x(), component_rect.bottom() + self.clearance)
            if left_distance < right_distance:
                p2 = QPointF(component_rect.left() - self.clearance, p1.y())
            else:
                p2 = QPointF(component_rect.right() + self.clearance, p1.y())
            p3 = QPointF(p2.x(), component_rect.top() - self.clearance)
            p4 = QPointF(p1.x(), p3.y())
            return [p1, p2, p3, p4]

    def _create_horizontal_detour(
        self, start_point: QPointF, end_point: QPointF, component_rect: QRectF, intersection_point: QPointF, line: QLineF
    ) -> List[QPointF]:
        """Create horizontal detour around components"""
        # if line if going from left to right, should consider left edge of component
        # if line if going from right to left, should consider right edge of component
        top_distance = abs(component_rect.top() - intersection_point.y())
        bottom_distance = abs(component_rect.bottom() - intersection_point.y())
        if start_point.x() < end_point.x():
            p1 = QPointF(component_rect.left() - self.clearance, intersection_point.y())
            if top_distance < bottom_distance:
                p2 = QPointF(p1.x(), component_rect.top() - self.clearance)
            else:
                p2 = QPointF(p1.x(), component_rect.bottom() + self.clearance)
            p3 = QPointF(component_rect.right() + self.clearance, p2.y())
            p4 = QPointF(p3.x(), p1.y())
            return [p1, p2, p3, p4]
        else:
            p1 = QPointF(component_rect.right() + self.clearance, intersection_point.y())
            if top_distance < bottom_distance:
                p2 = QPointF(p1.x(), component_rect.top() - self.clearance)
            else:
                p2 = QPointF(p1.x(), component_rect.bottom() + self.clearance)
            p3 = QPointF(component_rect.left() - self.clearance, p2.y())
            p4 = QPointF(p3.x(), p1.y())
            return [p1, p2, p3, p4]

    def _find_clear_detour_y(
        self, start_point: QPointF, end_point: QPointF, detour_x: float
    ) -> float:
        """Find a clear Y coordinate for vertical detour"""
        # Start with midpoint Y
        mid_y = (start_point.y() + end_point.y()) / 2

        # Try different Y levels to find one that doesn't intersect components
        for offset in range(0, 100, self.grid_size):
            for y in [mid_y - offset, mid_y + offset]:
                test_line = QLineF(detour_x, start_point.y(), detour_x, y)
                if not self._line_intersects_any_component(test_line):
                    return y

        return mid_y

    def _find_clear_detour_x(
        self, start_point: QPointF, end_point: QPointF, detour_y: float
    ) -> float:
        """Find a clear X coordinate for horizontal detour"""
        # Start with midpoint X
        mid_x = (start_point.x() + end_point.x()) / 2

        # Try different X levels to find one that doesn't intersect components
        for offset in range(0, 100, self.grid_size):
            for x in [mid_x - offset, mid_x + offset]:
                test_line = QLineF(start_point.x(), detour_y, x, detour_y)
                if not self._line_intersects_any_component(test_line):
                    return x

        return mid_x

    def _line_intersects_rect(self, line: QLineF, rect: QRectF) -> Optional[Tuple[QPointF, QLineF, str]]:
        """Check if a line intersects with a rectangle"""
        # Check if line endpoints are inside rect
        # if rect.contains(line.p1()) or rect.contains(line.p2()):
        #     return line.p1() if rect.contains(line.p1()) else line.p2()

        # Check if line intersects any of the rectangle's edges
        top_line = QLineF(rect.topLeft(), rect.topRight())
        right_line = QLineF(rect.topRight(), rect.bottomRight())
        bottom_line = QLineF(rect.bottomRight(), rect.bottomLeft())
        left_line = QLineF(rect.bottomLeft(), rect.topLeft())

        intersections = line.intersects(top_line)
        if intersections[0] == QLineF.BoundedIntersection:
            return intersections[1], top_line, 'top'
        intersections = line.intersects(right_line)
        if intersections[0] == QLineF.BoundedIntersection:
            return intersections[1], right_line, 'right'
        intersections = line.intersects(bottom_line)
        if intersections[0] == QLineF.BoundedIntersection:
            return intersections[1], bottom_line, 'bottom'
        intersections = line.intersects(left_line)
        if intersections[0] == QLineF.BoundedIntersection:
            return intersections[1], left_line, 'left'
        return None, None, None

    def get_path(self) -> QPainterPath:
        """Get the complete wire path as a QPainterPath"""
        path = QPainterPath()

        if not self.segments:
            return path

        # If connection was swapped, reverse the path
        if self._swapped:
            # Start at the end and go backwards
            path.moveTo(self.segments[-1])
            for point in reversed(self.segments[:-1]):
                path.lineTo(point)
        else:
            # Start at the beginning
            path.moveTo(self.segments[0])
            # Draw to each subsequent point
            for point in self.segments[1:]:
                path.lineTo(point)

        return path

    def add_intersection_bump(self, intersection_point: QPointF, direction: str):
        """Add a bump at wire intersection point - DISABLED for new approach"""
        # Bump logic disabled - new approach focuses on clean detours
        pass

    def clear_bumps(self):
        """Clear all intersection bumps"""
        self.intersection_bumps.clear()

    def get_segments(self) -> List[Tuple[QPointF, QPointF]]:
        """Get the wire segments as pairs of points"""
        if not self.segments or len(self.segments) < 2:
            return []

        segments = []
        for i in range(len(self.segments) - 1):
            segments.append((self.segments[i], self.segments[i + 1]))
        return segments

    def update_endpoints(self, start_point: QPointF, end_point: QPointF):
        """Update start and end points and recalculate path"""
        self.start_point = start_point
        self.end_point = end_point
        self.get_start_and_end_approach_points()
        self.segments.clear()
        self.intersection_bumps.clear()
        self._calculate_orthogonal_path()


class Wire(QGraphicsPathItem):
    """Enhanced wire connection between component pins with advanced routing"""

    def __init__(
        self,
        start_pin: ComponentPin,
        end_pin: Optional[ComponentPin] = None,
        scene=None,
    ):
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

        # Disable bounding rect display and geometry changes for cleaner appearance
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges, False)

        # Disable any default selection rectangle display
        self.setFlag(self.GraphicsItemFlag.ItemIsFocusable, False)

        # Wire path and routing
        self.wire_path = None
        self.avoided_components = []

        # Don't set initial path until we have both pins
        # Initialize wire path asynchronously to avoid main thread blocking
        self.wire_path = None
        self._calculation_in_progress = False

        # Start async calculation if both pins are available
        if self.start_pin and self.end_pin:
            self._start_async_calculation()

    def _start_async_calculation(self):
        """Start asynchronous wire path calculation using scene thread manager

        Uses "latest data wins" approach:
        - No mutex locks for maximum responsiveness
        - Old calculations are discarded when new ones start
        - Component positions read at calculation time (latest data)
        """
        if not self.scene or not hasattr(self.scene, "wire_thread_manager"):
            # Fallback to synchronous calculation if no thread manager
            self._calculate_path_sync()
            return

        if self._calculation_in_progress:
            return  # Already calculating

        self._calculation_in_progress = True

        # Generate unique wire ID
        wire_id = f"wire_{id(self)}"

        # Start async calculation (old calculations for this wire will be discarded)
        self.scene.wire_thread_manager.calculate_wire_async(
            wire_id,
            self.start_pin,
            self.end_pin,
            self.scene,
            self._on_calculation_complete,
        )

    def _on_calculation_complete(self, wire_id: str, wire_path):
        """Handle completed wire path calculation"""
        self._calculation_in_progress = False

        if wire_path:
            self.wire_path = wire_path
            # Update graphics
            self.setPath(wire_path.get_path())
            self.setPen(QPen(self.wire_color, self.wire_width))
            # Timing end for async calculation
            try:
                if hasattr(self, "_update_start_perf") and self._update_start_perf is not None:
                    elapsed_ms = (time.perf_counter() - self._update_start_perf) * 1000.0
                    start_ts = getattr(self, "_update_start_wall", None)
                    end_ts = datetime.now().strftime("%H:%M:%S.%f")
                    print(f"[Wire.update_path][{wire_id}] start={start_ts} end={end_ts} duration_ms={elapsed_ms:.2f}")
                    self._update_start_perf = None
                    self._update_start_wall = None
            except Exception:
                pass
            print(f"✅ Wire path calculated and updated for {wire_id}")
        else:
            print(f"❌ Wire path calculation failed for {wire_id}")
            # Fallback to simple straight line
            self._calculate_path_sync()

    def _calculate_path_sync(self):
        """Fallback synchronous path calculation"""
        try:
            start_wall = datetime.now().strftime("%H:%M:%S.%f")
            start_perf = time.perf_counter()
            start_pos = self.start_pin.get_connection_point()
            end_pos = self.end_pin.get_connection_point()
            self.wire_path = WirePath(
                start_pos, end_pos, self.start_pin, self.end_pin, self.scene
            )
            self.setPath(self.wire_path.get_path())
            self.setPen(QPen(self.wire_color, self.wire_width))
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            end_ts = datetime.now().strftime("%H:%M:%S.%f")
            print(f"[Wire._calculate_path_sync] start={start_wall} end={end_ts} duration_ms={elapsed_ms:.2f}")
        except Exception as e:
            import traceback
            print(f"Error in sync wire calculation: {e}")
            print(traceback.format_exc())

    def update_path(self, temp_end_pos: Optional[QPointF] = None):
        """Update wire path position and routing"""
        start_pos = self.start_pin.get_connection_point()

        if self.end_pin:
            # Permanent wire with end pin
            end_pos = self.end_pin.get_connection_point()
            self.setPen(QPen(self.wire_color, self.wire_width))
        elif temp_end_pos:
            # Temporary wire being drawn - use sync calculation for immediate feedback
            end_pos = temp_end_pos
            self.setPen(QPen(self.temp_color, self.wire_width))
            # Timing for temporary path calculation
            start_wall = datetime.now().strftime("%H:%M:%S.%f")
            start_perf = time.perf_counter()
            self._calculate_optimal_path(start_pos, end_pos)
            if self.wire_path:
                self.setPath(self.wire_path.get_path())
            elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
            end_ts = datetime.now().strftime("%H:%M:%S.%f")
            print(f"[Wire.update_path:temp] start={start_wall} end={end_ts} duration_ms={elapsed_ms:.2f}")
            return
        else:
            return

        # Check if position actually changed to avoid unnecessary recalculations
        if (
            hasattr(self, "_last_start_pos")
            and hasattr(self, "_last_end_pos")
            and self._last_start_pos == start_pos
            and self._last_end_pos == end_pos
        ):
            return  # No change, skip update

        # Store current positions for next comparison
        self._last_start_pos = start_pos
        self._last_end_pos = end_pos

        # Use async calculation for permanent wires
        if not self._calculation_in_progress:
            # Record timing start for async update
            self._update_start_wall = datetime.now().strftime("%H:%M:%S.%f")
            self._update_start_perf = time.perf_counter()
            self._start_async_calculation()

    def _calculate_optimal_path(self, start_pos: QPointF, end_pos: QPointF):
        """Calculate optimal wire path avoiding components and other wires"""
        # Start with smart perpendicular routing
        self.wire_path = WirePath(
            start_pos, end_pos, self.start_pin, self.end_pin, self.scene
        )

        # Clear old intersection bumps before recalculating
        if self.wire_path:
            self.wire_path.intersection_bumps.clear()

        # Only handle wire intersections for permanent wires (not temporary ones being drawn)
        if not self.is_temporary:
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
                hasattr(item, "component_type")  # ComponentWithPins
                or hasattr(item, "name")
                and hasattr(item, "rect")  # Graphics items with name and rect
                or (
                    hasattr(item, "boundingRect") and not hasattr(item, "is_temporary")
                )  # Items with bounding rect but not temporary
            )

            # Make sure it's not the current wire's parent component
            if is_component and item != self.start_pin.parent_component:
                components.append(item)

        # Only run collision detection if there are components to avoid
        if not components:
            return

        # Check each segment for collisions
        segments = self.wire_path.get_segments()
        if not segments:
            return

        new_segments: List[Tuple[QPointF, QPointF]] = []
        for segment_start, segment_end in segments:
            if self._segment_collides_with_components(
                segment_start, segment_end, components
            ):
                # Reroute this segment to avoid collision
                rerouted_segments = self._reroute_segment_around_components(
                    segment_start, segment_end, components
                )
                new_segments.extend(rerouted_segments)
            else:
                new_segments.append((segment_start, segment_end))

        # Convert rerouted segments back to a list of points
        rebuilt_points: List[QPointF] = []
        if new_segments:
            # Start with the first segment's start
            rebuilt_points.append(new_segments[0][0])
            for seg_start, seg_end in new_segments:
                if not rebuilt_points[-1] == seg_start:
                    rebuilt_points.append(seg_start)
                if not rebuilt_points[-1] == seg_end:
                    rebuilt_points.append(seg_end)

        # Update wire path with rebuilt point list (maintains invariant: points list)
        if rebuilt_points:
            self.wire_path.segments = rebuilt_points

    def _segment_collides_with_components(
        self, start: QPointF, end: QPointF, components: list
    ) -> bool:
        """Check if a line segment collides with any component"""
        for component in components:
            if hasattr(component, "boundingRect"):
                rect = component.boundingRect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height(),
                )

                # Check if line segment intersects with component rectangle
                if self._line_intersects_rect(start, end, component_rect):
                    return True
            elif hasattr(component, "rect"):
                # Handle QGraphicsRectItem components
                rect = component.rect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height(),
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
            abs(end.y() - start.y()),
        )

        return rect.intersects(line_rect)

    def _reroute_segment_around_components(
        self, start: QPointF, end: QPointF, components: list
    ) -> List[Tuple[QPointF, QPointF]]:
        """Reroute a segment to avoid components by adding perpendicular detours"""
        # Find the component that's blocking this segment
        blocking_component = None
        for component in components:
            if hasattr(component, "boundingRect"):
                rect = component.boundingRect()
                component_rect = QRectF(
                    component.pos().x() + rect.x(),
                    component.pos().y() + rect.y(),
                    rect.width(),
                    rect.height(),
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
            rect.height(),
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
                (QPointF(end.x(), detour_y), end),
            ]
        else:
            # Vertical segment - add horizontal detour
            detour_x = component_rect.right() + 20  # 20px to the right of component

            # Create three segments: start to detour, detour across, detour to end
            segments = [
                (start, QPointF(detour_x, start.y())),
                (QPointF(detour_x, start.y()), QPointF(detour_x, end.y())),
                (QPointF(detour_x, end.y()), end),
            ]

        return segments

    def _handle_wire_intersections(self):
        """Handle intersections with other wires by adding bumps"""
        if not self.scene:
            return

        # Get all other wires in the scene
        other_wires = []
        for item in self.scene.items():
            # Check if this is a wire (not a component, not a pin)
            is_wire = (
                isinstance(item, Wire)  # Enhanced wire
                or hasattr(item, "is_temporary")  # Any item with is_temporary flag
                or hasattr(item, "start_pin")
                and hasattr(item, "end_pin")  # Items with pins
            )

            if is_wire and item != self:
                other_wires.append(item)

        # Only process intersections if there are other wires
        if not other_wires:
            return

        # Process intersections with other wires
        for other_wire in other_wires:
            # Check if the other wire has a path to analyze
            if hasattr(other_wire, "wire_path") and other_wire.wire_path:
                intersection_data = self._find_wire_intersections_with_angles(
                    other_wire
                )
                if intersection_data:
                    for point, direction in intersection_data:
                        self.wire_path.add_intersection_bump(point, direction)

    def _find_wire_intersections_with_angles(
        self, other_wire
    ) -> List[Tuple[QPointF, str]]:
        """Find intersection points between this wire and another wire with angle-based bump logic"""
        intersections = []

        if not self.wire_path or not other_wire.wire_path:
            return intersections

        # Calculate the overall angle of this wire relative to horizontal
        this_wire_angle = self._calculate_wire_angle()

        # Calculate the overall angle of the other wire relative to horizontal
        other_wire_angle = self._calculate_wire_angle_for_wire(other_wire)

        # Check each segment of this wire against each segment of the other wire
        for i, (seg1_start, seg1_end) in enumerate(self.wire_path.get_segments()):
            for j, (seg2_start, seg2_end) in enumerate(other_wire.wire_path.get_segments()):
                intersection = self._segment_intersection(
                    seg1_start, seg1_end, seg2_start, seg2_end
                )
                if intersection:
                    # Determine direction for bump
                    direction = (
                        "horizontal"
                        if abs(seg1_end.y() - seg1_start.y()) < 1
                        else "vertical"
                    )

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
        first_point = self.wire_path.segments[0]
        last_point = self.wire_path.segments[-1]

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
        if (
            not hasattr(other_wire, "wire_path")
            or not other_wire.wire_path
            or not other_wire.wire_path.segments
        ):
            return 0.0

        # Use the first and last points to determine overall direction
        first_point = other_wire.wire_path.segments[0]
        last_point = other_wire.wire_path.segments[-1]

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

    def _segment_intersection(
        self,
        seg1_start: QPointF,
        seg1_end: QPointF,
        seg2_start: QPointF,
        seg2_end: QPointF,
    ) -> Optional[QPointF]:
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

    def complete_wire(self, end_pin: ComponentPin) -> bool:
        """Complete the wire connection"""
        if end_pin == self.start_pin:
            return False  # Can't connect to self

        self.end_pin = end_pin
        self.is_temporary = False

        # Now create the wire path since we have both pins
        self.update_path()

        # Now that the wire is permanent, calculate intersections
        if self.wire_path:
            self._handle_wire_intersections()
            # Update the graphics with the final path including bumps
            self.setPath(self.wire_path.get_path())

        return True

    def update_wire_position(self):
        """Update wire position when pins move"""
        if self.start_pin and self.end_pin:
            self.update_path()

    def update_wire_position_dragging(self):
        """Update wire during component dragging with real-time orthogonal routing"""
        if not self.start_pin or not self.end_pin:
            return

        # During dragging, use real-time orthogonal routing for immediate feedback
        start_pos = self.start_pin.get_connection_point()
        end_pos = self.end_pin.get_connection_point()

        # Create new WirePath with orthogonal routing (fast calculation)
        self.wire_path = WirePath(
            start_pos,
            end_pos,
            self.start_pin,
            self.end_pin,
            self.scene,
            calculate_now=True,
        )

        # Update graphics immediately
        if self.wire_path:
            self.setPath(self.wire_path.get_path())

    def update_wire_position_lightweight(self):
        """Lightweight update that only recalculates wire positions without full routing"""
        if not self.start_pin or not self.end_pin or not self.wire_path:
            return

        start_pos = self.start_pin.get_connection_point()
        end_pos = self.end_pin.get_connection_point()

        # Check if position actually changed
        if (
            hasattr(self, "_last_start_pos")
            and hasattr(self, "_last_end_pos")
            and self._last_start_pos == start_pos
            and self._last_end_pos == end_pos
        ):
            return  # No change, skip update

        # Store current positions
        self._last_start_pos = start_pos
        self._last_end_pos = end_pos

        # Use async calculation for lightweight updates
        if not self._calculation_in_progress:
            self._start_async_calculation()

    def update_wire_position_final(self):
        """Update wire after dragging is complete with full orthogonal routing"""
        if not self.start_pin or not self.end_pin:
            return

        # Final calculation with complete orthogonal routing
        start_pos = self.start_pin.get_connection_point()
        end_pos = self.end_pin.get_connection_point()

        # Create new WirePath with full orthogonal routing
        self.wire_path = WirePath(
            start_pos,
            end_pos,
            self.start_pin,
            self.end_pin,
            self.scene,
            calculate_now=True,
        )

        # Update graphics with final path
        if self.wire_path:
            self.setPath(self.wire_path.get_path())

    def force_intersection_recalculation(self):
        """Force recalculation of intersections and bumps"""
        if not self.wire_path:
            return

        # Clear old bumps
        self.wire_path.intersection_bumps.clear()

        # Recalculate intersections
        self._handle_wire_intersections()

        # Update the graphics
        self.setPath(self.wire_path.get_path())

    def contextMenuEvent(self, event):
        """Handle right-click on wire"""
        menu = QMenu()
        delete_action = menu.addAction("Delete Wire")

        action = menu.exec(event.screenPos())

        if action == delete_action:
            self.scene.remove_wire(self)

    def itemChange(self, change, value):
        """Handle item state changes, particularly selection"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            # Change line format based on selection state
            if value:  # Selected
                # Change to dot-dash line when selected
                current_pen = self.pen()
                current_pen.setStyle(Qt.PenStyle.DashDotLine)
                self.setPen(current_pen)
            else:  # Not selected
                # Restore normal line when deselected
                if self.is_temporary:
                    self.setPen(QPen(self.temp_color, self.wire_width))
                else:
                    self.setPen(QPen(self.wire_color, self.wire_width))

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

    def boundingRect(self):
        """Override boundingRect to return a minimal rectangle that covers only the wire path"""
        if not self.wire_path:
            return super().boundingRect()

        # Get the wire path
        path = self.wire_path.get_path()
        if path.isEmpty():
            return super().boundingRect()

        # Return the bounding rectangle of the actual path
        # This eliminates the default bounding rect display
        return path.boundingRect()

    def paint(self, painter, option, widget):
        """Override paint to ensure no selection rectangle is drawn"""
        # Don't draw selection rectangle or bounding rect
        # Just draw the wire path itself
        if self.wire_path:
            path = self.wire_path.get_path()
            if not path.isEmpty():
                painter.setPen(self.pen())
                painter.drawPath(path)
