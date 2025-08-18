import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QGraphicsView
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from apps.RBM.BCF.gui.source.visual_bcf.scene import RFScene
from apps.RBM.BCF.source.models.chip import ChipModel
from apps.RBM.BCF.gui.custom_widgets.components.chip import Chip


@pytest.fixture
def qapp():
    """Create QApplication instance for testing"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def rf_scene(qapp):
    """Create an RFScene instance for testing"""
    scene = RFScene()
    yield scene


@pytest.fixture
def mock_chip():
    """Create a mock chip with model for testing"""
    chip_model = ChipModel(name="Test Chip", width=100, height=80)
    chip_model.add_pin(0, 40, "Input")
    chip_model.add_pin(100, 40, "Output")
    chip = Chip(chip_model)
    return chip


class TestRFSceneInitialization:
    """Test suite for RFScene initialization"""
    
    def test_scene_initialization(self, rf_scene):
        """Test that RFScene initializes properly"""
        assert rf_scene is not None
        assert rf_scene.backgroundBrush() is not None
        assert rf_scene.temp_connection is None
        assert rf_scene.start_pin is None
    
    def test_scene_properties(self, rf_scene):
        """Test RFScene properties"""
        # Should have mouse position property
        assert hasattr(rf_scene, 'mouse_pos')
        assert isinstance(rf_scene.mouse_pos, QPointF)
        
        # Should have pins dictionary
        assert hasattr(rf_scene, '_pins')
        assert isinstance(rf_scene._pins, dict)
        
        # Should have context menu position
        assert hasattr(rf_scene, '_context_menu_pos')
        assert isinstance(rf_scene._context_menu_pos, QPointF)


class TestRFSceneComponentManagement:
    """Test suite for component management in RFScene"""
    
    def test_add_component(self, rf_scene, mock_chip):
        """Test adding a component to the scene"""
        initial_count = len(rf_scene.get_components())
        
        # Add component
        rf_scene.add_component(mock_chip)
        
        # Should have one more component
        new_count = len(rf_scene.get_components())
        assert new_count == initial_count + 1
        
        # Component should be in scene items
        assert mock_chip in rf_scene.items()
    
    def test_add_component_creates_pin_widgets(self, rf_scene, mock_chip):
        """Test that adding chip component creates pin widgets"""
        # Add component
        rf_scene.add_component(mock_chip)
        
        # Should have created pin widgets for each pin
        assert len(rf_scene._pins) >= len(mock_chip.model.pins)
        
        # Each pin should have a corresponding widget
        for pin in mock_chip.model.pins:
            assert pin in rf_scene._pins
    
    def test_remove_component(self, rf_scene, mock_chip):
        """Test removing a component from the scene"""
        # Add component first
        rf_scene.add_component(mock_chip)
        initial_count = len(rf_scene.get_components())
        
        # Remove component
        rf_scene.remove_component(mock_chip)
        
        # Should have one less component
        new_count = len(rf_scene.get_components())
        assert new_count == initial_count - 1
        
        # Component should not be in scene items
        assert mock_chip not in rf_scene.items()
    
    def test_remove_component_cleans_pin_widgets(self, rf_scene, mock_chip):
        """Test that removing component cleans up pin widgets"""
        # Add component first
        rf_scene.add_component(mock_chip)
        initial_pins = len(rf_scene._pins)
        
        # Remove component
        rf_scene.remove_component(mock_chip)
        
        # Pin widgets for this component should be removed
        final_pins = len(rf_scene._pins)
        assert final_pins < initial_pins
        
        # Pins from this component should not be in the pins dict
        for pin in mock_chip.model.pins:
            assert pin not in rf_scene._pins
    
    def test_get_components(self, rf_scene, mock_chip):
        """Test getting all components from the scene"""
        initial_components = rf_scene.get_components()
        
        # Add component
        rf_scene.add_component(mock_chip)
        
        # Should return all chip components
        components = rf_scene.get_components()
        assert len(components) == len(initial_components) + 1
        assert mock_chip in components
        
        # Should only return Chip instances
        for component in components:
            assert isinstance(component, Chip)
    
    def test_get_selected_components(self, rf_scene, mock_chip):
        """Test getting selected components"""
        # Add and select component
        rf_scene.add_component(mock_chip)
        mock_chip.setSelected(True)
        
        # Should return selected components
        selected = rf_scene.get_selected_components()
        assert len(selected) == 1
        assert mock_chip in selected
        
        # Deselect and test
        mock_chip.setSelected(False)
        selected = rf_scene.get_selected_components()
        assert len(selected) == 0


class TestRFSceneMouseEvents:
    """Test suite for mouse event handling in RFScene"""
    
    def test_mouse_position_tracking(self, rf_scene):
        """Test that mouse position is tracked"""
        # Create mock mouse move event
        position = QPointF(100, 150)
        
        with patch('PySide6.QtWidgets.QGraphicsSceneMouseEvent') as mock_event:
            mock_event.scenePos.return_value = position
            rf_scene.mouseMoveEvent(mock_event)
        
        # Mouse position should be updated
        assert rf_scene.mouse_pos == position
    
    def test_mouse_press_on_empty_space(self, rf_scene):
        """Test mouse press on empty space"""
        with patch('PySide6.QtWidgets.QGraphicsSceneMouseEvent') as mock_event:
            mock_event.button.return_value = Qt.LeftButton
            mock_event.scenePos.return_value = QPointF(50, 50)
            
            # Mock itemAt to return None (empty space)
            with patch.object(rf_scene, 'itemAt', return_value=None):
                rf_scene.mousePressEvent(mock_event)
                
                # Should not create temp connection
                assert rf_scene.temp_connection is None
                assert rf_scene.start_pin is None
    
    def test_mouse_release_without_connection(self, rf_scene):
        """Test mouse release without starting a connection"""
        with patch('PySide6.QtWidgets.QGraphicsSceneMouseEvent') as mock_event:
            mock_event.button.return_value = Qt.LeftButton
            mock_event.scenePos.return_value = QPointF(50, 50)
            
            rf_scene.mouseReleaseEvent(mock_event)
            
            # Should remain None
            assert rf_scene.temp_connection is None
            assert rf_scene.start_pin is None


class TestRFSceneContextMenu:
    """Test suite for context menu functionality"""
    
    def test_context_menu_position_tracking(self, rf_scene):
        """Test that context menu position is tracked"""
        position = QPointF(75, 125)
        
        with patch('PySide6.QtWidgets.QGraphicsSceneContextMenuEvent') as mock_event:
            mock_event.scenePos.return_value = position
            
            # Mock itemAt and QMenu to avoid actual menu display
            with patch.object(rf_scene, 'itemAt', return_value=None), \
                 patch('PySide6.QtWidgets.QMenu') as mock_menu_class:
                
                mock_menu = Mock()
                mock_menu.actions.return_value = [Mock()]  # At least one action
                mock_menu_class.return_value = mock_menu
                
                # Mock views to avoid errors
                rf_scene.views = Mock(return_value=[Mock()])
                
                rf_scene.contextMenuEvent(mock_event)
                
                # Context menu position should be stored
                assert rf_scene._context_menu_pos == position
    
    def test_context_menu_on_empty_space(self, rf_scene):
        """Test context menu on empty space"""
        with patch('PySide6.QtWidgets.QGraphicsSceneContextMenuEvent') as mock_event:
            mock_event.scenePos.return_value = QPointF(50, 50)
            
            # Mock itemAt to return None (empty space)
            with patch.object(rf_scene, 'itemAt', return_value=None), \
                 patch('PySide6.QtWidgets.QMenu') as mock_menu_class:
                
                mock_menu = Mock()
                mock_menu_class.return_value = mock_menu
                
                # Mock views to avoid errors
                rf_scene.views = Mock(return_value=[Mock()])
                
                rf_scene.contextMenuEvent(mock_event)
                
                # Should create menu with "Add Chip" option
                mock_menu_class.assert_called_once()
                mock_menu.addAction.assert_called()
    
    def test_context_menu_on_chip(self, rf_scene, mock_chip):
        """Test context menu on chip component"""
        rf_scene.add_component(mock_chip)
        
        with patch('PySide6.QtWidgets.QGraphicsSceneContextMenuEvent') as mock_event:
            mock_event.scenePos.return_value = QPointF(50, 50)
            
            # Mock itemAt to return the chip
            with patch.object(rf_scene, 'itemAt', return_value=mock_chip), \
                 patch('PySide6.QtWidgets.QMenu') as mock_menu_class:
                
                mock_menu = Mock()
                mock_menu_class.return_value = mock_menu
                
                # Mock views to avoid errors
                rf_scene.views = Mock(return_value=[Mock()])
                
                rf_scene.contextMenuEvent(mock_event)
                
                # Should create menu with chip-specific options
                mock_menu_class.assert_called_once()
                # Should have multiple addAction calls for chip operations
                assert mock_menu.addAction.call_count >= 3  # Select, Copy, Delete, Properties
    
    def test_add_chip_request_signal(self, rf_scene):
        """Test add chip request signal emission"""
        signal_mock = Mock()
        rf_scene.add_chip_requested.connect(signal_mock)
        
        position = QPointF(100, 200)
        rf_scene._context_menu_pos = position
        
        # Trigger add chip request
        rf_scene._request_add_chip()
        
        # Signal should be emitted with correct position
        signal_mock.assert_called_once_with(position)


class TestRFSceneChipOperations:
    """Test suite for chip operations via context menu"""
    
    def test_select_chip(self, rf_scene, mock_chip):
        """Test chip selection"""
        rf_scene.add_component(mock_chip)
        
        # Initially not selected
        assert not mock_chip.isSelected()
        
        # Select chip
        rf_scene._select_chip(mock_chip)
        
        # Should be selected
        assert mock_chip.isSelected()
    
    def test_select_chip_emits_signals(self, rf_scene, mock_chip):
        """Test that selecting chip emits appropriate signals"""
        rf_scene.add_component(mock_chip)
        
        chip_signal_mock = Mock()
        selection_signal_mock = Mock()
        rf_scene.chip_selected.connect(chip_signal_mock)
        rf_scene.selection_changed.connect(selection_signal_mock)
        
        # Select chip
        rf_scene._select_chip(mock_chip)
        
        # Signals should be emitted
        chip_signal_mock.assert_called_once_with(mock_chip)
        selection_signal_mock.assert_called_once_with(True)
    
    def test_delete_chip(self, rf_scene, mock_chip):
        """Test deleting a specific chip"""
        rf_scene.add_component(mock_chip)
        initial_count = len(rf_scene.get_components())
        
        # Delete chip
        rf_scene._delete_chip(mock_chip)
        
        # Should have one less component
        new_count = len(rf_scene.get_components())
        assert new_count == initial_count - 1
        assert mock_chip not in rf_scene.items()
    
    def test_delete_selected_chips(self, rf_scene):
        """Test deleting all selected chips"""
        # Add multiple chips
        chip1 = Mock(spec=Chip)
        chip2 = Mock(spec=Chip)
        
        rf_scene.add_component(chip1)
        rf_scene.add_component(chip2)
        
        # Select both chips
        chip1.setSelected(True)
        chip2.setSelected(True)
        
        # Mock get_selected_components to return selected chips
        with patch.object(rf_scene, 'get_selected_components', return_value=[chip1, chip2]):
            rf_scene._delete_selected()
        
        # Should call remove_component for each selected chip
        # Note: We can't easily test the actual removal here due to mocking,
        # but we can verify the method was called
    
    def test_copy_chip_placeholder(self, rf_scene, mock_chip):
        """Test copy chip functionality (currently placeholder)"""
        rf_scene.add_component(mock_chip)
        
        # Copy chip (currently just prints)
        with patch('builtins.print') as mock_print:
            rf_scene._copy_chip(mock_chip)
            mock_print.assert_called_once()
    
    def test_copy_selected_placeholder(self, rf_scene):
        """Test copy selected functionality (currently placeholder)"""
        # Mock some selected components
        selected_chips = [Mock(spec=Chip), Mock(spec=Chip)]
        
        with patch.object(rf_scene, 'get_selected_components', return_value=selected_chips), \
             patch('builtins.print') as mock_print:
            rf_scene._copy_selected()
            mock_print.assert_called_once()


class TestRFSceneChipProperties:
    """Test suite for chip properties functionality"""
    
    def test_show_chip_properties_with_metadata(self, rf_scene, mock_chip):
        """Test showing chip properties when chip has metadata"""
        # Add metadata to chip
        mock_chip.model.metadata = {
            'name': 'Test Chip',
            'part_number': 'TC123',
            'type': 'Amplifier'
        }
        rf_scene.add_component(mock_chip)
        
        # Mock the dialog
        with patch('apps.RBM.BCF.gui.source.views.chip_properties_dialog.ChipPropertiesDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            
            # Mock views
            rf_scene.views = Mock(return_value=[Mock()])
            
            rf_scene._show_chip_properties(mock_chip)
            
            # Dialog should be created and shown
            mock_dialog_class.assert_called_once()
            mock_dialog.exec.assert_called_once()
    
    def test_show_chip_properties_without_metadata(self, rf_scene, mock_chip):
        """Test showing chip properties when chip has no metadata"""
        rf_scene.add_component(mock_chip)
        
        # Mock the dialog
        with patch('apps.RBM.BCF.gui.source.views.chip_properties_dialog.ChipPropertiesDialog') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            
            # Mock views
            rf_scene.views = Mock(return_value=[Mock()])
            
            rf_scene._show_chip_properties(mock_chip)
            
            # Dialog should be created with default chip data
            mock_dialog_class.assert_called_once()
            args = mock_dialog_class.call_args[0][0]
            assert args['name'] == mock_chip.model.name
            assert args['type'] == 'Custom'
    
    def test_update_chip_properties(self, rf_scene, mock_chip):
        """Test updating chip properties with new data"""
        rf_scene.add_component(mock_chip)
        
        updated_data = {
            'name': 'Updated Chip Name',
            'part_number': 'UC456',
            'type': 'Updated Type'
        }
        
        # Mock the chip's update method
        mock_chip.update = Mock()
        
        rf_scene._update_chip_properties(mock_chip, updated_data)
        
        # Metadata should be updated
        assert mock_chip.model.metadata == updated_data
        assert mock_chip.model.name == updated_data['name']
        
        # Chip should be updated visually
        mock_chip.update.assert_called_once()


class TestRFSceneSignals:
    """Test suite for signal emissions"""
    
    def test_selection_changed_signal_on_selection_change(self, rf_scene, mock_chip):
        """Test selection changed signal emission"""
        rf_scene.add_component(mock_chip)
        
        signal_mock = Mock()
        rf_scene.selection_changed.connect(signal_mock)
        
        # Override selectionChanged to trigger the signal
        rf_scene.selectionChanged()
        
        # Signal should be emitted with False initially (no selection)
        signal_mock.assert_called_with(False)
    
    def test_chip_selected_signal(self, rf_scene, mock_chip):
        """Test chip selected signal emission"""
        rf_scene.add_component(mock_chip)
        
        signal_mock = Mock()
        rf_scene.chip_selected.connect(signal_mock)
        
        # Select chip
        rf_scene._select_chip(mock_chip)
        
        # Signal should be emitted
        signal_mock.assert_called_once_with(mock_chip)


class TestRFSceneErrorHandling:
    """Test suite for error handling in RFScene"""
    
    def test_show_chip_properties_error_handling(self, rf_scene, mock_chip):
        """Test error handling in show chip properties"""
        rf_scene.add_component(mock_chip)
        
        # Force an error by patching the dialog import to fail
        with patch('apps.RBM.BCF.gui.source.views.chip_properties_dialog.ChipPropertiesDialog', side_effect=ImportError("Test error")), \
             patch('builtins.print') as mock_print:
            
            rf_scene._show_chip_properties(mock_chip)
            
            # Should print error message
            mock_print.assert_called_once()
            assert "Error showing chip properties" in str(mock_print.call_args)
    
    def test_update_chip_properties_error_handling(self, rf_scene, mock_chip):
        """Test error handling in update chip properties"""
        rf_scene.add_component(mock_chip)
        
        # Force an error by making model.metadata assignment fail
        with patch.object(mock_chip.model, '__setattr__', side_effect=Exception("Test error")), \
             patch('builtins.print') as mock_print:
            
            rf_scene._update_chip_properties(mock_chip, {'name': 'test'})
            
            # Should print error message
            mock_print.assert_called_once()
            assert "Error updating chip properties" in str(mock_print.call_args)
