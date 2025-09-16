# Use centralized path setup and absolute imports
import apps.RBM5.BCF  # This automatically sets up the path
from apps.RBM5.BCF.source.RDB.rdb_manager import RDBManager
import apps.RBM5.BCF.source.RDB.paths as paths
from apps.RBM5.BCF.source.models.abstract_model import AbstractModel
from apps.RBM5.BCF.source.models.visual_bcf.rdb_table_model import TableModel
from apps.RBM5.BCF.gui.source.visual_bcf.device_settings import DeviceSettings


class DeviceSettingsModel(AbstractModel):

    @property
    def device_selection(self):
        return self.rdb[paths.DEVICE_SELECTION]

    @property
    def static_mipi_channels(self):
        return self.rdb[paths.STATIC_MIPI_CHANNELS]

    @property
    def bcf_data(self):
        return self.rdb[paths.BCF_CONFIG]

    @property
    def bcf_db(self):
        return self.rdb[paths.BCF_DB(self.current_revision)]

    @property
    def dcf_for_bcf(self):
        return self.rdb[paths.BCF_DCF_FOR_BCF]

    @property
    def mipi_version(self):
        return self.rdb[paths.DYNAMIC_MIPI_VERSION]

    def __init__(self, controller, rdb: "RDBManager"):
        print(f"✓ Device Settings model initialized with controller: {controller}")
        super().__init__(controller=controller, rdb=rdb)
        print(f"✓ Device Settings model initialized with rdb: {rdb}")
        print(f"✓ bcf_db type: {type(self.bcf_db)}, value: {self.bcf_db}")
        self.all_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.DCF_DEVICES,
            columns=[
                DeviceSettings.AllDevicesTable.DEVICE_ID(),
                DeviceSettings.AllDevicesTable.DEVICE_NAME(),
                DeviceSettings.AllDevicesTable.CONTROL_TYPE(),
                DeviceSettings.AllDevicesTable.MODULE(),
            ],
        )
        print(f"✓ Device Settings model initialized with all_devices_model: {self.all_devices_model}")
        self.mipi_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.BCF_DEV_MIPI(self.current_revision),
            columns=[
                DeviceSettings.MipiDevicesTable.ID(),
                DeviceSettings.MipiDevicesTable.DCF(),
                DeviceSettings.MipiDevicesTable.NAME(),
                DeviceSettings.MipiDevicesTable.USID(),
                DeviceSettings.MipiDevicesTable.MODULE(),
                DeviceSettings.MipiDevicesTable.MIPI_TYPE(),
                DeviceSettings.MipiDevicesTable.MIPI_CHANNEL(),
                DeviceSettings.MipiDevicesTable.DEFAULT_USID(),
                DeviceSettings.MipiDevicesTable.USER_USID(),
                DeviceSettings.MipiDevicesTable.PID(),
                DeviceSettings.MipiDevicesTable.EXT_PID(),
            ],
        )
        print(f"✓ Device Settings model initialized with mipi_devices_model: {self.mipi_devices_model}")
        self.gpio_devices_model = TableModel(
            self.rdb,  # Pass the RDBManager, not the bcf_db dict
            paths.BCF_DEV_GPIO(self.current_revision),
            columns=[
                DeviceSettings.GpioDevicesTable.ID(),
                DeviceSettings.GpioDevicesTable.DCF(),
                DeviceSettings.GpioDevicesTable.NAME(),
                DeviceSettings.GpioDevicesTable.CTRL_TYPE(),
                DeviceSettings.GpioDevicesTable.BOARD(),
            ],
        )
        print(f"✓ Device Settings model initialized with gpio_devices_model: {self.gpio_devices_model}")
