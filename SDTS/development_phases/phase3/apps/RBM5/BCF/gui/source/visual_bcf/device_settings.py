"""
Device Settings View for Visual BCF MVC Pattern

This module provides the DeviceSettingsView class with a simple vertical layout
containing two tables: All Devices and Selected Devices.
"""

import typing
from PySide6.QtWidgets import (
    QVBoxLayout,
    QTableView,
)
from apps.RBM5.BCF.config.constants.tabs import DeviceSettings

from apps.RBM5.BCF.gui.source.legacy_bcf.views.base_view import BaseView
if typing.TYPE_CHECKING:
    from apps.RBM5.BCF.source.models.visual_bcf.device_settings_model import (
        DeviceSettingsModel,
    )


class AllDevicesTable(QTableView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("AllDevicesTable")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setMinimumHeight(200)
        print(f"✓ All Devices table initialized with parent: {parent}")
        print(f"✓ All Devices table model before setting: {model}")
        print('model type', type(model), model)
        if model is not None:
            self.setModel(model)
            print(f"✓ All Devices table initialized with model: {model}")
        else:
            print("❌ All Devices table model is None - not setting model")

    def column_headers(self):
        return [
            DeviceSettings.AllDevicesTable.DEVICE_ID(),
            DeviceSettings.AllDevicesTable.DEVICE_NAME(),
            DeviceSettings.AllDevicesTable.CONTROL_TYPE(),
            DeviceSettings.AllDevicesTable.MODULE(),
        ]


class MipiDevicesTable(QTableView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("MipiDevicesTable")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setMinimumHeight(200)
        self.setModel(model)

    def column_headers(self):
        return [
            DeviceSettings.MipiDevicesTable.ID(),
            DeviceSettings.MipiDevicesTable.DCF(),
            DeviceSettings.MipiDevicesTable.NAME(),
            DeviceSettings.MipiDevicesTable.USID(),
            DeviceSettings.MipiDevicesTable.MODULE(),
        ]


class GpioDevicesTable(QTableView):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.setObjectName("GpioDevicesTable")
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setMinimumHeight(200)
        self.setModel(model)

    def column_headers(self):
        return [
            DeviceSettings.GpioDevicesTable.ID(),
            DeviceSettings.GpioDevicesTable.DCF(),
            DeviceSettings.GpioDevicesTable.NAME(),
            DeviceSettings.GpioDevicesTable.CTRL_TYPE(),
            DeviceSettings.GpioDevicesTable.BOARD(),
        ]


class View(BaseView):
    def __init__(self, controller, model: "DeviceSettingsModel"):
        super().__init__(controller, model)
        print(f"✓ Device Settings view initialized with controller: {controller}")
        print(f"✓ Device Settings view initialized with model: {model}")
        self.all_devices_table = AllDevicesTable(self, model.all_devices_model)
        print(f"✓ Device Settings view initialized with all_devices_table: {self.all_devices_table}")
        self.mipi_devices_table = MipiDevicesTable(self, model.mipi_devices_model)
        self.gpio_devices_table = GpioDevicesTable(self, model.gpio_devices_model)
        base_layout = QVBoxLayout(self)
        print(f"✓ Device Settings view initialized with all_devices_table: {self.all_devices_table}")
        print(f"✓ Device Settings view initialized with mipi_devices_table: {self.mipi_devices_table}")
        print(f"✓ Device Settings view initialized with gpio_devices_table: {self.gpio_devices_table}")
        base_layout.addWidget(self.all_devices_table)
        base_layout.addWidget(self.mipi_devices_table)
        base_layout.addWidget(self.gpio_devices_table)
        print(f"✓ Device Settings view initialized with base_layout: {base_layout}")
        self.setLayout(base_layout)
