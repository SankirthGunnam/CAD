from PySide6.QtWidgets import QGraphicsScene, QMenu, QApplication
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QAction
from typing import Optional, List, Dict

from apps.RBM.BCF.source.models.connection import Connection
from apps.RBM.BCF.source.models.pin import Pin
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip
from apps.RBM.BCF.gui.custom_widgets.components.pin import Pin as PinComponent
from apps.RBM.BCF.gui.custom_widgets.components.connection import (
    Connection as ConnectionComponent,
)


class RFScene(QGraphicsScene):
    """Scene for RF circuit components"""

    # Signals
    add_chip_requested = Signal(QPointF)  # Position where chip should be added
    chip_selected = Signal(object)  # Selected chip component
    selection_changed = Signal(bool)  # Whether there's a selection

    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(Qt.white)
        self.temp_connection = None
        self.start_pin = None
        self._mouse_pos = QPointF(0, 0)
        self._pins: Dict[Pin, PinComponent] = {}  # Map model pins to their widgets
        self._context_menu_pos = QPointF(0, 0)
        self._selected_components = []

        # Controller reference for user deletions (set by Visual BCF Manager)
        self._controller = None

    @property
    def mouse_pos(self) -> QPointF:
        return self._mouse_pos

    def set_controller(self, controller):
        """Set the controller reference for handling user deletions"""
        self._controller = controller

    def add_component(self, component):
        """Add a component to the scene"""
        self.addItem(component)
        # Create pin widgets for the component
        if isinstance(component, Chip):
            for pin in component.model.pins:
                if pin not in self._pins:
                    pin_widget = PinComponent(pin, self)
                    self._pins[pin] = pin_widget

    def remove_component(self, component) -> None:
        """Remove a component and its connections from the scene"""
        # Remove all connections and pin widgets
        if isinstance(component, Chip):
            for pin in component.model.pins:
                # Remove connections
                for connection in pin.connections[
                    :
                ]:  # Create a copy to avoid modification during iteration
                    connection.remove()
                # Remove pin widget
                if pin in self._pins:
                    self.removeItem(self._pins[pin])
                    del self._pins[pin]
        self.removeItem(component)

    def get_components(self) -> List[Chip]:
        """Get all components in the scene"""
        return [item for item in self.items() if isinstance(item, Chip)]

    def get_selected_components(self) -> List[Chip]:
        """Get all selected components in the scene"""
        return [item for item in self.selectedItems() if isinstance(item, Chip)]

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, PinComponent):
                self.start_pin = item
                # Create a connection starting from this pin widget
                self.temp_connection = ConnectionComponent(item)
                self.addItem(self.temp_connection)
                # Update the path to start from the pin's position
                self.temp_connection.update_path()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        self._mouse_pos = event.scenePos()
        if self.temp_connection:
            self.temp_connection.update_path()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton and self.temp_connection:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, PinComponent) and item != self.start_pin:
                # Only allow connections between pins
                if self.temp_connection.model.finish_connection(item.model):
                    self.temp_connection = None
                else:
                    self.temp_connection.model.remove()
                    self.removeItem(self.temp_connection)
                    self.temp_connection = None
            else:
                # If not released on a valid pin, remove the temporary connection
                self.temp_connection.model.remove()
                self.removeItem(self.temp_connection)
                self.temp_connection = None
            self.start_pin = None
        else:
            super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        self._context_menu_pos = event.scenePos()

        # Check if we right-clicked on a component
        item = self.itemAt(event.scenePos(), self.views()[0].transform() if self.views() else None)

        context_menu = QMenu()

        if isinstance(item, Chip):
            # Right-clicked on a chip
            context_menu.addAction("Select Chip", lambda: self._select_chip(item))
            context_menu.addSeparator()
            context_menu.addAction("Copy Chip", lambda: self._copy_chip(item))
            context_menu.addAction("Delete Chip", lambda: self._delete_chip(item))
            context_menu.addSeparator()
            context_menu.addAction("Chip Properties", lambda: self._show_chip_properties(item))
        else:
            # Right-clicked on empty space
            context_menu.addAction("Add Chip", self._request_add_chip)

            if self.get_selected_components():
                context_menu.addSeparator()
                context_menu.addAction("Delete Selected", self._delete_selected)
                context_menu.addAction("Copy Selected", self._copy_selected)

            context_menu.addSeparator()
            context_menu.addAction("Clear Selection", self.clearSelection)

        # Show the context menu
        if context_menu.actions():
            # Convert scene position to global position for menu display
            if self.views():
                view = self.views()[0]
                global_pos = view.mapToGlobal(view.mapFromScene(event.scenePos()))
                context_menu.exec(global_pos)

    def _request_add_chip(self):
        """Request to add a chip at the context menu position"""
        self.add_chip_requested.emit(self._context_menu_pos)

    def _select_chip(self, chip: Chip):
        """Select a specific chip"""
        self.clearSelection()
        chip.setSelected(True)
        self.chip_selected.emit(chip)
        self.selection_changed.emit(True)

    def _copy_chip(self, chip: Chip):
        """Copy a specific chip to clipboard"""
        # TODO: Implement chip copying
        print(f"Copying chip: {chip.model.name}")

    def _delete_chip(self, chip: Chip):
        """Delete a specific chip (user-initiated)"""
        if self._controller:
            # Use controller to handle deletion (emits proper signals for Legacy BCF sync)
            self._controller.delete_component_by_graphics_item(chip)
        else:
            # Fallback to direct removal if no controller
            self.remove_component(chip)
        self.selection_changed.emit(len(self.get_selected_components()) > 0)

    def _delete_selected(self):
        """Delete all selected chips (user-initiated)"""
        selected = self.get_selected_components()[:]
        if self._controller and selected:
            # Use controller to handle deletions (emits proper signals for Legacy BCF sync)
            deleted_count = self._controller.delete_selected_components_by_graphics_items(selected)
        else:
            # Fallback to direct removal if no controller
            for chip in selected:
                self.remove_component(chip)
        self.selection_changed.emit(False)

    def _copy_selected(self):
        """Copy all selected chips"""
        selected = self.get_selected_components()
        if selected:
            print(f"Copying {len(selected)} selected chips")
            # TODO: Implement multiple chip copying

    def _show_chip_properties(self, chip: Chip):
        """Show chip properties dialog"""
        try:
            # Import here to avoid circular imports
            from ..views.chip_properties_dialog import ChipPropertiesDialog

            # Get chip data from model metadata or create basic data
            chip_data = getattr(chip.model, 'metadata', {})
            if not chip_data:
                # Create basic chip data from model
                chip_data = {
                    'name': chip.model.name,
                    'part_number': chip.model.name,
                    'type': 'Custom',
                    'width': chip.model.width,
                    'height': chip.model.height,
                    'description': f'Custom chip component: {chip.model.name}'
                }

            # Create and show properties dialog
            dialog = ChipPropertiesDialog(chip_data, parent=self.views()[0] if self.views() else None)
            dialog.properties_updated.connect(lambda updated_data: self._update_chip_properties(chip, updated_data))
            dialog.exec()

        except Exception as e:
            print(f"Error showing chip properties: {e}")

    def _update_chip_properties(self, chip: Chip, updated_data: dict):
        """Update chip properties with new data"""
        try:
            # Update model metadata
            chip.model.metadata = updated_data

            # Update model name if changed
            if 'name' in updated_data:
                chip.model.name = updated_data['name']

            # Force a repaint of the chip
            chip.update()

            print(f"Updated properties for chip: {chip.model.name}")

        except Exception as e:
            print(f"Error updating chip properties: {e}")

    def selectionChanged(self):
        """Override selection changed to emit our signal"""
        super().selectionChanged()
        has_selection = len(self.get_selected_components()) > 0
        self.selection_changed.emit(has_selection)
