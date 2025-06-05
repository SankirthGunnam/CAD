import time
from PySide6.QtCore import QObject, Signal, QThread, Slot
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
import logging
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from .build.build_master import BuildMaster
from .state_machine import StateMachine, ToolState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadWorker(QObject):
    event_signal = Signal(dict)
    finished = Signal()

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        self.event_signal.emit({"type": "status", "message": "Loading started"})
        time.sleep(3)  # Simulate long task
        self.event_signal.emit({"type": "status", "message": "Loading completed"})
        self.finished.emit()


class BuildWorker(QObject):
    event_signal = Signal(dict)
    finished = Signal()

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.build_master = BuildMaster(self)

    def run(self):
        self.event_signal.emit({"type": "status", "message": "Build started"})
        for i in range(10):
            print("Build Progress: ", i)
            time.sleep(1)
        self.event_signal.emit({"type": "status", "message": "Build completed"})
        self.finished.emit()


class ExportWorker(QObject):
    event_signal = Signal(dict)
    finished = Signal()

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        self.event_signal.emit({"type": "status", "message": "Export started"})
        for i in range(10):
            print("Export Progress: ", i)
            time.sleep(1)
        self.event_signal.emit({"type": "status", "message": "Export completed"})
        self.finished.emit()


class ConfigureWorker(QObject):
    event_signal = Signal(dict)
    finished = Signal()

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        self.event_signal.emit({"type": "status", "message": "Configure started"})
        for i in range(10):
            print("Configure Progress: ", i)
            time.sleep(1)
        self.event_signal.emit({"type": "status", "message": "Configure completed"})
        self.finished.emit()


