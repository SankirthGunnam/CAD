from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QSize, QPoint
from PySide6.QtGui import QMouseEvent
from typing import Optional

class FloatingToolbar(QWidget):
    """Floating toolbar for RF scene operations using QWidget for better stability"""
    
    # Signals for toolbar actions
    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_reset_requested = Signal()
    add_chip_requested = Signal()
    delete_chip_requested = Signal()
    copy_chip_requested = Signal()
    paste_chip_requested = Signal()
    select_mode_requested = Signal()
    connection_mode_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set window flags for floating behavior - safer combination
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Set size constraints
        self.setMinimumSize(400, 40)
        self.setMaximumHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Track current mode
        self.current_mode = "select"
        
        # Variables for dragging
        self._dragging = False
        self._drag_position = QPoint()
        
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the user interface with buttons"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
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
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep2)
        
        # Chip operations
        self.add_chip_btn = QPushButton("⊕", self)
        self.add_chip_btn.setToolTip("Add Chip (A)")
        self.add_chip_btn.setFixedSize(30, 30)
        self.add_chip_btn.clicked.connect(self.add_chip_requested.emit)
        layout.addWidget(self.add_chip_btn)
        
        self.delete_chip_btn = QPushButton("⊖", self)
        self.delete_chip_btn.setToolTip("Delete Selected Chip (Del)")
        self.delete_chip_btn.setFixedSize(30, 30)
        self.delete_chip_btn.setEnabled(False)
        self.delete_chip_btn.clicked.connect(self.delete_chip_requested.emit)
        layout.addWidget(self.delete_chip_btn)
        
        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)
        sep3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(sep3)
        
        # Edit operations
        self.copy_btn = QPushButton("⧉", self)
        self.copy_btn.setToolTip("Copy Chip (Ctrl+C)")
        self.copy_btn.setFixedSize(30, 30)
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self.copy_chip_requested.emit)
        layout.addWidget(self.copy_btn)
        
        self.paste_btn = QPushButton("⧪", self)
        self.paste_btn.setToolTip("Paste Chip (Ctrl+V)")
        self.paste_btn.setFixedSize(30, 30)
        self.paste_btn.setEnabled(False)
        self.paste_btn.clicked.connect(self.paste_chip_requested.emit)
        layout.addWidget(self.paste_btn)
        
    def _apply_styling(self):
        """Apply custom styling to the toolbar"""
        self.setStyleSheet("""
            FloatingToolbar {
                background-color: rgba(50, 50, 50, 200);
                border: 1px solid rgba(100, 100, 100, 150);
                border-radius: 6px;
            }
            
            QPushButton {
                background-color: rgba(70, 70, 70, 180);
                border: 1px solid rgba(120, 120, 120, 100);
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 2px;
                margin: 1px;
            }
            
            QPushButton:hover {
                background-color: rgba(90, 90, 90, 200);
                border-color: rgba(140, 140, 140, 150);
            }
            
            QPushButton:pressed {
                background-color: rgba(40, 40, 40, 220);
                border-color: rgba(160, 160, 160, 200);
            }
            
            QPushButton:checked {
                background-color: rgba(0, 120, 215, 180);
                border-color: rgba(0, 140, 255, 150);
            }
            
            QPushButton:disabled {
                background-color: rgba(50, 50, 50, 100);
                color: rgba(150, 150, 150, 100);
                border-color: rgba(80, 80, 80, 80);
            }
            
            QFrame[frameShape="5"] {
                color: rgba(120, 120, 120, 150);
                max-width: 1px;
            }
        """)
        
    def _on_select_mode(self):
        """Handle select mode action"""
        self.current_mode = "select"
        self.connection_btn.setChecked(False)
        self.select_mode_requested.emit()
        
    def _on_connection_mode(self):
        """Handle connection mode action"""
        self.current_mode = "connection"
        self.select_btn.setChecked(False)
        self.connection_mode_requested.emit()
        
    def set_selection_available(self, available: bool):
        """Enable/disable selection-dependent actions"""
        self.delete_chip_btn.setEnabled(available)
        self.copy_btn.setEnabled(available)
        
    def set_paste_available(self, available: bool):
        """Enable/disable paste action"""
        self.paste_btn.setEnabled(available)
        
    def get_current_mode(self) -> str:
        """Get the current mode"""
        return self.current_mode
        
    def position_at_center_top(self, parent_widget):
        """Position the toolbar at the center top of the parent widget"""
        toolbar_width = self.sizeHint().width()
        toolbar_height = self.sizeHint().height()
        
        # Get the parent widget's geometry in global coordinates
        parent_rect = parent_widget.geometry()
        parent_global_pos = parent_widget.mapToGlobal(parent_widget.rect().topLeft())
        
        # Calculate center position relative to the parent widget
        x = parent_global_pos.x() + (parent_rect.width() - toolbar_width) // 2
        y = parent_global_pos.y() + 20  # 20px from top of parent
        
        self.move(x, y)
        
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging"""
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
        if event.button() == Qt.LeftButton:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
    def paintEvent(self, event):
        """Custom paint event for rounded corners"""
        super().paintEvent(event)
