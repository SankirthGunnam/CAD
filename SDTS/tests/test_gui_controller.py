import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from apps.RBM.BCF.gui.src.gui_controller import GUIController
from apps.RBM.BCF.src.models.chip_model import ChipModel


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestGUIController:
    def test_initialization(self, qapp):
        """Test GUIController initialization"""
        controller = GUIController()
        assert controller.windowTitle() == "RBM GUI Controller"
        assert controller.minimumSize().width() == 1000
        assert controller.minimumSize().height() == 800

    def test_mode_switching(self, qapp):
        """Test switching between legacy and visual modes"""
        controller = GUIController()

        # Test initial mode
        assert controller.current_mode == "legacy"
        assert controller.stacked_widget.currentWidget() == controller.legacy_manager

        # Switch to visual mode
        controller.switch_mode("visual")
        assert controller.current_mode == "visual"
        assert controller.stacked_widget.currentWidget() == controller.visual_manager

    def test_build_request_signal(self, qapp):
        """Test build request signal emission"""
        controller = GUIController()

        # Create mock slot
        mock_slot = Mock()
        controller.build_requested.connect(mock_slot)

        # Trigger build request
        test_data = {"mode": "legacy", "project": "test"}
        controller._on_build()

        # Verify signal was emitted
        mock_slot.emit.assert_called_once()
        assert mock_slot.emit.call_args[0][0]["mode"] == "legacy"

    def test_error_handling(self, qapp):
        """Test error handling and display"""
        controller = GUIController()

        # Create mock slots
        mock_error_slot = Mock()
        controller.error_occurred.connect(mock_error_slot)

        # Simulate error
        test_error = "Test error"
        controller._on_error(test_error)

        # Verify error signal was emitted
        mock_error_slot.emit.assert_called_once_with(test_error)

    def test_data_update(self, qapp):
        """Test data update handling"""
        controller = GUIController()

        # Create mock slots
        mock_data_slot = Mock()
        controller.data_changed.connect(mock_data_slot)

        # Test data update
        test_data = {"key": "value"}
        controller.update_data(test_data)

        # Verify data was updated in both managers
        assert controller.legacy_manager.update_table.called
        assert controller.visual_manager.update_scene.called

    def test_chip_addition(self, qapp):
        """Test adding a chip to the model"""
        controller = GUIController()

        # Create mock slot
        mock_slot = Mock()
        controller.add_chip_signal.connect(mock_slot)

        # Create test chip
        test_chip = ChipModel("test_chip", 0, 0)

        # Add chip
        controller.add_chip(test_chip)

        # Verify signal was emitted
        mock_slot.emit.assert_called_once_with(test_chip)

    def test_export_request(self, qapp):
        """Test export request handling"""
        controller = GUIController()

        # Create mock slot
        mock_slot = Mock()
        controller.export_requested.connect(mock_slot)

        # Trigger export request
        controller._on_export()

        # Verify signal was emitted
        mock_slot.emit.assert_called_once()
        assert mock_slot.emit.call_args[0][0]["mode"] == controller.current_mode

    def test_cleanup(self, qapp):
        """Test cleanup on window close"""
        controller = GUIController()

        # Mock cleanup methods
        controller.legacy_manager.cleanup = Mock()
        controller.visual_manager.cleanup = Mock()

        # Simulate window close
        controller.closeEvent(None)

        # Verify cleanup was called
        assert controller.legacy_manager.cleanup.called
        assert controller.visual_manager.cleanup.called
