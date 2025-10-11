from typing import Any, Dict, List, Optional


class LegacyTableModel:
    """Simple in-memory model for legacy table views."""

    def __init__(self, initial_data: Optional[Dict[str, List[Any]]] = None) -> None:
        if initial_data is None:
            # Provide default sample rows so the table is immediately visible
            initial_data = {
                "row_0": [1, "Item A", "Type X", "Active"],
                "row_1": [2, "Item B", "Type Y", "Inactive"],
                "row_2": [3, "Item C", "Type Z", "Active"],
            }
        self._data: Dict[str, List[Any]] = dict(initial_data)

    def get_data(self) -> Dict[str, List[Any]]:
        return dict(self._data)

    def update_data(self, data: Dict[str, List[Any]]) -> None:
        # Replace entirely for simplicity
        self._data = dict(data)

    def set_row(self, index: int, row_data: List[Any]) -> None:
        key = f"row_{index}"
        self._data[key] = list(row_data)


