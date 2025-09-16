"""
Database path constants for the JSON database.
These paths are used to access data in the JSON structure using Path objects.
"""

from typing import Union, List

class Path:
    """A pathlib.Path-like class for JSON database paths using slash notation."""

    def __init__(self, path: Union[str, "Path"] = ""):
        if isinstance(path, Path):
            self._path = path._path
        else:
            self._path = str(path).strip("/")

    def __truediv__(self, other: Union[str, "Path"]) -> "Path":
        """Implement the / operator for path concatenation."""
        if isinstance(other, Path):
            other_path = other._path
        else:
            other_path = str(other).strip("/")

        if not self._path:
            return Path(other_path)
        elif not other_path:
            return Path(self._path)
        else:
            return Path(f"{self._path}/{other_path}")

    def __str__(self) -> str:
        """Return the path as a string."""
        return self._path

    def __repr__(self) -> str:
        """Return the path representation."""
        return f"Path('{self._path}')"

    def __eq__(self, other) -> bool:
        """Check equality with another Path or string."""
        if isinstance(other, Path):
            return self._path == other._path
        return self._path == str(other)

    def __hash__(self) -> int:
        """Make Path hashable."""
        return hash(self._path)

    @property
    def parts(self) -> List[str]:
        """Return path parts as a list."""
        return self._path.split("/") if self._path else []

    @property
    def parent(self) -> "Path":
        """Return the parent path."""
        parts = self.parts
        if len(parts) <= 1:
            return Path()
        return Path("/".join(parts[:-1]))

    @property
    def name(self) -> str:
        """Return the final component of the path."""
        parts = self.parts
        return parts[-1] if parts else ""

    def joinpath(self, *others: Union[str, "Path"]) -> "Path":
        """Join multiple path components."""
        result = Path(self._path)
        for other in others:
            result = result / other
        return result


# Base configuration paths
CONFIG = Path("config")

# Device Configuration
DEVICE_CONFIG = CONFIG / "device"
DEVICE_SELECTION = DEVICE_CONFIG / "selection"
DEVICE_SETTINGS = DEVICE_CONFIG / "settings"
DEVICE_PROPERTIES = DEVICE_CONFIG / "properties"
DEVICE_INTERFACE = DEVICE_CONFIG / "interface"
DEVICE_MIPI = DEVICE_INTERFACE / "mipi"
DEVICE_GPIO = DEVICE_INTERFACE / "gpio"
STATIC_MIPI_CHANNELS = DEVICE_INTERFACE / "static_mipi_channels"

# Band Management
BAND_CONFIG = CONFIG / "band"
BAND_SETTINGS = BAND_CONFIG / "settings"
BAND_PROPERTIES = BAND_CONFIG / "properties"
BAND_LTE = BAND_CONFIG / "lte"
BAND_5G = BAND_CONFIG / "5g"
BAND_NR = BAND_CONFIG / "nr"

# Board Configuration
BOARD_CONFIG = CONFIG / "board"
BOARD_SETTINGS = BOARD_CONFIG / "settings"
BOARD_PROPERTIES = BOARD_CONFIG / "properties"
BOARD_DEVICE_INFO = BOARD_CONFIG / "device_info"
BOARD_INTERFACE = BOARD_CONFIG / "interface"

# RCC Configuration
RCC_CONFIG = CONFIG / "rcc"
RCC_SETTINGS = RCC_CONFIG / "settings"
RCC_PROPERTIES = RCC_CONFIG / "properties"
RCC_SYNC = RCC_CONFIG / "sync"
RCC_BUILD = RCC_CONFIG / "build"


# ============================================================================
# MODEL INFORMATION PATHS - Added as per NEW_CHANGES.md requirements
# ============================================================================

# Model Configurations
MODEL_INFO = Path("model")
MODEL = MODEL_INFO / "model"
MODEM = MODEL_INFO / "modem"
RFIC = MODEL_INFO / "rfic"
MFRVAR = MODEL_INFO / "mfrvar"
BOARD = MODEL_INFO / "board"
CARRIER = MODEL_INFO / "carrier"
MODEL_PATH = MODEL_INFO / "model_path"
PROJECT_CODE = MODEL_INFO / "project_code"
MODEL_BRANCH = MODEL_INFO / "branch"
SDTS_VERSION = "sdts/version"
RBM_VERSION = "rbm/version"
REVISIONS = MODEL_INFO / "revisions"
CURRENT_REVISION = MODEL_INFO / "current_revision"
REVISION_STRING = MODEL_INFO / "revision_string"
REVISION_HEX = MODEL_INFO / "revision_hex"
REVISION_INT = MODEL_INFO / "revision_int"
REVISION_BASE_FLAG = MODEL_INFO / "revision_base_flag"

