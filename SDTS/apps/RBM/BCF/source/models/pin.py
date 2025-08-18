from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Pin:
    """Core pin model without UI dependencies"""

    x: float
    y: float
    name: str
    connections: List["Connection"]
    chip: Optional["ChipModel"] = None

    def __init__(self, x: float, y: float, name: str = ""):
        self.x = x
        self.y = y
        self.name = name
        self.connections = []
        self.chip = None
        self._id = id(self)  # Unique identifier for hashing

    def __hash__(self) -> int:
        """Make Pin hashable for use in dictionaries"""
        return self._id

    def __eq__(self, other) -> bool:
        """Equality comparison for dictionary use"""
        if not isinstance(other, Pin):
            return False
        return self._id == other._id

    def add_connection(self, connection: "Connection") -> None:
        """Add a connection to this pin"""
        if connection not in self.connections:
            self.connections.append(connection)

    def remove_connection(self, connection: "Connection") -> None:
        """Remove a connection from this pin"""
        if connection in self.connections:
            self.connections.remove(connection)

    def update_position(self, x: float, y: float) -> None:
        """Update the pin's position"""
        self.x = x
        self.y = y
