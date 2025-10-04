from PySide6.QtWidgets import (

    QWidget,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QFrame,
    QLabel
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QMouseEvent
from typing import Optional, List, Dict, Any


class FloatingToolbar(QWidget):
    """Floating toolbar for all scene operations using QWidget for better stability"""

    # Signals for toolbar actions
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
    zoom_fit_requested = Signal()
    add_chip_requested = Signal()
    add_resistor_requested = Signal()
    add_capacitor_requested = Signal()
    add_component_requested = Signal(dict)  # component_data
    delete_selected_requested = Signal()
    clear_scene_requested = Signal()
    copy_chip_requested = Signal()
    paste_chip_requested = Signal()
    select_mode_requested = Signal()
    connection_mode_requested = Signal()
    phase_info_requested = Signal()
    save_scene_requested = Signal()
    load_scene_requested = Signal()

    def __init__(self, parent=None, device_data_provider=None):
        super().__init__(parent)
        
        # Store reference to device data provider (VisualBCFController)
        self.device_data_provider = device_data_provider

        # Set object name for CSS targeting
        self.setObjectName("FloatingToolbar")

        # Keep it simple - no special window flags, just a regular widget
        # This will be positioned as an overlay within the parent widget

        # Set size constraints - make toolbar flexible
        self.setMinimumSize(400, 40)  # Reduced minimum width for better fit
        self.setMaximumSize(800, 60)  # Maximum width to prevent overflow
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed)

        # Track current mode
        self.current_mode = "select"

        # Variables for dragging
        self._dragging = False
        self._drag_position = QPoint()

        self._setup_ui()
        self._apply_styling()

        # Enable mouse tracking for the entire toolbar
        self.setMouseTracking(True)

    def _setup_ui(self):
        """Setup the user interface with buttons"""
        root_layout = QHBoxLayout()
        # Reduced left margin for handle
        root_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root_layout)
        self.central_widget = QWidget()
        root_layout.addWidget(self.central_widget)
        layout = QHBoxLayout()
        self.central_widget.setLayout(layout)
        layout.setContentsMargins(2, 2, 5, 2)  # Reduced left margin for handle
        layout.setSpacing(3)

        # Add move handle at the beginning - use QLabel instead of QPushButton
        self.move_handle = QLabel("⋮⋮", self)
        self.move_handle.setToolTip("Drag to move toolbar")
        self.move_handle.setFixedSize(20, 30)
        self.move_handle.setObjectName("MoveHandle")
        self.move_handle.setAlignment(Qt.AlignCenter)
        # Set cursor to indicate draggable
        self.move_handle.setCursor(Qt.SizeAllCursor)
        # Enable mouse tracking for the handle
        self.move_handle.setMouseTracking(True)
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
        self.select_btn.setFixedSize(30, 30)
        self.select_btn.clicked.connect(self._on_select_mode)
        layout.addWidget(self.select_btn)

        self.connection_btn = QPushButton("C", self)
        self.connection_btn.setToolTip("Connection Mode (C)")
        self.connection_btn.setCheckable(True)
        self.connection_btn.setFixedSize(30, 30)
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
        self.add_chip_btn.setFixedSize(30, 30)
        self.add_chip_btn.clicked.connect(self._on_add_chip_clicked)
        layout.addWidget(self.add_chip_btn)

        self.add_resistor_btn = QPushButton("⧈", self)
        self.add_resistor_btn.setToolTip("Add Resistor")
        self.add_resistor_btn.setCheckable(True)
        self.add_resistor_btn.setFixedSize(30, 30)
        self.add_resistor_btn.clicked.connect(self._on_add_resistor_clicked)
        layout.addWidget(self.add_resistor_btn)

        self.add_capacitor_btn = QPushButton("⧇", self)
        self.add_capacitor_btn.setToolTip("Add Capacitor")
        self.add_capacitor_btn.setCheckable(True)
        self.add_capacitor_btn.setFixedSize(30, 30)
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
        self.zoom_in_btn.setFixedSize(30, 30)
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("−", self)
        self.zoom_out_btn.setToolTip("Zoom Out (-)")
        self.zoom_out_btn.setFixedSize(30, 30)
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        layout.addWidget(self.zoom_out_btn)

        self.zoom_reset_btn = QPushButton("⊡", self)
        self.zoom_reset_btn.setToolTip("Reset Zoom (0)")
        self.zoom_reset_btn.setFixedSize(30, 30)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset_requested.emit)
        layout.addWidget(self.zoom_reset_btn)

        self.zoom_fit_btn = QPushButton("⊞", self)
        self.zoom_fit_btn.setToolTip("Zoom Fit (F)")
        self.zoom_fit_btn.setFixedSize(30, 30)
        self.zoom_fit_btn.clicked.connect(self.zoom_fit_requested.emit)
        layout.addWidget(self.zoom_fit_btn)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep3)

        # Component operations
        self.delete_selected_btn = QPushButton("🗑", self)
        self.delete_selected_btn.setToolTip("Delete Selected (Del)")
        self.delete_selected_btn.setFixedSize(30, 30)
        self.delete_selected_btn.setEnabled(False)
        self.delete_selected_btn.clicked.connect(
            self.delete_selected_requested.emit)
        layout.addWidget(self.delete_selected_btn)

        self.clear_scene_btn = QPushButton("🗋", self)
        self.clear_scene_btn.setToolTip("Clear Scene")
        self.clear_scene_btn.setFixedSize(30, 30)
        self.clear_scene_btn.clicked.connect(self.clear_scene_requested.emit)
        layout.addWidget(self.clear_scene_btn)

        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.VLine)
        sep4.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep4)

        # Edit operations
        self.copy_btn = QPushButton("⧉", self)
        self.copy_btn.setToolTip("Copy (Ctrl+C)")
        self.copy_btn.setFixedSize(30, 30)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_chip_requested.emit)
        layout.addWidget(self.copy_btn)

        self.paste_btn = QPushButton("⧪", self)
        self.paste_btn.setToolTip("Paste (Ctrl+V)")
        self.paste_btn.setFixedSize(30, 30)
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
        self.phase_info_btn.setFixedSize(30, 30)
        self.phase_info_btn.clicked.connect(self.phase_info_requested.emit)
        layout.addWidget(self.phase_info_btn)

        # Separator
        sep6 = QFrame()
        sep6.setFrameShape(QFrame.VLine)
        sep6.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep6)

        # Scene operations
        self.save_scene_btn = QPushButton("💾", self)
        self.save_scene_btn.setToolTip("Save Scene")
        self.save_scene_btn.setFixedSize(30, 30)
        self.save_scene_btn.clicked.connect(self._on_save_scene)
        layout.addWidget(self.save_scene_btn)

        self.load_scene_btn = QPushButton("📂", self)
        self.load_scene_btn.setToolTip("Load Scene")
        self.load_scene_btn.setFixedSize(30, 30)
        self.load_scene_btn.clicked.connect(self.load_scene_requested.emit)
        layout.addWidget(self.load_scene_btn)

    def _on_save_scene(self):
        # Persist view scrollbars/zoom before emitting save
        try:
            if self.device_data_provider and hasattr(self.device_data_provider, 'save_view_state'):
                self.device_data_provider.save_view_state()
        except Exception:
            pass
        self.save_scene_requested.emit()

    def _apply_styling(self):
        """Apply custom styling to the toolbar"""
        # Set a solid background color and ensure the widget has
        # autoFillBackground enabled
        self.setAutoFillBackground(True)

        self.setStyleSheet("""
            QWidget {
                background-color: rgb(248, 249, 250);
                border: 2px solid lightgray;
                border-radius: 8px;
                padding: 3px;
            }

            QPushButton {
                background-color: transparent;
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 4px;
                color: black;
                font-weight: bold;
                font-size: 13px;
                padding: 2px;
                margin: 1px;
            }

            QPushButton:hover {
                background-color: rgba(255, 255, 255, 50);
                border-color: rgba(255, 255, 255, 150);
            }

            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 100);
                border-color: rgba(255, 255, 255, 200);
            }

            QPushButton:checked {
                background-color: rgba(255, 200, 0, 180);
                border-color: rgba(255, 220, 0, 200);
                color: black;
                font-weight: bold;
            }

            QPushButton:disabled {
                background-color: transparent;
                color: rgba(150, 150, 150, 120);
                border-color: rgba(150, 150, 150, 60);
            }

            /* Special styling for move handle (now QLabel) */
            QLabel#MoveHandle {
                border: 1px solid rgba(255, 255, 255, 150);
                border-radius: 3px;
                color: rgba(50, 50, 50, 220);
                font-size: 12px;
                font-weight: bold;
            }

            QFrame[frameShape="5"] {
                color: rgba(200, 200, 200, 150);
                max-width: 1px;
            }
        """)

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
        """Handle add chip button click - show component selection dialog"""
        self.current_mode = "add_component"
        self._clear_mode_selection()
        self._clear_component_selection()
        self.add_chip_btn.setChecked(True)
        self._show_component_selection_dialog()

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

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging - only on move handle"""
        if event.button() == Qt.LeftButton:
            # Check if the click is on the move handle
            widget_under_mouse = self.childAt(event.pos())

            if widget_under_mouse == self.move_handle:
                self._dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.pos()
                event.accept()
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
            except Exception:
                # Ignore any drag-related errors to prevent crashes
                pass
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging"""
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Custom paint event for rounded corners"""
        super().paintEvent(event)

    def _show_component_selection_dialog(self):
        """Show the component selection dialog"""
        if not self.device_data_provider:
            print("No device data provider available")
            return
            
        try:
            # Import here to avoid circular imports
            from apps.RBM5.BCF.gui.source.visual_bcf.chip_selection_dialog import ChipSelectionDialog
            import apps.RBM5.BCF.source.RDB.paths as paths
            
            # Get all devices data from the provider
            all_devices = self.device_data_provider.data_model.rdb_manager[paths.DCF_DEVICES]
            
            # Create and show dialog
            dialog = ChipSelectionDialog(all_devices, self)
            dialog.component_selected.connect(self._on_component_selected)
            dialog.exec()
            
        except Exception as e:
            print(f"Error showing component selection dialog: {e}")
            import traceback
            traceback.print_exc()

    def _on_component_selected(self, component_data: Dict[str, Any]):
        """Handle component selection from dialog"""
        print(f"Component selected: {component_data}")
        self.add_component_requested.emit(component_data)
