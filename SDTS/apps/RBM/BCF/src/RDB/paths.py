"""
Database path constants for the JSON database.
These paths are used to access data in the JSON structure.
"""

# Device Configuration
DEVICE_CONFIG = "config/device"
DEVICE_SETTINGS = "config/device/settings"
DEVICE_PROPERTIES = "config/device/properties"
DEVICE_INTERFACE = "config/device/interface"
DEVICE_MIPI = "config/device/interface/mipi"
DEVICE_GPIO = "config/device/interface/gpio"

# Band Management
BAND_CONFIG = "config/band"
BAND_SETTINGS = "config/band/settings"
BAND_PROPERTIES = "config/band/properties"
BAND_LTE = "config/band/lte"
BAND_5G = "config/band/5g"
BAND_NR = "config/band/nr"

# Board Configuration
BOARD_CONFIG = "config/board"
BOARD_SETTINGS = "config/board/settings"
BOARD_PROPERTIES = "config/board/properties"
BOARD_DEVICE_INFO = "config/board/device_info"
BOARD_INTERFACE = "config/board/interface"

# RCC Configuration
RCC_CONFIG = "config/rcc"
RCC_SETTINGS = "config/rcc/settings"
RCC_PROPERTIES = "config/rcc/properties"
RCC_SYNC = "config/rcc/sync"
RCC_BUILD = "config/rcc/build"


# Helper function to build paths
def build_path(*parts: str) -> str:
    """Build a path from parts using dot notation"""
    return ".".join(parts)
