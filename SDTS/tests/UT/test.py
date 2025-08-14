# core_controller.py
from PySide6.QtCore import QObject, Signal, QThread
from typing import Dict, Any, Optional
from enum import Enum, auto
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal
import logging

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer

import sys

logger = logging.getLogger(__name__)


class ToolState(Enum):
    IDLE = auto()
    LOADING = auto()
    BUILDING = auto()
    EXPORTING = auto()
    ERROR = auto()


class CoreController(QObject):
    state_changed = Signal(ToolState)
    reply_signal = Signal(dict)
    load_event = Signal(dict)
    build_event = Signal(dict)
    export_event = Signal(dict)

    def __init__(self):
        super().__init__()
        self.state_machine = StateMachine()
        self.state_machine.state_changed.connect(self._on_state_changed)
        self.state_machine.transition_failed.connect(self._on_transition_failed)

        self.error_message = ""
        self.load_worker: Optional[LoadWorker] = None
        self.build_worker: Optional[BuildWorker] = None
        self.export_worker: Optional[ExportWorker] = None

        self.load_thread: Optional[QThread] = None
        self.build_thread: Optional[QThread] = None
        self.export_thread: Optional[QThread] = None

    def process_event(self, event: Dict[str, Any]):
        event_type = event.get("type")
        data = event.get("data", {})

        if event_type == "load":
            self._start_load(data)
        elif event_type == "build":
            self._start_build(data)
        elif event_type == "export":
            self._start_export(data)

    def _on_state_changed(self, old_state: ToolState, new_state: ToolState):
        logger.info(f"State changed from {old_state.name} to {new_state.name}")

    def _on_transition_failed(self, msg: str):
        logger.error(f"Transition failed: {msg}")
        self.reply_signal.emit({"status": "error", "message": msg})

    def _start_load(self, data: Dict[str, Any]):
        self.load_thread = QThread()
        self.load_worker = LoadWorker(data)
        self.load_worker.moveToThread(self.load_thread)
        self.load_worker.event_signal.connect(self.load_event.emit)
        self.load_worker.finished.connect(self.load_thread.quit)
        self.load_worker.finished.connect(self.load_worker.deleteLater)
        self.load_thread.finished.connect(self.load_thread.deleteLater)
        self.load_thread.started.connect(self.load_worker.run)
        self.load_thread.start()

    def _start_build(self, data: Dict[str, Any]):
        self.build_thread = QThread()
        self.build_worker = BuildWorker(data)
        self.build_worker.moveToThread(self.build_thread)
        self.build_worker.event_signal.connect(self.build_event.emit)
        self.build_worker.finished.connect(self.build_thread.quit)
        self.build_worker.finished.connect(self.build_worker.deleteLater)
        self.build_thread.finished.connect(self.build_thread.deleteLater)
        self.build_thread.started.connect(self.build_worker.run)
        self.build_thread.start()

    def _start_export(self, data: Dict[str, Any]):
        self.export_thread = QThread()
        self.export_worker = ExportWorker(data)
        self.export_worker.moveToThread(self.export_thread)
        self.export_worker.event_signal.connect(self.export_event.emit)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self.export_thread.started.connect(self.export_worker.run)
        self.export_thread.start()

    def get_status(self):
        return {
            "state": self.state_machine.get_state(),
            "error_message": self.error_message,
            # "load_status": self.load_worker.get_status() if self.load_worker else None,
            # "build_status": (
            #     self.build_worker.get_status() if self.build_worker else None
            # ),
            # "export_status": (
            #     self.export_worker.get_status() if self.export_worker else None
            # ),
        }


# state_machine.py
logger = logging.getLogger(__name__)


class ToolState(Enum):
    IDLE = auto()
    CONFIGURING = auto()
    BUILDING = auto()
    EXPORTING = auto()
    ERROR = auto()


class StateTransition:
    def __init__(
        self,
        target_state: ToolState,
        condition: Callable[[Dict[str, Any]], bool] = None,
    ):
        self.target_state = target_state
        self.condition = condition or (lambda _: True)


