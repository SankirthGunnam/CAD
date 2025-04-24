import sys
import os
import threading
from queue import Queue, PriorityQueue
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtCore import QObject, Signal, Slot, QThread

from apps.RBM.BCF.gui.src.gui_controller import GUIController


class RBMMain(QWidget):
    """Main controller that coordinates all application entities"""

    # Signals for communication between controllers
    data_changed = Signal(str)  # Signal when data changes (path)
    error_occurred = Signal(str)  # Signal when error occurs (error_message)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create and add GUIController
        self.gui_controller = GUIController()
        layout.addWidget(self.gui_controller)

        # Connect signals
        self.gui_controller.data_changed.connect(self._on_data_changed)
        self.gui_controller.error_occurred.connect(self._on_error)

    def _on_data_changed(self, data: dict):
        """Handle data changes"""
        self.data_changed.emit(str(data))

    def _on_error(self, error_message: str):
        """Handle errors"""
        self.error_occurred.emit(error_message)

    def showEvent(self, event):
        """Connect to database when window is shown"""
        super().showEvent(event)

    def closeEvent(self, event):
        """Disconnect from database when window is closed"""
        super().closeEvent(event)


if __name__ == "__main__":
    main = RBMMain()
    sys.exit(main.exec())
