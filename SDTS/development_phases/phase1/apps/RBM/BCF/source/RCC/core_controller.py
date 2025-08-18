import time
from PySide6.QtCore import QObject, Signal, QThread, Slot, QWaitCondition, QMutex
from typing import Dict, Any, Callable, Optional, List, Tuple
from enum import Enum, auto
import logging
import queue
from dataclasses import dataclass
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager
from .build.build_master import BuildMaster
from .state_machine import StateMachine, ToolState, ToolEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2


@dataclass
class WorkerRequest:
    worker_type: str
    data: Dict[str, Any]
    priority: WorkerPriority
    callback: Optional[Callable] = None


class BaseWorker(QObject):
    event_signal = Signal(dict)
    finished = Signal()
    input_requested = Signal(str, str)  # request_id, message
    input_received = Signal(str, Any)  # request_id, value

    def __init__(self, data: Dict[str, Any]):
        super().__init__()
        self.data = data
        self._wait_condition = QWaitCondition()
        self._mutex = QMutex()
        self._paused = False
        self._input_queue = queue.Queue()
        self._current_request_id = None

    def pause(self):
        """Pause the worker execution"""
        self._mutex.lock()
        self._paused = True
        self._mutex.unlock()

    def resume(self):
        """Resume the worker execution"""
        self._mutex.lock()
        self._paused = False
        self._wait_condition.wakeAll()
        self._mutex.unlock()

    def wait_for_input(self, message: str) -> Any:
        """Request input from the core controller and wait for response"""
        request_id = str(time.time())
        self._current_request_id = request_id
        self.input_requested.emit(request_id, message)

        # Wait for input
        while True:
            self._mutex.lock()
            if self._paused:
                self._wait_condition.wait(self._mutex)
            self._mutex.unlock()

            try:
                response = self._input_queue.get_nowait()
                if response[0] == request_id:
                    return response[1]
            except queue.Empty:
                time.sleep(0.1)

    def handle_input(self, request_id: str, value: Any):
        """Handle input received from core controller"""
        if request_id == self._current_request_id:
            self._input_queue.put((request_id, value))


class LoadWorker(BaseWorker):
    def run(self):
        self.event_signal.emit({"type": "status", "message": "Loading started"})
        time.sleep(3)  # Simulate long task
        self.event_signal.emit({"type": "status", "message": "Loading completed"})
        self.finished.emit()


class BuildWorker(BaseWorker):
    def __init__(self, data: Dict[str, Any], rdb_manager, callback, event_handler):
        super().__init__(data)
        self.build_master = BuildMaster(rdb_manager, callback, event_handler)

    def run(self):
        self.event_signal.emit({"type": "status", "message": "Build started"})
        try:
            self.build_master.generate_files(self.data)
        except Exception as e:
            self.event_signal.emit({"type": "error", "message": str(e)})
        self.event_signal.emit({"type": "status", "message": "Build completed"})
        self.finished.emit()


class ExportWorker(BaseWorker):
    def run(self):
        self.event_signal.emit({"type": "status", "message": "Export started"})
        for i in range(10):
            print("Export Progress: ", i)
            time.sleep(1)
        self.event_signal.emit({"type": "status", "message": "Export completed"})
        self.finished.emit()


