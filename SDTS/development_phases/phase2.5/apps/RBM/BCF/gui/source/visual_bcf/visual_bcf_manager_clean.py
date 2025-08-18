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

from apps.RBM.BCF.gui.source.visual_bcf.scene import RFScene
from apps.RBM.BCF.gui.source.visual_bcf.view import RFView
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.gui.custom_widgets.components.rfic_chip import RFICChip
from apps.RBM.BCF.source.models.chip import ChipModel
from apps.RBM.BCF.source.models.rfic_chip import RFICChipModel
from apps.RBM.BCF.gui.source.views.chip_selection_dialog import ChipSelectionDialog
from apps.RBM.BCF.gui.source.views.floating_toolbar import FloatingToolbar

# Import Architecture components
from apps.RBM.BCF.source.models.visual_bcf_data_model import VisualBCFDataModel
from apps.RBM.BCF.source.controllers.visual_bcf_controller import VisualBCFController
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager


class VisualBCFManager(QWidget):
    """
    Manager for the visual BCF interface with graphics scene and view.
    
    This class acts as the View layer in the MVC architecture, handling:
    - UI coordination and layout
    - Signal connections and event handling
    - View management (zoom, fit, reset)
    - Delegates all business logic to the Controller
    
    Architecture is always enabled - no fallback logic.
    """

    # Signals
    data_changed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, parent_controller=None, rdb_manager: Optional[RDBManager] = None):
        super().__init__(parent)
        self.setWindowTitle("Visual BCF Manager")
        self.parent_controller = parent_controller
        self.rdb_manager = rdb_manager

        # Architecture Components (always enabled)
        self.data_model: VisualBCFDataModel
        self.controller: VisualBCFController

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

        # Initialize architecture components (required)
        if not self.rdb_manager:
            raise ValueError("RDB manager is required for Visual BCF Manager")
        self._setup_architecture_components()

        # Chip selection dialog
        self.chip_selection_dialog = None

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

        # Auto-import from Legacy BCF on startup
        # This will handle adding components, including default RFIC if needed
        QTimer.singleShot(500, self.auto_import_on_startup)

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
        """Add the selected chip from dialog to the scene (delegate to controller)"""
        try:
            chip_name = f"{chip_data['name']} ({chip_data['part_number']})"
            
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
            
            # Add component via controller
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

        except Exception as e:
            self.error_occurred.emit(f"Error adding selected chip: {str(e)}")

    def _on_selection_changed(self, has_selection: bool):
        """Handle selection change in the scene"""
        # Update floating toolbar button states
        if self.rf_toolbar:
            self.rf_toolbar.set_selection_available(has_selection)

    def _on_delete_selected(self):
        """Delete selected chips (delegate to controller)"""
        try:
            # Use controller for proper bidirectional sync
            self.controller.delete_selected_components()
        except Exception as e:
            self.error_occurred.emit(f"Error deleting components: {str(e)}")

    def _on_copy_selected(self):
        """Copy selected chips to clipboard (delegate to controller)"""
        try:
            # Use controller for copy operation
            self.controller.copy_selected_components()
        except Exception as e:
            self.error_occurred.emit(f"Error copying components: {str(e)}")

    def _on_paste_chips(self):
        """Paste chips from clipboard (delegate to controller)"""
        try:
            # Use controller for paste operation
            self.controller.paste_components()
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
            
            # Connect user deletion signal to handle Legacy BCF synchronization
            self.controller.component_removed_by_user.connect(self._on_visual_component_removed_by_user)
            
            # Set controller reference in scene for user deletions
            self.scene.set_controller(self.controller)
            
            logger.info("Architecture components setup complete")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error setting up architecture components: {e}")
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
    
    # View Coordination Methods (delegate business logic to Controller)
    
    def add_lte_modem(self, position: tuple = None, name: str = None) -> str:
        """Add LTE modem component"""
        if not position:
            # Get center of current view
            center = self.view.mapToScene(self.view.viewport().rect().center())
            position = (center.x(), center.y())
        return self.controller.add_lte_modem(position, name)
    
    def add_5g_modem(self, position: tuple = None, name: str = None) -> str:
        """Add 5G modem component"""
        if not position:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            position = (center.x() + 150, center.y())
        return self.controller.add_5g_modem(position, name)
    
    def add_rfic_chip_data_driven(self, position: tuple = None, name: str = None) -> str:
        """Add RFIC chip component"""
        if not position:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            position = (center.x(), center.y() + 150)
        return self.controller.add_rfic_chip(position, name)
    
    def add_generic_chip_data_driven(self, position: tuple = None, name: str = None) -> str:
        """Add generic chip component"""
        if not position:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            position = (center.x() + 300, center.y())
        return self.controller.add_generic_chip(position, name)
    
    def sync_with_legacy_bcf(self):
        """Sync with Legacy BCF"""
        self.controller.sync_with_legacy_bcf()
    
    def import_from_legacy_bcf(self, component_names: List[str] = None):
        """Import components from Legacy BCF with duplicate prevention"""
        try:
            result = self.controller.import_from_legacy_bcf(component_names)
            
            if result['imported'] > 0 or result['skipped'] > 0:
                self.data_changed.emit({
                    "action": "import_legacy",
                    "count": result['imported'],
                    "skipped": result['skipped'],
                    "message": f"Imported {result['imported']} new devices, skipped {result['skipped']} duplicates",
                    "source": "data_driven"
                })
                
        except Exception as e:
            self.error_occurred.emit(f"Failed to import from Legacy BCF: {str(e)}")
    
    def auto_import_on_startup(self):
        """Auto-import devices from Legacy BCF on startup (delegate to controller)"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔄 Auto-importing devices from Legacy BCF on startup...")
            
            result = self.controller.auto_import_on_startup()
            
            # Emit startup import complete signal
            self.data_changed.emit({
                "action": "auto_import_startup",
                "message": "Auto-imported devices from Legacy BCF on startup",
                "imported": result['imported'],
                "skipped": result['skipped'],
                "source": "data_driven"
            })
            
            logger.info(f"✅ Auto-import completed: {result['imported']} imported, {result['skipped']} skipped")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during auto-import on startup: {e}")
            self.error_occurred.emit(f"Auto-import failed: {str(e)}")
    
    def remove_component_by_name(self, name: str) -> bool:
        """Remove component by name"""
        return self.controller.remove_component_by_name(name)
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics from data model"""
        return self.controller.get_statistics()
    
    def is_architecture_enabled(self) -> bool:
        """Check if data-driven architecture is enabled (always True)"""
        return True
    
    def get_data_model(self) -> VisualBCFDataModel:
        """Get the data model"""
        return self.data_model
    
    def get_controller(self) -> VisualBCFController:
        """Get the controller"""
        return self.controller
    
    def clear_scene_data_driven(self):
        """Clear scene using data-driven controller"""
        self.controller.clear_scene()
    
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
            if self.controller:
                # Disconnect controller signals
                try:
                    self.controller.operation_completed.disconnect()
                    self.controller.error_occurred.disconnect()
                    self.controller.component_selected.disconnect()
                except:
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

        except Exception as e:
            self.error_occurred.emit(f"Error during cleanup: {str(e)}")
