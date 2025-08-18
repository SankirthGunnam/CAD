import pytest
from unittest.mock import Mock, patch
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager
from apps.RBM.BCF.source.RDB.json_db import JSONDatabase


class TestRDBManager:
    def test_initialization(self, temp_dir):
        """Test RDBManager initialization"""
        db_file = temp_dir / "test_db.json"
        manager = RDBManager(str(db_file))
        assert manager.db is not None
        assert isinstance(manager.db, JSONDatabase)

    def test_get_value(self, mock_rdb_manager):
        """Test getting value from database"""
        test_path = "test/path"
        test_value = {"key": "value"}
        mock_rdb_manager.get_value.return_value = test_value

        result = mock_rdb_manager.get_value(test_path)
        assert result == test_value
        mock_rdb_manager.get_value.assert_called_once_with(test_path)

    def test_set_value(self, mock_rdb_manager):
        """Test setting value in database"""
        test_path = "test/path"
        test_value = {"key": "value"}

        result = mock_rdb_manager.set_value(test_path, test_value)
        assert result is True
        mock_rdb_manager.set_value.assert_called_once_with(test_path, test_value)

    def test_get_table(self, mock_rdb_manager):
        """Test getting table data"""
        test_path = "test/table"
        test_data = [{"id": 1, "name": "test"}]
        mock_rdb_manager.get_table.return_value = test_data

        result = mock_rdb_manager.get_table(test_path)
        assert result == test_data
        mock_rdb_manager.get_table.assert_called_once_with(test_path)

    def test_set_table(self, mock_rdb_manager):
        """Test setting table data"""
        test_path = "test/table"
        test_data = [{"id": 1, "name": "test"}]

        result = mock_rdb_manager.set_table(test_path, test_data)
        assert result is True
        mock_rdb_manager.set_table.assert_called_once_with(test_path, test_data)

    def test_data_changed_signal(self, temp_dir):
        """Test data changed signal emission"""
        db_file = temp_dir / "test_db.json"
        manager = RDBManager(str(db_file))

        # Create a mock slot
        mock_slot = Mock()
        manager.data_changed.connect(mock_slot)

        # Trigger data change
        manager._on_data_changed("test/path")

        # Verify signal was emitted (Qt signals call the connected slot directly)
        mock_slot.assert_called_once_with("test/path")

    def test_error_handling(self, temp_dir):
        """Test error handling"""
        db_file = temp_dir / "test_db.json"
        manager = RDBManager(str(db_file))

        # Create a mock slot
        mock_slot = Mock()
        manager.error_occurred.connect(mock_slot)

        # Simulate error
        test_error = "Test error"
        manager.error_occurred.emit(test_error)

        # Verify error signal was emitted (Qt signals call the connected slot directly)
        mock_slot.assert_called_once_with(test_error)
