import pytest
from unittest.mock import Mock, patch
from apps.RBM.BCF.source.RCC.core_controller import CoreController, ToolState, ToolEvent
from apps.RBM.BCF.source.RCC.build.build_master import BuildMaster


class TestCoreController:
    def test_initialization(self, mock_rdb_manager):
        """Test CoreController initialization"""
        controller = CoreController(mock_rdb_manager)
        assert controller.rdb_manager == mock_rdb_manager
        assert controller.state_machine is not None
        assert controller.workers == {}

    def test_state_transitions(self, mock_rdb_manager):
        """Test state machine transitions"""
        controller = CoreController(mock_rdb_manager)

        # Test initial state
        assert controller.state_machine.get_state() == ToolState.IDLE

        # Test transition to BUILDING state
        controller.state_machine.transition(ToolEvent.BUILD)
        assert controller.state_machine.get_state() == ToolState.BUILDING

        # Test transition to ERROR state from BUILDING
        controller.state_machine.transition(
            ToolEvent.ERROR, {"error_message": "Test error"}
        )
        assert controller.state_machine.get_state() == ToolState.ERROR

    def test_build_request_handling(self, mock_rdb_manager):
        """Test handling of build requests"""
        controller = CoreController(mock_rdb_manager)

        # Test build event processing
        build_event = {"type": "build_started", "message": "Starting test build"}
        controller._on_build_event(build_event)

        # Verify state machine transitioned to BUILDING
        assert controller.state_machine.get_state() == ToolState.BUILDING

    def test_error_handling(self, mock_rdb_manager):
        """Test error handling"""
        controller = CoreController(mock_rdb_manager)

        # First transition to BUILDING state (valid from IDLE)
        controller.state_machine.transition(ToolEvent.BUILD)
        assert controller.state_machine.get_state() == ToolState.BUILDING

        # Then transition to ERROR state (valid from BUILDING)
        controller.state_machine.transition(ToolEvent.ERROR, {"error_message": "Test error"})

        # Verify state is ERROR and error message is set
        assert controller.state_machine.get_state() == ToolState.ERROR
        assert controller.error_message == "Test error"

    def test_worker_request_creation(self, mock_rdb_manager):
        """Test worker request creation"""
        controller = CoreController(mock_rdb_manager)

        # Import WorkerRequest and WorkerPriority for proper format
        from apps.RBM.BCF.source.RCC.core_controller import WorkerRequest, WorkerPriority

        # Test WorkerRequest creation
        worker_request = WorkerRequest(
            worker_type="load",
            data={"project": "test"},
            priority=WorkerPriority.HIGH
        )

        # Verify worker request properties
        assert worker_request.worker_type == "load"
        assert worker_request.data == {"project": "test"}
        assert worker_request.priority == WorkerPriority.HIGH

    def test_get_status(self, mock_rdb_manager):
        """Test status reporting"""
        controller = CoreController(mock_rdb_manager)

        # Test initial status
        status = controller.get_status()
        assert status["state"] == "IDLE"
        assert status["error_message"] == ""

        # Test status after build
        controller.state_machine.transition(ToolEvent.BUILD)
        status = controller.get_status()
        assert status["state"] == "BUILDING"

        # Test status after error (from BUILDING state)
        controller.state_machine.transition(ToolEvent.ERROR, {"error_message": "Test error"})
        status = controller.get_status()
        assert status["state"] == "ERROR"
        assert status["error_message"] == "Test error"
