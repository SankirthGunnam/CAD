from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QPen
from PySide6.QtCore import Qt, QPointF, QLineF, QRectF
import sys


class GraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        # Small step size for detours
        self.small_step = 10.0

        # Define pins (start and end points)
        self.start_pin = QPointF(50, 50)  # Start pin
        self.end_pin = QPointF(180, 350)  # End pin

        # Define obstacles (components as rectangles)
        self.obstacles = [
            QRectF(100, 100, 50, 50),  # Obstacle 1
            QRectF(150, 200, 50, 50),  # Obstacle 2
        ]

        # Visualize pins and obstacles
        self.scene.addEllipse(
            self.start_pin.x() - 5, self.start_pin.y() - 5, 10, 10, QPen(Qt.blue), Qt.blue)
        self.scene.addEllipse(
            self.end_pin.x() - 5, self.end_pin.y() - 5, 10, 10, QPen(Qt.green), Qt.green)
        for rect in self.obstacles:
            self.scene.addRect(rect, QPen(Qt.red, 2))

        # Find and draw the path using DFS
        visited = set()
        path = self.dfs(self.start_pin, self.end_pin, [
                        self.start_pin], visited, depth=0)
        if path:
            self.draw_path(path)
        else:
            print("No valid path found")

    def get_neighbors(self, current):
        """Get neighbors of a point."""
        neighbors = []
        for dx in [-self.small_step, 0, self.small_step]:
            for dy in [-self.small_step, 0, self.small_step]:
                neighbors.append(QPointF(current.x() + dx, current.y() + dy))
        return neighbors

    def dfs(self, current, end, path, visited, depth):
        # Limit recursion depth to prevent stack overflow
        if depth > 100:
            return None

        current_tuple = (current.x(), current.y())
        if current_tuple in visited:
            return None
        visited.add(current_tuple)

        if current == end:
            return path

        # Determine relative position for preferred directions
        dx = end.x() - current.x()
        dy = end.y() - current.y()

        # Check if we're close enough to the end point
        distance_to_end = (dx * dx + dy * dy) ** 0.5
        if distance_to_end < self.small_step:
            return path + [end]

        # Preferred alignments: try long horizontal/vertical projections first
        alignment_attempts = []
        if abs(dx) > 0:  # Try to align x (horizontal projection)
            target_point = QPointF(end.x(), current.y())
            segment = QLineF(current, target_point)
            intersection_point = self.does_segment_intersect_obstacles(segment)
            if intersection_point:
                alignment_attempts.append(intersection_point)
            else:
                alignment_attempts.append(target_point)
        if abs(dy) > 0:  # Try to align y (vertical projection)
            target_point = QPointF(current.x(), end.y())
            segment = QLineF(current, target_point)
            intersection_point = self.does_segment_intersect_obstacles(segment)
            if intersection_point:
                alignment_attempts.append(intersection_point)
            else:
                alignment_attempts.append(target_point)

        # Try long alignment jumps (prioritize based on larger delta)
        if abs(dx) > abs(dy):
            alignment_attempts = alignment_attempts[:1] + alignment_attempts[1:] if len(
                alignment_attempts) > 1 else alignment_attempts
        for next_point in alignment_attempts:
            next_tuple = (next_point.x(), next_point.y())
            if next_tuple not in visited:
                new_path = path + [next_point]
                result = self.dfs(next_point, end, new_path,
                                  visited, depth + 1)
                if result:
                    return result

        # If long jumps blocked, fall back to small steps in orthogonal directions
        directions = []
        if dx > 0:
            directions.append((self.small_step, 0))  # Right
        elif dx < 0:
            directions.append((-self.small_step, 0))  # Left
        if dy > 0:
            directions.append((0, self.small_step))  # Down
        elif dy < 0:
            directions.append((0, -self.small_step))  # Up
        # Add secondary directions
        secondary = [(self.small_step, 0), (-self.small_step, 0),
                     (0, self.small_step), (0, -self.small_step)]
        directions += [d for d in secondary if d not in directions]

        for dir_dx, dir_dy in directions:
            next_point = QPointF(current.x() + dir_dx, current.y() + dir_dy)
            segment = QLineF(current, next_point)
            next_tuple = (next_point.x(), next_point.y())
            if (not self.does_segment_intersect_obstacles(segment) and
                self.is_point_valid(next_point) and
                    next_tuple not in visited):
                new_path = path + [next_point]
                result = self.dfs(next_point, end, new_path,
                                  visited, depth + 1)
                if result:
                    return result

        # Remove current point from visited set when backtracking
        visited.remove(current_tuple)
        return None  # No path in this branch

    def is_point_valid(self, point):
        """Check if a point is not inside any obstacle."""
        for rect in self.obstacles:
            if rect.contains(point):
                return False
        return True

    def does_segment_intersect_obstacles(self, segment):
        """Check if a line segment intersects any obstacle."""
        for rect in self.obstacles:
            intersects, intersection_point = self.line_intersects_rect(segment, rect)
            if intersects:
                return intersection_point
        return None

    def line_intersects_rect(self, line, rect):
        """Check if a line segment intersects a rectangle."""
        # Get line endpoints
        p1 = line.p1()
        p2 = line.p2()

        # Check if either endpoint is inside the rectangle
        if rect.contains(p1) or rect.contains(p2):
            return True, None

        # Check if line intersects any of the rectangle's edges
        bounded_intersection_points = self.get_intersection_points(rect, line, QLineF.BoundedIntersection)
        if bounded_intersection_points:
            return True, bounded_intersection_points
        unbounded_intersection_points = self.get_intersection_points(rect, line, QLineF.UnboundedIntersection)
        if unbounded_intersection_points:
            return True, unbounded_intersection_points
        return False, None

    def get_intersection_points(self, rect, line, intersection_type=QLineF.BoundedIntersection):
        intersection_points = []
        for edge_index, edge in enumerate([(rect.topLeft(), rect.topRight()),
                     (rect.bottomLeft(), rect.bottomRight()),
                     (rect.topLeft(), rect.bottomLeft()),
                     (rect.topRight(), rect.bottomRight())]):
            edge_line = QLineF(edge[0], edge[1])
            intersection_point = line.intersects(edge_line)
            if intersection_point[0] == intersection_type and intersection_type == QLineF.BoundedIntersection:
                if edge_index == 0:
                    intersection_points.append(QPointF(intersection_point[1].x(), edge[0].y() - 5))
                elif edge_index == 1:
                    intersection_points.append(QPointF(edge[1].x(), intersection_point[1].y() + 5))
                elif edge_index == 2:
                    intersection_points.append(QPointF(edge[0].x() - 5, intersection_point[1].y()))
                elif edge_index == 3:
                    intersection_points.append(QPointF(edge[1].x() + 5, intersection_point[1].y()))
            elif intersection_point[0] == intersection_type and intersection_type == QLineF.UnboundedIntersection:
                if abs(edge_line.angleTo(line)) == 90 and edge[0].x() <= intersection_point[1].x() <= edge[1].x() and edge[0].y() <= intersection_point[1].y() <= edge[1].y():
                    if edge_index == 0:
                        intersection_points.append(QPointF(intersection_point[1].x(), edge[0].y() - 5))
                    elif edge_index == 1:
                        intersection_points.append(QPointF(edge[1].x(), intersection_point[1].y() + 5))
                    elif edge_index == 2:
                        intersection_points.append(QPointF(edge[0].x() - 5, intersection_point[1].y()))
                    elif edge_index == 3:
                        intersection_points.append(QPointF(edge[1].x() + 5, intersection_point[1].y()))
        if intersection_points:
            # Find the intersection point closest to the end of the line
            intersection_distances = [((ip.x() - line.p1().x()) ** 2 + (ip.y() - line.p1().y()) ** 2) ** 0.5 for ip in intersection_points]
            return intersection_points[intersection_distances.index(min(intersection_distances))]

        return None


    def draw_path(self, path):
        """Draw the path as a series of line segments."""
        pen = QPen(Qt.black, 2)
        for i in range(len(path) - 1):
            line = QLineF(path[i], path[i + 1])
            self.scene.addLine(line, pen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = GraphicsView()
    view.resize(400, 400)
    view.show()
    sys.exit(app.exec())
