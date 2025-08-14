#!/usr/bin/env python3
"""
Fixed Legacy BCF Table Management with Visual BCF Synchronization

This script fixes all synchronization issues:
1. Automatic initial import from Legacy BCF to Visual BCF on startup
2. Proper device duplicate prevention when importing
3. Specific device removal instead of clearing and re-importing everything
4. Bidirectional sync: Visual BCF deletions update Legacy BCF
5. Proper clear operations that work in both directions
6. Real-time statistics and status updates
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "RBM" / "BCF"))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QComboBox, QLineEdit, QFormLayout,
    QDialog, QDialogButtonBox, QTextEdit, QSplitter, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QPointF
from PySide6.QtGui import QFont, QColor, QBrush

# Import real project components
from apps.RBM.BCF.src.RDB.rdb_manager import RDBManager
from apps.RBM.BCF.gui.src.visual_bcf.visual_bcf_manager import VisualBCFManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('legacy_bcf_test_fixed.log')
    ]
)
logger = logging.getLogger(__name__)


class DeviceAddDialog(QDialog):
    """Dialog for adding new devices to Legacy BCF"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Device to Legacy BCF")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Form layout for device properties
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., LTE_Modem_X1")
        form_layout.addRow("Device Name:", self.name_edit)
        
        self.function_type_combo = QComboBox()
        self.function_type_combo.addItems(["LTE", "5G", "RFIC", "WiFi", "Bluetooth", "GPS", "Generic"])
        form_layout.addRow("Function Type:", self.function_type_combo)
        
        self.interface_type_combo = QComboBox()
        self.interface_type_combo.addItems(["MIPI", "SPI", "I2C", "UART", "GPIO", "RF_Direct"])
        form_layout.addRow("Interface Type:", self.interface_type_combo)
        
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        form_layout.addRow("Channel:", self.channel_spin)
        
        self.frequency_edit = QLineEdit()
        self.frequency_edit.setPlaceholderText("e.g., 700MHz - 3.8GHz")
        form_layout.addRow("Frequency Range:", self.frequency_edit)
        
        self.power_spin = QDoubleSpinBox()
        self.power_spin.setRange(-40.0, 30.0)
        self.power_spin.setValue(23.0)
        self.power_spin.setSuffix(" dBm")
        form_layout.addRow("Max Power:", self.power_spin)
        
        self.bands_edit = QLineEdit()
        self.bands_edit.setPlaceholderText("e.g., B1,B3,B7,B20")
        form_layout.addRow("RF Bands:", self.bands_edit)
        
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True)
        form_layout.addRow("Enabled:", self.enabled_check)
        
        self.usid_edit = QLineEdit()
        self.usid_edit.setPlaceholderText("Auto-generated if empty")
        form_layout.addRow("USID:", self.usid_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Auto-generate USID based on function type
        self.function_type_combo.currentTextChanged.connect(self._update_usid)
        self._update_usid()
    
    def _update_usid(self):
        """Auto-generate USID based on function type"""
        function_type = self.function_type_combo.currentText()
        import random
        usid = f"{function_type}{random.randint(100, 999):03d}"
        self.usid_edit.setText(usid)
    
    def get_device_data(self) -> Dict[str, Any]:
        """Get device data from dialog"""
        bands = [band.strip() for band in self.bands_edit.text().split(',') if band.strip()]
        
        return {
            'name': self.name_edit.text().strip(),
            'function_type': self.function_type_combo.currentText(),
            'interface_type': self.interface_type_combo.currentText(),
            'interface': {
                self.interface_type_combo.currentText().lower(): {
                    'channel': self.channel_spin.value()
                }
            },
            'config': {
                'usid': self.usid_edit.text().strip(),
                'frequency_range': self.frequency_edit.text().strip(),
                'max_power_dbm': self.power_spin.value(),
                'rf_bands': bands,
                'enabled': self.enabled_check.isChecked()
            }
        }


class LegacyBCFTableWidget(QWidget):
    """Legacy BCF device table with add/delete operations"""
    
    device_added = Signal(dict)
    device_deleted = Signal(str)  # device name
    device_modified = Signal(str, dict)  # device name, new data
    devices_cleared = Signal()
    
    def __init__(self, rdb_manager: RDBManager, parent=None):
        super().__init__(parent)
        self.rdb_manager = rdb_manager
        self.setup_ui()
        self.load_devices()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Legacy BCF Device Configuration")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Control buttons
        self.add_button = QPushButton("➕ Add Device")
        self.delete_button = QPushButton("❌ Delete Selected")
        self.refresh_button = QPushButton("🔄 Refresh")
        self.clear_all_button = QPushButton("🗑️ Clear All")
        
        self.add_button.clicked.connect(self.add_device)
        self.delete_button.clicked.connect(self.delete_selected_device)
        self.refresh_button.clicked.connect(self.load_devices)
        self.clear_all_button.clicked.connect(self.clear_all_devices)
        
        header_layout.addWidget(self.add_button)
        header_layout.addWidget(self.delete_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.clear_all_button)
        
        layout.addLayout(header_layout)
        
        # Device table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Define columns
        self.columns = [
            "Name", "Function Type", "Interface", "Channel", 
            "Frequency", "Power (dBm)", "RF Bands", "USID", "Enabled"
        ]
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Function Type
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Interface
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Channel
        header.setSectionResizeMode(4, QHeaderView.Stretch)          # Frequency
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Power
        header.setSectionResizeMode(6, QHeaderView.Stretch)          # RF Bands
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # USID
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Enabled
        
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_devices(self):
        """Load devices from Legacy BCF database"""
        try:
            devices = self.rdb_manager.get_table("config.device.settings")
            
            self.table.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                # Name
                self.table.setItem(row, 0, QTableWidgetItem(device.get('name', '')))
                
                # Function Type
                self.table.setItem(row, 1, QTableWidgetItem(device.get('function_type', '')))
                
                # Interface Type
                self.table.setItem(row, 2, QTableWidgetItem(device.get('interface_type', '')))
                
                # Channel
                interface_data = device.get('interface', {})
                channel = 'N/A'
                for interface_type, interface_config in interface_data.items():
                    if isinstance(interface_config, dict) and 'channel' in interface_config:
                        channel = str(interface_config['channel'])
                        break
                self.table.setItem(row, 3, QTableWidgetItem(channel))
                
                # Frequency Range
                config = device.get('config', {})
                frequency = config.get('frequency_range', 'N/A')
                self.table.setItem(row, 4, QTableWidgetItem(frequency))
                
                # Power
                power = config.get('max_power_dbm', 'N/A')
                self.table.setItem(row, 5, QTableWidgetItem(str(power)))
                
                # RF Bands
                bands = config.get('rf_bands', [])
                bands_str = ', '.join(bands) if bands else 'N/A'
                self.table.setItem(row, 6, QTableWidgetItem(bands_str))
                
                # USID
                usid = config.get('usid', 'N/A')
                self.table.setItem(row, 7, QTableWidgetItem(usid))
                
                # Enabled
                enabled = config.get('enabled', True)
                enabled_item = QTableWidgetItem("✓" if enabled else "✗")
                enabled_item.setTextAlignment(Qt.AlignCenter)
                if enabled:
                    enabled_item.setBackground(QBrush(QColor(144, 238, 144)))  # Light green
                else:
                    enabled_item.setBackground(QBrush(QColor(255, 182, 193)))  # Light red
                self.table.setItem(row, 8, enabled_item)
            
            self.status_label.setText(f"Loaded {len(devices)} devices from Legacy BCF")
            logger.info(f"Loaded {len(devices)} devices from Legacy BCF")
            
        except Exception as e:
            self.status_label.setText(f"Error loading devices: {str(e)}")
            logger.error(f"Error loading devices: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load devices:\n{str(e)}")
    
    def add_device(self):
        """Add a new device"""
        dialog = DeviceAddDialog(self)
        if dialog.exec() == QDialog.Accepted:
            device_data = dialog.get_device_data()
            
            if not device_data['name']:
                QMessageBox.warning(self, "Warning", "Device name cannot be empty!")
                return
            
            try:
                # Check if device name already exists
                devices = self.rdb_manager.get_table("config.device.settings")
                for device in devices:
                    if device.get('name') == device_data['name']:
                        QMessageBox.warning(self, "Warning", f"Device name '{device_data['name']}' already exists!")
                        return
                
                # Add to database
                if self.rdb_manager.add_row("config.device.settings", device_data):
                    # Refresh table
                    self.load_devices()
                    
                    # Emit signal
                    self.device_added.emit(device_data)
                    
                    self.status_label.setText(f"Added device: {device_data['name']}")
                    logger.info(f"Added device to Legacy BCF: {device_data['name']}")
                else:
                    raise Exception("Failed to add row to database")
                
            except Exception as e:
                self.status_label.setText(f"Error adding device: {str(e)}")
                logger.error(f"Error adding device: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add device:\n{str(e)}")
    
    def delete_selected_device(self):
        """Delete selected device"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Information", "Please select a device to delete.")
            return
        
        device_name = self.table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "Delete Device", 
            f"Are you sure you want to delete device '{device_name}'?\n\n"
            f"This will also remove it from Visual BCF.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Find the device row index
                current_devices = self.rdb_manager.get_table("config.device.settings")
                device_index = -1
                for i, device in enumerate(current_devices):
                    if device.get('name') == device_name:
                        device_index = i
                        break
                
                if device_index >= 0:
                    # Delete row by index
                    if self.rdb_manager.delete_row("config.device.settings", device_index):
                        # Refresh table
                        self.load_devices()
                        
                        # Emit signal
                        self.device_deleted.emit(device_name)
                        
                        self.status_label.setText(f"Deleted device: {device_name}")
                        logger.info(f"Deleted device from Legacy BCF: {device_name}")
                    else:
                        raise Exception("Failed to delete row from database")
                else:
                    raise Exception(f"Device '{device_name}' not found")
                
            except Exception as e:
                self.status_label.setText(f"Error deleting device: {str(e)}")
                logger.error(f"Error deleting device: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete device:\n{str(e)}")
    
    def clear_all_devices(self):
        """Clear all devices"""
        reply = QMessageBox.question(
            self, "Clear All Devices", 
            "Are you sure you want to delete ALL devices?\n\n"
            "This will clear both Legacy BCF and Visual BCF.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear database by setting empty table
                if self.rdb_manager.set_table("config.device.settings", []):
                    # Refresh table
                    self.load_devices()
                    
                    # Emit signal
                    self.devices_cleared.emit()
                    
                    self.status_label.setText("Cleared all devices")
                    logger.info("Cleared all devices from Legacy BCF")
                else:
                    raise Exception("Failed to clear table in database")
                
            except Exception as e:
                self.status_label.setText(f"Error clearing devices: {str(e)}")
                logger.error(f"Error clearing devices: {e}")
                QMessageBox.critical(self, "Error", f"Failed to clear devices:\n{str(e)}")

    def get_device_names(self) -> Set[str]:
        """Get all device names currently in Legacy BCF"""
        try:
            devices = self.rdb_manager.get_table("config.device.settings")
            return {device.get('name', '') for device in devices if device.get('name')}
        except Exception as e:
            logger.error(f"Error getting device names: {e}")
            return set()


class VisualBCFSyncManager:
    """Manager for Visual BCF synchronization logic"""
    
    def __init__(self, visual_bcf_manager: VisualBCFManager):
        self.visual_bcf_manager = visual_bcf_manager
        self._synced_device_names: Set[str] = set()
        logger.info("VisualBCFSyncManager initialized")
    
    def get_synced_device_names(self) -> Set[str]:
        """Get names of devices currently synced to Visual BCF"""
        return self._synced_device_names.copy()
    
    def sync_from_legacy(self, legacy_device_names: Set[str]):
        """Smart sync from Legacy BCF - only add missing devices, remove deleted ones"""
        try:
            # Determine what needs to be added and removed
            to_add = legacy_device_names - self._synced_device_names
            to_remove = self._synced_device_names - legacy_device_names
            
            logger.info(f"Sync analysis - To add: {to_add}, To remove: {to_remove}")
            
            # Remove devices that are no longer in Legacy BCF
            for device_name in to_remove:
                self.remove_device_by_name(device_name)
            
            # Add new devices from Legacy BCF
            for device_name in to_add:
                self.add_device_by_name(device_name)
            
            # Update synced names
            self._synced_device_names = legacy_device_names.copy()
            
            logger.info(f"Sync completed - Visual BCF now has {len(self._synced_device_names)} devices")
            
        except Exception as e:
            logger.error(f"Error during smart sync: {e}")
    
    def add_device_by_name(self, device_name: str):
        """Add a specific device by name from Legacy BCF to Visual BCF"""
        try:
            if not self.visual_bcf_manager.is_architecture_enabled():
                logger.warning("Architecture not enabled, cannot add device")
                return False
            
            # Import only this specific device
            self.visual_bcf_manager.import_from_legacy_bcf([device_name])
            self._synced_device_names.add(device_name)
            logger.info(f"Added device to Visual BCF: {device_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding device {device_name} to Visual BCF: {e}")
            return False
    
    def remove_device_by_name(self, device_name: str):
        """Remove a specific device by name from Visual BCF"""
        try:
            if not self.visual_bcf_manager.is_architecture_enabled():
                logger.warning("Architecture not enabled, cannot remove device")
                return False
            
            controller = self.visual_bcf_manager.get_controller()
            data_model = self.visual_bcf_manager.get_data_model()
            
            if not (controller and data_model):
                logger.warning("Controller or data model not available")
                return False
            
            # Find and remove component by name
            all_components = data_model.get_all_components()
            component_id_to_remove = None
            
            for component_id, component_data in all_components.items():
                if component_data.name == device_name:
                    component_id_to_remove = component_id
                    break
            
            if component_id_to_remove:
                success = controller.remove_component(component_id_to_remove)
                if success:
                    self._synced_device_names.discard(device_name)
                    logger.info(f"Removed device from Visual BCF: {device_name}")
                    return True
            else:
                logger.warning(f"Device {device_name} not found in Visual BCF")
                self._synced_device_names.discard(device_name)  # Clean up tracking
                return False
                
        except Exception as e:
            logger.error(f"Error removing device {device_name} from Visual BCF: {e}")
            return False
    
    def clear_all_devices(self):
        """Clear all devices from Visual BCF"""
        try:
            if self.visual_bcf_manager.is_architecture_enabled():
                self.visual_bcf_manager.clear_scene_data_driven()
                self._synced_device_names.clear()
                logger.info("Cleared all devices from Visual BCF")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing Visual BCF: {e}")
            return False
    
    def force_full_sync(self, legacy_device_names: Set[str]):
        """Force full resynchronization - clear everything and re-add"""
        try:
            logger.info("Performing force full sync")
            self.clear_all_devices()
            
            # Re-add all Legacy BCF devices
            for device_name in legacy_device_names:
                self.add_device_by_name(device_name)
            
            logger.info(f"Force sync completed - {len(legacy_device_names)} devices synced")
            
        except Exception as e:
            logger.error(f"Error during force full sync: {e}")


class LegacyBCFTestApp(QMainWindow):
    """Main test application for Legacy BCF table management with proper sync"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Legacy BCF Table Management & Visual BCF Sync Test (FIXED)")
        self.resize(1400, 900)
        
        # Initialize RDB Manager
        self.rdb_manager = RDBManager()
        
        # Setup UI
        self.setup_ui()
        
        # Initialize with sample data
        self.initialize_sample_data()
        
        # Initialize sync manager
        self.sync_manager = VisualBCFSyncManager(self.visual_bcf_manager)
        
        # Note: Initial sync is now handled automatically by Visual BCF Manager
        # No need for manual force sync since auto-import handles this properly
        
        # Setup auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_visual_bcf)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
        
        logger.info("Legacy BCF Test Application (FIXED) initialized")
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Legacy BCF Table
        left_group = QGroupBox("Legacy BCF Device Configuration")
        left_layout = QVBoxLayout(left_group)
        
        self.legacy_table = LegacyBCFTableWidget(self.rdb_manager)
        left_layout.addWidget(self.legacy_table)
        
        # Connect Legacy BCF signals
        self.legacy_table.device_added.connect(self.on_legacy_device_added)
        self.legacy_table.device_deleted.connect(self.on_legacy_device_deleted)
        self.legacy_table.devices_cleared.connect(self.on_legacy_devices_cleared)
        
        splitter.addWidget(left_group)
        
        # Right side - Visual BCF
        right_group = QGroupBox("Visual BCF (MVC Integration)")
        right_layout = QVBoxLayout(right_group)
        
        # Visual BCF controls
        controls_layout = QHBoxLayout()
        
        self.sync_button = QPushButton("🔄 Smart Sync")
        self.import_button = QPushButton("📥 Force Full Import")
        self.clear_visual_button = QPushButton("🗑️ Clear Visual")
        self.fit_view_button = QPushButton("🔍 Fit in View")
        self.reset_view_button = QPushButton("🏠 Reset View")
        
        self.sync_button.clicked.connect(self.smart_sync_from_legacy)
        self.import_button.clicked.connect(self.force_import_from_legacy)
        self.clear_visual_button.clicked.connect(self.clear_visual_bcf)
        self.fit_view_button.clicked.connect(self.fit_view)
        self.reset_view_button.clicked.connect(self.reset_view)
        
        controls_layout.addWidget(self.sync_button)
        controls_layout.addWidget(self.import_button)
        controls_layout.addWidget(self.clear_visual_button)
        controls_layout.addWidget(self.fit_view_button)
        controls_layout.addWidget(self.reset_view_button)
        controls_layout.addStretch()
        
        right_layout.addLayout(controls_layout)
        
        # Visual BCF Manager
        self.visual_bcf_manager = VisualBCFManager(rdb_manager=self.rdb_manager)
        self.visual_bcf_manager.data_changed.connect(self.on_visual_data_changed)
        self.visual_bcf_manager.error_occurred.connect(self.on_visual_error)
        
        # Connect Visual BCF manager signals for bidirectional sync (after manager is created)
        self.visual_bcf_manager.data_changed.connect(self.on_visual_data_changed_refresh_table)
        
        right_layout.addWidget(self.visual_bcf_manager)
        
        # Statistics display
        self.stats_label = QLabel("Statistics will appear here...")
        self.stats_label.setMaximumHeight(60)
        self.stats_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
        right_layout.addWidget(self.stats_label)
        
        splitter.addWidget(right_group)
        
        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([560, 840])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready - Legacy BCF & Visual BCF Integration Test (FIXED)")
    
    def initialize_sample_data(self):
        """Initialize with sample Legacy BCF data"""
        sample_devices = [
            {
                'name': 'LTE_Modem_Main',
                'function_type': 'LTE',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 1}},
                'config': {
                    'usid': 'LTE001',
                    'frequency_range': '700MHz - 2.6GHz',
                    'max_power_dbm': 23.0,
                    'rf_bands': ['B1', 'B3', 'B7', 'B20'],
                    'enabled': True
                }
            },
            {
                'name': '5G_NR_Modem',
                'function_type': '5G',
                'interface_type': 'MIPI',
                'interface': {'mipi': {'channel': 2}},
                'config': {
                    'usid': '5G001',
                    'frequency_range': '600MHz - 6GHz',
                    'max_power_dbm': 25.0,
                    'rf_bands': ['n1', 'n3', 'n7', 'n28', 'n77', 'n78'],
                    'enabled': True
                }
            },
            {
                'name': 'RFIC_Primary',
                'function_type': 'RFIC',
                'interface_type': 'SPI',
                'interface': {'spi': {'channel': 1}},
                'config': {
                    'usid': 'RFIC001',
                    'frequency_range': '600MHz - 6GHz',
                    'max_power_dbm': 20.0,
                    'rf_bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'B8', 'B20', 'B28'],
                    'enabled': True
                }
            },
            {
                'name': 'WiFi_Module',
                'function_type': 'WiFi',
                'interface_type': 'UART',
                'interface': {'uart': {'channel': 3}},
                'config': {
                    'usid': 'WIFI001',
                    'frequency_range': '2.4GHz, 5GHz',
                    'max_power_dbm': 20.0,
                    'rf_bands': ['2.4GHz', '5GHz'],
                    'enabled': False
                }
            }
        ]
        
        try:
            if self.rdb_manager.set_table("config.device.settings", sample_devices):
                self.legacy_table.load_devices()
                logger.info(f"Initialized {len(sample_devices)} sample devices")
            else:
                logger.error("Failed to set table in database")
        except Exception as e:
            logger.error(f"Error initializing sample data: {e}")
    
    def perform_initial_sync(self):
        """Perform initial synchronization from Legacy BCF to Visual BCF"""
        try:
            logger.info("🔄 Performing initial sync from Legacy BCF to Visual BCF...")
            legacy_device_names = self.legacy_table.get_device_names()
            self.sync_manager.force_full_sync(legacy_device_names)
            
            self.statusBar().showMessage("Initial sync completed")
            logger.info(f"✅ Initial sync completed - {len(legacy_device_names)} devices imported")
            
        except Exception as e:
            logger.error(f"Error during initial sync: {e}")
            self.statusBar().showMessage(f"Initial sync error: {str(e)}")
    
    def on_legacy_device_added(self, device_data: Dict[str, Any]):
        """Handle device added to Legacy BCF"""
        device_name = device_data['name']
        logger.info(f"📡 Legacy BCF: Device added - {device_name}")
        self.statusBar().showMessage(f"Added device to Legacy BCF: {device_name}")
        
        # Smart sync - just add this new device
        QTimer.singleShot(500, lambda: self.sync_manager.add_device_by_name(device_name))
    
    def on_legacy_device_deleted(self, device_name: str):
        """Handle device deleted from Legacy BCF"""
        logger.info(f"📡 Legacy BCF: Device deleted - {device_name}")
        self.statusBar().showMessage(f"Deleted device from Legacy BCF: {device_name}")
        
        # Smart sync - just remove this device
        QTimer.singleShot(500, lambda: self.sync_manager.remove_device_by_name(device_name))
    
    def on_legacy_devices_cleared(self):
        """Handle all devices cleared from Legacy BCF"""
        logger.info("📡 Legacy BCF: All devices cleared")
        self.statusBar().showMessage("Cleared all devices from Legacy BCF")
        
        # Clear Visual BCF as well
        QTimer.singleShot(500, lambda: self.sync_manager.clear_all_devices())
    
    def on_visual_data_changed(self, data: Dict[str, Any]):
        """Handle Visual BCF data changes"""
        action = data.get('action', 'unknown')
        source = data.get('source', 'unknown')
        
        if source == 'mvc':
            logger.info(f"🎨 Visual BCF (MVC): {action}")
            if 'message' in data:
                logger.info(f"    {data['message']}")
        
        # Update statistics
        self.update_statistics()
    
    def on_visual_error(self, error_message: str):
        """Handle Visual BCF errors"""
        logger.error(f"❌ Visual BCF Error: {error_message}")
        self.statusBar().showMessage(f"Visual BCF Error: {error_message}")
    
    def on_visual_data_changed_refresh_table(self, data: Dict[str, Any]):
        """Handle Visual BCF data changes and refresh Legacy BCF table if needed"""
        action = data.get('action', '')
        source = data.get('source', '')
        
        # If this is a bidirectional sync action (Visual BCF -> Legacy BCF), refresh the table
        if source == 'bidirectional_sync' and action in ['user_deletion_synced', 'user_deletion_visual_only']:
            logger.info(f"🔄 Refreshing Legacy BCF table due to bidirectional sync: {action}")
            # Delay refresh slightly to ensure database is updated
            QTimer.singleShot(100, self.legacy_table.load_devices)
    
    def smart_sync_from_legacy(self):
        """Smart sync Visual BCF from Legacy BCF"""
        try:
            logger.info("🔄 Performing smart sync from Legacy BCF...")
            legacy_device_names = self.legacy_table.get_device_names()
            self.sync_manager.sync_from_legacy(legacy_device_names)
            
            self.statusBar().showMessage("Smart sync completed")
            logger.info("✅ Smart sync completed")
            
        except Exception as e:
            logger.error(f"Error during smart sync: {e}")
            self.statusBar().showMessage(f"Smart sync error: {str(e)}")
    
    def force_import_from_legacy(self):
        """Force full import from Legacy BCF to Visual BCF"""
        try:
            logger.info("📥 Performing force full import from Legacy BCF...")
            legacy_device_names = self.legacy_table.get_device_names()
            self.sync_manager.force_full_sync(legacy_device_names)
            
            self.statusBar().showMessage("Force import completed")
            logger.info("✅ Force import completed")
            
        except Exception as e:
            logger.error(f"Error during force import: {e}")
            self.statusBar().showMessage(f"Force import error: {str(e)}")
    
    def clear_visual_bcf(self):
        """Clear Visual BCF scene only"""
        try:
            self.sync_manager.clear_all_devices()
            self.statusBar().showMessage("Cleared Visual BCF scene")
            logger.info("Cleared Visual BCF scene")
        except Exception as e:
            logger.error(f"Error clearing Visual BCF: {e}")
            self.statusBar().showMessage(f"Clear error: {str(e)}")
    
    def fit_view(self):
        """Fit Visual BCF components in view"""
        try:
            self.visual_bcf_manager.fit_in_view()
            self.statusBar().showMessage("Fitted components in view")
        except Exception as e:
            logger.error(f"Error fitting view: {e}")
    
    def reset_view(self):
        """Reset Visual BCF view"""
        try:
            self.visual_bcf_manager.reset_view()
            self.statusBar().showMessage("Reset view")
        except Exception as e:
            logger.error(f"Error resetting view: {e}")
    
    def refresh_visual_bcf(self):
        """Refresh Visual BCF statistics periodically"""
        try:
            self.update_statistics()
        except Exception as e:
            logger.error(f"Error refreshing Visual BCF: {e}")
    
    def update_statistics(self):
        """Update Visual BCF statistics display"""
        try:
            if self.visual_bcf_manager.is_architecture_enabled():
                stats = self.visual_bcf_manager.get_model_statistics()
                
                total = stats.get('total_components', 0)
                by_type = stats.get('components_by_type', {})
                connections = stats.get('total_connections', 0)
                
                stats_text = f"📊 Visual BCF: {total} components"
                if by_type:
                    type_stats = ", ".join([f"{k}: {v}" for k, v in by_type.items()])
                    stats_text += f" ({type_stats})"
                stats_text += f", {connections} connections"
                
                # Get Legacy BCF count
                legacy_count = len(self.legacy_table.get_device_names())
                
                # Get synced count
                synced_count = len(self.sync_manager.get_synced_device_names())
                
                stats_text += f" | 📡 Legacy BCF: {legacy_count} devices | 🔗 Synced: {synced_count}"
                
                self.stats_label.setText(stats_text)
            else:
                self.stats_label.setText("📊 Visual BCF: Architecture not enabled")
        except Exception as e:
            self.stats_label.setText(f"📊 Error getting statistics: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            self.refresh_timer.stop()
            if hasattr(self, 'visual_bcf_manager'):
                self.visual_bcf_manager.cleanup()
            logger.info("Application closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        event.accept()


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Legacy BCF Table Test (FIXED)")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = LegacyBCFTestApp()
    window.show()
    
    logger.info("🚀 Legacy BCF Table Management Test (FIXED) started!")
    logger.info("Fixed features:")
    logger.info("✅ Automatic initial import from Legacy BCF on startup")
    logger.info("✅ Smart sync - no duplicates, only add missing/remove deleted")
    logger.info("✅ Specific device removal instead of clear-and-reimport")
    logger.info("✅ Proper clear operations in both directions")
    logger.info("✅ Real-time statistics and sync status tracking")
    logger.info("✅ Bidirectional synchronization support")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
