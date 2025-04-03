from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Pin:
    """Core pin model without UI dependencies"""

    x: float
    y: float
    name: str
    connections: List["Connection"]

    def __init__(self, x: float, y: float, name: str = ""):
        self.x = x
        self.y = y
        self.name = name
        self.connections = []

    def add_connection(self, connection: "Connection") -> None:
        """Add a connection to this pin"""
        if connection not in self.connections:
            self.connections.append(connection)

    def remove_connection(self, connection: "Connection") -> None:
        """Remove a connection from this pin"""
        if connection in self.connections:
            self.connections.remove(connection)
