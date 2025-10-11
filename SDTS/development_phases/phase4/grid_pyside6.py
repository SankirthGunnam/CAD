"""
Grid-based Pathfinding Demo with PySide6

A grid-based pathfinding application using A* algorithm with interactive
obstacle placement and real-time pathfinding visualization.
"""

from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                               QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem,
                               QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                               QLabel, QMessageBox, QSlider)
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QObject
import sys
import heapq
import math
from typing import List, Tuple, Set, Optional, Dict


class GridCell(QGraphicsRectItem):
    """Represents a single cell in the grid."""
    
    CELL_TYPES = {
        'empty': QColor(255, 255, 255),      # White
        'obstacle': QColor(0, 0, 0),         # Black
        'start': QColor(0, 0, 255),          # Blue
        'goal': QColor(0, 255, 0),           # Green
        'visited': QColor(255, 255, 0),      # Yellow
        'path': QColor(255, 0, 0),           # Red
        'current': QColor(147, 112, 219),    # Purple
    }
    
    def __init__(self, x: int, y: int, size: int, grid_x: int, grid_y: int):
        super().__init__(x, y, size, size)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.cell_type = 'empty'
        self.setPen(QPen(QColor(128, 128, 128), 1))  # Gray border
        self.setBrush(QBrush(self.CELL_TYPES['empty']))
        
    def set_type(self, cell_type: str) -> None:
        """Set the cell type and update its appearance."""
        if cell_type in self.CELL_TYPES:
            self.cell_type = cell_type
            self.setBrush(QBrush(self.CELL_TYPES[cell_type]))
            
    def is_obstacle(self) -> bool:
        """Check if this cell is an obstacle."""
        return self.cell_type == 'obstacle'
        
    def is_empty(self) -> bool:
        """Check if this cell is empty."""
        return self.cell_type == 'empty'


