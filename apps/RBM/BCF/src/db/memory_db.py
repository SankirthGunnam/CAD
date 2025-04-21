import uuid
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Optional


class MemoryDB(QObject):
    """Simple in-memory database for testing"""

    data_changed = Signal(str)  # Signal emits table name that changed

    def __init__(self):
        super().__init__()
        self.chips = {}
        self.pins = {}
        self.connected = False

    def connect(self) -> None:
        """Connect to the database"""
        self.connected = True

    def disconnect(self) -> None:
        """Disconnect from the database"""
        self.connected = False

    def create_tables(self) -> None:
        """Create database tables"""
        # In-memory database doesn't need to create tables
        pass

    def get_chip(self, chip_id: str) -> Optional[Dict[str, Any]]:
        """Get a chip by ID"""
        return self.chips.get(chip_id)

    def add_chip(self, chip_data: Dict[str, Any]) -> Optional[str]:
        """Add a new chip"""
        return self._add_chip(chip_data)

    def _add_chip(self, chip_data: Dict[str, Any]) -> str:
        """Internal method to add a chip"""
        chip_id = str(uuid.uuid4())
        chip_data["id"] = chip_id

        # Ensure parameters dictionary exists
        if "parameters" not in chip_data:
            chip_data["parameters"] = {}
        if "material" not in chip_data["parameters"]:
            chip_data["parameters"]["material"] = ""
        if "thickness" not in chip_data["parameters"]:
            chip_data["parameters"]["thickness"] = 0.0

        self.chips[chip_id] = chip_data
        self.data_changed.emit("chips")
        return chip_id

    def update_chip(self, chip_id: str, chip_data: Dict[str, Any]) -> bool:
        """Update an existing chip"""
        if chip_id in self.chips:
            chip_data["id"] = chip_id

            # Ensure parameters dictionary exists
            if "parameters" not in chip_data:
                chip_data["parameters"] = {}
            if "material" not in chip_data["parameters"]:
                chip_data["parameters"]["material"] = ""
            if "thickness" not in chip_data["parameters"]:
                chip_data["parameters"]["thickness"] = 0.0

            self.chips[chip_id] = chip_data
            self.data_changed.emit("chips")
            return True
        return False

    def delete_chip(self, chip_id: str) -> bool:
        """Delete a chip"""
        if chip_id in self.chips:
            del self.chips[chip_id]
            self.data_changed.emit("chips")
            return True
        return False

    def get_all_chips(self) -> List[Dict[str, Any]]:
        """Get all chips"""
        return list(self.chips.values())

    def add_pin(self, chip_id: str, pin_data: Dict[str, Any]) -> Optional[str]:
        """Add a pin to a chip"""
        if chip_id not in self.chips:
            return None

        pin_id = str(uuid.uuid4())
        pin_data["id"] = pin_id
        pin_data["chip_id"] = chip_id
        self.pins[pin_id] = pin_data
        self.data_changed.emit("pins")
        return pin_id

    def get_chip_pins(self, chip_id: str) -> List[Dict[str, Any]]:
        """Get all pins for a chip"""
        return [pin for pin in self.pins.values() if pin["chip_id"] == chip_id]

    def commit(self) -> None:
        """Commit changes to the database"""
        # In-memory database doesn't need to commit
        pass

    def rollback(self) -> None:
        """Rollback changes"""
        # In-memory database doesn't need to rollback
        pass
