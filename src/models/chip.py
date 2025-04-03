from dataclasses import dataclass
from typing import List, Dict, Optional
from .pin import Pin


@dataclass
class ChipModel:
    """Core chip model without UI dependencies"""

    name: str
    width: float
    height: float
    pins: List[Pin]
    properties: Dict[str, str]

    def __init__(self, name: str = "Chip", width: float = 50, height: float = 50):
        self.name = name
        self.width = width
        self.height = height
        self.pins = []
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
