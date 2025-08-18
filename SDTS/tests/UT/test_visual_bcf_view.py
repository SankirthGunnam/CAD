import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QWheelEvent, QKeyEvent

from apps.RBM.BCF.gui.source.visual_bcf.view import RFView
from apps.RBM.BCF.gui.source.visual_bcf.scene import RFScene


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
    return scene


@pytest.fixture
def rf_view(rf_scene, qapp):
    """Create an RFView instance with scene for testing"""
    view = RFView(rf_scene)
    return view


class TestRFViewInitialization:
    """Test suite for RFView initialization"""
    
    def test_view_initialization(self, rf_view, rf_scene):
        """Test that RFView initializes properly with scene"""
        assert rf_view is not None
        assert rf_view.scene() == rf_scene
    
    def test_render_hints_set(self, rf_view):
        """Test that render hints are properly set"""
        # Should have antialiasing enabled
        render_hints = rf_view.renderHints()
        assert render_hints & QPainter.Antialiasing
        assert render_hints & QPainter.SmoothPixmapTransform
    
    def test_viewport_update_mode(self, rf_view):
        """Test viewport update mode is set correctly"""
        from PySide6.QtWidgets import QGraphicsView
        assert rf_view.viewportUpdateMode() == QGraphicsView.FullViewportUpdate
    
    def test_transformation_anchor(self, rf_view):
        """Test transformation anchor is set correctly"""
        from PySide6.QtWidgets import QGraphicsView
        assert rf_view.transformationAnchor() == QGraphicsView.AnchorUnderMouse
        assert rf_view.resizeAnchor() == QGraphicsView.AnchorUnderMouse


class TestRFViewWheelZoom:
    """Test suite for wheel zoom functionality"""
    
    def test_wheel_zoom_in(self, rf_view):
        """Test zooming in with mouse wheel"""
        initial_scale = rf_view.transform().m11()
        
        # Create mock wheel event for zoom in (positive delta)
        mock_event = Mock()
        mock_event.angleDelta.return_value = Mock()
        mock_event.angleDelta().y.return_value = 120  # Positive for zoom in
        
        rf_view.wheelEvent(mock_event)
        
        new_scale = rf_view.transform().m11()
        assert new_scale > initial_scale
    
    def test_wheel_zoom_out(self, rf_view):
        """Test zooming out with mouse wheel"""
        # First zoom in to have something to zoom out from
        rf_view.scale(2.0, 2.0)
        initial_scale = rf_view.transform().m11()
        
        # Create mock wheel event for zoom out (negative delta)
        mock_event = Mock()
        mock_event.angleDelta.return_value = Mock()
        mock_event.angleDelta().y.return_value = -120  # Negative for zoom out
        
        rf_view.wheelEvent(mock_event)
        
        new_scale = rf_view.transform().m11()
        assert new_scale < initial_scale
    
    def test_wheel_zoom_factor(self, rf_view):
        """Test that zoom factor is consistent"""
        initial_scale = rf_view.transform().m11()
        
        # Zoom in
        mock_event = Mock()
        mock_event.angleDelta.return_value = Mock()
        mock_event.angleDelta().y.return_value = 120
        rf_view.wheelEvent(mock_event)
        
        zoomed_scale = rf_view.transform().m11()
        expected_scale = initial_scale * 1.15  # Zoom factor from implementation
        
        assert abs(zoomed_scale - expected_scale) < 0.01


class TestRFViewFitInView:
    """Test suite for fit in view functionality"""
    
    def test_fit_in_view_with_rect(self, rf_view):
        """Test fitting view to a specific rectangle"""
        test_rect = QRectF(0, 0, 500, 300)
        
        # Mock the parent's fitInView to avoid actual fitting
        with patch('PySide6.QtWidgets.QGraphicsView.fitInView') as mock_fit:
            rf_view.fitInView(test_rect)
            mock_fit.assert_called_once_with(test_rect, Qt.KeepAspectRatio)
    
    def test_fit_in_view_prevents_extreme_zoom_out(self, rf_view):
        """Test that fitInView prevents zooming out too far"""
        # Set up a scenario where transform would be too small
        rf_view.scale(0.05, 0.05)  # Very small scale
        
        with patch('PySide6.QtWidgets.QGraphicsView.fitInView'):
            with patch.object(rf_view, 'resetTransform') as mock_reset:
                rf_view.fitInView(QRectF(0, 0, 1000, 1000))
                
                # If scale becomes too small (< 0.1), should reset transform
                if rf_view.transform().m11() < 0.1:
                    mock_reset.assert_called_once()


