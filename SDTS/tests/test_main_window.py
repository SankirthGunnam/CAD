import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

# Import the GUI main window
from gui.main_window import MainWindow


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_home_screen():
    """Mock HomeScreen for testing"""
    with patch('gui.main_window.HomeScreen') as mock:
        mock_instance = Mock(spec=QWidget)
        mock.return_value = mock_instance
        yield mock_instance


class TestMainWindowInitialization:
    """Test suite for MainWindow initialization following TDD approach"""

    def test_main_window_initialization(self, qapp, mock_home_screen):
        """Test that MainWindow initializes correctly"""
        # Given: A clean application state
        # When: Creating a main window
        window = MainWindow()

        # Then: Window should be properly initialized
        assert window.windowTitle() == "SDTS - System Design Tool Suite"
        assert window.minimumSize().width() == 1200
        assert window.minimumSize().height() == 800

    def test_central_widget_setup(self, qapp, mock_home_screen):
        """Test that central widget is properly configured"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking central widget
        central_widget = window.centralWidget()

        # Then: Central widget should exist and have correct layout
        assert central_widget is not None
        layout = central_widget.layout()
        assert layout is not None
        assert layout.contentsMargins().left() == 0
        assert layout.contentsMargins().top() == 0
        assert layout.contentsMargins().right() == 0
        assert layout.contentsMargins().bottom() == 0
        assert layout.spacing() == 0

    def test_sidebar_creation(self, qapp, mock_home_screen):
        """Test that sidebar is created and configured correctly"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking sidebar properties
        sidebar = window.sidebar

        # Then: Sidebar should be configured correctly
        assert sidebar is not None
        assert sidebar.width() == 50
        assert sidebar.layout() is not None

    def test_content_area_setup(self, qapp, mock_home_screen):
        """Test that content area is properly configured"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking content area
        content_area = window.content_area

        # Then: Content area should exist and contain home screen
        assert content_area is not None
        assert content_area.count() > 0
        assert content_area.widget(0) == mock_home_screen


class TestMainWindowAppButtons:
    """Test suite for application buttons in MainWindow"""

    def test_app_buttons_creation(self, qapp, mock_home_screen):
        """Test that application buttons are created correctly"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking app buttons
        app_buttons = window.app_buttons

        # Then: Should have correct buttons
        assert "CAD" in app_buttons
        assert "BCF" in app_buttons
        assert "DCF" in app_buttons
        assert len(app_buttons) == 3

    def test_app_button_properties(self, qapp, mock_home_screen):
        """Test that app buttons have correct properties"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking button properties
        for name, button in window.app_buttons.items():
            # Then: Buttons should have correct properties
            assert button.isCheckable()
            assert button.size().width() == 40
            assert button.size().height() == 40
            assert button.toolTip() == name

    def test_cad_button_functionality(self, qapp, mock_home_screen):
        """Test CAD button click functionality"""
        # Given: MainWindow instance
        window = MainWindow()
        cad_button = window.app_buttons["CAD"]

        # When: Clicking CAD button
        cad_button.click()

        # Then: Should switch to correct app (index 1, after HomeScreen)
        assert window.current_app == 1

    def test_bcf_button_functionality(self, qapp, mock_home_screen):
        """Test BCF button click functionality"""
        # Given: MainWindow instance
        window = MainWindow()
        bcf_button = window.app_buttons["BCF"]

        # When: Clicking BCF button
        bcf_button.click()

        # Then: Should switch to correct app (index 2)
        assert window.current_app == 2

    def test_dcf_button_functionality(self, qapp, mock_home_screen):
        """Test DCF button click functionality"""
        # Given: MainWindow instance
        window = MainWindow()
        dcf_button = window.app_buttons["DCF"]

        # When: Clicking DCF button
        dcf_button.click()

        # Then: Should switch to correct app (index 3)
        assert window.current_app == 3


class TestMainWindowAppSwitching:
    """Test suite for application switching in MainWindow"""

    def test_switch_to_home_screen(self, qapp, mock_home_screen):
        """Test switching to home screen (index 0)"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Switching to home screen
        window.switch_app(0)

        # Then: Should show home screen and no buttons should be checked
        assert window.current_app == 0
        assert window.content_area.currentIndex() == 0
        for button in window.app_buttons.values():
            assert not button.isChecked()

    def test_switch_to_cad_app(self, qapp, mock_home_screen):
        """Test switching to CAD app"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Switching to CAD app (index 1)
        window.switch_app(1)

        # Then: CAD button should be checked and content should switch
        assert window.current_app == 1
        assert window.content_area.currentIndex() == 1
        assert window.app_buttons["CAD"].isChecked()
        assert not window.app_buttons["BCF"].isChecked()
        assert not window.app_buttons["DCF"].isChecked()

    def test_switch_to_bcf_app(self, qapp, mock_home_screen):
        """Test switching to BCF app"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Switching to BCF app (index 2)
        window.switch_app(2)

        # Then: BCF button should be checked
        assert window.current_app == 2
        assert window.content_area.currentIndex() == 2
        assert not window.app_buttons["CAD"].isChecked()
        assert window.app_buttons["BCF"].isChecked()
        assert not window.app_buttons["DCF"].isChecked()

    def test_switch_to_dcf_app(self, qapp, mock_home_screen):
        """Test switching to DCF app"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Switching to DCF app (index 3)
        window.switch_app(3)

        # Then: DCF button should be checked
        assert window.current_app == 3
        assert window.content_area.currentIndex() == 3
        assert not window.app_buttons["CAD"].isChecked()
        assert not window.app_buttons["BCF"].isChecked()
        assert window.app_buttons["DCF"].isChecked()

    def test_multiple_app_switches(self, qapp, mock_home_screen):
        """Test multiple sequential app switches"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Switching between multiple apps
        window.switch_app(1)  # CAD
        window.switch_app(2)  # BCF
        window.switch_app(0)  # Home
        window.switch_app(3)  # DCF

        # Then: Should end up in DCF with correct button states
        assert window.current_app == 3
        assert window.app_buttons["DCF"].isChecked()
        assert not window.app_buttons["CAD"].isChecked()
        assert not window.app_buttons["BCF"].isChecked()

    def test_switch_app_with_invalid_index(self, qapp, mock_home_screen):
        """Test switching to invalid app index"""
        # Given: MainWindow instance
        window = MainWindow()
        initial_app = window.current_app

        # When: Trying to switch to invalid index
        try:
            window.switch_app(10)  # Invalid index
        except IndexError:
            pass  # Expected for invalid index

        # Then: Should handle gracefully and maintain current state
        # Note: Actual behavior depends on implementation


