import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from apps.RBM.BCF.src.RCC.core_controller import CoreController
from apps.RBM.BCF.src.RCC.build.build_master import BuildMaster


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_rdb_manager():
    """Create a mock RDBManager"""
    manager = Mock(spec=RDBManager)
    # Setup common mock behaviors
    manager.get_value.return_value = {}
    manager.set_value.return_value = True
    manager.get_table.return_value = []
    manager.set_table.return_value = True
    return manager


@pytest.fixture
def mock_core_controller(mock_rdb_manager):
    """Create a mock CoreController"""
    controller = Mock(spec=CoreController)
    controller.rdb_manager = mock_rdb_manager
    return controller


@pytest.fixture
def build_master(mock_core_controller):
    """Create a BuildMaster instance with mocked dependencies"""
    master = BuildMaster(mock_core_controller)
    return master


@pytest.fixture
def sample_build_data():
    """Sample build data for testing"""
    return {
        "name": "test_project",
        "version": "1.0.0",
        "config": {
            "device": {"settings": [], "properties": {}},
            "band": {"settings": [], "properties": {}},
        },
    }
