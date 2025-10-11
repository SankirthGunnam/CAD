import dataclasses
from enum import Enum


@dataclasses.dataclass
class IOConnect:
    class IOConnectTable(Enum):
        SOURCE_DEVICE = "Source Device"
        SOURCE_SUB_BLOCK = "Source Sub Block"
        SOURCE_PIN = "Source Pin"
        DEST_DEVICE = "Dest Device"
        DEST_SUB_BLOCK = "Dest Sub Block"
        DEST_PIN = "Dest Pin"

        def __call__(self):
            return self.value


class DeviceSettings:

    class AllDevicesTable(Enum):
        DEVICE_ID = "ID"
        DEVICE_NAME = "Device Name"
        CONTROL_TYPE = "Control Type"
        MODULE = "Module"
        USID = "USID"
        MID_MSB = "MID (MSB)"
        MID_LSB = "MID (LSB)"
        PID = "PID"
        EXT_PID = "EXT PID"
        REV_ID = "REV ID"
        DCF_TYPE = "DCF Type"

        def __call__(self):
            return self.value

    class MipiDevicesTable(Enum):
        ID = "ID"
        DCF = "DCF"
        NAME = "Name"
        USID = "USID"
        MODULE = "Module"
        MIPI_TYPE = "MIPI Type"
        MIPI_CHANNEL = "MIPI Channel"
        DEFAULT_USID = "DEFAULT USID"
        USER_USID = "USER USID"
        PID = "PID"
        EXT_PID = "EXT PID"

        def __call__(self):
            return self.value

    class GpioDevicesTable(Enum):
        ID = "ID"
        DCF = "DCF"
        NAME = "Name"
        CTRL_TYPE = "Control Type"
        BOARD = "Board"

        def __call__(self):
            return self.value
