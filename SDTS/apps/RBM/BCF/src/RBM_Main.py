import sys
import threading
from queue import Queue, PriorityQueue
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStackedWidget,
)
from PySide6.QtCore import QObject, Signal, Slot, QThread

from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from apps.RBM.BCF.src.RCC.core_controller import CoreController
from apps.RBM.BCF.gui.src.gui_controller import GUIController
from apps.RBM.BCF.gui.src.styles import load_stylesheet
from apps.RBM.BCF.src.views.chip_table_view import ChipTableView
from apps.RBM.BCF.src.models.chip_table_model import ChipTableModel
from apps.RBM.BCF.src.init_db import init_database


class RBMMain(QWidget):
    """Main controller that coordinates all application entities"""

    # Signals for communication between controllers
    core_event_signal = Signal(dict)  # Signal to send events to RCC
    rcc_reply_signal = Signal(dict)  # Signal to receive replies from RCC
    gui_event_signal = Signal(dict)  # Signal to send events to GUI
    db_event_signal = Signal(dict)  # Signal to send events to RDB

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize event queues
        self.event_queue = PriorityQueue()  # For prioritized events
        self.gui_events = Queue()  # For GUI events
        self.rcc_events = Queue()  # For RCC events
        self.rdb_events = Queue()  # For RDB events

        # Initialize threads for RCC and RDB
        self.rcc_thread = QThread()
        self.rdb_thread = QThread()
        self.rcc_thread.start()
        self.rdb_thread.start()

        # Initialize controllers in their respective threads
        self.rdb_manager = RDBManager()
        self.rdb_manager.moveToThread(self.rdb_thread)

        self.core_controller = CoreController(self.rdb_manager)
        self.core_controller.moveToThread(self.rcc_thread)

        # Connect signals
        self.core_event_signal.connect(self.handle_core_event)
        self.rcc_reply_signal.connect(self.handle_rcc_reply)

        # Initialize GUI controller (stays in main thread)
        self.gui_controller = GUIController(self.rdb_manager, self.core_controller)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add gui_controller to layout
        layout.addWidget(self.gui_controller)

        # Event history for tracking
        self.event_history: List[Dict[str, Any]] = []

    def setup_bcf_tool(self):
        """Setup the BCF tool tab"""
        pass

    def setup_cad_tool(self):
        """Setup the CAD tool tab"""
        pass

    def start_controllers(self):
        """Start RCC and RDB threads (GUI runs in main thread)"""
        self.rcc_thread.start()
        self.rdb_thread.start()

    def stop_controllers(self):
        """Stop RCC and RDB threads"""
        self.rcc_thread.quit()
        self.rdb_thread.quit()
        self.rcc_thread.wait()
        self.rdb_thread.wait()

    @Slot(dict)
    def handle_core_event(self, event: dict):
        """Handle events sent to RCC"""
        self.event_history.append({"type": "core_event", "event": event})
        self.core_controller.process_event(event)

    @Slot(dict)
    def handle_rcc_reply(self, reply: dict):
        """Handle replies from RCC"""
        self.event_history.append({"type": "rcc_reply", "reply": reply})
        # Process reply based on status
        if reply.get("status") == "success":
            self.process_successful_reply(reply)
        else:
            self.process_failed_reply(reply)

    def process_successful_reply(self, reply: dict):
        """Process successful replies from RCC"""
        # Implement logic for successful replies
        pass

    def process_failed_reply(self, reply: dict):
        """Process failed replies from RCC"""
        # Implement error handling and recovery
        pass

    def get_controller_status(self) -> Dict[str, Any]:
        """Get current status of all controllers"""
        return {
            "gui_status": self.gui_controller.get_status(),
            "rcc_status": self.core_controller.get_status(),
            "rdb_status": self.rdb_manager.get_status(),
        }

    def get_event_history(self) -> List[Dict[str, Any]]:
        """Get the complete event history"""
        return self.event_history

    def recover_controller(self, controller_name: str):
        """Recover a failed controller"""
        if controller_name == "gui":
            self.gui_controller.recover()
        elif controller_name == "rcc":
            self.core_controller.recover()
        elif controller_name == "rdb":
            self.rdb_manager.recover()

    def showEvent(self, event):
        """Start controllers when window is shown"""
        super().showEvent(event)
        self.start_controllers()

    def closeEvent(self, event):
        """Cleanup when the window is closed"""
        self.stop_controllers()
        super().closeEvent(event)


if __name__ == "__main__":
    main = RBMMain()
    sys.exit(main.exec())