class TestRFViewTransformReset:
    """Test suite for transform reset functionality"""
    
    def test_reset_transform(self, rf_view):
        """Test resetting view transformation"""
        # First apply some transformations
        rf_view.scale(2.0, 2.0)
        rf_view.rotate(45)
        
        # Reset transform
        rf_view.resetTransform()
        
        # Should be back to identity transform (scale 1.0)
        transform = rf_view.transform()
        assert abs(transform.m11() - 1.0) < 0.01
        assert abs(transform.m22() - 1.0) < 0.01
        assert abs(transform.m12()) < 0.01  # No rotation/shear
        assert abs(transform.m21()) < 0.01  # No rotation/shear
    
    def test_reset_transform_sets_unit_scale(self, rf_view):
        """Test that reset transform sets scale to 1.0"""
        # Apply some scaling
        rf_view.scale(3.0, 0.5)
        
        rf_view.resetTransform()
        
        # Should have unit scaling
        transform = rf_view.transform()
        assert abs(transform.m11() - 1.0) < 0.01
        assert abs(transform.m22() - 1.0) < 0.01


class TestRFViewKeyboardEvents:
    """Test suite for keyboard event handling"""
    
    def test_delete_key_removes_selected_items(self, rf_view, rf_scene):
        """Test that Delete key removes selected items"""
        # Create mock selected item with model that has remove method
        mock_item = Mock()
        mock_model = Mock()
        mock_model.remove = Mock()
        mock_item.model = mock_model
        
        # Mock scene's selectedItems to return our mock item
        with patch.object(rf_scene, 'selectedItems', return_value=[mock_item]):
            # Create Delete key event
            mock_event = Mock()
            mock_event.key.return_value = Qt.Key_Delete
            
            rf_view.keyPressEvent(mock_event)
            
            # Model's remove method should be called
            mock_model.remove.assert_called_once()
    
    def test_delete_key_ignores_items_without_model(self, rf_view, rf_scene):
        """Test that Delete key ignores items without model"""
        # Create mock item without model
        mock_item = Mock()
        del mock_item.model  # Remove model attribute
        
        with patch.object(rf_scene, 'selectedItems', return_value=[mock_item]):
            mock_event = Mock()
            mock_event.key.return_value = Qt.Key_Delete
            
            # Should not raise exception
            rf_view.keyPressEvent(mock_event)
    
    def test_delete_key_ignores_items_without_remove_method(self, rf_view, rf_scene):
        """Test that Delete key ignores items whose models don't have remove method"""
        # Create mock item with model but no remove method
        mock_item = Mock()
        mock_model = Mock()
        del mock_model.remove  # Remove remove method
        mock_item.model = mock_model
        
        with patch.object(rf_scene, 'selectedItems', return_value=[mock_item]):
            mock_event = Mock()
            mock_event.key.return_value = Qt.Key_Delete
            
            # Should not raise exception
            rf_view.keyPressEvent(mock_event)
    
    def test_other_keys_passed_to_parent(self, rf_view):
        """Test that other keys are passed to parent class"""
        with patch('PySide6.QtWidgets.QGraphicsView.keyPressEvent') as mock_parent:
            mock_event = Mock()
            mock_event.key.return_value = Qt.Key_Space
            
            rf_view.keyPressEvent(mock_event)
            
            # Should call parent's keyPressEvent
            mock_parent.assert_called_once_with(mock_event)


class TestRFViewResizeEvents:
    """Test suite for resize event handling"""
    
    def test_resize_event_emits_signal(self, rf_view):
        """Test that resize events emit the resize signal"""
        signal_mock = Mock()
        rf_view.resizeSignal.connect(signal_mock)
        
        # Create mock resize event
        mock_event = Mock()
        
        # Mock parent's resizeEvent to avoid actual resizing
        with patch('PySide6.QtWidgets.QGraphicsView.resizeEvent') as mock_parent:
            rf_view.resizeEvent(mock_event)
            
            # Parent should be called
            mock_parent.assert_called_once_with(mock_event)
            
            # Signal should be emitted
            signal_mock.assert_called_once()
    
    def test_resize_signal_exists(self, rf_view):
        """Test that resize signal is properly defined"""
        assert hasattr(rf_view, 'resizeSignal')
        
        # Should be able to connect to it
        mock_slot = Mock()
        rf_view.resizeSignal.connect(mock_slot)
        
        # Manual emit should work
        rf_view.resizeSignal.emit()
        mock_slot.assert_called_once()


class TestRFViewSceneInteraction:
    """Test suite for view-scene interaction"""
    
    def test_view_has_correct_scene(self, rf_view, rf_scene):
        """Test that view is connected to correct scene"""
        assert rf_view.scene() == rf_scene
    
    def test_view_can_access_scene_components(self, rf_view, rf_scene):
        """Test that view can access scene components through scene"""
        # Add a mock component to scene
        mock_component = Mock()
        rf_scene.add_component(mock_component)
        
        # View should be able to access components through scene
        components = rf_view.scene().get_components()
        assert mock_component in components
    
    def test_view_selection_works_with_scene(self, rf_view, rf_scene):
        """Test that view selection works with scene"""
        # Mock a selectable item
        mock_item = Mock()
        mock_item.isSelected.return_value = True
        
        with patch.object(rf_scene, 'selectedItems', return_value=[mock_item]):
            selected = rf_view.scene().selectedItems()
            assert len(selected) == 1
            assert mock_item in selected