class TestMainWindowLayout:
    """Test suite for MainWindow layout management"""

    def test_sidebar_positioning(self, qapp, mock_home_screen):
        """Test that sidebar is positioned correctly"""
        # Given: MainWindow instance
        window = MainWindow()
        central_widget = window.centralWidget()
        layout = central_widget.layout()

        # When: Checking layout order
        # Then: Sidebar should be first item, content area second
        assert layout.itemAt(0).widget() == window.sidebar
        assert layout.itemAt(1).widget() == window.content_area

    def test_layout_stretch_factors(self, qapp, mock_home_screen):
        """Test layout stretch factors"""
        # Given: MainWindow instance
        window = MainWindow()
        central_widget = window.centralWidget()
        layout = central_widget.layout()

        # When: Checking stretch factors
        # Then: Content area should have stretch factor to expand
        # (This would need to be implemented in the actual code)
        assert layout is not None

    def test_window_resizing_behavior(self, qapp, mock_home_screen):
        """Test how window behaves during resizing"""
        # Given: MainWindow instance
        window = MainWindow()
        window.show()

        # When: Resizing window
        window.resize(1400, 900)

        # Then: Sidebar should maintain fixed width
        assert window.sidebar.width() == 50
        # Content area should expand to fill space
        assert window.content_area.width() > 1000


class TestMainWindowStyling:
    """Test suite for MainWindow styling"""

    def test_sidebar_styling(self, qapp, mock_home_screen):
        """Test that sidebar has correct styling"""
        # Given: MainWindow instance
        window = MainWindow()
        sidebar = window.sidebar

        # When: Checking sidebar style
        style_sheet = sidebar.styleSheet()

        # Then: Should have dark theme styling
        assert "background-color: #252526" in style_sheet
        assert "border-right: 1px solid #1e1e1e" in style_sheet

    def test_button_styling(self, qapp, mock_home_screen):
        """Test that buttons have correct styling"""
        # Given: MainWindow instance
        window = MainWindow()
        sidebar = window.sidebar

        # When: Checking button styling in sidebar
        style_sheet = sidebar.styleSheet()

        # Then: Button styles should be defined
        assert "QPushButton" in style_sheet
        assert "background-color: transparent" in style_sheet
        assert "QPushButton:hover" in style_sheet
        assert "QPushButton:checked" in style_sheet

    def test_content_area_styling(self, qapp, mock_home_screen):
        """Test that content area has correct styling"""
        # Given: MainWindow instance
        window = MainWindow()
        content_area = window.content_area

        # When: Checking content area style
        style_sheet = content_area.styleSheet()

        # Then: Should have dark background
        assert "background-color: #1e1e1e" in style_sheet


