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

from apps.RBM5.BCF.gui.source.gui_controller import GUIController
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM5.BCF.source.RCC.core_controller import CoreController


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

        # Initialize managers and controllers
        self.rdb_manager = RDBManager()
        self.core_controller = CoreController(self.rdb_manager)

        # Create and add GUIController with RDB manager for Visual BCF MVC
        # architecture
        self.gui_controller = GUIController(rdb_manager=self.rdb_manager)
        layout.addWidget(self.gui_controller)

        # Connect signals
        self._setup_connections()

    def _setup_connections(self):
        """Setup all signal connections"""
        # GUI to Core connections
        self.gui_controller.build_requested.connect(self._on_build_requested)
        self.gui_controller.configure_requested.connect(
            self._on_configure_requested)
        self.gui_controller.export_requested.connect(self._on_export_requested)

        # Core to GUI connections
        self.core_controller.reply_signal.connect(self._on_core_reply)
        self.core_controller.build_event.connect(self._on_build_event)
        self.core_controller.state_changed.connect(self._on_state_changed)

        # Database connections
        self.rdb_manager.data_changed.connect(self._on_data_changed)
        self.rdb_manager.error_occurred.connect(self._on_error)

    def _on_build_requested(self, build_data: Dict[str, Any]):
        """Handle build request from GUI"""
        self.core_controller.process_event(
            {"type": "build", "data": build_data})

    def _on_configure_requested(self, config_data: Dict[str, Any]):
        """Handle configuration request from GUI"""
        self.core_controller.process_event(
            {"type": "configure", "data": config_data})

    def _on_export_requested(self, export_data: Dict[str, Any]):
        """Handle export request from GUI"""
        self.core_controller.process_event(
            {"type": "export", "data": export_data})

    def _on_core_reply(self, reply: Dict[str, Any]):
        """Handle replies from core controller"""
        status = reply.get("status")
        message = reply.get("message")

        if status == "error":
            self.gui_controller.show_error(message)
        else:
            self.gui_controller.show_status(message)

    def _on_build_event(self, event: Dict[str, Any]):
        """Handle build events from core controller"""
        event_type = event.get("type")

        if event_type == "status":
            self.gui_controller.show_status(event.get("message"))
        elif event_type == "error":
            self.gui_controller.show_error(event.get("message"))
        elif event_type == "warning":
            self.gui_controller.show_warning(event.get("message"))
        elif event_type == "file":
            self.gui_controller.add_generated_file(event.get("file_path"))

    def _on_state_changed(self, state):
        """Handle state changes from core controller"""
        self.gui_controller.update_state(state)

    def _on_data_changed(self, data: dict):
        """Handle data changes"""
        self.data_changed.emit(str(data))
        self.gui_controller.refresh_data()

    def _on_error(self, error_message: str):
        """Handle errors"""
        self.error_occurred.emit(error_message)
        self.gui_controller.show_error(error_message)

    def showEvent(self, event):
        """Connect to database when window is shown"""
        super().showEvent(event)
        # Initialize core controller
        self.core_controller.process_event({"type": "initialize"})

    def closeEvent(self, event):
        """Clean up when window is closed"""
        super().closeEvent(event)
        # Clean up resources
        self.rdb_manager.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = RBMMain()
    main.show()
    sys.exit(app.exec())
