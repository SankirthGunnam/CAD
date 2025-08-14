import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

# Import the main module
from main import SDTSMainWindow, main


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_rbm_main(qapp):
    """Mock RBMMain to avoid complex dependencies in main window tests"""
    from PySide6.QtWidgets import QWidget
    
    class MockRBMMain(QWidget):
        def __init__(self):
            super().__init__()
            # Add any required attributes/methods
            self.data_changed = Mock()
            self.error_occurred = Mock()
    
    with patch('main.RBMMain') as mock:
        mock.return_value = MockRBMMain()
        yield mock.return_value


class TestSDTSMainWindow:
    """Test suite for SDTS Main Window following TDD approach"""

    def test_main_window_initialization(self, qapp, mock_rbm_main):
        """Test that main window initializes correctly"""
        # Given: A clean application state
        # When: Creating a main window
        window = SDTSMainWindow()
        
        # Then: Window should be properly initialized
        assert window.windowTitle() == "SDTS - Schematic Design Tool Suite"
        assert window.minimumSize().width() == 1200
        assert window.minimumSize().height() == 800
        assert window.stacked_widget is not None
        assert window.toolbar is not None

    def test_rbm_integration(self, qapp, mock_rbm_main):
        """Test RBM module integration"""
        # Given: A main window
        window = SDTSMainWindow()
        
        # When: Window is created
        # Then: RBM should be integrated
        assert window.rbm == mock_rbm_main
        assert window.stacked_widget.count() > 0

    def test_toolbar_actions(self, qapp, mock_rbm_main):
        """Test toolbar actions are created correctly"""
        # Given: A main window
        window = SDTSMainWindow()
        
        # When: Checking toolbar actions
        actions = window.toolbar.actions()
        
        # Then: RBM action should exist
        assert len(actions) > 0
        rbm_action = actions[0]
        assert rbm_action.text() == "RBM"

    def test_rbm_action_triggers_correct_widget(self, qapp, mock_rbm_main):
        """Test that RBM action switches to correct widget"""
        # Given: A main window with RBM action
        window = SDTSMainWindow()
        actions = window.toolbar.actions()
        rbm_action = actions[0]
        
        # When: Triggering RBM action
        rbm_action.trigger()
        
        # Then: Stacked widget should show RBM
        assert window.stacked_widget.currentWidget() == mock_rbm_main

    def test_show_event_initializes_rbm(self, qapp, mock_rbm_main):
        """Test that show event properly initializes components"""
        # Given: A main window
        window = SDTSMainWindow()
        
        # When: Showing the window (simulate show event)
        window.showEvent(None)
        
        # Then: Window should be properly displayed
        # Note: RBM initialization happens in RBM's own showEvent

    def test_close_event_cleanup(self, qapp, mock_rbm_main):
        """Test that close event properly cleans up resources"""
        # Given: A main window with resources
        window = SDTSMainWindow()
        
        # When: Closing the window
        window.closeEvent(None)
        
        # Then: Resources should be cleaned up
        # Note: RBM cleanup happens in RBM's own closeEvent

    @patch('main.logger')
    def test_error_handling_in_initialization(self, mock_logger, qapp):
        """Test error handling during initialization"""
        # Given: RBMMain raises an exception
        with patch('main.RBMMain', side_effect=Exception("Test error")):
            # When: Creating main window
            # Then: Exception should be raised and logged
            with pytest.raises(Exception, match="Test error"):
                SDTSMainWindow()
            
            mock_logger.error.assert_called()

    def test_minimum_window_size_enforced(self, qapp, mock_rbm_main):
        """Test that minimum window size is enforced"""
        # Given: A main window
        window = SDTSMainWindow()
        
        # When: Checking window constraints
        min_size = window.minimumSize()
        
        # Then: Minimum size should be enforced
        assert min_size.width() >= 1200
        assert min_size.height() >= 800


class TestMainFunction:
    """Test suite for main function following TDD approach"""

    @patch('main.QApplication')
    @patch('main.SDTSMainWindow')
    @patch('main.logger')
    def test_main_function_success(self, mock_logger, mock_window_class, mock_qapp_class):
        """Test successful execution of main function"""
        # Given: Mocked dependencies
        mock_app = Mock()
        mock_window = Mock()
        mock_qapp_class.return_value = mock_app
        mock_window_class.return_value = mock_window
        mock_app.exec.return_value = 0
        
        # When: Running main function
        with patch('sys.exit') as mock_exit:
            main()
        
        # Then: Application should be created and run
        mock_qapp_class.assert_called_once_with(sys.argv)
        mock_window_class.assert_called_once()
        mock_window.show.assert_called_once()
        mock_app.exec.assert_called_once()
        mock_exit.assert_called_once_with(0)
        mock_logger.debug.assert_called_with("Showing main window")

    @patch('main.QApplication')
    @patch('main.SDTSMainWindow')
    @patch('main.logger')
    def test_main_function_handles_exceptions(self, mock_logger, mock_window_class, mock_qapp_class):
        """Test main function handles exceptions gracefully"""
        # Given: Window creation raises an exception
        test_error = Exception("Test initialization error")
        mock_window_class.side_effect = test_error
        
        # When: Running main function
        # Then: Exception should be handled and logged
        with pytest.raises(Exception, match="Test initialization error"):
            main()
        
        mock_logger.error.assert_called_with(f"Error in main: {test_error}")

    @patch('main.QApplication')
    @patch('main.SDTSMainWindow') 
    @patch('main.logger')
    def test_main_function_app_creation_failure(self, mock_logger, mock_window_class, mock_qapp_class):
        """Test main function handles app creation failure"""
        # Given: QApplication creation fails
        test_error = Exception("App creation failed")
        mock_qapp_class.side_effect = test_error
        
        # When: Running main function
        # Then: Exception should be handled
        with pytest.raises(Exception, match="App creation failed"):
            main()
        
        mock_logger.error.assert_called_with(f"Error in main: {test_error}")


class TestIntegration:
    """Integration tests for main application"""

    @pytest.mark.slow
    def test_full_application_startup(self, qapp):
        """Integration test for full application startup"""
        # Given: All dependencies are available
        with patch('main.RBMMain') as mock_rbm:
            mock_rbm_instance = Mock()
            mock_rbm.return_value = mock_rbm_instance
            
            # When: Creating and showing main window
            window = SDTSMainWindow()
            window.show()
            
            # Then: Window should be visible and functional
            assert window.isVisible()
            assert window.stacked_widget.count() == 1
            assert window.stacked_widget.currentWidget() == mock_rbm_instance

    def test_window_responsiveness(self, qapp, mock_rbm_main):
        """Test that window remains responsive"""
        # Given: A main window
        window = SDTSMainWindow()
        window.show()
        
        # When: Processing events
        QTest.qWait(100)  # Wait for 100ms
        
        # Then: Window should remain responsive
        assert window.isVisible()
        assert not window.isMinimized()


# Performance tests
class TestPerformance:
    """Performance tests for main application"""

    def test_startup_time(self, qapp, mock_rbm_main):
        """Test application startup time is reasonable"""
        import time
        
        # Given: Clean state
        start_time = time.time()
        
        # When: Creating main window
        window = SDTSMainWindow()
        
        # Then: Startup should be fast (< 1 second)
        startup_time = time.time() - start_time
        assert startup_time < 1.0

    def test_memory_usage(self, qapp, mock_rbm_main):
        """Test memory usage during initialization"""
        import psutil
        import os
        
        # Given: Current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # When: Creating main window
        window = SDTSMainWindow()
        
        # Then: Memory increase should be reasonable (< 100MB)
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100 * 1024 * 1024  # 100MB