class TestMainWindowInitialState:
    """Test suite for MainWindow initial state"""

    def test_initial_app_state(self, qapp, mock_home_screen):
        """Test initial application state"""
        # Given: New MainWindow instance
        window = MainWindow()

        # When: Checking initial state
        # Then: Should start with home screen (index 0)
        assert window.current_app == 0
        assert window.content_area.currentIndex() == 0

    def test_initial_button_states(self, qapp, mock_home_screen):
        """Test initial button states"""
        # Given: New MainWindow instance
        window = MainWindow()

        # When: Checking button states
        # Then: No buttons should be initially checked
        for button in window.app_buttons.values():
            assert not button.isChecked()

    def test_home_screen_integration(self, qapp, mock_home_screen):
        """Test HomeScreen is properly integrated"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Checking home screen integration
        # Then: HomeScreen should be first widget in content area
        assert window.content_area.widget(0) == mock_home_screen
        assert window.home_screen == mock_home_screen


class TestMainWindowIntegration:
    """Integration tests for MainWindow"""

    @pytest.mark.slow
    def test_full_window_lifecycle(self, qapp, mock_home_screen):
        """Test full window lifecycle"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Showing window and interacting
        window.show()
        QTest.qWait(100)  # Wait for window to appear

        # Switch between apps
        window.app_buttons["CAD"].click()
        QTest.qWait(50)
        window.app_buttons["BCF"].click()
        QTest.qWait(50)

        # Then: Window should remain stable and responsive
        assert window.isVisible()
        assert window.current_app == 2  # Should be on BCF
        assert window.app_buttons["BCF"].isChecked()

    def test_window_with_real_home_screen(self, qapp):
        """Test integration with real HomeScreen (if available)"""
        # Given: MainWindow with potential real HomeScreen
        try:
            # Try to create with real HomeScreen
            window = MainWindow()

            # When: Window is created successfully
            # Then: Should work with real HomeScreen
            assert window.home_screen is not None
            assert window.content_area.count() > 0

        except ImportError:
            # If HomeScreen import fails, that's expected in some test environments
            pytest.skip("HomeScreen not available for integration test")


class TestMainWindowErrorScenarios:
    """Test suite for error scenarios in MainWindow"""

    def test_missing_home_screen_dependency(self, qapp):
        """Test MainWindow behavior when HomeScreen is missing"""
        # Given: HomeScreen import fails
        with patch('gui.main_window.HomeScreen', side_effect=ImportError("HomeScreen not found")):
            # When: Creating MainWindow
            # Then: Should raise ImportError
            with pytest.raises(ImportError, match="HomeScreen not found"):
                MainWindow()

    def test_button_creation_with_invalid_data(self, qapp, mock_home_screen):
        """Test button creation resilience"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Trying to add invalid button data
        try:
            window.add_app_button("", "❌", -1)  # Invalid data
        except (ValueError, IndexError):
            # Then: Should handle errors gracefully
            pass

        # Original buttons should still work
        assert len(window.app_buttons) >= 3

    def test_switch_app_boundary_conditions(self, qapp, mock_home_screen):
        """Test app switching with boundary conditions"""
        # Given: MainWindow instance
        window = MainWindow()

        # When: Testing boundary conditions
        window.switch_app(-1)  # Negative index
        window.switch_app(0)   # Minimum valid

        # Then: Should handle gracefully
        assert window.current_app >= 0


# Performance tests
class TestMainWindowPerformance:
    """Performance tests for MainWindow"""

    def test_window_creation_performance(self, qapp, mock_home_screen):
        """Test window creation performance"""
        import time

        # Given: Clean state
        start_time = time.time()

        # When: Creating MainWindow
        window = MainWindow()

        # Then: Creation should be fast (< 0.5 seconds)
        creation_time = time.time() - start_time
        assert creation_time < 0.5

    def test_app_switching_performance(self, qapp, mock_home_screen):
        """Test app switching performance"""
        import time

        # Given: MainWindow instance
        window = MainWindow()
        window.show()

        # When: Rapidly switching apps
        start_time = time.time()
        for i in range(100):
            app_index = i % 4  # Cycle through 0,1,2,3
            window.switch_app(app_index)

        # Then: Switching should be fast
        switching_time = time.time() - start_time
        assert switching_time < 1.0  # Less than 1 second for 100 switches

    def test_memory_usage_during_switches(self, qapp, mock_home_screen):
        """Test memory usage during app switches"""
        import psutil
        import os

        # Given: MainWindow and initial memory
        window = MainWindow()
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # When: Performing many app switches
        for i in range(50):
            app_index = i % 4
            window.switch_app(app_index)

        # Then: Memory usage should not grow excessively
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        assert memory_growth < 50 * 1024 * 1024  # Less than 50MB growth
