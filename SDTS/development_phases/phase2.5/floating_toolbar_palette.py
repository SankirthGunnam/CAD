#!/usr/bin/env python3
"""
Floating Toolbar using QPalette for background styling instead of CSS
This approach should be more reliable for background colors
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent, QPalette, QColor, QPainter
from typing import Optional

class FloatingToolbarPalette(QWidget):
    """
    Floating toolbar using QPalette for background instead of CSS.
    This approach should be more reliable for showing background colors.
    """

    # Signals for toolbar actions
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
    zoom_fit_requested = Signal()
    add_chip_requested = Signal()
    add_resistor_requested = Signal()
    add_capacitor_requested = Signal()
    delete_selected_requested = Signal()
    clear_scene_requested = Signal()
    copy_chip_requested = Signal()
    paste_chip_requested = Signal()
    select_mode_requested = Signal()
    connection_mode_requested = Signal()
    phase_info_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"🔧 FloatingToolbarPalette: Initializing with parent: {parent}")

        # Set object name for debugging
        self.setObjectName("FloatingToolbarPalette")

        # Set fixed size for the toolbar
        self.setFixedSize(500, 45)

        # Initialize current mode and dragging variables
        self.current_mode = "select"
        self._dragging = False
        self._drag_position = QPoint()

        # Setup UI first
        self.setup_ui()

        # Apply QPalette background styling
        self.apply_palette_styling()

        print(f"🔧 FloatingToolbarPalette: Initialization complete")

    def setup_ui(self):
        """Setup the complete toolbar UI with all buttons and functionality"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        # Add move handle at the beginning - use QLabel for dragging
        self.move_handle = QLabel("⋮⋮", self)
        self.move_handle.setToolTip("Drag to move toolbar")
        self.move_handle.setFixedSize(20, 35)
        self.move_handle.setObjectName("MoveHandle")
        self.move_handle.setAlignment(Qt.AlignCenter)
        self.move_handle.setCursor(Qt.SizeAllCursor)
        layout.addWidget(self.move_handle)

        # Separator after handle
        sep_handle = QFrame()
        sep_handle.setFrameShape(QFrame.VLine)
        sep_handle.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep_handle)

        # Mode selection group
        self.select_btn = QPushButton("S", self)
        self.select_btn.setToolTip("Select Mode (S)")
        self.select_btn.setCheckable(True)
        self.select_btn.setChecked(True)
        self.select_btn.setFixedSize(30, 35)
        self.select_btn.clicked.connect(self._on_select_mode)
        layout.addWidget(self.select_btn)

        self.connection_btn = QPushButton("C", self)
        self.connection_btn.setToolTip("Connection Mode (C)")
        self.connection_btn.setCheckable(True)
        self.connection_btn.setFixedSize(30, 35)
        self.connection_btn.clicked.connect(self._on_connection_mode)
        layout.addWidget(self.connection_btn)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep1)

        # Component add buttons
        self.add_chip_btn = QPushButton("🔲", self)
        self.add_chip_btn.setToolTip("Add Chip")
        self.add_chip_btn.setCheckable(True)
        self.add_chip_btn.setFixedSize(30, 35)
        self.add_chip_btn.clicked.connect(self._on_add_chip_clicked)
        layout.addWidget(self.add_chip_btn)

        self.add_resistor_btn = QPushButton("R", self)
        self.add_resistor_btn.setToolTip("Add Resistor")
        self.add_resistor_btn.setCheckable(True)
        self.add_resistor_btn.setFixedSize(30, 35)
        self.add_resistor_btn.clicked.connect(self._on_add_resistor_clicked)
        layout.addWidget(self.add_resistor_btn)

        self.add_capacitor_btn = QPushButton("C", self)
        self.add_capacitor_btn.setToolTip("Add Capacitor")
        self.add_capacitor_btn.setCheckable(True)
        self.add_capacitor_btn.setFixedSize(30, 35)
        self.add_capacitor_btn.clicked.connect(self._on_add_capacitor_clicked)
        layout.addWidget(self.add_capacitor_btn)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)

        # Zoom controls
        self.zoom_in_btn = QPushButton("+", self)
        self.zoom_in_btn.setToolTip("Zoom In (+)")
        self.zoom_in_btn.setFixedSize(30, 35)
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("−", self)
        self.zoom_out_btn.setToolTip("Zoom Out (-)")
        self.zoom_out_btn.setFixedSize(30, 35)
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        layout.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = QPushButton("0", self)
        self.zoom_reset_btn.setToolTip("Reset Zoom (0)")
        self.zoom_reset_btn.setFixedSize(30, 35)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset_requested.emit)
        layout.addWidget(self.zoom_reset_btn)

        self.zoom_fit_btn = QPushButton("F", self)
        self.zoom_fit_btn.setToolTip("Zoom Fit (F)")
        self.zoom_fit_btn.setFixedSize(30, 35)
        self.zoom_fit_btn.clicked.connect(self.zoom_fit_requested.emit)
        layout.addWidget(self.zoom_fit_btn)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep3)

        # Component operations
        self.delete_selected_btn = QPushButton("Del", self)
        self.delete_selected_btn.setToolTip("Delete Selected (Del)")
        self.delete_selected_btn.setFixedSize(30, 35)
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.clicked.connect(self.delete_selected_requested.emit)
        layout.addWidget(self.delete_selected_btn)

        self.clear_scene_btn = QPushButton("Clr", self)
        self.clear_scene_btn.setToolTip("Clear Scene")
        self.clear_scene_btn.setFixedSize(30, 35)
        self.clear_scene_btn.clicked.connect(self.clear_scene_requested.emit)
        layout.addWidget(self.clear_scene_btn)

        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.VLine)
        sep4.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep4)

        # Edit operations
        self.copy_btn = QPushButton("Cp", self)
        self.copy_btn.setToolTip("Copy (Ctrl+C)")
        self.copy_btn.setFixedSize(30, 35)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_chip_requested.emit)
        layout.addWidget(self.copy_btn)

        self.paste_btn = QPushButton("Ps", self)
        self.paste_btn.setToolTip("Paste (Ctrl+V)")
        self.paste_btn.setFixedSize(30, 35)
        self.paste_btn.setEnabled(False)
        self.paste_btn.clicked.connect(self.paste_chip_requested.emit)
        layout.addWidget(self.paste_btn)

        # Separator
        sep5 = QFrame()
        sep5.setFrameShape(QFrame.VLine)
        sep5.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep5)

        # Info button
        self.phase_info_btn = QPushButton("ℹ", self)
        self.phase_info_btn.setToolTip("Phase Info")
        self.phase_info_btn.setFixedSize(30, 35)
        self.phase_info_btn.clicked.connect(self.phase_info_requested.emit)
        layout.addWidget(self.phase_info_btn)

    def apply_palette_styling(self):
        """
        Apply background styling using QPalette - this should be more reliable than CSS
        """
        print("🎨 FloatingToolbarPalette: Applying QPalette background styling...")

        # Enable auto fill background
        self.setAutoFillBackground(True)

        # Create and configure palette with bright visible colors
        palette = self.palette()

        # Set background color to bright blue
        palette.setColor(QPalette.Window, QColor(0, 100, 255))  # Bright blue
        palette.setColor(QPalette.Base, QColor(0, 100, 255))    # Bright blue
        palette.setColor(QPalette.Button, QColor(0, 80, 200))   # Darker blue for buttons
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White button text

        # Apply the palette
        self.setPalette(palette)

        # Also set individual button styling using QPalette
        for button in self.findChildren(QPushButton):
            button_palette = button.palette()
            button_palette.setColor(QPalette.Button, QColor(50, 150, 255))  # Light blue buttons
            button_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White text
            button.setPalette(button_palette)
            button.setAutoFillBackground(True)

        # Style the move handle
        handle_palette = self.move_handle.palette()
        handle_palette.setColor(QPalette.Window, QColor(255, 255, 0))  # Yellow handle
        handle_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))  # Black text
        self.move_handle.setPalette(handle_palette)
        self.move_handle.setAutoFillBackground(True)

        print("🎨 FloatingToolbarPalette: QPalette styling applied successfully")

    def paintEvent(self, event):
        """Custom paint event to ensure background is drawn"""
        super().paintEvent(event)

        # Additional painting to ensure visibility
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 0, 0))  # Red fallback background
        painter.end()

    # Event handlers for toolbar actions (same as before)
    def _on_select_mode(self):
        """Handle select mode action"""
        self.current_mode = "select"
        self.connection_btn.setChecked(False)
        self._clear_component_selection()
        self.select_mode_requested.emit()

    def _on_connection_mode(self):
        """Handle connection mode action"""
        self.current_mode = "connection"
        self.select_btn.setChecked(False)
        self._clear_component_selection()
        self.connection_mode_requested.emit()

    def _on_add_chip_clicked(self):
        """Handle add chip button click"""
        self.current_mode = "add_chip"
        self._clear_mode_selection()
        self._clear_component_selection()
        self.add_chip_btn.setChecked(True)
        self.add_chip_requested.emit()

    def _on_add_resistor_clicked(self):
        """Handle add resistor button click"""
        self.current_mode = "add_resistor"
        self._clear_mode_selection()
        self._clear_component_selection()
        self.add_resistor_btn.setChecked(True)
        self.add_resistor_requested.emit()

    def _on_add_capacitor_clicked(self):
        """Handle add capacitor button click"""
        self.current_mode = "add_capacitor"
        self._clear_mode_selection()
        self._clear_component_selection()
        self.add_capacitor_btn.setChecked(True)
        self.add_capacitor_requested.emit()

    def _clear_mode_selection(self):
        """Clear mode button selections"""
        self.select_btn.setChecked(False)
        self.connection_btn.setChecked(False)

    def _clear_component_selection(self):
        """Clear component button selections"""
        self.add_chip_btn.setChecked(False)
        self.add_resistor_btn.setChecked(False)
        self.add_capacitor_btn.setChecked(False)

    # Public methods for external state management
    def set_selection_available(self, available: bool):
        """Enable/disable selection-dependent actions"""
        self.delete_selected_btn.setEnabled(available)
        self.copy_btn.setEnabled(available)

    def set_paste_available(self, available: bool):
        """Enable/disable paste action"""
        self.paste_btn.setEnabled(available)

    def get_current_mode(self) -> str:
        """Get the current mode"""
        return self.current_mode

    def position_at_center_top(self, parent_widget):
        """Position the toolbar at the center top of the parent widget"""
        if not parent_widget:
            print("🔧 FloatingToolbarPalette: No parent widget provided for positioning")
            return

        # Get toolbar dimensions
        toolbar_width = self.width() if self.width() > 0 else self.sizeHint().width()
        toolbar_height = self.height() if self.height() > 0 else self.sizeHint().height()

        # Get parent widget dimensions
        parent_rect = parent_widget.rect()

        # Calculate center position
        x = (parent_rect.width() - toolbar_width) // 2
        y = 20  # 20px from top

        # Position relative to parent
        self.move(x, y)

        print(f"🔧 FloatingToolbarPalette: Positioned at ({x}, {y}) within parent {parent_rect}")

        # Ensure toolbar is visible and on top
        self.raise_()
        self.show()

    # Mouse events for dragging functionality (same as before)
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging - only on move handle"""
        if event.button() == Qt.LeftButton:
            # Check if the click is on the move handle
            widget_under_mouse = self.childAt(event.pos())
            if widget_under_mouse == self.move_handle:
                self._dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.pos()
                event.accept()
                print("🔧 FloatingToolbarPalette: Started dragging")
                return

        # If not on move handle, pass to parent
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging - only when dragging started on move handle"""
        if self._dragging and event.buttons() == Qt.LeftButton:
            try:
                new_pos = event.globalPosition().toPoint() - self._drag_position
                self.move(new_pos)
                event.accept()
            except Exception as e:
                print(f"🔧 FloatingToolbarPalette: Drag error: {e}")
                pass
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging"""
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
            print("🔧 FloatingToolbarPalette: Stopped dragging")
        else:
            super().mouseReleaseEvent(event)


class TestMainWindow(QMainWindow):
    """Test window to demonstrate the QPalette-based floating toolbar"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Floating Toolbar Test - QPalette Implementation")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget with graphics view
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create graphics view
        self.graphics_view = QGraphicsView()
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        layout.addWidget(self.graphics_view)

        # Create the floating toolbar using QPalette approach
        self.floating_toolbar = FloatingToolbarPalette(self.graphics_view)

        # Connect signals for testing
        self.floating_toolbar.add_chip_requested.connect(self.on_add_chip)
        self.floating_toolbar.zoom_in_requested.connect(self.on_zoom_in)
        self.floating_toolbar.zoom_out_requested.connect(self.on_zoom_out)
        self.floating_toolbar.delete_selected_requested.connect(self.on_delete_selected)

        # Position the toolbar after the window is shown
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.position_toolbar)

    def position_toolbar(self):
        """Position the floating toolbar in the center top of the graphics view"""
        self.floating_toolbar.position_at_center_top(self.graphics_view)

    def on_add_chip(self):
        """Handle add chip request"""
        print("🔧 Test: Add chip requested")

    def on_zoom_in(self):
        """Handle zoom in request"""
        print("🔧 Test: Zoom in requested")
        self.graphics_view.scale(1.2, 1.2)

    def on_zoom_out(self):
        """Handle zoom out request"""
        print("🔧 Test: Zoom out requested")
        self.graphics_view.scale(0.8, 0.8)

    def on_delete_selected(self):
        """Handle delete selected request"""
        print("🔧 Test: Delete selected requested")


def main():
    """Main function to test the QPalette-based floating toolbar implementation"""
    app = QApplication(sys.argv)

    print("🚀 Starting Floating Toolbar Test (QPalette Implementation)...")

    # Create and show test window
    window = TestMainWindow()
    window.show()

    print("📋 Test Instructions:")
    print("1. The floating toolbar should appear with a RED background (from paintEvent)")
    print("2. The handle should be YELLOW and buttons should have color")
    print("3. You should be able to drag it using the '⋮⋮' handle on the left")
    print("4. All buttons should be functional")
    print("5. Close the window to exit")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