class CoreController(QObject):
    """RBM Core Controller that manages the state and processing of core events"""

    # Signals for communication
    state_changed = Signal(ToolState)  # Signal when state changes
    reply_signal = Signal(dict)  # Signal to send replies
    build_event = Signal(dict)  # Single signal for all build events

    def __init__(self, rdb_manager: RDBManager):
        super().__init__()
        self.rdb_manager = rdb_manager
        self.error_message = ""

        # Initialize state machine
        self.state_machine = StateMachine()
        self.state_machine.state_changed.connect(self._on_state_changed)
        self.state_machine.transition_failed.connect(self._on_transition_failed)

        self.load_worker: Optional[LoadWorker] = None
        self.build_worker: Optional[BuildWorker] = None
        self.export_worker: Optional[ExportWorker] = None

        self.load_thread: Optional[QThread] = None
        self.build_thread: Optional[QThread] = None
        self.export_thread: Optional[QThread] = None

        # Initialize build master
        self.setup_connections()

    def setup_connections(self):
        """Setup signal connections with BuildMaster"""
        self.build_master.build_event.connect(self._on_build_event)

    def _on_state_changed(self, old_state: ToolState, new_state: ToolState):
        """Handle state changes from state machine"""
        logger.info(f"State changed from {old_state.name} to {new_state.name}")

        if new_state == ToolState.ERROR:
            self._handle_error()

    def _handle_error(self):
        """Handle business logic for ERROR state"""
        self.error_message = self.state_machine.get_state_data(
            "error_message", "Unknown error"
        )
        self.reply_signal.emit({"status": "error", "message": self.error_message})

    def _on_transition_failed(self, error_message: str):
        """Handle failed state transitions"""
        logger.error(f"State transition failed: {error_message}")
        self.state_machine.transition("error", {"error_message": error_message})

    def _on_build_event(self, event: Dict[str, Any]):
        """Handle all build events"""
        event_type = event.get("type")

        if event_type == "build_started":
            self.state_machine.transition("build")
            self.build_event.emit(
                {"type": "status", "message": f"Build started: {event.get('message')}"}
            )

        elif event_type == "build_completed":
            self.state_machine.transition("complete")
            self.build_event.emit(
                {
                    "type": "status",
                    "message": f"Build completed: {event.get('message')}",
                }
            )

        elif event_type == "build_failed":
            self.state_machine.transition(
                "error", {"error_message": event.get("message")}
            )
            self.build_event.emit(
                {
                    "type": "error",
                    "message": event.get("message"),
                    "details": event.get("details"),
                }
            )

        elif event_type == "build_warning":
            self.build_event.emit({"type": "warning", "message": event.get("message")})

        elif event_type == "file_generated":
            self.build_event.emit({"type": "file", "file_path": event.get("file_path")})

    def process_event(self, event: Dict[str, Any]) -> None:
        """Process an incoming event based on current state"""
        event_type = event.get("type")
        event_data = event.get("data", {})

        try:
            # Attempt state transition
            if self.state_machine.transition(event_type, event_data):
                # Handle successful transition
                if event_type == "load":
                    self.start_load(event_data)
                elif event_type == "build":
                    self.start_build(event_data)
                elif event_type == "configure":
                    self._handle_configure(event_data)
                elif event_type == "export":
                    self._handle_export(event_data)
                elif event_type == "recover":
                    self._handle_recover(event_data)

                self._send_reply(
                    {
                        "status": "success",
                        "message": f"Event {event_type} processed successfully",
                    }
                )
            else:
                self._send_reply(
                    {
                        "status": "error",
                        "message": f"Event {event_type} not handled in current state",
                    }
                )

        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")
            self.state_machine.transition("error", {"error_message": str(e)})

    def _send_reply(self, reply: Dict[str, Any]) -> None:
        """Send a reply through the signal"""
        self.reply_signal.emit(reply)

    def handle_build_error(self, error_msg: str):
        """Handle build error from BuildMaster"""
        self.state_machine.transition("error", {"error_message": error_msg})

    def start_load(self, data: Dict[str, Any]):
        try:
            self.load_thread = QThread()
            self.load_worker = LoadWorker(data)
            self.load_worker.moveToThread(self.load_thread)
            self.load_worker.event_signal.connect(self.load_event.emit)
            self.load_worker.finished.connect(self.load_thread.quit)
            self.load_worker.finished.connect(self.load_worker.deleteLater)
            self.load_thread.finished.connect(self.load_thread.deleteLater)
            self.load_thread.started.connect(self.load_worker.run)
            self.load_thread.start()
        except Exception as e:
            self.state_machine.transition(
                "error", {"error_message": f"Failed to start load: {str(e)}"}
            )

    def start_build(self, data: Dict[str, Any], output_dir: Optional[str] = None):
        """Start the build process"""
        try:
            self.build_thread = QThread()
            self.build_worker = BuildWorker(data)
            self.build_worker.moveToThread(self.build_thread)
            self.build_worker.event_signal.connect(self.build_event.emit)
            self.build_worker.finished.connect(self.build_thread.quit)
            self.build_worker.finished.connect(self.build_worker.deleteLater)
            self.build_thread.finished.connect(self.build_thread.deleteLater)
            self.build_thread.started.connect(self.build_worker.run)
            self.build_thread.start()
        except Exception as e:
            self.state_machine.transition(
                "error", {"error_message": f"Failed to start build: {str(e)}"}
            )

    def _handle_configure(self, data: Dict[str, Any]):
        """Handle configuration"""
        try:
            # Implement configuration logic here
            self.state_machine.transition("configure")
            self.export_thread = QThread()
            self.export_worker = ConfigureWorker(data)
            self.export_worker.moveToThread(self.export_thread)
            self.export_worker.event_signal.connect(self.export_event.emit)
            self.export_worker.finished.connect(self.export_thread.quit)
            self.export_worker.finished.connect(self.export_worker.deleteLater)
            self.export_thread.finished.connect(self.export_thread.deleteLater)
            self.export_thread.started.connect(self.export_worker.run)
            self.export_thread.start()
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_export(self, data: Dict[str, Any]):
        """Handle export"""
        try:
            self.state_machine.transition("export")
            # Implement export logic here
            self.export_thread = QThread()
            self.export_worker = ExportWorker(data)
            self.export_worker.moveToThread(self.export_thread)
            self.export_worker.event_signal.connect(self.export_event.emit)
            self.export_worker.finished.connect(self.export_thread.quit)
            self.export_worker.finished.connect(self.export_worker.deleteLater)
            self.export_thread.finished.connect(self.export_thread.deleteLater)
            self.export_thread.started.connect(self.export_worker.run)
            self.export_thread.start()
        except Exception as e:
            self.state_machine.transition(
                "error", {"error_message": f"Failed to start export: {str(e)}"}
            )

    def _handle_recover(self, data: Dict[str, Any]):
        """Handle recovery from error state"""
        self.error_message = ""
        self.state_machine.transition("recover")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the controller"""
        return {
            "state": self.state_machine.get_state().name,
            "error_message": self.error_message,
            "is_error": self.state_machine.get_state() == ToolState.ERROR,
            "build_status": self.build_master.get_build_status(),
        }

    def set_output_directory(self, output_dir: str):
        """Set the output directory for generated files"""
        self.build_master.set_output_directory(output_dir)
