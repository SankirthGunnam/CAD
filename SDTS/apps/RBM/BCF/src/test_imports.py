import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../..")
)
sys.path.insert(0, project_root)

# Try importing our modules
try:
    from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
    from apps.RBM.BCF.src.RDB.paths import (
        DEVICE_SETTINGS,
        BAND_CONFIG,
        BOARD_CONFIG,
        RCC_CONFIG,
    )

    print("Imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
