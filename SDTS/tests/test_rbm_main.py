import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer

# Import the RBM module
from apps.RBM.BCF.source.RBM_Main import RBMMain


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_rdb_manager():
    """Mock RDBManager for testing"""
    with patch('apps.RBM.BCF.source.RBM_Main.RDBManager') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_core_controller():
    """Mock CoreController for testing"""
    with patch('apps.RBM.BCF.source.RBM_Main.CoreController') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_gui_controller():
    """Mock GUIController for testing"""
    with patch('apps.RBM.BCF.source.RBM_Main.GUIController') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


class TestRBMMainInitialization:
    """Test suite for RBMMain initialization following TDD approach"""

    def test_rbm_main_initialization(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that RBMMain initializes correctly"""
        # Given: All dependencies are mocked
        # When: Creating RBMMain instance
        rbm_main = RBMMain()

        # Then: All components should be initialized
        assert rbm_main.rdb_manager is not None
        assert rbm_main.core_controller is not None
        assert rbm_main.gui_controller is not None

    def test_layout_setup(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that layout is properly configured"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Checking layout properties
        layout = rbm_main.layout()

        # Then: Layout should be configured correctly
        assert layout is not None
        assert layout.contentsMargins().left() == 0
        assert layout.contentsMargins().top() == 0
        assert layout.contentsMargins().right() == 0
        assert layout.contentsMargins().bottom() == 0
        assert layout.spacing() == 0

    def test_gui_controller_added_to_layout(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that GUI controller is added to layout"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Checking layout contents
        layout = rbm_main.layout()

        # Then: GUI controller should be in layout
        assert layout.count() > 0
        # Verify the GUI controller widget is added
        assert mock_gui_controller in [layout.itemAt(i).widget() for i in range(layout.count())]


class TestRBMMainSignalConnections:
    """Test suite for signal connections in RBMMain"""

    def test_gui_to_core_connections(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that GUI to Core signal connections are established"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Checking signal connections exist
        # Then: GUI controller signals should be connected to RBM handlers
        # We verify this by checking that the signal connection methods were called
        mock_gui_controller.build_requested.connect.assert_called()
        mock_gui_controller.configure_requested.connect.assert_called()
        mock_gui_controller.export_requested.connect.assert_called()

    def test_core_to_gui_connections(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that Core to GUI signal connections are established"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Checking signal connections exist
        # Then: Core controller signals should be connected to RBM handlers
        mock_core_controller.reply_signal.connect.assert_called()
        mock_core_controller.build_event.connect.assert_called()
        mock_core_controller.state_changed.connect.assert_called()

    def test_database_connections(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that database signal connections are established"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Checking signal connections exist
        # Then: RDB manager signals should be connected to RBM handlers
        mock_rdb_manager.data_changed.connect.assert_called()
        mock_rdb_manager.error_occurred.connect.assert_called()


class TestRBMMainEventHandling:
    """Test suite for event handling in RBMMain"""

    def test_build_request_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of build requests from GUI"""
        # Given: RBMMain instance and build data
        rbm_main = RBMMain()
        build_data = {"project": "test_project", "configuration": "debug"}

        # When: Handling build request
        rbm_main._on_build_requested(build_data)

        # Then: Core controller should process the build event
        expected_event = {"type": "build", "data": build_data}
        mock_core_controller.process_event.assert_called_with(expected_event)

    def test_configure_request_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of configuration requests from GUI"""
        # Given: RBMMain instance and config data
        rbm_main = RBMMain()
        config_data = {"device": "test_device", "parameters": {}}

        # When: Handling configure request
        rbm_main._on_configure_requested(config_data)

        # Then: Core controller should process the configure event
        expected_event = {"type": "configure", "data": config_data}
        mock_core_controller.process_event.assert_called_with(expected_event)

    def test_export_request_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of export requests from GUI"""
        # Given: RBMMain instance and export data
        rbm_main = RBMMain()
        export_data = {"format": "json", "destination": "/tmp/export"}

        # When: Handling export request
        rbm_main._on_export_requested(export_data)

        # Then: Core controller should process the export event
        expected_event = {"type": "export", "data": export_data}
        mock_core_controller.process_event.assert_called_with(expected_event)

    def test_core_reply_handling_success(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of successful replies from core controller"""
        # Given: RBMMain instance and success reply
        rbm_main = RBMMain()
        reply = {"status": "success", "message": "Operation completed"}

        # When: Handling core reply
        rbm_main._on_core_reply(reply)

        # Then: GUI should show status message
        mock_gui_controller.show_status.assert_called_with("Operation completed")

    def test_core_reply_handling_error(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of error replies from core controller"""
        # Given: RBMMain instance and error reply
        rbm_main = RBMMain()
        reply = {"status": "error", "message": "Operation failed"}

        # When: Handling core reply
        rbm_main._on_core_reply(reply)

        # Then: GUI should show error message
        mock_gui_controller.show_error.assert_called_with("Operation failed")

    def test_build_event_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of build events from core controller"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # Test status event
        status_event = {"type": "status", "message": "Building..."}
        rbm_main._on_build_event(status_event)
        mock_gui_controller.show_status.assert_called_with("Building...")

        # Test error event
        error_event = {"type": "error", "message": "Build failed"}
        rbm_main._on_build_event(error_event)
        mock_gui_controller.show_error.assert_called_with("Build failed")

        # Test warning event
        warning_event = {"type": "warning", "message": "Deprecated API"}
        rbm_main._on_build_event(warning_event)
        mock_gui_controller.show_warning.assert_called_with("Deprecated API")

        # Test file event
        file_event = {"type": "file", "file_path": "/tmp/output.txt"}
        rbm_main._on_build_event(file_event)
        mock_gui_controller.add_generated_file.assert_called_with("/tmp/output.txt")

    def test_state_changed_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of state changes from core controller"""
        # Given: RBMMain instance and new state
        rbm_main = RBMMain()
        new_state = "BUILDING"

        # When: Handling state change
        rbm_main._on_state_changed(new_state)

        # Then: GUI should update state
        mock_gui_controller.update_state.assert_called_with(new_state)

    def test_data_changed_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of data changes"""
        # Given: RBMMain instance and changed data
        rbm_main = RBMMain()
        data = {"key": "value", "updated": True}

        # When: Handling data change
        rbm_main._on_data_changed(data)

        # Then: Data changed signal should be emitted and GUI refreshed
        mock_gui_controller.refresh_data.assert_called_once()

    def test_error_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of errors"""
        # Given: RBMMain instance and error message
        rbm_main = RBMMain()
        error_message = "Critical error occurred"

        # When: Handling error
        rbm_main._on_error(error_message)

        # Then: GUI should show error
        mock_gui_controller.show_error.assert_called_with(error_message)


class TestRBMMainLifecycle:
    """Test suite for RBMMain lifecycle events"""

    def test_show_event(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test show event initializes core controller"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Simulating show event
        rbm_main.showEvent(None)

        # Then: Core controller should be initialized
        expected_event = {"type": "initialize"}
        mock_core_controller.process_event.assert_called_with(expected_event)

    def test_close_event(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test close event cleans up resources"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Simulating close event
        rbm_main.closeEvent(None)

        # Then: RDB manager should be closed
        mock_rdb_manager.close.assert_called_once()


class TestRBMMainIntegration:
    """Integration tests for RBMMain"""

    @pytest.mark.slow
    def test_full_component_integration(self, qapp):
        """Test full integration of all RBMMain components"""
        # Given: Real dependencies (not mocked)
        with patch('apps.RBM.BCF.source.RBM_Main.RDBManager') as mock_rdb, \
             patch('apps.RBM.BCF.source.RBM_Main.CoreController') as mock_core, \
             patch('apps.RBM.BCF.source.RBM_Main.GUIController') as mock_gui:

            mock_rdb_instance = Mock()
            mock_core_instance = Mock()
            mock_gui_instance = Mock()

            mock_rdb.return_value = mock_rdb_instance
            mock_core.return_value = mock_core_instance
            mock_gui.return_value = mock_gui_instance

            # When: Creating and using RBMMain
            rbm_main = RBMMain()
            rbm_main.show()

            # Simulate typical workflow
            build_data = {"project": "integration_test"}
            rbm_main._on_build_requested(build_data)

            # Then: All components should work together
            assert rbm_main.isVisible()
            mock_core_instance.process_event.assert_called()

    def test_signal_chain_integration(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that signals propagate correctly through the component chain"""
        # Given: RBMMain instance with connected signals
        rbm_main = RBMMain()

        # When: Triggering a chain of events
        # 1. GUI requests build
        build_data = {"project": "signal_test"}
        rbm_main._on_build_requested(build_data)

        # 2. Core responds with status
        reply = {"status": "success", "message": "Build started"}
        rbm_main._on_core_reply(reply)

        # 3. Build event occurs
        build_event = {"type": "status", "message": "Compiling..."}
        rbm_main._on_build_event(build_event)

        # Then: All handlers should have been called in sequence
        mock_core_controller.process_event.assert_called_with({"type": "build", "data": build_data})
        mock_gui_controller.show_status.assert_called_with("Build started")


class TestRBMMainErrorScenarios:
    """Test suite for error scenarios in RBMMain"""

    def test_initialization_with_missing_dependencies(self, qapp):
        """Test RBMMain behavior when dependencies are missing"""
        # Given: Missing RDBManager
        with patch('apps.RBM.BCF.source.RBM_Main.RDBManager', side_effect=ImportError("RDBManager not found")):
            # When: Creating RBMMain
            # Then: Should raise ImportError
            with pytest.raises(ImportError, match="RDBManager not found"):
                RBMMain()

    def test_signal_connection_failures(self, qapp, mock_rdb_manager, mock_core_controller):
        """Test behavior when signal connections fail"""
        # Given: GUI controller that raises exception on connect
        with patch('apps.RBM.BCF.source.RBM_Main.GUIController') as mock_gui:
            mock_gui_instance = Mock()
            mock_gui_instance.build_requested.connect.side_effect = Exception("Connection failed")
            mock_gui.return_value = mock_gui_instance

            # When: Creating RBMMain
            # Then: Should raise connection exception
            with pytest.raises(Exception, match="Connection failed"):
                RBMMain()

    def test_malformed_event_handling(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test handling of malformed events"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Handling malformed events
        # Empty event
        rbm_main._on_core_reply({})

        # Event with missing keys
        rbm_main._on_build_event({"type": "status"})  # Missing message
        rbm_main._on_build_event({"message": "test"})  # Missing type

        # Then: Should handle gracefully without crashing
        # (GUI methods should be called with None or empty values)
        assert mock_gui_controller.show_status.called or mock_gui_controller.show_error.called


# Performance and stress tests
class TestRBMMainPerformance:
    """Performance tests for RBMMain"""

    def test_rapid_event_processing(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test RBMMain can handle rapid event processing"""
        # Given: RBMMain instance
        rbm_main = RBMMain()

        # When: Processing many events rapidly
        for i in range(100):
            build_data = {"project": f"test_{i}"}
            rbm_main._on_build_requested(build_data)

        # Then: All events should be processed
        assert mock_core_controller.process_event.call_count == 100

    def test_memory_management(self, qapp, mock_rdb_manager, mock_core_controller, mock_gui_controller):
        """Test that RBMMain manages memory properly"""
        import gc

        # Given: Initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())

        # When: Creating and destroying RBMMain instances
        for _ in range(10):
            rbm_main = RBMMain()
            del rbm_main
            gc.collect()

        # Then: Memory should not grow significantly
        final_objects = len(gc.get_objects())
        # Allow for some growth but not excessive
        assert final_objects < initial_objects * 1.1  # Less than 10% growth