class AStarPathfinder:
    """A* pathfinding algorithm implementation."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.directions = [
            (0, 1), (1, 0), (0, -1), (-1, 0),      # Cardinal directions
            (1, 1), (1, -1), (-1, 1), (-1, -1)     # Diagonal directions
        ]
        
    def is_valid_position(self, pos: Tuple[int, int], obstacles: Set[Tuple[int, int]]) -> bool:
        """Check if a position is valid (within bounds and not an obstacle)."""
        x, y = pos
        return (0 <= x < self.width and 
                0 <= y < self.height and 
                pos not in obstacles)
    
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Euclidean distance heuristic."""
        return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)
    
    def get_neighbors(self, pos: Tuple[int, int], obstacles: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions."""
        neighbors = []
        for dx, dy in self.directions:
            new_pos = (pos[0] + dx, pos[1] + dy)
            if self.is_valid_position(new_pos, obstacles):
                neighbors.append(new_pos)
        return neighbors
    
    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int], 
                  obstacles: Set[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
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
                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
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


class GridScene(QGraphicsScene):
    """Custom graphics scene for the grid."""
    
    def __init__(self, width: int, height: int, cell_size: int):
        super().__init__()
        self.grid_width = width
        self.grid_height = height
        self.cell_size = cell_size
        self.cells: List[List[GridCell]] = []
        self.start_pos: Optional[Tuple[int, int]] = None
        self.goal_pos: Optional[Tuple[int, int]] = None
        self.obstacles: Set[Tuple[int, int]] = set()
        self.pathfinder = AStarPathfinder(width, height)
        
        self._create_grid()
        self._add_default_components()
        
    def _create_grid(self) -> None:
        """Create the grid of cells."""
        self.cells = []
        for y in range(self.grid_height):
            row = []
            for x in range(self.grid_width):
                cell = GridCell(x * self.cell_size, y * self.cell_size, 
                               self.cell_size, x, y)
                row.append(cell)
                self.addItem(cell)
            self.cells.append(row)
            
    def _add_default_components(self) -> None:
        """Add some default components to make the grid interesting."""
        # Add some default obstacles
        default_obstacles = [
            (10, 5), (11, 5), (12, 5), (13, 5),
            (8, 8), (9, 8), (10, 8),
            (15, 10), (16, 10), (17, 10),
            (5, 15), (6, 15), (7, 15), (8, 15),
            (12, 18), (13, 18), (14, 18), (15, 18),
        ]
        
        for x, y in default_obstacles:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                self.cells[y][x].set_type('obstacle')
                self.obstacles.add((x, y))
                
        # Set default start and goal positions
        self.set_start_position(2, 2)
        self.set_goal_position(18, 18)
        
    def set_start_position(self, x: int, y: int) -> bool:
        """Set the start position."""
        if (0 <= x < self.grid_width and 0 <= y < self.grid_height and 
            not self.cells[y][x].is_obstacle()):
            
            # Clear previous start
            if self.start_pos:
                old_x, old_y = self.start_pos
                self.cells[old_y][old_x].set_type('empty')
                
            self.start_pos = (x, y)
            self.cells[y][x].set_type('start')
            return True
        return False
        
    def set_goal_position(self, x: int, y: int) -> bool:
        """Set the goal position."""
        if (0 <= x < self.grid_width and 0 <= y < self.grid_height and 
            not self.cells[y][x].is_obstacle()):
            
            # Clear previous goal
            if self.goal_pos:
                old_x, old_y = self.goal_pos
                self.cells[old_y][old_x].set_type('empty')
                
            self.goal_pos = (x, y)
            self.cells[y][x].set_type('goal')
            return True
        return False
        
    def toggle_obstacle(self, x: int, y: int) -> bool:
        """Toggle obstacle at the given position."""
        if (0 <= x < self.grid_width and 0 <= y < self.grid_height and
            (x, y) != self.start_pos and (x, y) != self.goal_pos):
            
            if self.cells[y][x].is_obstacle():
                self.cells[y][x].set_type('empty')
                self.obstacles.discard((x, y))
            else:
                self.cells[y][x].set_type('obstacle')
                self.obstacles.add((x, y))
            return True
        return False
        
    def clear_grid(self) -> None:
        """Clear all obstacles and reset start/goal positions."""
        for row in self.cells:
            for cell in row:
                cell.set_type('empty')
                
        self.obstacles.clear()
        self.start_pos = None
        self.goal_pos = None
        
    def find_path(self) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Find path using A* algorithm."""
        if self.start_pos and self.goal_pos:
            return self.pathfinder.find_path(self.start_pos, self.goal_pos, self.obstacles)
        return [], []
        
    def visualize_search(self, visited: List[Tuple[int, int]], 
                        path: List[Tuple[int, int]]) -> None:
        """Visualize the search process and final path."""
        # Clear previous visualization
        for row in self.cells:
            for cell in row:
                if cell.cell_type in ['visited', 'path', 'current']:
                    if cell.cell_type == 'visited':
                        cell.set_type('empty')
                    elif cell.cell_type == 'path':
                        cell.set_type('empty')
                        
        # Mark visited cells
        for x, y in visited:
            if (x, y) != self.start_pos and (x, y) != self.goal_pos:
                self.cells[y][x].set_type('visited')
                
        # Mark path cells
        for x, y in path:
            if (x, y) != self.start_pos and (x, y) != self.goal_pos:
                self.cells[y][x].set_type('path')


class GridMainWindow(QMainWindow):
    """Main window for the grid pathfinding application."""
    
    def __init__(self):
        super().__init__()
        self.grid_width = 20
        self.grid_height = 20
        self.cell_size = 25
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Grid Pathfinding Demo - A* Algorithm")
        self.setGeometry(100, 100, 800, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Create graphics view
        self.scene = GridScene(self.grid_width, self.grid_height, self.cell_size)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self.view)
        
        # Set scene rect to fit the grid
        self.scene.setSceneRect(0, 0, 
                               self.grid_width * self.cell_size,
                               self.grid_height * self.cell_size)
                               
    def _create_control_panel(self) -> QWidget:
        """Create the control panel with buttons and information."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Control buttons
        self.find_path_btn = QPushButton("Find Path (A*)")
        self.find_path_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        
        self.clear_btn = QPushButton("Clear Grid")
        self.clear_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        
        # Information label
        self.info_label = QLabel("Click to place Start (Blue), Goal (Green), or Obstacles (Black)")
        self.info_label.setStyleSheet("QLabel { color: #333; font-size: 12px; }")
        
        layout.addWidget(self.find_path_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.reset_btn)
        layout.addStretch()
        layout.addWidget(self.info_label)
        
        return panel
        
    def _setup_connections(self) -> None:
        """Set up signal connections."""
        self.find_path_btn.clicked.connect(self._find_path)
        self.clear_btn.clicked.connect(self._clear_grid)
        self.reset_btn.clicked.connect(self._reset_to_default)
        
        # Connect mouse events
        self.scene.selectionChanged.connect(self._on_selection_changed)
        
    def _on_selection_changed(self) -> None:
        """Handle selection changes in the scene."""
        pass
        
    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Get the cell position from the scene
            scene_pos = self.view.mapToScene(event.pos())
            grid_x = int(scene_pos.x() // self.cell_size)
            grid_y = int(scene_pos.y() // self.cell_size)
            
            if (0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height):
                # Try to set start, goal, or toggle obstacle
                if not self.scene.start_pos:
                    self.scene.set_start_position(grid_x, grid_y)
                    self.info_label.setText("Goal placed! Click to place Goal (Green) or Obstacles (Black)")
                elif not self.scene.goal_pos:
                    self.scene.set_goal_position(grid_x, grid_y)
                    self.info_label.setText("Setup complete! Click to place Obstacles (Black) or Find Path")
                else:
                    self.scene.toggle_obstacle(grid_x, grid_y)
                    
        super().mousePressEvent(event)
        
    def _find_path(self) -> None:
        """Find and visualize the path."""
        if not self.scene.start_pos or not self.scene.goal_pos:
            QMessageBox.warning(self, "Warning", "Please set both start and goal positions!")
            return
            
        path, visited = self.scene.find_path()
        
        if path:
            self.scene.visualize_search(visited, path)
            self.info_label.setText(f"Path found! Length: {len(path)} steps, Visited: {len(visited)} cells")
        else:
            QMessageBox.information(self, "No Path", "No valid path found between start and goal!")
            
    def _clear_grid(self) -> None:
        """Clear the entire grid."""
        self.scene.clear_grid()
        self.info_label.setText("Grid cleared! Click to place Start (Blue), Goal (Green), or Obstacles (Black)")
        
    def _reset_to_default(self) -> None:
        """Reset to default configuration."""
        self.scene.clear_grid()
        self.scene._add_default_components()
        self.info_label.setText("Reset to default! Click to place Start (Blue), Goal (Green), or Obstacles (Black)")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Grid Pathfinding Demo")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = GridMainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
