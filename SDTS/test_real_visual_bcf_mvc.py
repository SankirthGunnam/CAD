#!/usr/bin/env python3
"""
Real Visual BCF MVC Integration Test

This script tests the fully integrated MVC architecture with the real Visual BCF Manager,
using actual RDB manager and all real components.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import PySide6
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QSplitter, QGroupBox, QListWidget,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

try:
    # Import real components
    from apps.RBM.BCF.source.RDB.rdb_manager import RDBManager
    from apps.RBM.BCF.gui.source.visual_bcf.visual_bcf_manager import VisualBCFManager
    real_components_available = True
    logger.info("Real components imported successfully")
except ImportError as e:
    real_components_available = False
    logger.error(f"Failed to import real components: {e}")


class RealVisualBCFMVCTestApp(QMainWindow):
    """Test application for Real Visual BCF MVC Architecture"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real Visual BCF MVC Integration Test")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize components
        self.rdb_manager = None
        self.visual_bcf_manager = None

        # Setup UI
        self.setup_ui()

        # Initialize MVC components
        if real_components_available:
            self.setup_real_mvc()
        else:
            self.show_error("Real components not available. Please check imports.")

    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel - Controls
        controls_widget = self.create_controls_panel()
        main_layout.addWidget(controls_widget, 1)

        # Right panel - Visual BCF View
        if real_components_available:
            self.visual_bcf_widget = QWidget()  # Placeholder
            main_layout.addWidget(self.visual_bcf_widget, 2)
        else:
            error_widget = QLabel("Real components not available")
            error_widget.setStyleSheet("color: red; font-size: 14px;")
            main_layout.addWidget(error_widget, 2)

    def create_controls_panel(self):
        """Create controls panel"""
        group = QGroupBox("Real Visual BCF MVC Test Controls")
        layout = QVBoxLayout(group)

        # Status
        self.status_label = QLabel("Status: Initializing...")
        layout.addWidget(self.status_label)

        # Component operations
        layout.addWidget(QLabel("MVC Component Operations:"))

        add_lte_btn = QPushButton("Add LTE Modem (MVC)")
        add_lte_btn.clicked.connect(self.add_lte_modem)
        layout.addWidget(add_lte_btn)

        add_5g_btn = QPushButton("Add 5G Modem (MVC)")
        add_5g_btn.clicked.connect(self.add_5g_modem)
        layout.addWidget(add_5g_btn)

        add_rfic_btn = QPushButton("Add RFIC Chip (MVC)")
        add_rfic_btn.clicked.connect(self.add_rfic_chip)
        layout.addWidget(add_rfic_btn)

        add_generic_btn = QPushButton("Add Generic Chip (MVC)")
        add_generic_btn.clicked.connect(self.add_generic_chip)
        layout.addWidget(add_generic_btn)

        # Legacy BCF integration
        layout.addWidget(QLabel("Legacy BCF Integration:"))
        sync_btn = QPushButton("Sync with Legacy BCF")
        sync_btn.clicked.connect(self.sync_with_legacy)
        layout.addWidget(sync_btn)

        import_btn = QPushButton("Import from Legacy BCF")
        import_btn.clicked.connect(self.import_from_legacy)
        layout.addWidget(import_btn)

        # View controls
        layout.addWidget(QLabel("View Controls:"))

        fit_btn = QPushButton("Fit in View")
        fit_btn.clicked.connect(self.fit_in_view)
        layout.addWidget(fit_btn)

        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        layout.addWidget(reset_btn)

        clear_btn = QPushButton("Clear Scene")
        clear_btn.clicked.connect(self.clear_scene)
        layout.addWidget(clear_btn)

        # Components list
        layout.addWidget(QLabel("Components (MVC):"))
        self.components_list = QListWidget()
        layout.addWidget(self.components_list)

        # Statistics
        layout.addWidget(QLabel("Statistics:"))
        self.stats_label = QLabel("Components: 0, Connections: 0")
        layout.addWidget(self.stats_label)

        # Activity log
        layout.addWidget(QLabel("Activity Log:"))
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

        return group

    def setup_real_mvc(self):
        """Setup real MVC components"""
        try:
            # Create RDB Manager with test database
            self.rdb_manager = RDBManager("test_mvc_device_config.json")
            logger.info("RDB Manager created")

            # Create Visual BCF Manager with MVC enabled
            self.visual_bcf_manager = VisualBCFManager(
                parent=None,
                parent_controller=self,
                rdb_manager=self.rdb_manager
            )
            logger.info("Visual BCF Manager with MVC created")

            # Replace the placeholder widget with the real Visual BCF widget
            self.setCentralWidget(QWidget())
            main_layout = QHBoxLayout(self.centralWidget())

            # Re-add controls
            controls_widget = self.create_controls_panel()
            main_layout.addWidget(controls_widget, 1)

            # Add the real Visual BCF widget
            main_layout.addWidget(self.visual_bcf_manager, 2)

            # Connect signals
            self.visual_bcf_manager.data_changed.connect(self.on_data_changed)
            self.visual_bcf_manager.error_occurred.connect(self.on_error_occurred)

            # Update status
            self.status_label.setText("Status: MVC Ready ✅")

            # Add some test data to Legacy BCF
            self.add_test_legacy_data()

            # Set up auto-refresh
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.update_display)
            self.refresh_timer.start(3000)  # Update every 3 seconds

            self.log("Real Visual BCF MVC system initialized successfully!")

        except Exception as e:
            self.show_error(f"Failed to setup real MVC: {e}")
            logger.exception("Setup failed")

    def add_test_legacy_data(self):
        """Add some test data to Legacy BCF for testing"""
        try:
            test_devices = [
                {
                    "name": "Test LTE Modem",
                    "function_type": "LTE",
                    "interface_type": "MIPI",
                    "interface": {"mipi": {"channel": 1}},
                    "config": {"usid": "LTE001"}
                },
                {
                    "name": "Test 5G Modem",
                    "function_type": "5G",
                    "interface_type": "MIPI",
                    "interface": {"mipi": {"channel": 2}},
                    "config": {"usid": "5G001"}
                },
                {
                    "name": "Test RFIC",
                    "function_type": "RFIC",
                    "interface_type": "SPI",
                    "interface": {"spi": {"bus": 1}},
                    "config": {"device_id": "RFIC001"}
                }
            ]

            self.rdb_manager.set_table("config.device.settings", test_devices)
            self.log("Added test data to Legacy BCF")

        except Exception as e:
            self.log(f"Error adding test Legacy BCF data: {e}")

    # Button handlers

    def add_lte_modem(self):
        """Add LTE modem using MVC"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            component_id = self.visual_bcf_manager.add_lte_modem()
            if component_id:
                self.log(f"Added LTE Modem via MVC: {component_id}")
            else:
                self.log("Failed to add LTE Modem")
        else:
            self.log("MVC not enabled")

    def add_5g_modem(self):
        """Add 5G modem using MVC"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            component_id = self.visual_bcf_manager.add_5g_modem()
            if component_id:
                self.log(f"Added 5G Modem via MVC: {component_id}")
            else:
                self.log("Failed to add 5G Modem")
        else:
            self.log("MVC not enabled")

    def add_rfic_chip(self):
        """Add RFIC chip using MVC"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            component_id = self.visual_bcf_manager.add_rfic_chip_mvc()
            if component_id:
                self.log(f"Added RFIC Chip via MVC: {component_id}")
            else:
                self.log("Failed to add RFIC Chip")
        else:
            self.log("MVC not enabled")

    def add_generic_chip(self):
        """Add generic chip using MVC"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            component_id = self.visual_bcf_manager.add_generic_chip_mvc()
            if component_id:
                self.log(f"Added Generic Chip via MVC: {component_id}")
            else:
                self.log("Failed to add Generic Chip")
        else:
            self.log("MVC not enabled")

    def sync_with_legacy(self):
        """Sync with Legacy BCF"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            self.visual_bcf_manager.sync_with_legacy_bcf()
            self.log("Syncing with Legacy BCF...")
        else:
            self.log("MVC not enabled")

    def import_from_legacy(self):
        """Import from Legacy BCF"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            self.visual_bcf_manager.import_from_legacy_bcf()
            self.log("Importing from Legacy BCF...")
        else:
            self.log("MVC not enabled")

    def fit_in_view(self):
        """Fit components in view"""
        if self.visual_bcf_manager:
            self.visual_bcf_manager.fit_in_view()
            self.log("Fitted components in view")

    def reset_view(self):
        """Reset view"""
        if self.visual_bcf_manager:
            self.visual_bcf_manager.reset_view()
            self.log("Reset view")

    def clear_scene(self):
        """Clear scene"""
        if self.visual_bcf_manager and self.visual_bcf_manager.is_mvc_enabled():
            self.visual_bcf_manager.clear_scene_mvc()
            self.log("Clearing scene...")
        else:
            self.log("MVC not enabled")

    # Event handlers

    def on_data_changed(self, data: Dict[str, Any]):
        """Handle data changed from Visual BCF Manager"""
        action = data.get('action', 'unknown')
        source = data.get('source', 'legacy')

        if source == 'mvc':
            self.log(f"📊 MVC Event: {action}")
            if 'message' in data:
                self.log(f"   Message: {data['message']}")
            if 'component_name' in data:
                self.log(f"   Component: {data['component_name']}")
        else:
            self.log(f"📊 Legacy Event: {action}")

        # Update display
        QTimer.singleShot(500, self.update_display)

    def on_error_occurred(self, error_message: str):
        """Handle error from Visual BCF Manager"""
        self.log(f"❌ Error: {error_message}")

    def update_display(self):
        """Update the display with current data"""
        try:
            if not self.visual_bcf_manager or not self.visual_bcf_manager.is_mvc_enabled():
                return

            # Update statistics
            stats = self.visual_bcf_manager.get_mvc_statistics()
            self.stats_label.setText(
                f"Components: {stats.get('total_components', 0)}, "
                f"Connections: {stats.get('total_connections', 0)}"
            )

            # Update components list
            self.components_list.clear()
            data_model = self.visual_bcf_manager.get_data_model()
            if data_model:
                components = data_model.get_all_components()
                for comp_id, comp_data in components.items():
                    item_text = f"{comp_data.name} ({comp_data.component_type}) - {comp_id[:8]}"
                    self.components_list.addItem(item_text)

        except Exception as e:
            self.log(f"Error updating display: {e}")

    def log(self, message: str):
        """Add message to log"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        logger.info(message)

    def show_error(self, message: str):
        """Show error message"""
        self.log(f"ERROR: {message}")
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Status: Error ❌")
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """Handle close event"""
        if self.visual_bcf_manager:
            self.visual_bcf_manager.cleanup()
        event.accept()


def main():
    """Main function"""
    app = QApplication(sys.argv)

    # Create and show test application
    test_app = RealVisualBCFMVCTestApp()
    test_app.show()

    # Log startup message
    logger.info("Real Visual BCF MVC Integration Test started")

    if real_components_available:
        logger.info("✅ All real components available")
        logger.info("Features to test:")
        logger.info("- Add different types of components using MVC")
        logger.info("- Sync with Legacy BCF data")
        logger.info("- Import from Legacy BCF")
        logger.info("- View controls and scene management")
        logger.info("- Real-time data persistence")
    else:
        logger.error("❌ Real components not available")

    # Run the application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
