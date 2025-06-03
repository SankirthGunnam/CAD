from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
import logging
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from .build.build_master import BuildMaster

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
        self.current_state = RCCState.IDLE
        self.error_message = ""
        self.build_master = BuildMaster(self)
        self.setup_connections()

        # Event handlers for each state
        self.state_handlers: Dict[RCCState, Dict[str, Callable]] = {
            RCCState.IDLE: self._get_idle_handlers(),
            RCCState.BUILDING: self._get_building_handlers(),
            RCCState.LOADING: self._get_loading_handlers(),
            RCCState.SAVING: self._get_saving_handlers(),
            RCCState.EXPORTING: self._get_exporting_handlers(),
            RCCState.ERROR: self._get_error_handlers(),
        }

    def setup_connections(self):
        """Setup signal connections with BuildMaster"""
        self.build_master.build_event.connect(self._on_build_event)

    def _on_build_event(self, event: Dict[str, Any]):
        """Handle all build events"""
        event_type = event.get("type")

        if event_type == "build_started":
            self._set_state(RCCState.BUILDING)
            self.build_event.emit(
                {"type": "status", "message": f"Build started: {event.get('message')}"}
            )

        elif event_type == "build_completed":
            self._set_state(RCCState.IDLE)
            self.build_event.emit(
                {
                    "type": "status",
                    "message": f"Build completed: {event.get('message')}",
                }
            )

        elif event_type == "build_failed":
            self._set_error(event.get("message", "Build failed"))
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

    def _get_idle_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for IDLE state"""
        return {
            "create": self._handle_create,
            "load": self._handle_load,
            "build": self._handle_build,
            "save": self._handle_save,
            "export": self._handle_export,
        }

    def _get_building_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for BUILDING state"""
        return {"cancel": self._handle_cancel, "error": self._handle_error}

    def _get_loading_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for LOADING state"""
        return {"cancel": self._handle_cancel, "error": self._handle_error}

    def _get_saving_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for SAVING state"""
        return {"cancel": self._handle_cancel, "error": self._handle_error}

    def _get_exporting_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for EXPORTING state"""
        return {"cancel": self._handle_cancel, "error": self._handle_error}

    def _get_error_handlers(self) -> Dict[str, Callable]:
        """Get event handlers for ERROR state"""
        return {"recover": self._handle_recover}

    def process_event(self, event: Dict[str, Any]) -> None:
        """Process an incoming event based on current state"""
        event_type = event.get("type")
        event_data = event.get("data", {})

        try:
            # Get handlers for current state
            handlers = self.state_handlers.get(self.current_state, {})

            if event_type in handlers:
                # Process event with appropriate handler
                reply = handlers[event_type](event_data)
                self._send_reply(reply)
            else:
                # Event not handled in current state
                self._send_reply(
                    {
                        "status": "error",
                        "message": f"Event {event_type} not handled in state {self.current_state.name}",
                    }
                )

        except Exception as e:
            logger.error(f"Error processing event {event_type}: {str(e)}")
            self._set_error(str(e))

    def _send_reply(self, reply: Dict[str, Any]) -> None:
        """Send a reply through the signal"""
        self.reply_signal.emit(reply)

    def _set_state(self, new_state: RCCState) -> None:
        """Set new state and emit signal"""
        self.current_state = new_state
        self.state_changed.emit(new_state)
        logger.info(f"State changed to: {new_state.name}")

    def _set_error(self, message: str) -> None:
        """Set error state and message"""
        self.error_message = message
        self._set_state(RCCState.ERROR)
        self._send_reply({"status": "error", "message": message})

    # Event Handlers
    def _handle_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create event"""
        try:
            self._set_state(RCCState.BUILDING)
            # Implement create logic here
            return {"status": "success", "message": "Created successfully"}
        except Exception as e:
            self._set_error(str(e))
            return {"status": "error", "message": str(e)}

    def _handle_load(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle load event"""
        try:
            self._set_state(RCCState.LOADING)
            # Implement load logic here
            return {"status": "success", "message": "Loaded successfully"}
        except Exception as e:
            self._set_error(str(e))
            return {"status": "error", "message": str(e)}

    def _handle_build(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle build event"""
        try:
            self._set_state(RCCState.BUILDING)
            self.start_build(data)
            return {"status": "success", "message": "Build started"}
        except Exception as e:
            self._set_error(str(e))
            return {"status": "error", "message": str(e)}

    def _handle_save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle save event"""
        try:
            self._set_state(RCCState.SAVING)
            # Implement save logic here
            return {"status": "success", "message": "Saved successfully"}
        except Exception as e:
            self._set_error(str(e))
            return {"status": "error", "message": str(e)}

    def _handle_export(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export event"""
        try:
            self._set_state(RCCState.EXPORTING)
            # Implement export logic here
            return {"status": "success", "message": "Exported successfully"}
        except Exception as e:
            self._set_error(str(e))
            return {"status": "error", "message": str(e)}

    def _handle_cancel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancel event"""
        self._set_state(RCCState.IDLE)
        return {"status": "success", "message": "Operation cancelled"}

    def _handle_error(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error event"""
        error_msg = data.get("message", "Unknown error")
        self._set_error(error_msg)
        return {"status": "error", "message": error_msg}

    def _handle_recover(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle recover event"""
        self._set_state(RCCState.IDLE)
        self.error_message = ""
        return {"status": "success", "message": "Recovered from error state"}

    def handle_build_error(self, error_msg: str):
        """Handle build error from BuildMaster"""
        self._set_error(error_msg)

    def start_build(self, data: Dict[str, Any], output_dir: Optional[str] = None):
        """Start the build process"""
        try:
            self.build_master.generate_files(data, output_dir)
        except Exception as e:
            self._set_error(f"Failed to start build: {str(e)}")

    def get_build_status(self) -> Dict[str, Any]:
        """Get the current build status"""
        return self.build_master.get_build_status()

    def set_output_directory(self, output_dir: str):
        """Set the output directory for generated files"""
        self.build_master.set_output_directory(output_dir)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the controller"""
        return {
            "state": self.current_state.name,
            "error_message": self.error_message,
            "is_error": self.current_state == RCCState.ERROR,
        }

    def recover(self) -> None:
        """Recover from error state"""
        self._handle_recover({})
