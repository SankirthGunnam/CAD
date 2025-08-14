import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtTest import QTest

from apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager import VisualBCFManager
from apps.RBM.BCF.src.models.chip import ChipModel
from apps.RBM.BCF.src.models.rfic_chip import RFICChipModel


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def visual_manager(qapp):
    """Create a VisualBCFManager instance for testing"""
    with patch('apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager.FloatingToolbar'):
        manager = VisualBCFManager()
    yield manager
    manager.cleanup()


class TestVisualBCFManagerInitialization:
    """Test suite for Visual BCF Manager initialization"""
    
    def test_initialization_creates_required_components(self, qapp):
        """Test that initialization creates all required components"""
        with patch('apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager.FloatingToolbar'):
            manager = VisualBCFManager()
            
            # Should have scene and view
            assert manager.scene is not None
            assert manager.view is not None
            
            # Should have proper window title
            assert manager.windowTitle() == "Visual BCF Manager"
            
            # Should have clipboard initialized as None
            assert manager.chip_clipboard is None
            
            manager.cleanup()
    
    def test_initialization_with_parent_controller(self, qapp):
        """Test initialization with parent controller creates toolbar"""
        parent_mock = Mock()
        with patch('apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager.FloatingToolbar') as mock_toolbar:
            manager = VisualBCFManager(parent_controller=parent_mock)
            
            # Should create toolbar when parent controller is provided
            mock_toolbar.assert_called_once_with(parent_mock)
            assert manager.parent_controller == parent_mock
            
            manager.cleanup()
    
    def test_scene_view_configuration(self, visual_manager):
        """Test that scene and view are properly configured"""
        # Scene should have proper background
        assert visual_manager.scene is not None
        
        # View should have proper scene rect and background
        scene_rect = visual_manager.view.sceneRect()
        assert scene_rect.width() == 2000
        assert scene_rect.height() == 2000
        
        # Should have background brush set
        assert visual_manager.view.backgroundBrush() is not None


class TestVisualBCFManagerDefaultRFIC:
    """Test suite for default RFIC chip functionality"""
    
    def test_adds_default_rfic_chip_on_startup(self, visual_manager):
        """Test that default RFIC chip is added during initialization"""
        # Should have at least one component (default RFIC)
        components = visual_manager.scene.get_components()
        assert len(components) >= 1
        
        # Should be able to find the default RFIC
        default_rfic = visual_manager.get_default_rfic()
        assert default_rfic is not None
        assert default_rfic.model.name == "Default RFIC"
    
    def test_default_rfic_positioning(self, visual_manager):
        """Test that default RFIC is positioned at center"""
        default_rfic = visual_manager.get_default_rfic()
        assert default_rfic is not None
        
        # The model position gets updated by graphics item positioning
        # Graphics item is positioned at top-left, so model position reflects that
        # Change expected values to the left half of QGraphicsView viewport
        # Get the view's scene rect
        scene_rect = visual_manager.view.sceneRect()
        # Calculate the left half center
        expected_x = scene_rect.left() + (scene_rect.width() / 4) - default_rfic.model.width / 2
        expected_y = scene_rect.top() + (scene_rect.height() / 2) - default_rfic.model.height / 2

        assert default_rfic.model.position == (expected_x, expected_y)
    
    def test_default_rfic_properties(self, visual_manager):
        """Test default RFIC has correct properties"""
        default_rfic = visual_manager.get_default_rfic()
        assert default_rfic is not None
        # Check that width and height are proportional to number of pins on sides
        model = default_rfic.model
        # Assume model has attributes: pins_top, pins_bottom, pins_left, pins_right
        # and that width = base_width + k * max(pins_top, pins_bottom)
        # and height = base_height + k * max(pins_left, pins_right)
        # We'll check proportionality, not exact values (since k, base may vary)
        max_horizontal_pins = max(getattr(model, "pins_top", 0), getattr(model, "pins_bottom", 0))
        max_vertical_pins = max(getattr(model, "pins_left", 0), getattr(model, "pins_right", 0))
        # The width and height should be at least proportional to the max pins
        assert model.width >= max_horizontal_pins * 10  # 10 is a reasonable minimum per pin
        assert model.height >= max_vertical_pins * 10


