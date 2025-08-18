from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid
from enum import IntEnum


class ChipRoles(IntEnum):
    """Custom roles for chip data access"""
    # Standard display roles
    NameRole = Qt.DisplayRole
    TypeRole = Qt.UserRole + 1
    
    # Position and geometry
    PositionRole = Qt.UserRole + 10
    WidthRole = Qt.UserRole + 11
    HeightRole = Qt.UserRole + 12
    
    # Visual properties
    ColorRole = Qt.UserRole + 20
    SelectedRole = Qt.UserRole + 21
    VisibleRole = Qt.UserRole + 22
    
    # Circuit properties
    PinsRole = Qt.UserRole + 30
    ConnectionsRole = Qt.UserRole + 31
    PropertiesRole = Qt.UserRole + 32
    MetadataRole = Qt.UserRole + 33
    
    # Internal data
    ChipDataRole = Qt.UserRole + 100  # Full chip data dictionary


class VisualCircuitModel(QAbstractItemModel):
    """
    Circuit Model using QAbstractItemModel for proper Qt Model/View pattern.
    
    This provides the same interface as QTableModel but for circuit components:
    - Views can connect using standard Qt model/view patterns
    - Automatic view updates through standard Qt signals
    - Standard item selection, drag/drop, etc.
    - Works with QGraphicsView through custom graphics items
    
    Hierarchy:
    - Root (invisible)
      - Chip 1
      - Chip 2  
      - Chip N
      
    Each chip is a top-level item with all its data accessible via roles.
    """
    
    # Custom signals for graphics-specific operations
    chipPositionChanged = Signal(str, tuple)  # chip_id, (x, y)
    chipSelectionChanged = Signal(list)  # [chip_ids]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Core data storage
        self._chips: Dict[str, Dict[str, Any]] = {}
        self._chip_order: List[str] = []  # Maintains insertion order
        self._chip_counter = 0
        
        # Selection tracking (independent of Qt's selection model)
        self._selected_chips: List[str] = []
    
    # === QAbstractItemModel Interface ===
    
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create model index for given row/column"""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        
        # Only support flat structure (chips are top-level items)
        if parent.isValid():
            return QModelIndex()
        
        if 0 <= row < len(self._chip_order):
            chip_id = self._chip_order[row]
            return self.createIndex(row, column, chip_id)
        
        return QModelIndex()
    
    def parent(self, index: QModelIndex) -> QModelIndex:
        """Return parent index (always invalid for flat structure)"""
        return QModelIndex()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of chips"""
        if parent.isValid():
            return 0  # No children for chips
        return len(self._chip_order)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return number of columns (always 1 for our use case)"""
        return 1
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for given index and role"""
        if not index.isValid():
            return None
        
        chip_id = index.internalPointer()
        if chip_id not in self._chips:
            return None
        
        chip_data = self._chips[chip_id]
        
        # Standard display role
        if role == Qt.DisplayRole or role == ChipRoles.NameRole:
            return chip_data.get('name', 'Unknown Chip')
        
        elif role == Qt.ToolTipRole:
            return f"{chip_data.get('type', 'Generic')} - {chip_data.get('name', 'Unknown')}"
        
        # Custom roles
        elif role == ChipRoles.TypeRole:
            return chip_data.get('type', 'Generic')
        
        elif role == ChipRoles.PositionRole:
            return chip_data.get('position', (0, 0))
        
        elif role == ChipRoles.WidthRole:
            return chip_data.get('width', 100)
        
        elif role == ChipRoles.HeightRole:
            return chip_data.get('height', 100)
        
        elif role == ChipRoles.SelectedRole:
            return chip_id in self._selected_chips
        
        elif role == ChipRoles.VisibleRole:
            return chip_data.get('visible', True)
        
        elif role == ChipRoles.PinsRole:
            return chip_data.get('pins', [])
        
        elif role == ChipRoles.PropertiesRole:
            return chip_data.get('properties', {})
        
        elif role == ChipRoles.MetadataRole:
            return chip_data.get('metadata', {})
        
        elif role == ChipRoles.ChipDataRole:
            return chip_data.copy()
        
        return None
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """Set data for given index and role"""
        if not index.isValid():
            return False
        
        chip_id = index.internalPointer()
        if chip_id not in self._chips:
            return False
        
        chip_data = self._chips[chip_id]
        changed = False
        
        # Handle different roles
        if role == Qt.EditRole or role == ChipRoles.NameRole:
            if chip_data.get('name') != value:
                chip_data['name'] = value
                changed = True
        
        elif role == ChipRoles.PositionRole:
            old_position = chip_data.get('position', (0, 0))
            if old_position != value:
                chip_data['position'] = value
                changed = True
                # Emit special signal for graphics updates
                self.chipPositionChanged.emit(chip_id, value)
        
        elif role == ChipRoles.WidthRole:
            if chip_data.get('width') != value:
                chip_data['width'] = value
                changed = True
        
        elif role == ChipRoles.HeightRole:
            if chip_data.get('height') != value:
                chip_data['height'] = value
                changed = True
        
        elif role == ChipRoles.VisibleRole:
            if chip_data.get('visible', True) != value:
                chip_data['visible'] = value
                changed = True
        
        elif role == ChipRoles.PropertiesRole:
            if chip_data.get('properties', {}) != value:
                chip_data['properties'] = value
                changed = True
        
        elif role == ChipRoles.MetadataRole:
            if chip_data.get('metadata', {}) != value:
                chip_data['metadata'] = value
                changed = True
        
        if changed:
            # Standard Qt signal - views will automatically update
            self.dataChanged.emit(index, index, [role])
            return True
        
        return False
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return item flags"""
        if not index.isValid():
            return Qt.NoItemFlags
        
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Return header data"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Components"
        return None
    
    # === Custom Circuit Operations ===
    
    def add_chip(self, chip_spec: Dict[str, Any], position: Tuple[float, float] = (0, 0)) -> str:
        """
        Add chip to model using Qt model interface.
        Views will automatically create visual representation.
        """
        # Generate unique ID
        self._chip_counter += 1
        chip_id = f"chip_{self._chip_counter}"
        
        # Prepare row insertion
        row = len(self._chip_order)
        
        # Standard Qt pattern: beginInsertRows
        self.beginInsertRows(QModelIndex(), row, row)
        
        # Prepare chip data
        chip_data = {
            'id': chip_id,
            'name': chip_spec.get('name', f'Chip {self._chip_counter}'),
            'type': chip_spec.get('type', 'Generic'),
            'width': chip_spec.get('width', 100),
            'height': chip_spec.get('height', 100),
            'position': position,
            'visible': True,
            'pins': self._generate_pins(chip_spec),
            'properties': chip_spec.get('properties', {}),
            'metadata': chip_spec.copy(),
            'package': chip_spec.get('package', 'Generic')
        }
        
        # Add to model data
        self._chips[chip_id] = chip_data
        self._chip_order.append(chip_id)
        
        # Standard Qt pattern: endInsertRows (triggers views to update)
        self.endInsertRows()
        
        return chip_id
    
    def remove_chip(self, chip_id: str) -> bool:
        """
        Remove chip from model using Qt model interface.
        Views will automatically remove visual representation.
        """
        if chip_id not in self._chips:
            return False
        
        # Find row
        try:
            row = self._chip_order.index(chip_id)
        except ValueError:
            return False
        
        # Standard Qt pattern: beginRemoveRows
        self.beginRemoveRows(QModelIndex(), row, row)
        
        # Remove from model data
        del self._chips[chip_id]
        self._chip_order.remove(chip_id)
        
        # Update selection
        if chip_id in self._selected_chips:
            self._selected_chips.remove(chip_id)
            self.chipSelectionChanged.emit(self._selected_chips[:])
        
        # Standard Qt pattern: endRemoveRows (triggers views to update)
        self.endRemoveRows()
        
        return True
    
    def move_chip(self, chip_id: str, position: Tuple[float, float]) -> bool:
        """Move chip to new position"""
        if chip_id not in self._chips:
            return False
        
        try:
            row = self._chip_order.index(chip_id)
            index = self.index(row, 0)
            return self.setData(index, position, ChipRoles.PositionRole)
        except ValueError:
            return False
    
    def get_chip_data(self, chip_id: str) -> Optional[Dict[str, Any]]:
        """Get full chip data"""
        return self._chips.get(chip_id, {}).copy()
    
    def get_chip_position(self, chip_id: str) -> Tuple[float, float]:
        """Get chip position"""
        return self._chips.get(chip_id, {}).get('position', (0, 0))
    
    def get_all_chip_ids(self) -> List[str]:
        """Get all chip IDs in order"""
        return self._chip_order[:]
    
    # === Selection Management ===
    
    def set_chip_selection(self, selected_ids: List[str]):
        """Update chip selection"""
        # Validate IDs
        valid_ids = [chip_id for chip_id in selected_ids if chip_id in self._chips]
        
        if valid_ids != self._selected_chips:
            self._selected_chips = valid_ids[:]
            
            # Update data for all chips (selection state changed)
            for row, chip_id in enumerate(self._chip_order):
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [ChipRoles.SelectedRole])
            
            # Emit selection change signal
            self.chipSelectionChanged.emit(self._selected_chips[:])
    
    def get_selected_chips(self) -> List[str]:
        """Get selected chip IDs"""
        return self._selected_chips[:]
    
    # === Model State Management ===
    
    def clear_model(self):
        """Clear all data (equivalent to modelReset)"""
        self.beginResetModel()
        
        self._chips.clear()
        self._chip_order.clear()
        self._selected_chips.clear()
        self._chip_counter = 0
        
        self.endResetModel()  # Views will automatically clear
    
    def load_from_data(self, circuit_data: Dict[str, Any]):
        """Load circuit from serialized data"""
        self.beginResetModel()
        
        self._chips.clear()
        self._chip_order.clear()
        self._selected_chips.clear()
        
        # Load chips
        chips_data = circuit_data.get('chips', {})
        for chip_id, chip_data in chips_data.items():
            self._chips[chip_id] = chip_data
            self._chip_order.append(chip_id)
            
            # Update counter
            if chip_id.startswith('chip_'):
                try:
                    counter = int(chip_id.split('_')[1])
                    self._chip_counter = max(self._chip_counter, counter)
                except:
                    pass
        
        self.endResetModel()  # Views will automatically rebuild
    
    def export_data(self) -> Dict[str, Any]:
        """Export model data for serialization"""
        return {
            'chips': self._chips.copy(),
            'chip_order': self._chip_order[:],
            'version': '1.0'
        }
    
    # === Helper Methods ===
    
    def _generate_pins(self, chip_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate pin data based on chip specification"""
        chip_type = chip_spec.get('type', 'Generic')
        width = chip_spec.get('width', 100)
        height = chip_spec.get('height', 100)
        
        pins = []
        
        if chip_type == 'Power Amplifier':
            pins = [
                {'x': 0, 'y': height//2, 'name': 'RF_IN'},
                {'x': width, 'y': height//2, 'name': 'RF_OUT'},
                {'x': width//2, 'y': 0, 'name': 'BIAS'},
                {'x': width//2, 'y': height, 'name': 'GND'}
            ]
        elif chip_type == 'RF Front-End Module':
            pins = [
                {'x': 0, 'y': height//4, 'name': 'TX1_IN'},
                {'x': 0, 'y': 3*height//4, 'name': 'TX2_IN'},
                {'x': width, 'y': height//4, 'name': 'TX1_OUT'},
                {'x': width, 'y': 3*height//4, 'name': 'TX2_OUT'},
                {'x': width//2, 'y': 0, 'name': 'CTRL'},
                {'x': width//2, 'y': height, 'name': 'GND'}
            ]
        elif chip_type == 'RFIC':
            pins = [
                {'x': 0, 'y': height//4, 'name': 'TX_IN'},
                {'x': 0, 'y': 3*height//4, 'name': 'RX_IN'},
                {'x': width, 'y': height//4, 'name': 'TX_OUT'},
                {'x': width, 'y': 3*height//4, 'name': 'RX_OUT'},
                {'x': width//2, 'y': 0, 'name': 'VCC'},
                {'x': width//2, 'y': height, 'name': 'GND'}
            ]
        else:
            # Generic pins
            pins = [
                {'x': 0, 'y': height//2, 'name': 'IN'},
                {'x': width, 'y': height//2, 'name': 'OUT'},
                {'x': width//2, 'y': 0, 'name': 'VCC'},
                {'x': width//2, 'y': height, 'name': 'GND'}
            ]
        
        return pins
    
    # === Convenience Methods ===
    
    def get_chip_index(self, chip_id: str) -> QModelIndex:
        """Get QModelIndex for a chip"""
        try:
            row = self._chip_order.index(chip_id)
            return self.index(row, 0)
        except ValueError:
            return QModelIndex()
    
    def get_chip_id_from_index(self, index: QModelIndex) -> Optional[str]:
        """Get chip ID from QModelIndex"""
        if not index.isValid():
            return None
        return index.internalPointer()
