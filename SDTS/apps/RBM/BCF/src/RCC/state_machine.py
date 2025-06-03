from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
from PySide6.QtCore import QObject, Signal
import logging

logger = logging.getLogger(__name__)


class ToolState(Enum):
    """States of the RCC Tool"""

    IDLE = auto()
    INITIALIZING = auto()
    CONFIGURING = auto()
    BUILDING = auto()
    VALIDATING = auto()
    EXPORTING = auto()
    ERROR = auto()


class StateTransition:
    """Represents a state transition with its conditions"""

    def __init__(
        self,
        target_state: ToolState,
        condition: Callable[[Dict[str, Any]], bool] = None,
    ):
        """
        Args:
            target_state: The state to transition to if condition is met
            condition: Optional function that takes transition data and returns
                      True if transition should proceed, False otherwise.
                      If None, transition is always allowed.
        """
        self.target_state = target_state
        self.condition = condition or (lambda _: True)


class StateMachine(QObject):
    """State machine for managing tool states and transitions"""

    # Signals
    state_changed = Signal(ToolState, ToolState)  # old_state, new_state
    transition_failed = Signal(str)  # error message

    def __init__(self):
        super().__init__()
        self.current_state = ToolState.IDLE
        self.previous_state = None
        self.state_data: Dict[str, Any] = {}

        # Define valid transitions for each state
        self.transitions: Dict[ToolState, Dict[str, StateTransition]] = {
            ToolState.IDLE: {
                "initialize": StateTransition(ToolState.INITIALIZING),
                "configure": StateTransition(ToolState.CONFIGURING),
                "build": StateTransition(ToolState.BUILDING),
                "export": StateTransition(ToolState.EXPORTING),
            },
            ToolState.INITIALIZING: {
                "complete": StateTransition(ToolState.IDLE),
                "error": StateTransition(ToolState.ERROR),
            },
            ToolState.CONFIGURING: {
                "complete": StateTransition(ToolState.IDLE),
                "build": StateTransition(ToolState.BUILDING),
                "error": StateTransition(ToolState.ERROR),
            },
            ToolState.BUILDING: {
                "validate": StateTransition(ToolState.VALIDATING),
                "complete": StateTransition(ToolState.IDLE),
                "error": StateTransition(ToolState.ERROR),
            },
            ToolState.VALIDATING: {
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
        """Attempt to transition to a new state based on the event"""
        try:
            if data is None:
                data = {}

            # Get valid transitions for current state
            valid_transitions = self.transitions.get(self.current_state, {})
            transition = valid_transitions.get(event)

            if not transition:
                raise ValueError(
                    f"Invalid event '{event}' for state {self.current_state.name}"
                )

            # Check transition condition
            if not transition.condition(data):
                raise ValueError(f"Transition condition not met for event '{event}'")

            # Update state
            self.previous_state = self.current_state
            self.current_state = transition.target_state

            # Emit state change signal
            self.state_changed.emit(self.previous_state, self.current_state)

            return True

        except Exception as e:
            logger.error(f"State transition failed: {str(e)}")
            self.transition_failed.emit(str(e))
            return False

    def get_state(self) -> ToolState:
        """Get current state"""
        return self.current_state

    def get_previous_state(self) -> Optional[ToolState]:
        """Get previous state"""
        return self.previous_state

    def set_state_data(self, key: str, value: Any):
        """Set data for the current state"""
        self.state_data[key] = value

    def get_state_data(self, key: str, default: Any = None) -> Any:
        """Get data for the current state"""
        return self.state_data.get(key, default)
