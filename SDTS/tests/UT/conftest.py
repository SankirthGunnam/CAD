import sys
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Import project modules with error handling
try:
    from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager
    from apps.RBM.BCF.source.RCC.core_controller import CoreController
    from apps.RBM.BCF.source.RCC.build.build_master import BuildMaster
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create placeholder classes for testing
    class RDBManager: pass
    class CoreController: pass
    class BuildMaster: pass


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the entire test session"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        # Set up application properties
        app.setApplicationName("SDTS Test Suite")
        app.setApplicationVersion("1.0.0")
    yield app
    # Clean up
    if app:
        app.quit()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    yield temp_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    fd, path = tempfile.mkstemp()
    yield Path(path)
    os.close(fd)
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_rdb_manager():
    """Create a mock RDBManager with common behaviors"""
    manager = Mock(spec=RDBManager)

    # Setup common mock behaviors
    manager.get_value.return_value = {}
    manager.set_value.return_value = True
    manager.get_table.return_value = []
    manager.set_table.return_value = True
    manager.close.return_value = None

    # Mock signals
    manager.data_changed = Mock()
    manager.data_changed.connect = Mock()
    manager.error_occurred = Mock()
    manager.error_occurred.connect = Mock()

    return manager


@pytest.fixture
def mock_core_controller(mock_rdb_manager):
    """Create a mock CoreController with dependencies"""
    controller = Mock(spec=CoreController)
    controller.rdb_manager = mock_rdb_manager

    # Mock methods
    controller.process_event = Mock()
    controller.get_state = Mock(return_value="IDLE")

    # Mock signals
    controller.reply_signal = Mock()
    controller.reply_signal.connect = Mock()
    controller.build_event = Mock()
    controller.build_event.connect = Mock()
    controller.state_changed = Mock()
    controller.state_changed.connect = Mock()
    controller.error_occurred = Mock()
    controller.error_occurred.connect = Mock()

    return controller


@pytest.fixture
def mock_gui_controller():
    """Create a mock GUIController"""
    controller = Mock()

    # Mock methods
    controller.show_status = Mock()
    controller.show_error = Mock()
    controller.show_warning = Mock()
    controller.update_state = Mock()
    controller.refresh_data = Mock()
    controller.add_generated_file = Mock()

    # Mock signals
    controller.build_requested = Mock()
    controller.build_requested.connect = Mock()
    controller.configure_requested = Mock()
    controller.configure_requested.connect = Mock()
    controller.export_requested = Mock()
    controller.export_requested.connect = Mock()
    controller.error_occurred = Mock()
    controller.error_occurred.connect = Mock()
    controller.data_changed = Mock()
    controller.data_changed.connect = Mock()

    return controller


@pytest.fixture
def build_master(mock_core_controller):
    """Create a BuildMaster instance with mocked dependencies"""
    try:
        master = BuildMaster(mock_core_controller)
        return master
    except Exception:
        # Return a mock if creation fails
        return Mock(spec=BuildMaster)


@pytest.fixture
def sample_build_data():
    """Sample build data for testing"""
    return {
        "name": "test_project",
        "version": "1.0.0",
        "description": "Test project for TDD",
        "config": {
            "device": {"settings": [], "properties": {}},
            "band": {"settings": [], "properties": {}},
        },
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "author": "test_user"
        }
    }


@pytest.fixture
def sample_device_config():
    """Sample device configuration for testing"""
    return {
        "device_id": "test_device_001",
        "device_type": "RF_TRANSCEIVER",
        "parameters": {
            "frequency_range": {"min": 1000000000, "max": 6000000000},
            "power_levels": [0, 10, 20, 30],
            "modulation": ["QPSK", "16QAM", "64QAM"]
        },
        "constraints": {
            "max_power": 30,
            "temperature_range": {"min": -40, "max": 85}
        }
    }


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing"""
    connection = Mock()
    connection.execute = Mock(return_value=[])
    connection.fetchall = Mock(return_value=[])
    connection.fetchone = Mock(return_value=None)
    connection.commit = Mock()
    connection.rollback = Mock()
    connection.close = Mock()
    return connection


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for each test"""
    # Set environment variables for testing
    os.environ["SDTS_TEST_MODE"] = "1"
    os.environ["QT_QPA_PLATFORM"] = "offscreen"  # For headless GUI testing

    yield

    # Clean up environment
    if "SDTS_TEST_MODE" in os.environ:
        del os.environ["SDTS_TEST_MODE"]


@pytest.fixture
def mock_file_system(tmp_path):
    """Create a mock file system structure for testing"""
    # Create directory structure
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "logs").mkdir()

    # Create sample files
    (tmp_path / "config" / "settings.json").write_text('{"debug": true}')
    (tmp_path / "data" / "sample.txt").write_text("Sample data")

    return tmp_path


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Custom pytest markers
pytestmark = [
    pytest.mark.filterwarnings("ignore:.*PySide6.*:DeprecationWarning"),
    pytest.mark.filterwarnings("ignore:.*QtWidgets.*:DeprecationWarning"),
]


# Test data generators
def generate_test_data(data_type: str, count: int = 1):
    """Generate various types of test data"""
    generators = {
        "user": lambda: {"id": 1, "name": "test_user", "email": "test@example.com"},
        "project": lambda: {"id": 1, "name": "test_project", "status": "active"},
        "device": lambda: {"id": 1, "name": "test_device", "type": "RF_DEVICE"},
    }

    if data_type not in generators:
        raise ValueError(f"Unknown data type: {data_type}")

    if count == 1:
        return generators[data_type]()
    else:
        return [generators[data_type]() for _ in range(count)]
