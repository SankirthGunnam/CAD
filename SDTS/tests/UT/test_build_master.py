import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os
from apps.RBM.BCF.source.RCC.build.build_master import BuildMaster
from apps.RBM.BCF.source.RCC.core_controller import BuildWorker
from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager


class TestBuildMaster:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_rdb_manager(self):
        """Create a mock RDBManager"""
        manager = Mock(spec=RDBManager)
        # Setup common mock behaviors
        manager.get_value.return_value = {}
        manager.set_value.return_value = True
        manager.get_table.return_value = []
        manager.set_table.return_value = True
        return manager

    @pytest.fixture
    def build_master(self, mock_rdb_manager, temp_dir):
        """Create a BuildMaster instance with mocked dependencies"""
        # Create mock callback and event handler
        mock_callback = Mock()
        mock_event_handler = Mock()

        # Create BuildMaster instance
        master = BuildMaster(mock_rdb_manager, mock_callback, mock_event_handler)
        master.set_output_directory(str(temp_dir / "output"))
        return master

    def test_initialization(self, build_master, mock_rdb_manager):
        """Test BuildMaster initialization"""
        assert build_master.rdb_manager == mock_rdb_manager
        assert build_master.callback is not None
        assert build_master.event_handler is not None
        assert build_master.jinja_env is not None
        assert build_master.get_tool_version() == "1.0.0"
        assert build_master.get_project_code() == "RCC"

    def test_set_output_directory(self, build_master, temp_dir):
        """Test setting output directory"""
        new_dir = temp_dir / "new_dir"
        build_master.set_output_directory(str(new_dir))
        assert build_master.output_dir == new_dir
        assert new_dir.exists()

    def test_generate_files_with_invalid_output_dir(self, build_master):
        """Test generate_files with invalid output directory"""
        build_master.output_dir = None
        with pytest.raises(ValueError):
            build_master.generate_files({})

    @patch("jinja2.Environment.get_template")
    def test_generate_files_success(self, mock_get_template, build_master, temp_dir):
        """Test successful file generation"""
        # Mock template rendering
        mock_template = Mock()
        mock_template.render.return_value = "Generated content"
        mock_get_template.return_value = mock_template

        # Create a mock template file
        template_dir = build_master.template_dir
        template_dir.mkdir(parents=True, exist_ok=True)
        test_template = template_dir / "test.jinja"
        test_template.write_text("Test template")

        # Test data
        test_data = {"name": "test", "version": "1.0"}

        # Generate files
        build_master.generate_files(test_data)

        # Verify template was called with correct data
        mock_template.render.assert_called_once()
        call_args = mock_template.render.call_args[1]
        assert "data" in call_args
        assert call_args["data"] == test_data
        assert "build_time" in call_args
        assert "build_date" in call_args
        assert "tool_version" in call_args
        assert "project_code" in call_args

    def test_build_event_emission(self, build_master, temp_dir):
        """Test build event emission during file generation"""
        # Create a mock template file
        template_dir = build_master.template_dir
        template_dir.mkdir(parents=True, exist_ok=True)
        test_template = template_dir / "test.jinja"
        test_template.write_text("Test template")

        # Generate files
        build_master.generate_files({})

        # Verify event handler was called
        assert build_master.event_handler.called
        calls = build_master.event_handler.call_args_list

        # Check for build started event
        assert calls[0][0][0]["type"] == "build_started"

        # Check for build completed event
        assert calls[-1][0][0]["type"] == "build_completed"

    def test_error_handling(self, build_master):
        """Test error handling during file generation"""
        # Force an error by setting invalid template directory
        build_master.template_dir = Path("/nonexistent/path")

        # Generate files
        build_master.generate_files({})

        # Verify error event was emitted
        assert build_master.event_handler.called
        calls = build_master.event_handler.call_args_list
        assert calls[-1][0][0]["type"] == "build_failed"

    def test_build_worker_integration(self, build_master, mock_rdb_manager):
        """Test integration with BuildWorker"""
        # Create test data
        test_data = {"project": "test_project", "config": {"key": "value"}}

        # Create BuildWorker
        worker = BuildWorker(test_data, build_master)

        # Mock event signal
        mock_event_signal = Mock()
        worker.event_signal = mock_event_signal

        # Run the worker
        worker.run()

        # Verify events were emitted
        assert mock_event_signal.emit.called
        calls = mock_event_signal.emit.call_args_list
        assert calls[0][0][0]["type"] == "status"
        assert calls[0][0][0]["message"] == "Build started"
        assert calls[-1][0][0]["type"] == "status"
        assert calls[-1][0][0]["message"] == "Build completed"

    def test_rdb_manager_integration(self, build_master, mock_rdb_manager):
        """Test integration with RDBManager"""
        # Test data
        test_data = {
            "config": {
                "device": {"settings": [], "properties": {}},
                "band": {"settings": [], "properties": {}},
            }
        }

        # Setup mock RDB manager
        mock_rdb_manager.get_value.return_value = test_data

        # Generate files
        build_master.generate_files(test_data)

        # Verify RDB manager was used
        assert mock_rdb_manager.get_value.called

    def test_callback_execution(self, build_master):
        """Test callback execution after successful build"""
        # Generate files
        build_master.generate_files({})

        # Verify callback was called
        assert build_master.callback.called
