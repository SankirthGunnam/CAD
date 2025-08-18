from dataclasses import dataclass
from typing import Optional
from apps.RBM5.BCF.source.models.pin import Pin


@dataclass
class Connection:
    """Core connection model without UI dependencies"""

    start_pin: Pin
    end_pin: Optional[Pin]

    def __init__(self, start_pin: Pin, end_pin: Optional[Pin] = None):
        self.start_pin = start_pin
        self.end_pin = end_pin

        # Add this connection to the start pin
        self.start_pin.add_connection(self)
        if self.end_pin:
            self.end_pin.add_connection(self)

    def finish_connection(self, end_pin: Pin) -> bool:
        """Finish the connection with an end pin"""
        if end_pin == self.start_pin:
            return False

        self.end_pin = end_pin
        self.end_pin.add_connection(self)
        return True

    def remove(self) -> None:
        """Remove this connection and clean up references"""
        if self.start_pin:
            self.start_pin.remove_connection(self)
        if self.end_pin:
            self.end_pin.remove_connection(self)