# Board Configurations (Extended)
BOARD_CUSTOM_CODE = BOARD_CONFIG / "custom_code"
BOARD_CUSTOMDATA = BOARD_CONFIG / "customdata"
BOARD_RFIC_PORTMAP = BOARD_CONFIG / "rfic_portmap"
BOARD_RF_SUB_BOARD_REVISION = BOARD_CONFIG / "support_rf_sub_board_revision"
BOARD_POINTER_ASSIGNMENT = BOARD_CONFIG / "pointer_assignment"

# BCF Configurations
BCF_CONFIG = CONFIG / "bcf"
BCF_CONFIG_MAIN = BCF_CONFIG / "bcf_config"
BCF_MAIN = BCF_CONFIG / "bcf_main"
BCF_DEVICE_CONFIG = BCF_CONFIG / "bcf_device_config"
BCF_DB = lambda rev: BCF_CONFIG / rev / f"bcf_db" # type: ignore
BCF_DB_ANT = lambda rev: BCF_DB / rev / f"bcf_db_ant" # type: ignore
BCF_DB_CPL = lambda rev: BCF_DB / rev / f"bcf_db_cpl" # type: ignore
BCF_DB_FILTER = lambda rev: BCF_DB / rev / f"bcf_db_filter" # type: ignore
BCF_DB_EXT_IO = lambda rev: BCF_DB / rev / f"bcf_db_ext_io" # type: ignore
BCF_DEV_MIPI = lambda rev: BCF_CONFIG / rev / f"bcf_dev_mipi" # type: ignore
BCF_DEV_GPIO = lambda rev: BCF_CONFIG / rev / f"bcf_dev_gpio" # type: ignore
BCF_DCF_FOR_BCF = lambda rev: BCF_CONFIG / rev / f"dcf_for_bcf" # type: ignore


# DCF Configurations
DCF_CONFIG_ROOT = CONFIG / "dcf"
DCF_CONFIG_MAIN = DCF_CONFIG_ROOT / "dcf_config"
DCF_DEVICES = DCF_CONFIG_ROOT / "dcf_devices"

# Visual BCF Table Paths
VISUAL_BCF_CONFIG = CONFIG / "visual_bcf"
VISUAL_BCF_COMPONENTS = VISUAL_BCF_CONFIG / "components"
VISUAL_BCF_CONNECTIONS = VISUAL_BCF_CONFIG / "connections"

# Device Configuration Paths (Updated)
DEVICE_CONFIG = CONFIG / "device"
DEVICE_SETTINGS = DEVICE_CONFIG / "settings"
DEVICE_PROPERTIES = DEVICE_CONFIG / "properties"
DEVICE_INTERFACE = DEVICE_CONFIG / "interface"
DEVICE_MIPI = DEVICE_INTERFACE / "mipi"
DEVICE_GPIO = DEVICE_INTERFACE / "gpio"

# DCF Device Paths (New)
DCF_DEVICES_AVAILABLE = DCF_CONFIG_ROOT / "devices"
DCF_CONFIG = CONFIG / "dcf"


# IO Connect Table Paths (Enhanced)
BCF_DB_IO_CONNECT = "config/bcf/bcf_db_io_connect" # type: ignore

# Band Management (Enhanced from existing BAND_CONFIG)
BAND_FOR_RAT = BAND_CONFIG / "Band_for_rat"
BAND_EXCEPTIONAL_TABLE = BAND_CONFIG / "exceptional_table"
BAND_LIST_TABLE = BAND_CONFIG / "band_list_table"
BAND_SUPER_BAND_TABLE = BAND_CONFIG / "super_band_table"
BAND_NR_SUPER_BAND_TABLE = BAND_CONFIG / "nr_super_band_table"
BAND_REFARMING_BAND_TABLE = BAND_CONFIG / "refarming_band_table"
BAND_INTRABAND_SUPPORT = BAND_CONFIG / "intraband_support"
BAND_INTRABAND_EXCEPTION = BAND_CONFIG / "intraband_exception"

# Port Vs Band Configurations
PORT_BAND_CONFIG = CONFIG / "port_band"
PORT_BAND_RFIC_PORTS = PORT_BAND_CONFIG / "rfic_ports_mapping"
PORT_BAND_CONFIGURATION = PORT_BAND_CONFIG / "bands_configuration"
PORT_BAND_RELATIONSHIP = PORT_BAND_CONFIG / "port_band_relationship"

# Additional Configurations
LAN_CONFIG = CONFIG / "lan_configurations"
COUPLER_CONFIG = CONFIG / "coupler_configurations"
GSM_CONFIG = CONFIG / "gsm"
PAM_CONFIG = CONFIG / "pam"
ET_DPD_CONFIG = CONFIG / "et_dpd"


# Helper function to build paths (kept for backward compatibility)
DYNAMIC_MIPI_VERSION = CONFIG / "dynamic_mipi_version"
DYNAMIC_ANT_TYPES = CONFIG / "device_ant_types"

def build_path(*parts: str) -> str:
    """Build a path from parts using slash notation"""
    return "/".join(parts)
