from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
import logging
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from .build.build_master import BuildMaster
from .state_machine import StateMachine, ToolState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RCCState(Enum):
    """States of the RBM Core Controller"""

    IDLE = auto()
    BUILDING = auto()
    LOADING = auto()
    SAVING = auto()
    EXPORTING = auto()
    ERROR = auto()


class CoreController(QObject):
    """RBM Core Controller that manages the state and processing of core events"""

    # Signals for communication
    state_changed = Signal(RCCState)  # Signal when state changes
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

        # Initialize build master
        self.build_master = BuildMaster(self)
        self.setup_connections()

    def setup_connections(self):
        """Setup signal connections with BuildMaster"""
        self.build_master.build_event.connect(self._on_build_event)

    def _on_state_changed(self, old_state: ToolState, new_state: ToolState):
        """Handle state changes from state machine"""
        logger.info(f"State changed from {old_state.name} to {new_state.name}")

        # Handle state-specific business logic
        if new_state == ToolState.INITIALIZING:
            self._handle_initializing()
        elif new_state == ToolState.CONFIGURING:
            self._handle_configuring()
        elif new_state == ToolState.BUILDING:
            self._handle_building()
        elif new_state == ToolState.VALIDATING:
            self._handle_validating()
        elif new_state == ToolState.EXPORTING:
            self._handle_exporting()
        elif new_state == ToolState.ERROR:
            self._handle_error()
        elif new_state == ToolState.IDLE:
            self._handle_idle()

    def _handle_initializing(self):
        """Handle business logic for INITIALIZING state"""
        try:
            # Initialize components
            self.build_master.initialize()
            self.state_machine.transition("complete")
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_configuring(self):
        """Handle business logic for CONFIGURING state"""
        try:
            # Configure components
            config_data = self.state_machine.get_state_data("config_data", {})
            self.build_master.configure(config_data)
            self.state_machine.transition("complete")
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_building(self):
        """Handle business logic for BUILDING state"""
        try:
            # Start build process
            build_data = self.state_machine.get_state_data("build_data", {})
            self.build_master.generate_files(build_data)
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_validating(self):
        """Handle business logic for VALIDATING state"""
        try:
            # Validate build results
            validation_data = self.state_machine.get_state_data("validation_data", {})
            if self.build_master.validate_build(validation_data):
                self.state_machine.transition("complete")
            else:
                self.state_machine.transition(
                    "error", {"error_message": "Validation failed"}
                )
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_exporting(self):
        """Handle business logic for EXPORTING state"""
        try:
            # Export results
            export_data = self.state_machine.get_state_data("export_data", {})
            self.build_master.export_results(export_data)
            self.state_machine.transition("complete")
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_error(self):
        """Handle business logic for ERROR state"""
        self.error_message = self.state_machine.get_state_data(
            "error_message", "Unknown error"
        )
        self.reply_signal.emit({"status": "error", "message": self.error_message})

    def _handle_idle(self):
        """Handle business logic for IDLE state"""
        # Clean up any resources or reset state
        self.error_message = ""
        self.reply_signal.emit({"status": "success", "message": "System is idle"})

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
                if event_type == "build":
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

    def start_build(self, data: Dict[str, Any], output_dir: Optional[str] = None):
        """Start the build process"""
        try:
            self.build_master.generate_files(data, output_dir)
        except Exception as e:
            self.state_machine.transition(
                "error", {"error_message": f"Failed to start build: {str(e)}"}
            )

    def _handle_configure(self, data: Dict[str, Any]):
        """Handle configuration"""
        try:
            # Implement configuration logic here
            pass
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

    def _handle_export(self, data: Dict[str, Any]):
        """Handle export"""
        try:
            # Implement export logic here
            pass
        except Exception as e:
            self.state_machine.transition("error", {"error_message": str(e)})

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