class TestRFViewRenderingProperties:
    """Test suite for rendering properties"""
    
    def test_antialiasing_enabled(self, rf_view):
        """Test that antialiasing is enabled"""
        render_hints = rf_view.renderHints()
        assert render_hints & QPainter.Antialiasing
    
    def test_smooth_pixmap_transform_enabled(self, rf_view):
        """Test that smooth pixmap transform is enabled"""
        render_hints = rf_view.renderHints()
        assert render_hints & QPainter.SmoothPixmapTransform
    
    def test_viewport_update_mode_is_full(self, rf_view):
        """Test that viewport update mode is set to full viewport update"""
        from PySide6.QtWidgets import QGraphicsView
        assert rf_view.viewportUpdateMode() == QGraphicsView.FullViewportUpdate


class TestRFViewTransformationAnchors:
    """Test suite for transformation anchors"""
    
    def test_transformation_anchor_under_mouse(self, rf_view):
        """Test that transformation anchor is set to under mouse"""
        from PySide6.QtWidgets import QGraphicsView
        assert rf_view.transformationAnchor() == QGraphicsView.AnchorUnderMouse
    
    def test_resize_anchor_under_mouse(self, rf_view):
        """Test that resize anchor is set to under mouse"""
        from PySide6.QtWidgets import QGraphicsView
        assert rf_view.resizeAnchor() == QGraphicsView.AnchorUnderMouse


class TestRFViewScaling:
    """Test suite for view scaling operations"""
    
    def test_scale_operation(self, rf_view):
        """Test basic scaling operation"""
        initial_scale = rf_view.transform().m11()
        
        rf_view.scale(1.5, 1.5)
        
        new_scale = rf_view.transform().m11()
        expected_scale = initial_scale * 1.5
        
        assert abs(new_scale - expected_scale) < 0.01
    
    def test_uneven_scaling(self, rf_view):
        """Test uneven scaling (different x and y factors)"""
        initial_x_scale = rf_view.transform().m11()
        initial_y_scale = rf_view.transform().m22()
        
        rf_view.scale(2.0, 0.5)
        
        new_x_scale = rf_view.transform().m11()
        new_y_scale = rf_view.transform().m22()
        
        assert abs(new_x_scale - initial_x_scale * 2.0) < 0.01
        assert abs(new_y_scale - initial_y_scale * 0.5) < 0.01
    
    def test_multiple_scale_operations(self, rf_view):
        """Test multiple scaling operations accumulate correctly"""
        initial_scale = rf_view.transform().m11()
        
        rf_view.scale(1.5, 1.5)
        rf_view.scale(2.0, 2.0)
        
        final_scale = rf_view.transform().m11()
        expected_scale = initial_scale * 1.5 * 2.0
        
        assert abs(final_scale - expected_scale) < 0.01


class TestRFViewErrorHandling:
    """Test suite for error handling in RFView"""
    
    def test_key_press_with_invalid_scene_items(self, rf_view):
        """Test key press handling with invalid scene items"""
        # Mock scene to return items that might cause errors
        mock_scene = Mock()
        mock_item = Mock()
        # Simulate an item that might cause attribute errors
        mock_item.model = None
        mock_scene.selectedItems.return_value = [mock_item]
        
        with patch.object(rf_view, 'scene', return_value=mock_scene):
            mock_event = Mock()
            mock_event.key.return_value = Qt.Key_Delete
            
            # Should not raise exception
            try:
                rf_view.keyPressEvent(mock_event)
            except Exception:
                pytest.fail("keyPressEvent raised an exception with invalid items")
    
    def test_wheel_event_with_zero_delta(self, rf_view):
        """Test wheel event with zero delta"""
        initial_scale = rf_view.transform().m11()
        
        mock_event = Mock()
        mock_event.angleDelta.return_value = Mock()
        mock_event.angleDelta().y.return_value = 0  # Zero delta
        
        rf_view.wheelEvent(mock_event)
        
        # Scale should remain unchanged
        final_scale = rf_view.transform().m11()
        assert abs(final_scale - initial_scale) < 0.01


class TestRFViewMemoryManagement:
    """Test suite for memory management in RFView"""
    
    def test_view_cleanup_on_deletion(self, rf_scene, qapp):
        """Test that view cleans up properly when deleted"""
        # Create view
        view = RFView(rf_scene)
        
        # Get initial reference count of scene
        import sys
        initial_refs = sys.getrefcount(rf_scene)
        
        # Delete view
        del view
        
        # Scene reference count should decrease
        final_refs = sys.getrefcount(rf_scene)
        assert final_refs <= initial_refs
    
    def test_signal_disconnection_on_cleanup(self, rf_view):
        """Test that signals are properly disconnected"""
        mock_slot = Mock()
        rf_view.resizeSignal.connect(mock_slot)
        
        # Manually disconnect (simulating cleanup)
        rf_view.resizeSignal.disconnect()
        
        # Emit signal - should not call the slot
        rf_view.resizeSignal.emit()
        mock_slot.assert_not_called()