class ConfigureWorker(BaseWorker):
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
    worker_event = Signal(dict)  # Signal for all worker events
    input_dialog_requested = Signal(str, str)  # request_id, message

    def __init__(self, rdb_manager: RDBManager):
        super().__init__()
        self.rdb_manager = rdb_manager
        self.error_message = ""
        self.state_machine = StateMachine()
        self.state_machine.state_changed.connect(self._on_state_changed)
        self.state_machine.transition_failed.connect(self._on_transition_failed)
        # self.setup_connections()  # Commented out - build_master is not initialized yet
        self.workers: Dict[str, Tuple[BaseWorker, QThread]] = {}
        self.worker_queue = queue.PriorityQueue()
        self._process_worker_queue()

    def setup_connections(self):
        """Setup signal connections"""
        self.build_master.build_event.connect(self._on_build_event)

    def _on_state_changed(self, old_state: ToolState, new_state: ToolState):
        """Handle state changes from state machine"""
        logger.info(f"State changed from {old_state.name} to {new_state.name}")
        self.state_changed.emit(new_state)

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
        self.state_machine.transition(ToolEvent.ERROR, {"error_message": error_message})

    def _on_build_event(self, event: Dict[str, Any]):
        """Handle all build events"""
        event_type = event.get("type")

        if event_type == "build_started":
            self.state_machine.transition(ToolEvent.BUILD)
            self.build_event.emit(
                {"type": "status", "message": f"Build started: {event.get('message')}"}
            )

        elif event_type == "build_completed":
            self.state_machine.transition(ToolEvent.COMPLETE)
            self.build_event.emit(
                {
                    "type": "status",
                    "message": f"Build completed: {event.get('message')}",
                }
            )

        elif event_type == "build_failed":
            self.state_machine.transition(
                ToolEvent.ERROR, {"error_message": event.get("message")}
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
            if self.state_machine.transition(ToolEvent(event_type), event_data):
                # Queue worker request
                worker_type = event_type
                priority = WorkerPriority.NORMAL
                if event_type == "build":
                    worker_type = "build"
                    priority = WorkerPriority.HIGH

                request = WorkerRequest(
                    worker_type=worker_type,
                    data=event_data,
                    priority=priority,
                    callback=lambda: self._send_reply(
                        {
                            "status": "success",
                            "message": f"Event {event_type} processed successfully",
                        }
                    ),
                )
                self.worker_queue.put((-priority.value, request))
            else:
                self._send_reply(
                    {
                        "status": "error",
                        "message": f"Event {event_type} not handled in current state",
                    }
                )

        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")
            self.state_machine.transition(ToolEvent.ERROR, {"error_message": str(e)})

    def _process_worker_queue(self):
        """Process the worker queue"""
        try:
            while True:
                _, request = self.worker_queue.get_nowait()
                self._create_and_start_worker(request)
        except queue.Empty:
            pass

    def _create_and_start_worker(self, request: WorkerRequest):
        """Create and start a worker based on the request"""
        try:
            worker = None
            if request.worker_type == "load":
                worker = LoadWorker(request.data)
            elif request.worker_type == "build":
                worker = BuildWorker(
                    request.data,
                    self.rdb_manager,
                    request.callback,
                    self._on_build_event,
                )
            elif request.worker_type == "export":
                worker = ExportWorker(request.data)
            elif request.worker_type == "configure":
                worker = ConfigureWorker(request.data)

            if worker:
                thread = QThread()
                worker.moveToThread(thread)
                worker.event_signal.connect(self.worker_event.emit)
                worker.input_requested.connect(self._handle_worker_input_request)
                worker.finished.connect(thread.quit)
                worker.finished.connect(worker.deleteLater)
                thread.finished.connect(thread.deleteLater)
                thread.started.connect(worker.run)
                thread.start()

                self.workers[request.worker_type] = (worker, thread)
                if request.callback:
                    request.callback()

        except Exception as e:
            logger.error(f"Error creating worker: {str(e)}")
            self.state_machine.transition(
                ToolEvent.ERROR, {"error_message": f"Failed to create worker: {str(e)}"}
            )

    def _handle_worker_input_request(self, request_id: str, message: str):
        """Handle input request from worker"""
        self.input_dialog_requested.emit(request_id, message)

    def handle_worker_input(self, request_id: str, value: Any):
        """Handle input response for worker"""
        for worker, _ in self.workers.values():
            if isinstance(worker, BaseWorker):
                worker.handle_input(request_id, value)

    def _send_reply(self, reply: Dict[str, Any]) -> None:
        """Send a reply through the signal"""
        self.reply_signal.emit(reply)

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "state": self.state_machine.get_state().name,
            "error_message": self.error_message,
        }

    def set_output_directory(self, output_dir: str):
        """Set output directory for build process"""
        self.build_master.set_output_directory(output_dir)