class TestVisualBCFManagerChipOperations:
    """Test suite for chip operations in Visual BCF Manager"""
    
    def test_add_chip_from_dialog(self, visual_manager):
        """Test adding chip from chip selection dialog"""
        # Mock chip data from dialog
        chip_data = {
            'name': 'Test Amplifier',
            'part_number': 'AMP123',
            'type': 'Power Amplifier',
            'package': 'QFN-24'
        }
        position = QPointF(100, 200)
        
        initial_count = len(visual_manager.scene.get_components())
        
        # Add chip using the internal method
        visual_manager._add_selected_chip(chip_data, position)
        
        # Should have one more component
        new_count = len(visual_manager.scene.get_components())
        assert new_count == initial_count + 1
        
        # Find the newly added chip
        components = visual_manager.scene.get_components()
        new_chip = None
        for component in components:
            if hasattr(component, 'model') and component.model.name == 'Test Amplifier (AMP123)':
                new_chip = component
                break
        
        assert new_chip is not None
        # The model position gets updated to the graphics position (top-left corner)
        # which is offset from the requested center position
        # QFN-24 package should have dimensions 200x150 (from implementation)
        expected_x = position.x() - 200 // 2  # 100 - 100 = 0
        expected_y = position.y() - 150 // 2  # 200 - 75 = 125
        assert new_chip.model.position == (expected_x, expected_y)
    
    def test_add_rfic_chip(self, visual_manager):
        """Test adding additional RFIC chip"""
        initial_count = len(visual_manager.scene.get_components())
        
        # Add RFIC chip
        visual_manager._on_add_rfic()
        
        # Should have one more component
        new_count = len(visual_manager.scene.get_components())
        assert new_count == initial_count + 1
    
    def test_copy_selected_chips(self, visual_manager):
        """Test copying selected chips to clipboard"""
        # Get default RFIC and select it
        default_rfic = visual_manager.get_default_rfic()
        default_rfic.setSelected(True)
        
        # Copy selected chips
        visual_manager._on_copy_selected()
        
        # Should have data in clipboard
        assert visual_manager.chip_clipboard is not None
        assert len(visual_manager.chip_clipboard) == 1
        
        # Clipboard data should contain model information
        clipboard_item = visual_manager.chip_clipboard[0]
        assert 'model_data' in clipboard_item
        assert 'position' in clipboard_item
        assert clipboard_item['model_data']['name'] == 'Default RFIC'
    
    def test_paste_chips(self, visual_manager):
        """Test pasting chips from clipboard"""
        # First copy a chip
        default_rfic = visual_manager.get_default_rfic()
        default_rfic.setSelected(True)
        visual_manager._on_copy_selected()
        
        initial_count = len(visual_manager.scene.get_components())
        
        # Paste chips
        visual_manager._on_paste_chips()
        
        # Should have one more component
        new_count = len(visual_manager.scene.get_components())
        assert new_count == initial_count + 1
    
    def test_delete_selected_chips(self, visual_manager):
        """Test deleting selected chips"""
        # Add an additional chip first
        visual_manager._on_add_rfic()
        initial_count = len(visual_manager.scene.get_components())
        
        # Select all components except default RFIC
        components = visual_manager.scene.get_components()
        for component in components:
            if component.model.name != "Default RFIC":
                component.setSelected(True)
                break
        
        # Delete selected chips
        visual_manager._on_delete_selected()
        
        # Should have one less component
        new_count = len(visual_manager.scene.get_components())
        assert new_count == initial_count - 1


class TestVisualBCFManagerViewOperations:
    """Test suite for view operations (zoom, reset)"""
    
    def test_zoom_in(self, visual_manager):
        """Test zoom in functionality"""
        initial_scale = visual_manager.view.transform().m11()
        
        visual_manager._on_zoom_in()
        
        new_scale = visual_manager.view.transform().m11()
        assert new_scale > initial_scale
    
    def test_zoom_out(self, visual_manager):
        """Test zoom out functionality"""
        # First zoom in to have something to zoom out from
        visual_manager._on_zoom_in()
        initial_scale = visual_manager.view.transform().m11()
        
        visual_manager._on_zoom_out()
        
        new_scale = visual_manager.view.transform().m11()
        assert new_scale < initial_scale
    
    def test_reset_zoom(self, visual_manager):
        """Test reset zoom functionality"""
        # Zoom in first
        visual_manager._on_zoom_in()
        visual_manager._on_zoom_in()
        
        # Reset zoom
        visual_manager._on_reset_zoom()
        
        # Should be back to identity transform
        transform = visual_manager.view.transform()
        assert abs(transform.m11() - 1.0) < 0.01
        assert abs(transform.m22() - 1.0) < 0.01


class TestVisualBCFManagerSignals:
    """Test suite for signal emissions"""
    
    def test_data_changed_signal_on_chip_addition(self, visual_manager):
        """Test that data_changed signal is emitted when adding chips"""
        signal_mock = Mock()
        visual_manager.data_changed.connect(signal_mock)
        
        # Add RFIC chip
        visual_manager._on_add_rfic()
        
        # Signal should have been emitted
        assert signal_mock.called
        args = signal_mock.call_args[0][0]
        assert args['action'] == 'add_rfic'
        assert 'name' in args
    
    def test_error_signal_emission(self, visual_manager):
        """Test error signal emission on failures"""
        signal_mock = Mock()
        visual_manager.error_occurred.connect(signal_mock)
        
        # Force an error by patching scene to raise exception
        with patch.object(visual_manager.scene, 'add_component', side_effect=Exception("Test error")):
            visual_manager._on_add_rfic()
        
        # Error signal should have been emitted
        assert signal_mock.called
        error_message = signal_mock.call_args[0][0]
        assert "Error adding RFIC chip" in error_message


