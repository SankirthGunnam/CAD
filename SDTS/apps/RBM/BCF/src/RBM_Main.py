import sys
import threading
from queue import Queue, PriorityQueue
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStackedWidget,
    QTableView,
)
from PySide6.QtCore import QObject, Signal, Slot, QThread

from .RDB.rdb_manager import RDBManager
from .RDB.paths import DEVICE_SETTINGS, BAND_CONFIG, BOARD_CONFIG, RCC_CONFIG


class RBMMain(QWidget):
    """Main controller that coordinates all application entities"""

    # Signals for communication between controllers
    data_changed = Signal(str)  # Signal when data changes (path)
    error_occurred = Signal(str)  # Signal when error occurs (error_message)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize RDB Manager
        self.rdb_manager = RDBManager()
        self.rdb_manager.data_changed.connect(self._on_data_changed)
        self.rdb_manager.error_occurred.connect(self._on_error)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Setup tabs
        self.setup_device_tab()
        self.setup_band_tab()
        self.setup_board_tab()
        self.setup_rcc_tab()

    def setup_device_tab(self):
        """Setup the device configuration tab"""
        device_widget = QWidget()
        device_layout = QVBoxLayout(device_widget)

        # Create device settings table
        device_columns = [
            {"name": "Device Name", "key": "name"},
            {"name": "Function Type", "key": "function_type"},
            {"name": "Interface Type", "key": "interface_type"},
            {"name": "MIPI Channel", "key": "interface.mipi.channel"},
            {"name": "GPIO Pin", "key": "interface.gpio.pin"},
            {"name": "USID", "key": "config.usid"},
            {"name": "Product ID", "key": "config.product_id"},
            {"name": "Manufacturer ID", "key": "config.manufacturer_id"},
        ]

        device_model = self.rdb_manager.get_model(DEVICE_SETTINGS, device_columns)
        device_table = QTableView()
        device_table.setModel(device_model)
        device_layout.addWidget(device_table)

        self.tab_widget.addTab(device_widget, "Device Settings")

    def setup_band_tab(self):
        """Setup the band configuration tab"""
        band_widget = QWidget()
        band_layout = QVBoxLayout(band_widget)

        # Create band settings table
        band_columns = [
            {"name": "Band", "key": "band"},
            {"name": "Power", "key": "power"},
            {"name": "Status", "key": "status"},
        ]

        band_model = self.rdb_manager.get_model(BAND_CONFIG, band_columns)
        band_table = QTableView()
        band_table.setModel(band_model)
        band_layout.addWidget(band_table)

        self.tab_widget.addTab(band_widget, "Band Settings")

    def setup_board_tab(self):
        """Setup the board configuration tab"""
        board_widget = QWidget()
        board_layout = QVBoxLayout(board_widget)

        # Create board settings table
        board_columns = [
            {"name": "Setting", "key": "name"},
            {"name": "Value", "key": "value"},
        ]

        board_model = self.rdb_manager.get_model(BOARD_CONFIG, board_columns)
        board_table = QTableView()
        board_table.setModel(board_model)
        board_layout.addWidget(board_table)

        self.tab_widget.addTab(board_widget, "Board Settings")

    def setup_rcc_tab(self):
        """Setup the RCC configuration tab"""
        rcc_widget = QWidget()
        rcc_layout = QVBoxLayout(rcc_widget)

        # Create RCC settings table
        rcc_columns = [
            {"name": "Setting", "key": "name"},
            {"name": "Value", "key": "value"},
        ]

        rcc_model = self.rdb_manager.get_model(RCC_CONFIG, rcc_columns)
        rcc_table = QTableView()
        rcc_table.setModel(rcc_model)
        rcc_layout.addWidget(rcc_table)

        self.tab_widget.addTab(rcc_widget, "RCC Settings")

    def _on_data_changed(self, path: str):
        """Handle data changes"""
        self.data_changed.emit(path)

    def _on_error(self, error_message: str):
        """Handle errors"""
        self.error_occurred.emit(error_message)

    def showEvent(self, event):
        """Connect to database when window is shown"""
        super().showEvent(event)
        self.rdb_manager.connect()

    def closeEvent(self, event):
        """Disconnect from database when window is closed"""
        self.rdb_manager.disconnect()
        super().closeEvent(event)


if __name__ == "__main__":
    main = RBMMain()
    sys.exit(main.exec())
