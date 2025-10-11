"""
Examples of using the JSON database with different data structures.
"""

from typing import Dict, List

from apps.RBM5.BCF.source.RDB.json_db import JSONDatabase
from apps.RBM5.BCF.source.RDB.paths import (

    DEVICE_SETTINGS,
    DEVICE_MIPI,
    DEVICE_GPIO,
    BAND_LTE,
    BAND_5G,
    BOARD_DEVICE_INFO,
    BOARD_INTERFACE,
    RCC_SYNC,
    RCC_BUILD,
)


def setup_device_settings(db: JSONDatabase) -> None:
    """Setup device settings table"""
    # Define columns for device settings table
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

    # Example device settings data
    device_data = [
        {
            "name": "Device1",
            "function_type": "LTE",
            "interface_type": "MIPI",
            "interface": {"mipi": {"channel": 1}, "gpio": {"pin": 2}},
            "config": {
                "usid": "12345",
                "product_id": "P001",
                "manufacturer_id": "M001",
            },
        }
    ]

    # Set the data
    db.set_table(DEVICE_SETTINGS, device_data)


def setup_band_config(db: JSONDatabase) -> None:
    """Setup band configuration"""
    # LTE band configuration
    lte_bands = [
        {"band": "B1", "power": 20, "status": "active"},
        {"band": "B2", "power": 25, "status": "active"},
        {"band": "B3", "power": 30, "status": "inactive"},
    ]
    db.set_table(BAND_LTE, lte_bands)

    # 5G band configuration
    nr_bands = [
        {"band": "N1", "power": 20, "status": "active"},
        {"band": "N2", "power": 25, "status": "active"},
        {"band": "N3", "power": 30, "status": "inactive"},
    ]
    db.set_table(BAND_5G, nr_bands)


def setup_board_config(db: JSONDatabase) -> None:
    """Setup board configuration"""
    # Device info
    device_info = {
        "model": "RBM-1000",
        "version": "1.0",
        "serial_number": "SN123456",
        "manufacturer": "Company XYZ",
    }
    db.set_value(BOARD_DEVICE_INFO, device_info)

    # Interface configuration
    interface_config = {
        "mipi": {"channels": 4, "speed": "1.5Gbps", "voltage": "1.8V"},
        "gpio": {"pins": 16, "voltage": "3.3V"},
    }
    db.set_value(BOARD_INTERFACE, interface_config)


def setup_rcc_config(db: JSONDatabase) -> None:
    """Setup RCC configuration"""
    # Sync configuration
    sync_config = {
        "mode": "auto",
        "interval": 60,
        "last_sync": "2024-01-01T12:00:00Z"}
    db.set_value(RCC_SYNC, sync_config)

    # Build configuration
    build_config = {
        "version": "1.0.0",
        "build_date": "2024-01-01",
        "target": "x86_64",
        "options": ["debug", "test"],
    }
    db.set_value(RCC_BUILD, build_config)


def main():
    """Main function to demonstrate usage"""
    # Create database instance
    db = JSONDatabase("device_config.json")
    db.connect()

    # Setup all configurations
    setup_device_settings(db)
    setup_band_config(db)
    setup_board_config(db)
    setup_rcc_config(db)

    # Example: Get device settings
    device_settings = db.get_table(DEVICE_SETTINGS)
    print("Device Settings:", device_settings)

    # Example: Update a specific value
    db.set_value(f"{DEVICE_SETTINGS}/0/interface/mipi/channel", 2)

    # Example: Get band configuration
    lte_bands = db.get_table(BAND_LTE)
    print("LTE Bands:", lte_bands)

    # Example: Get board info
    board_info = db.get_value(BOARD_DEVICE_INFO)
    print("Board Info:", board_info)

    # Disconnect from database
    db.disconnect()


if __name__ == "__main__":
    main()
