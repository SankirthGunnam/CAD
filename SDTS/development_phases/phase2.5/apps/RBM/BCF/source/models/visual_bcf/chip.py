from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from apps.RBM.BCF.source.models.pin import Pin


@dataclass
class ChipModel:
    """Core chip model without UI dependencies"""

    name: str
    width: float
    height: float
    pins: List[Pin]
    properties: Dict[str, str]
    position: Tuple[float, float]

    def __init__(self, name: str = "Chip", width: float = 50, height: float = 50):
        self.name = name
        self.width = width
        self.height = height
        self.pins = []
        self.position = (0, 0)  # Default position
        self.properties = {
            "name": name,
            "type": "Chip",
            "width": str(width),
            "height": str(height),
            "function": "Generic Chip",
        }

    def add_pin(self, x: float, y: float, name: str = "") -> Pin:
        """Add a pin to the chip"""
        pin = Pin(x, y, name)
        pin.chip = self  # Set reference to this chip
        self.pins.append(pin)
        return pin

    def get_property(self, key: str) -> Optional[str]:
        """Get a property value"""
        return self.properties.get(key)

    def set_property(self, key: str, value: str) -> None:
        """Set a property value"""
        self.properties[key] = value
        if key == "name":
            self.name = value

    def update_position(self, x: float, y: float) -> None:
        """Update the chip's position"""
        old_x, old_y = self.position
        self.position = (x, y)

        # Update scene if pins have moved
        if old_x != x or old_y != y:
            pass  # The scene will handle updating pin positions during paint
