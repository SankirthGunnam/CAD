"""
Pathfinding Demo with PySide6

A demonstration of pathfinding algorithms with obstacle avoidance
for CAD wire routing applications.
"""

from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsRectItem, QMainWindow, QWidget,
                        QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsPathItem)
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from PySide6.QtCore import Qt, QPointF, QLineF, QRectF
import sys
import math
import heapq
from typing import List, Tuple, Optional, Set, Dict


class MovableObstacle(QGraphicsRectItem):
    """Custom draggable obstacle rectangle."""

    def __init__(self, rect: QRectF):
        super().__init__(rect)
        self.setPen(QPen(Qt.red, 2))
        # Semi-transparent red
        self.setBrush(QBrush(QColor(255, 100, 100, 128)))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)

    def mouseMoveEvent(self, event) -> None:
        super().mouseMoveEvent(event)
        # print('mouseMoveEvent', self.rect(), event.scenePos(), self.pos())
        # self.setPos(event.scenePos())

class AStarPathfinder:
    """A* pathfinding algorithm implementation."""

    def __init__(self, width: int, height: int, unit: int):
        self.width = width
        self.height = height
        self.unit = unit
        self.directions = [
            (0, self.unit), (self.unit, 0), 
            (0, -self.unit), (-self.unit, 0),      # Cardinal directions
            (self.unit, self.unit), (self.unit, -self.unit),
            (-self.unit, self.unit), (-self.unit, -self.unit)     # Diagonal directions
        ]

    def is_valid_position(self, pos: Tuple[int, int], obstacles: List[QRectF]) -> bool:
        """Check if a position is valid (within bounds and not an obstacle)."""
        x, y = pos
        if (0 <= x < self.width and 0 <= y < self.height):
            for obstacle in obstacles:
                if obstacle.contains(QPointF(x, y)):
                    return False
        return True

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic."""
        return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

    def get_neighbors(self, pos: Tuple[int, int], obstacles: List[QRectF]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions."""
        neighbors = []
        for dx, dy in self.directions:
            new_pos = (pos[0] + dx, pos[1] + dy)
            if self.is_valid_position(new_pos, obstacles):
                neighbors.append(new_pos)
        return neighbors

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int],
                  obstacles: List) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Find path using A* algorithm."""
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        cost_so_far: Dict[Tuple[int, int], float] = {start: 0}
        visited: List[Tuple[int, int]] = []

        while frontier:
            current = heapq.heappop(frontier)[1]
            visited.append(current)

            if current == goal:
                break

            for next_pos in self.get_neighbors(current, obstacles):
                # Calculate movement cost (diagonal moves cost more)
                dx, dy = next_pos[0] - current[0], next_pos[1] - current[1]
                move_cost = 1.414 * self.unit if abs(dx) + abs(dy) == 2 * self.unit else self.unit
                # move_cost = 1.414 if abs(dx) + abs(dy) == 2  else 1.0
                new_cost = cost_so_far[current] + move_cost

                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + self.heuristic(goal, next_pos)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        # Reconstruct path
        path = []
        if goal in came_from:
            current = goal
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()

        return path, visited


class PathfindingDemo(QMainWindow):
    """Main pathfinding demonstration class."""

    def __init__(self):
        super().__init__()
        self.grid_unit = 50

        # Define start and end points (aligned to grid)
        self.start_point = (50, 50)    # Grid position (1, 1)
        self.end_point = (500, 350)    # Grid position (10, 7)
        self.scene_width = 600
        self.scene_height = 450
        self.pathfinder = AStarPathfinder(self.scene_width, self.scene_height, self.grid_unit)
        self._setup_ui()
        self._create_obstacles()
        self._visualize_elements()
        self._find_and_draw_path()

    def _setup_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Pathfinding Demo - Movable Obstacles")
        self.setGeometry(100, 100, 700, 550)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout(central_widget)

        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.scene_width, self.scene_height)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self.view)

        # Add grid lines
        self._draw_grid_lines()

    def _create_control_panel(self) -> QWidget:
        """Create the control panel with buttons."""
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Redraw path button
        self.redraw_btn = QPushButton("Redraw Path")
        self.redraw_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.redraw_btn.clicked.connect(self._redraw_path)

        # Clear path button
        self.clear_path_btn = QPushButton("Clear Path")
        self.clear_path_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
        self.clear_path_btn.clicked.connect(self._clear_path)

        # Information label
        self.info_label = QLabel(
            "Drag obstacles to move them, then click 'Redraw Path'")
        self.info_label.setStyleSheet(
            "QLabel { color: #333; font-size: 12px; }")

        layout.addWidget(self.redraw_btn)
        layout.addWidget(self.clear_path_btn)
        layout.addStretch()
        layout.addWidget(self.info_label)

        return panel

    def _draw_grid_lines(self) -> None:
        """Draw grid lines with unit size of 50."""
        grid_unit = self.grid_unit
        scene_rect = self.scene.sceneRect()

        # Create light gray pen for grid lines
        # Light gray, semi-transparent
        grid_pen = QPen(QColor(200, 200, 200, 100), 1)

        # Draw vertical grid lines
        x = 0
        while x <= scene_rect.width():
            line = self.scene.addLine(x, 0, x, scene_rect.height(), grid_pen)
            line.setZValue(-1)  # Place grid lines behind other items
            x += grid_unit

        # Draw horizontal grid lines
        y = 0
        while y <= scene_rect.height():
            line = self.scene.addLine(0, y, scene_rect.width(), y, grid_pen)
            line.setZValue(-1)  # Place grid lines behind other items
            y += grid_unit

    def _create_obstacles(self) -> None:
        """Create a challenging obstacle layout with movable obstacles aligned to grid."""
        obstacle_rects = [
            # Block direct path (aligned to grid)
            # Horizontal barrier at grid (2,2) to (5,2)
            QRectF(100, 50, 100, 100),
            # Vertical barrier at grid (4,2) to (4,4)
            # QRectF(200, 0, 20, 100),

            # # Create maze structure
            # QRectF(100, 50, 20, 100),     # Left wall at grid (2,1) to (2,3)
            # QRectF(100, 50, 150, 20),     # Top wall at grid (2,1) to (5,1)
            # QRectF(250, 50, 20, 100),     # Right wall at grid (5,1) to (5,3)

            # # Bottom maze section
            # # Bottom horizontal at grid (7,7) to (9,7)
            # QRectF(250, 300, 100, 20),
            # # QRectF(150, 250, 100, 20),    # Central horizontal at grid (3,5) to (5,5)
            # Left narrow passage at grid (1,4) to (1,6)
            QRectF(50, 250, 100, 100),
        ]

        # Create movable obstacle items
        for rect in obstacle_rects:
            obstacle_item = MovableObstacle(rect)
            self.scene.addItem(obstacle_item)

    def _visualize_elements(self) -> None:
        """Draw start point and end point."""
        # Draw start point (blue circle)
        start_brush = QBrush(Qt.blue)
        self.start_item = self.scene.addEllipse(
            self.start_point[0] - 6, self.start_point[1] - 6,
            12, 12, QPen(Qt.blue, 2), start_brush
        )

        # Draw end point (green circle)
        end_brush = QBrush(Qt.green)
        self.end_item = self.scene.addEllipse(
            self.end_point[0] - 6, self.end_point[1] - 6,
            12, 12, QPen(Qt.green, 2), end_brush
        )

    def _find_and_draw_path(self) -> None:
        """Find path and visualize it."""
        path, visited = self.pathfinder.find_path(
            self.start_point,
            self.end_point, 
            [i for i in self.scene.items() if isinstance(i, MovableObstacle)]
        )

        [print(i.rect(), i.pos()) for i in self.scene.items() if isinstance(i, MovableObstacle)]
        self._draw_path(path)

    def _draw_path(self, path: List[Tuple[int, int]]) -> None:
        """Draw the path as connected line segments."""
        # Clear existing path
        self._clear_path()

        if len(path) < 2:
            return

        pen = QPen(Qt.black, 3)
        painter_path = QPainterPath()
        painter_path.moveTo(QPointF(*path[0]))
        for i in range(1, len(path)):
            painter_path.lineTo(QPointF(*path[i]))
        self.scene.addPath(painter_path, pen)

    def _redraw_path(self) -> None:
        """Redraw the path with current obstacle positions."""
        # self.scene.clear()
        # obstacle_rects = [i.rect() for i in self.scene.items() if isinstance(i, MovableObstacle)]
        # for rect in obstacle_rects:
        #     obstacle_item = MovableObstacle(rect)
        #     self.scene.addItem(obstacle_item)

        self._find_and_draw_path()

    def _clear_path(self) -> None:
        """Clear the current path from the scene."""
        for item in self.scene.items():
            if isinstance(item, QGraphicsPathItem):
                self.scene.removeItem(item)

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Create and configure the main window
    demo = PathfindingDemo()
    demo.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