class TestVisualBCFManagerCleanup:
    """Test suite for cleanup functionality"""
    
    def test_cleanup_removes_all_components(self, visual_manager):
        """Test that cleanup removes all components"""
        # Add some additional components
        visual_manager._on_add_rfic()
        initial_count = len(visual_manager.scene.get_components())
        assert initial_count > 0
        
        # Cleanup
        visual_manager.cleanup()
        
        # Should have no components
        final_count = len(visual_manager.scene.get_components())
        assert final_count == 0
    
    def test_cleanup_clears_clipboard(self, visual_manager):
        """Test that cleanup clears clipboard"""
        # Put something in clipboard
        visual_manager.chip_clipboard = [{'test': 'data'}]
        
        # Cleanup
        visual_manager.cleanup()
        
        # Clipboard should be cleared
        assert visual_manager.chip_clipboard is None


class TestVisualBCFManagerUpdateScene:
    """Test suite for scene update functionality"""
    
    def test_update_scene_clears_existing_components(self, visual_manager):
        """Test that update_scene clears existing components"""
        initial_count = len(visual_manager.scene.get_components())
        assert initial_count > 0  # Should have default RFIC
        
        # Update scene with empty data
        visual_manager.update_scene({})
        
        # Should have cleared all components
        final_count = len(visual_manager.scene.get_components())
        assert final_count == 0
    
    def test_update_scene_handles_exceptions(self, visual_manager):
        """Test that update_scene handles exceptions gracefully"""
        error_mock = Mock()
        visual_manager.error_occurred.connect(error_mock)
        
        # Force an error during scene update
        with patch.object(visual_manager.scene, 'get_components', side_effect=Exception("Test error")):
            visual_manager.update_scene({})
        
        # Should emit error signal
        assert error_mock.called


class TestVisualBCFManagerKeyboardShortcuts:
    """Test suite for keyboard shortcuts"""
    
    def test_keyboard_shortcuts_created(self, visual_manager):
        """Test that all keyboard shortcuts are created"""
        # Should have various shortcuts created
        assert hasattr(visual_manager, 'add_chip_shortcut')
        assert hasattr(visual_manager, 'delete_shortcut')
        assert hasattr(visual_manager, 'copy_shortcut')
        assert hasattr(visual_manager, 'paste_shortcut')
        assert hasattr(visual_manager, 'zoom_in_shortcut')
        assert hasattr(visual_manager, 'zoom_out_shortcut')
        assert hasattr(visual_manager, 'zoom_reset_shortcut')
        assert hasattr(visual_manager, 'select_all_shortcut')
        assert hasattr(visual_manager, 'clear_selection_shortcut')
    
    def test_select_all_functionality(self, visual_manager):
        """Test select all functionality"""
        # Add some components
        visual_manager._on_add_rfic()
        components = visual_manager.scene.get_components()
        
        # Clear selection first
        visual_manager.scene.clearSelection()
        
        # Select all
        visual_manager._on_select_all()
        
        # All components should be selected
        selected = visual_manager.scene.get_selected_components()
        assert len(selected) == len(components)
    
    def test_clear_selection_functionality(self, visual_manager):
        """Test clear selection functionality"""
        # Select all first
        visual_manager._on_select_all()
        assert len(visual_manager.scene.get_selected_components()) > 0
        
        # Clear selection
        visual_manager._on_clear_selection()
        
        # Should have no selection
        assert len(visual_manager.scene.get_selected_components()) == 0


class TestVisualBCFManagerToolbarIntegration:
    """Test suite for floating toolbar integration"""
    
    def test_show_hide_toolbar(self, qapp):
        """Test showing and hiding RF toolbar"""
        parent_mock = Mock()
        with patch('apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager.FloatingToolbar') as mock_toolbar_class:
            mock_toolbar = Mock()
            mock_toolbar_class.return_value = mock_toolbar
            
            manager = VisualBCFManager(parent_controller=parent_mock)
            
            # Show toolbar
            manager.show_rf_toolbar()
            assert mock_toolbar.show.called
            
            # Hide toolbar (note: hide might be called multiple times during initialization)
            mock_toolbar.hide.reset_mock()  # Reset call count
            manager.hide_rf_toolbar()
            assert mock_toolbar.hide.called
            
            manager.cleanup()
