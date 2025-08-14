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
from typing import Dict, Any, Optional

from .scene import RFScene
from .view import RFView
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.gui.custom_widgets.components.rfic_chip import RFICChip
from apps.RBM.BCF.src.models.chip import ChipModel
from apps.RBM.BCF.src.models.rfic_chip import RFICChipModel
from ..views.chip_selection_dialog import ChipSelectionDialog
from ..views.floating_toolbar import FloatingToolbar


class VisualBCFManager(QWidget):
    """Manager for the visual BCF interface with graphics scene and view"""

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, parent_controller=None):
        super().__init__(parent)
        self.setWindowTitle("Visual BCF Manager")
        self.parent_controller = parent_controller

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

        # Chip selection dialog
        self.chip_selection_dialog = None

        # Chip clipboard for copy/paste
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

        # Initialize with default RFIC chip
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
        """Add default RFIC chip to the graphics scene on startup"""
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
            # Create a generic chip model based on selected chip data
            chip_name = f"{chip_data['name']} ({chip_data['part_number']})"

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
                "chip_data": chip_data
            })

        except Exception as e:
            self.error_occurred.emit(f"Error adding selected chip: {str(e)}")

    def _on_selection_changed(self, has_selection: bool):
        """Handle selection change in the scene"""
        # Update floating toolbar button states
        if self.rf_toolbar:
            self.rf_toolbar.set_selection_available(has_selection)

    def _on_delete_selected(self):
        """Delete selected chips"""
        try:
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
        """Copy selected chips to clipboard"""
        try:
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
        """Paste chips from clipboard"""
        try:
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

    def cleanup(self):
        """Clean up resources"""
        try:
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
