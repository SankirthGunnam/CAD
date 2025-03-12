# connection.py
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPainterPath, QColor, QPen
from a_star import a_star_pathfinding

class Connection(QGraphicsPathItem):
    def __init__(self, start_pin, end_pin, obstacles, grid_size=20):
        super().__init__()
        self.start_pin = start_pin
        self.end_pin = end_pin
        self.obstacles = obstacles
        self.grid_size = grid_size

        self.setPen(QPen(QColor("blue"), 2))
        self.update_path()

    def update_path(self):
        start_pos = self.start_pin.scenePos()
        end_pos = self.end_pin.scenePos()

        start = (round(start_pos.x() / self.grid_size) * self.grid_size,
                 round(start_pos.y() / self.grid_size) * self.grid_size)
        end = (round(end_pos.x() / self.grid_size) * self.grid_size,
               round(end_pos.y() / self.grid_size) * self.grid_size)

        path_points = a_star_pathfinding(start, end, self.obstacles, self.grid_size)

        if path_points:
            path = QPainterPath()
            path.moveTo(*path_points[0])
            for point in path_points[1:]:
                path.lineTo(*point)
            self.setPath(path)