class StateMachine(QObject):
    state_changed = Signal(ToolState, ToolState)
    transition_failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_state = ToolState.IDLE
        self.previous_state = None
        self.state_data: Dict[str, Any] = {}
        self.transitions: Dict[ToolState, Dict[str, StateTransition]] = {
            ToolState.IDLE: {
                "build": StateTransition(ToolState.BUILDING),
                "export": StateTransition(ToolState.EXPORTING),
            },
            ToolState.BUILDING: {
                "complete": StateTransition(ToolState.IDLE),
                "error": StateTransition(ToolState.ERROR),
            },
            ToolState.EXPORTING: {
                "complete": StateTransition(ToolState.IDLE),
                "error": StateTransition(ToolState.ERROR),
            },
            ToolState.ERROR: {
                "recover": StateTransition(ToolState.IDLE),
            },
        }

    def transition(self, event: str, data: Optional[Dict[str, Any]] = None) -> bool:
        if data is None:
            data = {}
        valid_transitions = self.transitions.get(self.current_state, {})
        transition = valid_transitions.get(event)

        if not transition:
            self.transition_failed.emit(
                f"Invalid event '{event}' from {self.current_state.name}"
            )
            return False

        if not transition.condition(data):
            self.transition_failed.emit(f"Transition condition failed for '{event}'")
            return False

        old = self.current_state
        self.current_state = transition.target_state
        self.state_changed.emit(old, self.current_state)
        return True

    def get_state(self):
        return self.current_state


# workers.py
from PySide6.QtCore import QObject, Signal
import time


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


class SampleGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RBM Tool Demo")
        self.setMinimumSize(400, 300)

        # Create layout and widgets
        layout = QVBoxLayout()

        self.status_label = QLabel("Status: IDLE")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.btn_load = QPushButton("Start Load")
        self.btn_build = QPushButton("Start Build")
        self.btn_export = QPushButton("Start Export")

        layout.addWidget(self.btn_load)
        layout.addWidget(self.btn_build)
        layout.addWidget(self.btn_export)

        self.setLayout(layout)

        # Setup CoreController
        self.controller = CoreController()
        self.core_thread = QThread()
        self.controller.moveToThread(self.core_thread)

        # Connect GUI signals
        self.btn_load.clicked.connect(self.trigger_load)
        self.btn_build.clicked.connect(self.trigger_build)
        self.btn_export.clicked.connect(self.trigger_export)

        # Connect controller signals
        self.controller.reply_signal.connect(self.on_reply)
        self.controller.state_changed.connect(self.on_state_changed)
        self.controller.load_event.connect(self.on_load_event)
        self.controller.build_event.connect(self.on_build_event)
        self.controller.export_event.connect(self.on_export_event)
        self.core_thread.start()

        # Polling current status every 500ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(500)

    def on_load_event(self, event: dict):
        self.log_output.append(f"Load event: {event.get('message')}")

    def on_build_event(self, event: dict):
        self.log_output.append(f"Build event: {event.get('message')}")

    def on_export_event(self, event: dict):
        self.log_output.append(f"Export event: {event.get('message')}")

    def trigger_load(self):
        self.controller.process_event(
            {"type": "load", "data": {"source": "dummy_file"}}
        )

    def trigger_build(self):
        self.controller.process_event(
            {"type": "build", "data": {"project": "demo_project"}}
        )

    def trigger_export(self):
        self.controller.process_event(
            {"type": "export", "data": {"target": "demo_output"}}
        )

    def on_reply(self, message: dict):
        self.log_output.append(f"Reply: {message.get('message')}")

    def on_state_changed(self, state):
        self.status_label.setText(f"Status: {state.name}")

    def refresh_status(self):
        status = self.controller.get_status()
        print(status)
        self.status_label.setText(f"Status: {status['state']}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SampleGUI()
    window.show()
    sys.exit(app.exec())
