import pytest
from unittest.mock import Mock, patch
from apps.RBM.BCF.src.RCC.core_controller import CoreController, ToolState, ToolEvent
from apps.RBM.BCF.src.RCC.build.build_master import BuildMaster


class TestCoreController:
    def test_initialization(self, mock_rdb_manager):
        """Test CoreController initialization"""
        controller = CoreController(mock_rdb_manager)
        assert controller.rdb_manager == mock_rdb_manager
        assert controller.build_master is not None
        assert isinstance(controller.build_master, BuildMaster)

    def test_state_transitions(self, mock_rdb_manager):
        """Test state machine transitions"""
        controller = CoreController(mock_rdb_manager)

        # Test initial state
        assert controller.state_machine.get_state() == ToolState.IDLE

        # Test transition to BUILDING state
        controller.state_machine.transition(ToolEvent.BUILD_STARTED)
        assert controller.state_machine.get_state() == ToolState.BUILDING

        # Test transition to ERROR state
        controller.state_machine.transition(
            ToolEvent.ERROR, {"error_message": "Test error"}
        )
        assert controller.state_machine.get_state() == ToolState.ERROR

    def test_build_request_handling(self, mock_rdb_manager):
        """Test handling of build requests"""
        controller = CoreController(mock_rdb_manager)

        # Mock the build_master
        mock_build_master = Mock(spec=BuildMaster)
        controller.build_master = mock_build_master

        # Test build request
        build_data = {"type": "build", "data": {"project": "test"}}
        controller.process_event(build_data)

        # Verify build_master was called
        assert mock_build_master.build.called

    def test_error_handling(self, mock_rdb_manager):
        """Test error handling"""
        controller = CoreController(mock_rdb_manager)

        # Create mock slots
        mock_reply_slot = Mock()
        mock_error_slot = Mock()
        controller.reply_signal.connect(mock_reply_slot)
        controller.error_occurred.connect(mock_error_slot)

        # Simulate error
        test_error = "Test error"
        controller._handle_error()

        # Verify error signals were emitted
        mock_reply_slot.emit.assert_called_once()
        assert mock_reply_slot.emit.call_args[0][0]["status"] == "error"

    def test_worker_management(self, mock_rdb_manager):
        """Test worker thread management"""
        controller = CoreController(mock_rdb_manager)

        # Test worker creation
        worker_data = {"type": "build", "data": {"project": "test"}, "priority": 1}

        # Create and start worker
        controller._create_and_start_worker(worker_data)

        # Verify worker was created and started
        assert len(controller.workers) > 0
        assert "build" in controller.workers

    @patch("apps.RBM.BCF.src.RCC.core_controller.QThread")
    def test_worker_thread_cleanup(self, mock_qthread, mock_rdb_manager):
        """Test worker thread cleanup"""
        controller = CoreController(mock_rdb_manager)

        # Create a worker
        worker_data = {"type": "build", "data": {"project": "test"}, "priority": 1}

        # Create and start worker
        controller._create_and_start_worker(worker_data)

        # Simulate worker completion
        worker, thread = controller.workers["build"]
        worker.finished.emit()

        # Verify thread cleanup
        assert thread.quit.called
        assert thread.deleteLater.called
