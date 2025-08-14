from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QDockWidget,
    QLabel,
    QPushButton,
    QMessageBox,
    QMainWindow,
)
from PySide6.QtCore import Qt, Signal, QPointF, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QKeySequence, QShortcut
from typing import Dict, Any, Optional, List

from .scene import RFScene
from .view import RFView
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.gui.custom_widgets.components.rfic_chip import RFICChip
from apps.RBM.BCF.src.models.chip import ChipModel
from apps.RBM.BCF.src.models.rfic_chip import RFICChipModel
from ..views.chip_selection_dialog import ChipSelectionDialog
from ..views.floating_toolbar import FloatingToolbar

# Import MVC components
from apps.RBM.BCF.src.models.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM.BCF.src.controllers.visual_bcf_controller import VisualBCFController
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager


class VisualBCFManager(QWidget):
    """Manager for the visual BCF interface with graphics scene and view"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, parent_controller=None, rdb_manager: Optional[RDBManager] = None):
        super().__init__(parent)
        self.setWindowTitle("Visual BCF Manager")
        self.parent_controller = parent_controller
        self.rdb_manager = rdb_manager

        # Architecture Components
        self.data_model: Optional[VisualBCFDataModel] = None
        self.controller: Optional[VisualBCFController] = None
        self.architecture_enabled = False

        # Create main layout - now just for the view
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create graphics scene and view
        self.scene = RFScene()
        self.view = RFView(self.scene)
        # Set a large scene rect
        self.view.setSceneRect(-1000, -1000, 2000, 2000)
        self.view.setBackgroundBrush(
            QColor(100, 100, 100))  # Set background color

        # Add view to main layout (takes all the space)
        main_layout.addWidget(self.view)

        # Initialize architecture components if RDB manager is provided
        if self.rdb_manager:
            self._setup_architecture_components()

        # Chip selection dialog
        self.chip_selection_dialog = None

        # Chip clipboard for copy/paste (legacy)
        self.chip_clipboard = None

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Connect scene signals
        self.scene.add_chip_requested.connect(self._on_add_chip_requested)
        self.scene.selection_changed.connect(self._on_selection_changed)

        # Create simple toolbar and add it to parent controller
        self.rf_toolbar = None
        self.toolbar_position_set = False  # Track if user has manually positioned toolbar
        if self.parent_controller:
            self.rf_toolbar = self._create_rf_toolbar()

        # Initialize with default RFIC chip and auto-import from Legacy BCF
        if self.architecture_enabled:
            # Auto-import from Legacy BCF on startup (fixes issue #1)
            # This will handle adding components, including default RFIC if needed
            QTimer.singleShot(500, self.auto_import_on_startup)
        else:
            # For legacy mode, add default RFIC directly to scene
            self._add_default_rfic_chip()

    def _create_rf_toolbar(self):
        """Create and add RF floating toolbar to parent controller"""
        try:
            # Create FloatingToolbar
            rf_toolbar = FloatingToolbar(self.parent_controller)

            # Connect toolbar signals to handler methods
            rf_toolbar.zoom_in_requested.connect(self._on_zoom_in)
            rf_toolbar.zoom_out_requested.connect(self._on_zoom_out)
            rf_toolbar.zoom_reset_requested.connect(self._on_reset_zoom)
            rf_toolbar.add_chip_requested.connect(self._on_add_chip_toolbar)
            rf_toolbar.delete_chip_requested.connect(self._on_delete_selected)
            rf_toolbar.copy_chip_requested.connect(self._on_copy_selected)
            rf_toolbar.paste_chip_requested.connect(self._on_paste_chips)
            rf_toolbar.select_mode_requested.connect(self._on_select_mode)
            rf_toolbar.connection_mode_requested.connect(self._on_connect_mode)

            # Position the toolbar at the center top of the view
            rf_toolbar.position_at_center_top(self.view)

            # Hide toolbar initially - will be shown only in visual mode
            rf_toolbar.hide()

            return rf_toolbar

        except Exception as e:
            print(f"Error creating RF floating toolbar: {e}")
            return None

    def _on_select_mode(self):
        """Handle select mode"""
        if hasattr(self, 'connect_action'):
            self.connect_action.setChecked(False)

    def _on_connect_mode(self):
        """Handle connect mode"""
        if hasattr(self, 'select_action'):
            self.select_action.setChecked(False)

    def _on_zoom_in(self):
        """Handle zoom in button click"""
        self.view.scale(1.2, 1.2)

    def _on_zoom_out(self):
        """Handle zoom out button click"""
        self.view.scale(1 / 1.2, 1 / 1.2)

    def _on_reset_zoom(self):
        """Handle reset zoom button click"""
        self.view.resetTransform()

    def _on_add_rfic(self):
        """Handle add RFIC button click"""
        try:
            # Create a new RFIC model and component
            rfic_count = len(
                [c for c in self.scene.get_components() if isinstance(c, RFICChip)])
            rfic_model = RFICChipModel(
                name=f"RFIC_{rfic_count + 1}",
                width=250,
                height=180
            )

            # Position it offset from center to avoid overlap
            offset_x = (rfic_count % 3) * 300 - 300  # Arrange in a grid
            offset_y = (rfic_count // 3) * 200 - 200
            rfic_model.update_position(offset_x, offset_y)

            # Create RFIC visual component
            rfic_component = RFICChip(rfic_model)

            # Position the component in the scene
            rfic_component.setPos(
                rfic_model.position[0] - rfic_model.width / 2,
                rfic_model.position[1] - rfic_model.height / 2
            )

            # Add to scene
            self.scene.add_component(rfic_component)

            # Emit data change signal
            self.data_changed.emit({
                "action": "add_rfic",
                "component": "RFIC",
                "name": rfic_model.name,
                "position": rfic_model.position,
                "properties": rfic_model.get_detailed_info()
            })

        except Exception as e:
            self.error_occurred.emit(f"Error adding RFIC chip: {str(e)}")

    def _on_clear_scene(self):
        """Handle clear scene button click"""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Clear Scene",
                "Are you sure you want to clear all components from the scene?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Clear all components
                # Make a copy of the list
                components = self.scene.get_components()[:]
                for component in components:
                    self.scene.remove_component(component)

                # Emit data change signal
                self.data_changed.emit(
                    {"action": "clear_scene", "components_removed": len(components)})

        except Exception as e:
            self.error_occurred.emit(f"Error clearing scene: {str(e)}")

    def _add_default_rfic_chip(self) -> None:
        """Add default RFIC chip to the graphics scene on startup (legacy mode)"""
        try:
            # Create default RFIC model
            rfic_model = RFICChipModel(
                name="Default RFIC",
                width=250,
                height=180
            )

            # Set position at the center of the scene
            rfic_model.update_position(0, 0)  # Center position

            # Create RFIC visual component
            rfic_component = RFICChip(rfic_model)

            # Position the component in the scene
            rfic_component.setPos(
                rfic_model.position[0] - rfic_model.width / 2,
                rfic_model.position[1] - rfic_model.height / 2
            )

            # Add to scene
            self.scene.add_component(rfic_component)

            # Emit data change signal
            self.data_changed.emit({
                "action": "add_default_rfic",
                "component": "RFIC",
                "name": rfic_model.name,
                "position": rfic_model.position,
                "properties": rfic_model.get_detailed_info()
            })

        except Exception as e:
            self.error_occurred.emit(
                f"Error adding default RFIC chip: {str(e)}")
    
    def _add_default_rfic_data_driven(self) -> str:
        """Add default RFIC chip component in data-driven mode (only if no components exist)"""
        if not (self.architecture_enabled and self.controller and self.data_model):
            return ""
        
        try:
            # Check if any components already exist in the database
            existing_components = self.data_model.get_all_components()
            if existing_components:
                # Components already exist, no need to add default
                return ""
            
            # Add a default RFIC chip at center
            name = "Default RFIC Chip"
            position = (0, 0)
            component_type = "rfic"
            properties = {
                'function_type': 'RFIC',
                'frequency_range': '600MHz - 6GHz',
                'technology': 'CMOS',
                'package': 'BGA',
                'rf_bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B8', 'B20', 'B28']
            }
            
            component_id = self.controller.add_component(name, component_type, position, properties)
            
            if component_id:
                self.data_changed.emit({
                    "action": "add_default_rfic_data_driven",
                    "component_id": component_id,
                    "component": "RFIC",
                    "name": name,
                    "position": position,
                    "source": "data_driven"
                })
            
            return component_id
            
        except Exception as e:
            self.error_occurred.emit(f"Error adding default RFIC chip (Data-Driven): {str(e)}")
            return ""

    def get_default_rfic(self) -> Optional[RFICChip]:
        """Get the default RFIC chip if it exists in the scene"""
        for component in self.scene.get_components():
            if isinstance(component, RFICChip) and component.model.name == "Default RFIC":
                return component
        return None

    def update_scene(self, data: Dict[str, Any]):
        """Update the scene with new data"""
        try:
            # Clear existing items
            for component in self.scene.get_components():
                self.scene.remove_component(component)

            # TODO: Add items based on data
            pass
        except Exception as e:
            self.error_occurred.emit(f"Error updating scene: {str(e)}")

    def _on_add_chip_requested(self, position: QPointF):
        """Handle add chip request from scene context menu"""
        self._show_chip_selection_dialog(position)

    def _on_add_chip_toolbar(self):
        """Handle add chip request from floating toolbar"""
        # Add chip at the center of the current view
        center = self.view.mapToScene(self.view.viewport().rect().center())
        self._show_chip_selection_dialog(center)

    def _show_chip_selection_dialog(self, position: QPointF):
        """Show the chip selection dialog"""
        try:
            if not self.chip_selection_dialog:
                self.chip_selection_dialog = ChipSelectionDialog(self)
                self.chip_selection_dialog.chip_selected.connect(
                    lambda chip_data: self._add_selected_chip(
                        chip_data, position)
                )

            self.chip_selection_dialog.show()
            self.chip_selection_dialog.raise_()

        except Exception as e:
            self.error_occurred.emit(
                f"Error showing chip selection dialog: {str(e)}")

    def _add_selected_chip(self, chip_data: Dict, position: QPointF):
        """Add the selected chip from dialog to the scene"""
        try:
            chip_name = f"{chip_data['name']} ({chip_data['part_number']})"
            
            if self.architecture_enabled and self.controller:
                # Use controller for proper data management and auto-export
                
                # Determine component type based on chip type
                chip_type = chip_data.get('type', '')
                if 'RF Front-End Module' in chip_type:
                    component_type = 'device'
                    function_type = 'FEM'
                elif 'Power Amplifier' in chip_type:
                    component_type = 'device' 
                    function_type = 'PA'
                elif 'Switch' in chip_type:
                    component_type = 'device'
                    function_type = 'Switch'
                elif 'Modem' in chip_type or 'LTE' in chip_type or '5G' in chip_type:
                    component_type = 'modem'
                    function_type = chip_type
                else:
                    component_type = 'chip'
                    function_type = 'Generic'
                
                # Determine chip size based on package type
                package = chip_data.get('package', '')
                if 'QFN' in package:
                    width, height = 200, 150
                elif 'TQFN' in package:
                    width, height = 180, 120
                elif 'LGA' in package:
                    width, height = 160, 100
                elif 'CSP' in package:
                    width, height = 120, 80
                else:
                    width, height = 180, 120  # Default size
                
                # Create properties from chip data
                properties = {
                    'function_type': function_type,
                    'interface_type': 'MIPI' if component_type in ['modem', 'device'] else 'Generic',
                    'interface': {'mipi': {'channel': 1}} if component_type in ['modem', 'device'] else {},
                    'config': {'usid': f'{function_type.upper()}001'},
                    'width': width,
                    'height': height,
                    'package': package,
                    'part_number': chip_data.get('part_number', ''),
                    'metadata': chip_data
                }
                
                # Add component via MVC controller
                component_id = self.controller.add_component(
                    name=chip_name,
                    component_type=component_type,
                    position=(position.x(), position.y()),
                    properties=properties
                )
                
                if component_id:
                    print(f"✅ Added chip '{chip_name}' via controller with ID: {component_id}")
                else:
                    print(f"❌ Failed to add chip '{chip_name}' via controller")
            
            else:
                # Fallback to legacy method
                print(f"⚠️ Using legacy method to add chip '{chip_name}' (Architecture not enabled)")
                
                # Determine chip size based on package type
                package = chip_data.get('package', '')
                if 'QFN' in package:
                    width, height = 200, 150
                elif 'TQFN' in package:
                    width, height = 180, 120
                elif 'LGA' in package:
                    width, height = 160, 100
                elif 'CSP' in package:
                    width, height = 120, 80
                else:
                    width, height = 180, 120  # Default size

                # Create chip model
                chip_model = ChipModel(name=chip_name, width=width, height=height)

                # Add pins based on chip type
                if 'RF Front-End Module' in chip_data.get('type', ''):
                    # FEM typically has TX, RX, and control pins
                    chip_model.add_pin(0, height//4, "TX1_IN")
                    chip_model.add_pin(0, 3*height//4, "TX2_IN")
                    chip_model.add_pin(width, height//4, "TX1_OUT")
                    chip_model.add_pin(width, 3*height//4, "TX2_OUT")
                    chip_model.add_pin(width//2, 0, "CTRL")
                    chip_model.add_pin(width//2, height, "GND")
                elif 'Power Amplifier' in chip_data.get('type', ''):
                    # PA has input, output, bias pins
                    chip_model.add_pin(0, height//2, "RF_IN")
                    chip_model.add_pin(width, height//2, "RF_OUT")
                    chip_model.add_pin(width//2, 0, "BIAS")
                    chip_model.add_pin(width//2, height, "GND")
                elif 'Switch' in chip_data.get('type', ''):
                    # RF switch has multiple ports
                    num_ports = 6  # Default for SP6T
                    for i in range(num_ports):
                        angle = i * 60  # degrees
                        x = width//2 + (width//3) * (1 if angle < 180 else -1)
                        y = height//2 + (height//3) * (1 if angle <
                                                       90 or angle > 270 else -1)
                        chip_model.add_pin(x, y, f"P{i+1}")
                else:
                    # Generic chip with basic pins
                    chip_model.add_pin(0, height//2, "IN")
                    chip_model.add_pin(width, height//2, "OUT")
                    chip_model.add_pin(width//2, 0, "VCC")
                    chip_model.add_pin(width//2, height, "GND")

                # Set position
                chip_model.update_position(position.x(), position.y())

                # Store chip data as metadata
                chip_model.metadata = chip_data

                # Create visual component
                chip_component = Chip(chip_model)
                chip_component.setPos(
                    position.x() - width // 2,
                    position.y() - height // 2
                )

                # Add to scene
                self.scene.add_component(chip_component)

                # Emit data change signal
                self.data_changed.emit({
                    "action": "add_chip",
                    "component": chip_data['type'],
                    "name": chip_name,
                    "position": [position.x(), position.y()],
                    "chip_data": chip_data,
                    "source": "legacy"
                })

        except Exception as e:
            self.error_occurred.emit(f"Error adding selected chip: {str(e)}")

    def _on_selection_changed(self, has_selection: bool):
        """Handle selection change in the scene"""
        # Update floating toolbar button states
        if self.rf_toolbar:
            self.rf_toolbar.set_selection_available(has_selection)

    def _on_delete_selected(self):
        """Delete selected chips (user-initiated via toolbar/keyboard)"""
        try:
            if self.architecture_enabled and self.controller:
                # Use controller for proper bidirectional sync
                self.controller.delete_selected_components()
            else:
                # Fallback to legacy method
                selected_components = self.scene.get_selected_components()
                if not selected_components:
                    return

                # Show confirmation for multiple items
                if len(selected_components) > 1:
                    reply = QMessageBox.question(
                        self,
                        "Delete Components",
                        f"Are you sure you want to delete {len(selected_components)} components?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return

                # Delete all selected components
                for component in selected_components[:]:
                    self.scene.remove_component(component)

                self.data_changed.emit({
                    "action": "delete_components",
                    "count": len(selected_components)
                })

        except Exception as e:
            self.error_occurred.emit(f"Error deleting components: {str(e)}")

    def _on_copy_selected(self):
        """Copy selected chips to clipboard (user-initiated via toolbar/keyboard)"""
        try:
            if self.architecture_enabled and self.controller:
                # Use controller for copy operation
                self.controller.copy_selected_components()
            else:
                # Fallback to legacy method
                selected_components = self.scene.get_selected_components()
                if not selected_components:
                    return

                # Store component data for pasting
                self.chip_clipboard = []
                for component in selected_components:
                    if isinstance(component, Chip):
                        chip_data = {
                            'model_data': {
                                'name': component.model.name,
                                'width': component.model.width,
                                'height': component.model.height,
                                'pins': [(p.x, p.y, p.name) for p in component.model.pins],
                                'metadata': getattr(component.model, 'metadata', {})
                            },
                            'position': component.model.position
                        }
                        self.chip_clipboard.append(chip_data)

                # Enable paste button in floating toolbar if available
                if self.rf_toolbar:
                    self.rf_toolbar.set_paste_available(
                        len(self.chip_clipboard) > 0)

                # Show feedback
                self.data_changed.emit({
                    "action": "copy_components",
                    "count": len(self.chip_clipboard)
                })

        except Exception as e:
            self.error_occurred.emit(f"Error copying components: {str(e)}")

    def _on_paste_chips(self):
        """Paste chips from clipboard (user-initiated via toolbar/keyboard)"""
        try:
            if self.architecture_enabled and self.controller:
                # Use controller for paste operation
                self.controller.paste_components()
            else:
                # Fallback to legacy method
                if not self.chip_clipboard:
                    return

                # Get current view center as paste location
                center = self.view.mapToScene(self.view.viewport().rect().center())

                pasted_components = []
                for i, chip_data in enumerate(self.chip_clipboard):
                    # Create new chip model
                    model_data = chip_data['model_data']
                    chip_model = ChipModel(
                        name=f"{model_data['name']}_copy_{i+1}",
                        width=model_data['width'],
                        height=model_data['height']
                    )

                    # Add pins
                    for pin_data in model_data['pins']:
                        chip_model.add_pin(pin_data[0], pin_data[1], pin_data[2])

                    # Restore metadata
                    if 'metadata' in model_data:
                        chip_model.metadata = model_data['metadata']

                    # Position with offset to avoid overlap
                    offset_x = (i % 3) * 50  # Arrange in grid
                    offset_y = (i // 3) * 50
                    chip_model.update_position(
                        center.x() + offset_x, center.y() + offset_y)

                    # Create visual component
                    chip_component = Chip(chip_model)
                    chip_component.setPos(
                        chip_model.position[0] - chip_model.width // 2,
                        chip_model.position[1] - chip_model.height // 2
                    )

                    # Add to scene
                    self.scene.add_component(chip_component)
                    pasted_components.append(chip_component)

                self.data_changed.emit({
                    "action": "paste_components",
                    "count": len(pasted_components)
                })

        except Exception as e:
            self.error_occurred.emit(f"Error pasting components: {str(e)}")

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for common actions"""
        # Add chip shortcut (A key)
        self.add_chip_shortcut = QShortcut(QKeySequence("A"), self)
        self.add_chip_shortcut.activated.connect(self._on_add_chip_toolbar)

        # Delete chip shortcut (Delete key)
        self.delete_shortcut = QShortcut(QKeySequence.Delete, self)
        self.delete_shortcut.activated.connect(self._on_delete_selected)

        # Copy shortcut (Ctrl+C)
        self.copy_shortcut = QShortcut(QKeySequence.Copy, self)
        self.copy_shortcut.activated.connect(self._on_copy_selected)

        # Paste shortcut (Ctrl+V)
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.activated.connect(self._on_paste_chips)

        # Zoom shortcuts
        self.zoom_in_shortcut = QShortcut(QKeySequence("+"), self)
        self.zoom_in_shortcut.activated.connect(self._on_zoom_in)

        self.zoom_out_shortcut = QShortcut(QKeySequence("-"), self)
        self.zoom_out_shortcut.activated.connect(self._on_zoom_out)

        self.zoom_reset_shortcut = QShortcut(QKeySequence("0"), self)
        self.zoom_reset_shortcut.activated.connect(self._on_reset_zoom)

        # Select all shortcut (Ctrl+A)
        self.select_all_shortcut = QShortcut(QKeySequence.SelectAll, self)
        self.select_all_shortcut.activated.connect(self._on_select_all)

        # Escape to clear selection
        self.clear_selection_shortcut = QShortcut(
            QKeySequence(Qt.Key_Escape), self)
        self.clear_selection_shortcut.activated.connect(
            self._on_clear_selection)

    def _on_select_all(self):
        """Select all components in the scene"""
        try:
            components = self.scene.get_components()
            self.scene.clearSelection()
            for component in components:
                component.setSelected(True)

            has_selection = len(components) > 0
            if self.rf_toolbar:
                self.rf_toolbar.set_selection_available(has_selection)

        except Exception as e:
            self.error_occurred.emit(
                f"Error selecting all components: {str(e)}")

    def _on_clear_selection(self):
        """Clear all selections"""
        try:
            self.scene.clearSelection()
            if self.rf_toolbar:
                self.rf_toolbar.set_selection_available(False)

        except Exception as e:
            self.error_occurred.emit(f"Error clearing selection: {str(e)}")

    def show_rf_toolbar(self):
        """Show the RF toolbar (called when switching to visual mode)"""
        if self.rf_toolbar:
            self.rf_toolbar.show()

    def hide_rf_toolbar(self):
        """Hide the RF toolbar (called when switching to legacy mode)"""
        if self.rf_toolbar:
            self.rf_toolbar.hide()

    def _setup_architecture_components(self):
        """Setup architecture components for data-driven Visual BCF"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Model - Data access layer
            self.data_model = VisualBCFDataModel(self.rdb_manager)
            logger.info("Visual BCF Data Model created")
            
            # Controller - Coordinates between model and view
            self.controller = VisualBCFController(self.view, self.data_model)
            logger.info("Visual BCF Controller created")
            
            # Connect controller signals to manager signals
            self.controller.operation_completed.connect(self._on_controller_operation_completed)
            self.controller.error_occurred.connect(self._on_controller_error_occurred)
            self.controller.component_selected.connect(self._on_controller_component_selected)
            
            # NEW: Connect user deletion signal to handle Legacy BCF synchronization
            self.controller.component_removed_by_user.connect(self._on_visual_component_removed_by_user)
            
            # Set controller reference in scene for user deletions
            self.scene.set_controller(self.controller)
            
            self.architecture_enabled = True
            logger.info("Architecture components setup complete")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error setting up MVC components: {e}")
            self.error_occurred.emit(f"Failed to setup architecture: {str(e)}")
    
    def _on_controller_operation_completed(self, operation: str, message: str):
        """Handle controller operation completed"""
        self.data_changed.emit({
            "action": operation,
            "message": message,
            "source": "controller"
        })
    
    def _on_controller_error_occurred(self, error_message: str):
        """Handle controller error"""
        self.error_occurred.emit(error_message)
    
    def _on_controller_component_selected(self, component_id: str):
        """Handle controller component selection"""
        if self.data_model:
            component_data = self.data_model.get_component(component_id)
            if component_data:
                self.data_changed.emit({
                    "action": "component_selected",
                    "component_id": component_id,
                    "component_name": component_data.name,
                    "component_type": component_data.component_type,
                    "source": "controller"
                })
    
    def _on_visual_component_removed_by_user(self, component_name: str):
        """Handle user-initiated component deletion from Visual BCF scene"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🎨 Visual BCF: User deleted component '{component_name}' - removing from Legacy BCF")
            
            # Find and remove the corresponding device from Legacy BCF
            device_settings = self.rdb_manager.get_table("config.device.settings")
            device_index_to_remove = -1
            
            for i, device in enumerate(device_settings):
                if device.get('name') == component_name:
                    device_index_to_remove = i
                    break
            
            if device_index_to_remove >= 0:
                # Remove the device from Legacy BCF
                success = self.rdb_manager.delete_row("config.device.settings", device_index_to_remove)
                
                if success:
                    logger.info(f"✅ Successfully removed device '{component_name}' from Legacy BCF")
                    self.data_changed.emit({
                        "action": "user_deletion_synced",
                        "component_name": component_name,
                        "message": f"Removed '{component_name}' from both Visual BCF and Legacy BCF",
                        "source": "bidirectional_sync"
                    })
                else:
                    logger.error(f"Failed to remove device '{component_name}' from Legacy BCF")
                    self.error_occurred.emit(f"Failed to remove device '{component_name}' from Legacy BCF")
            else:
                logger.warning(f"Device '{component_name}' not found in Legacy BCF table")
                # This might be a component that was only in Visual BCF, which is fine
                self.data_changed.emit({
                    "action": "user_deletion_visual_only",
                    "component_name": component_name,
                    "message": f"Removed '{component_name}' from Visual BCF (not found in Legacy BCF)",
                    "source": "bidirectional_sync"
                })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error handling Visual BCF user deletion for '{component_name}': {e}")
            self.error_occurred.emit(f"Failed to sync deletion of '{component_name}': {str(e)}")
    
    # Data-driven methods (when architecture is active, use these instead of legacy methods)
    
    def add_lte_modem(self, position: tuple = None, name: str = None) -> str:
        """Add LTE modem component (data-driven version)"""
        if self.architecture_enabled and self.controller:
            if not position:
                # Get center of current view
                center = self.view.mapToScene(self.view.viewport().rect().center())
                position = (center.x(), center.y())
            if not name:
                name = f"LTE_Modem_{len(self.data_model.get_components_by_type('modem')) + 1}"
            
            properties = {
                'function_type': 'LTE',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 1}},
                'config': {'usid': f'LTE{len(self.data_model.get_all_components()) + 1:03d}'}
            }
            
            return self.controller.add_component(name, 'modem', position, properties)
        return ""
    
    def add_5g_modem(self, position: tuple = None, name: str = None) -> str:
        """Add 5G modem component (data-driven version)"""
        if self.architecture_enabled and self.controller:
            if not position:
                center = self.view.mapToScene(self.view.viewport().rect().center())
                position = (center.x() + 150, center.y())
            if not name:
                name = f"5G_Modem_{len(self.data_model.get_components_by_type('modem')) + 1}"
            
            properties = {
                'function_type': '5G',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 2}},
                'config': {'usid': f'5G{len(self.data_model.get_all_components()) + 1:03d}'}
            }
            
            return self.controller.add_component(name, 'modem', position, properties)
        return ""
    
    def add_rfic_chip_data_driven(self, position: tuple = None, name: str = None) -> str:
        """Add RFIC chip component (data-driven version)"""
        if self.architecture_enabled and self.controller:
            if not position:
                center = self.view.mapToScene(self.view.viewport().rect().center())
                position = (center.x(), center.y() + 150)
            if not name:
                name = f"RFIC_{len(self.data_model.get_components_by_type('rfic')) + 1}"
            
            properties = {
                'function_type': 'RFIC',
                'frequency_range': '600MHz - 6GHz',
                'technology': 'CMOS',
                'package': 'BGA',
                'rf_bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B8', 'B20', 'B28']
            }
            
            return self.controller.add_component(name, 'rfic', position, properties)
        return ""
    
    def add_generic_chip_data_driven(self, position: tuple = None, name: str = None) -> str:
        """Add generic chip component (data-driven version)"""
        if self.architecture_enabled and self.controller:
            if not position:
                center = self.view.mapToScene(self.view.viewport().rect().center())
                position = (center.x() + 300, center.y())
            if not name:
                name = f"Chip_{len(self.data_model.get_all_components()) + 1}"
            
            properties = {'function_type': 'generic'}
            
            return self.controller.add_component(name, 'chip', position, properties)
        return ""
    
    def sync_with_legacy_bcf(self):
        """Sync with Legacy BCF (data-driven version)"""
        if self.architecture_enabled and self.controller:
            self.controller.sync_with_legacy_bcf()
    
    def import_from_legacy_bcf(self, component_names: List[str] = None):
        """Import components from Legacy BCF (data-driven version) with duplicate prevention"""
        if self.architecture_enabled and self.controller:
            try:
                # Get Legacy BCF device settings
                device_settings = self.rdb_manager.get_table("config.device.settings")
                
                # Get existing components to avoid duplicates
                existing_components = self.data_model.get_all_components()
                existing_names = {comp.name for comp in existing_components.values()}
                
                imported_count = 0
                skipped_count = 0
                
                for i, device in enumerate(device_settings):
                    device_name = device.get('name', f'Device_{i}')
                    
                    # Skip if specific components requested and this isn't one of them
                    if component_names and device_name not in component_names:
                        continue
                    
                    # Skip if component already exists (prevent duplicates)
                    if device_name in existing_names:
                        skipped_count += 1
                        continue
                    
                    # Determine component type based on function type
                    function_type = device.get('function_type', '').upper()
                    if function_type in ['LTE', '5G']:
                        component_type = 'modem'
                    elif function_type == 'RFIC':
                        component_type = 'rfic'
                    else:
                        component_type = 'device'
                    
                    # Create component with Legacy BCF properties
                    properties = {
                        'function_type': function_type,
                        'interface_type': device.get('interface_type', ''),
                        'interface': device.get('interface', {}),
                        'config': device.get('config', {})
                    }
                    
                    # Add with automatic positioning
                    position = (100 + (imported_count * 150), 100 + (imported_count * 100))
                    
                    component_id = self.controller.add_component(
                        name=device_name,
                        component_type=component_type,
                        position=position,
                        properties=properties
                    )
                    
                    if component_id:
                        imported_count += 1
                        existing_names.add(device_name)  # Track newly added
                
                if imported_count > 0 or skipped_count > 0:
                    self.data_changed.emit({
                        "action": "import_legacy",
                        "count": imported_count,
                        "skipped": skipped_count,
                        "message": f"Imported {imported_count} new devices, skipped {skipped_count} duplicates",
                        "source": "data_driven"
                    })
                    
            except Exception as e:
                self.error_occurred.emit(f"Failed to import from Legacy BCF: {str(e)}")
    
    def auto_import_on_startup(self):
        """Auto-import devices from Legacy BCF on startup (fixes issue #1)"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔄 Auto-importing devices from Legacy BCF on startup...")
            
            # Check if there are any Legacy BCF devices to import
            device_settings = self.rdb_manager.get_table("config.device.settings")
            
            if device_settings:
                # Import all devices from Legacy BCF
                self.import_from_legacy_bcf()
                logger.info(f"Imported {len(device_settings)} devices from Legacy BCF")
            else:
                # No Legacy BCF devices exist, add default RFIC instead
                logger.info("No Legacy BCF devices found, adding default RFIC")
                self._add_default_rfic_data_driven()
            
            # Emit startup import complete signal
            self.data_changed.emit({
                "action": "auto_import_startup",
                "message": "Auto-imported devices from Legacy BCF on startup",
                "source": "data_driven"
            })
            
            logger.info("✅ Auto-import on startup completed")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during auto-import on startup: {e}")
            self.error_occurred.emit(f"Auto-import failed: {str(e)}")
    
    def remove_component_by_name(self, name: str) -> bool:
        """Remove component by name (fixes issue #3 and #4)"""
        if self.architecture_enabled and self.controller:
            return self.controller.remove_component_by_name(name)
        return False
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics from data model"""
        if self.architecture_enabled and self.controller:
            return self.controller.get_statistics()
        return {}
    
    def is_architecture_enabled(self) -> bool:
        """Check if data-driven architecture is enabled"""
        return self.architecture_enabled
    
    def get_data_model(self) -> Optional[VisualBCFDataModel]:
        """Get the data model (if architecture enabled)"""
        return self.data_model
    
    def get_controller(self) -> Optional[VisualBCFController]:
        """Get the controller (if architecture enabled)"""
        return self.controller
    
    def clear_scene_data_driven(self):
        """Clear scene using data-driven controller"""
        if self.architecture_enabled and self.controller:
            self.controller.clear_scene()
        else:
            # Fallback to legacy method
            self._on_clear_scene()
    
    def fit_in_view(self):
        """Fit all components in view"""
        scene_rect = self.scene.itemsBoundingRect()
        if not scene_rect.isEmpty():
            self.view.fitInView(scene_rect, Qt.KeepAspectRatio)
    
    def reset_view(self):
        """Reset view transformation"""
        self.view.resetTransform()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Cleanup architecture components
            if self.architecture_enabled:
                if self.controller:
                    # Disconnect controller signals
                    try:
                        self.controller.operation_completed.disconnect()
                        self.controller.error_occurred.disconnect()
                        self.controller.component_selected.disconnect()
                    except:
                        pass
                
                if self.data_model:
                    # Data model cleanup is handled internally
                    pass
            
            # Clear all components from scene
            components = self.scene.get_components()[:]
            for component in components:
                self.scene.remove_component(component)

            # Close floating toolbar
            if self.rf_toolbar:
                self.rf_toolbar.close()
                self.rf_toolbar = None

            # Close chip selection dialog if open
            if self.chip_selection_dialog:
                self.chip_selection_dialog.close()
                self.chip_selection_dialog = None

            # Clear clipboard
            self.chip_clipboard = None

        except Exception as e:
            self.error_occurred.emit(f"Error during cleanup: {str(e)}")
