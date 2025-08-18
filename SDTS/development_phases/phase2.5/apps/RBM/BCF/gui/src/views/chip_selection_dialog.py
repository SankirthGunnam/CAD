from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
    QFrame,
    QScrollArea,
    QGroupBox,
    QSplitter,
    QLineEdit,
    QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont
from typing import Dict, Optional, List
from .package_image_generator import PackageImageGenerator

class ChipSelectionDialog(QDialog):
    """Dialog for selecting RF front-end devices with vendor categorization"""
    
    chip_selected = Signal(dict)  # Emits selected chip information
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select RF Front-End Device")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # Initialize chip database
        self.chip_database = self._initialize_chip_database()
        self.selected_chip = None
        self.current_search = ""
        self.current_type_filter = "All Types"
        
        # Initialize package image generator
        self.package_generator = PackageImageGenerator()
        
        self._setup_ui()
        self._connect_signals()
        self._populate_vendor_list()
        
    def _initialize_chip_database(self) -> Dict[str, List[Dict]]:
        """Initialize the RF chip database with vendors and their chips"""
        return {
            "QORVO": [
                {
                    "name": "QM77XXX Series",
                    "part_number": "QM77001",
                    "type": "RF Front-End Module",
                    "frequency": "600 MHz - 6 GHz",
                    "applications": "5G Sub-6GHz, LTE",
                    "channels": "4TX/4RX",
                    "gain": "15-25 dB",
                    "power": "28 dBm",
                    "package": "QFN 7x7mm",
                    "image": "qfn_7x7.png",
                    "description": "Highly integrated RF front-end module for 5G Sub-6GHz applications"
                },
                {
                    "name": "QM78XXX Series", 
                    "part_number": "QM78001",
                    "type": "Power Amplifier",
                    "frequency": "3.3 - 4.2 GHz",
                    "applications": "5G C-Band",
                    "channels": "2TX",
                    "gain": "28 dB",
                    "power": "31 dBm",
                    "package": "QFN 4x4mm",
                    "image": "qfn_4x4.png",
                    "description": "High-power amplifier for 5G C-Band applications"
                },
                {
                    "name": "QPQ1904",
                    "part_number": "QPQ1904",
                    "type": "RF Filter",
                    "frequency": "1900 - 1980 MHz",
                    "applications": "LTE Band 2/25",
                    "channels": "1",
                    "gain": "0.8 dB IL",
                    "power": "33 dBm",
                    "package": "CSP 1.5x0.8mm",
                    "image": "csp_1p5x0p8.png",
                    "description": "Ultra-compact BAW filter for mobile applications"
                },
                {
                    "name": "QPA2308",
                    "part_number": "QPA2308",
                    "type": "Power Amplifier",
                    "frequency": "2.3 - 2.4 GHz",
                    "applications": "WiFi, ISM Band",
                    "channels": "1TX",
                    "gain": "31 dB",
                    "power": "27 dBm",
                    "package": "QFN 3x3mm",
                    "image": "qfn_3x3.png",
                    "description": "High-efficiency 2.4GHz power amplifier"
                }
            ],
            "INFINEON": [
                {
                    "name": "BGM13P22",
                    "part_number": "BGM13P22F12",
                    "type": "RF Power Amplifier",
                    "frequency": "1.8 - 2.2 GHz",
                    "applications": "LTE Band 3, 5G",
                    "channels": "1TX",
                    "gain": "32 dB",
                    "power": "30 dBm",
                    "package": "TQFN 3x3mm",
                    "image": "tqfn_3x3.png",
                    "description": "High-efficiency power amplifier with integrated bias control"
                },
                {
                    "name": "BGM13P28",
                    "part_number": "BGM13P28F12",
                    "type": "RF Power Amplifier", 
                    "frequency": "2.5 - 2.8 GHz",
                    "applications": "LTE Band 7/41, 5G",
                    "channels": "1TX",
                    "gain": "30 dB",
                    "power": "29 dBm",
                    "package": "TQFN 3x3mm",
                    "image": "tqfn_3x3.png",
                    "description": "Ultra-linear power amplifier for high-performance applications"
                },
                {
                    "name": "BGS14GA14",
                    "part_number": "BGS14GA14",
                    "type": "RF Switch",
                    "frequency": "DC - 4 GHz",
                    "applications": "Multi-band cellular",
                    "channels": "SP4T",
                    "gain": "0.35 dB IL",
                    "power": "35 dBm",
                    "package": "TSFP 2x2mm",
                    "image": "tsfp_2x2.png",
                    "description": "High-linearity antenna switch"
                },
                {
                    "name": "BGA2869",
                    "part_number": "BGA2869",
                    "type": "Low Noise Amplifier",
                    "frequency": "1.8 - 2.2 GHz",
                    "applications": "Cellular, GPS",
                    "channels": "1RX",
                    "gain": "16.5 dB",
                    "power": "N/A",
                    "package": "SOT363",
                    "image": "sot363.png",
                    "description": "Ultra low-noise amplifier for receive applications"
                }
            ],
            "AVAGO/BROADCOM": [
                {
                    "name": "AFEM-8092",
                    "part_number": "AFEM-8092",
                    "type": "Antenna Tuner",
                    "frequency": "700 MHz - 2.7 GHz",
                    "applications": "Multi-band LTE/5G",
                    "channels": "Tunable",
                    "gain": "Variable",
                    "power": "N/A",
                    "package": "CSP 2.5x2.0mm",
                    "image": "csp_2p5x2p0.png",
                    "description": "High-performance antenna tuner with wide frequency coverage"
                },
                {
                    "name": "AFEM-8030",
                    "part_number": "AFEM-8030",
                    "type": "RF Front-End Module",
                    "frequency": "1.71 - 2.2 GHz",
                    "applications": "LTE/5G Sub-6GHz",
                    "channels": "2TX/2RX",
                    "gain": "25 dB",
                    "power": "27 dBm", 
                    "package": "LGA 4x4mm",
                    "image": "lga_4x4.png",
                    "description": "Integrated FEM with PA, LNA, and switch functions"
                },
                {
                    "name": "AFEM-8020",
                    "part_number": "AFEM-8020",
                    "type": "Diversity Module",
                    "frequency": "699 - 960 MHz",
                    "applications": "LTE Low Band",
                    "channels": "1RX + Switch",
                    "gain": "13 dB",
                    "power": "N/A",
                    "package": "LGA 3x3mm",
                    "image": "lga_3x3.png",
                    "description": "Integrated diversity receive module"
                },
                {
                    "name": "ACPM-7800",
                    "part_number": "ACPM-7800",
                    "type": "Power Amplifier Module",
                    "frequency": "824 - 915 MHz",
                    "applications": "GSM900, CDMA",
                    "channels": "1TX",
                    "gain": "29 dB",
                    "power": "35 dBm",
                    "package": "LGA 5x5mm",
                    "image": "lga_5x5.png",
                    "description": "High power GSM/CDMA power amplifier module"
                }
            ],
            "SKYWORKS": [
                {
                    "name": "SKY67100",
                    "part_number": "SKY67100-396LF",
                    "type": "RF Front-End Module",
                    "frequency": "2.3 - 2.7 GHz",
                    "applications": "5G Band n41",
                    "channels": "4TX/4RX",
                    "gain": "30 dB",
                    "power": "28 dBm",
                    "package": "QFN 6x6mm",
                    "image": "qfn_6x6.png",
                    "description": "High-performance FEM for 5G mid-band applications"
                },
                {
                    "name": "SKY67030",
                    "part_number": "SKY67030-11",
                    "type": "Power Amplifier",
                    "frequency": "3.3 - 4.2 GHz",
                    "applications": "5G C-Band",
                    "channels": "1TX",
                    "gain": "35 dB",
                    "power": "30 dBm",
                    "package": "QFN 3x3mm",
                    "image": "qfn_3x3.png",
                    "description": "Ultra-linear PA for 5G infrastructure applications"
                },
                {
                    "name": "SKY13350",
                    "part_number": "SKY13350-374LF",
                    "type": "RF Switch",
                    "frequency": "DC - 6 GHz",
                    "applications": "Multi-band cellular",
                    "channels": "SP6T",
                    "gain": "0.4 dB IL",
                    "power": "34 dBm",
                    "package": "CSP 2.0x1.5mm",
                    "image": "csp_2p0x1p5.png",
                    "description": "Ultra-compact high-isolation switch"
                },
                {
                    "name": "SKY67151",
                    "part_number": "SKY67151-396LF",
                    "type": "Low Noise Amplifier",
                    "frequency": "700 - 960 MHz",
                    "applications": "LTE Low Band RX",
                    "channels": "1RX",
                    "gain": "15.5 dB",
                    "power": "N/A",
                    "package": "DFN 2x2mm",
                    "image": "dfn_2x2.png",
                    "description": "High-linearity LNA with bypass mode"
                },
                {
                    "name": "SKY85703",
                    "part_number": "SKY85703-11",
                    "type": "RF Front-End Module",
                    "frequency": "824 - 915 MHz",
                    "applications": "GSM850/900",
                    "channels": "1TX/1RX",
                    "gain": "32 dB",
                    "power": "35 dBm",
                    "package": "LGA 4x4mm",
                    "image": "lga_4x4.png",
                    "description": "Complete GSM FEM with integrated PA/switch/LNA"
                }
            ],
            "MURATA": [
                {
                    "name": "MYRJ2",
                    "part_number": "MYRJ21G1ANF-R10",
                    "type": "RF Switch",
                    "frequency": "DC - 6 GHz",
                    "applications": "Multi-band switching",
                    "channels": "SP6T",
                    "gain": "0.4 dB IL",
                    "power": "34 dBm",
                    "package": "LGA 2.5x2.0mm",
                    "image": "lga_2p5x2p0.png",
                    "description": "High-isolation RF switch for antenna diversity"
                },
                {
                    "name": "MYRJ4",
                    "part_number": "MYRJ41G2A6F-R25",
                    "type": "RF Filter",
                    "frequency": "2110 - 2200 MHz",
                    "applications": "LTE Band 1 Rx",
                    "channels": "1",
                    "gain": "1.5 dB IL",
                    "power": "N/A",
                    "package": "LGA 2.0x1.6mm",
                    "image": "lga_2p0x1p6.png",
                    "description": "Ultra-compact SAW filter for cellular receive"
                }
            ],
            "ANALOG DEVICES": [
                {
                    "name": "ADAR7251",
                    "part_number": "ADAR7251",
                    "type": "Beamformer IC",
                    "frequency": "24 - 29.5 GHz",
                    "applications": "5G mmWave, Radar",
                    "channels": "4TX/4RX",
                    "gain": "Variable",
                    "power": "20 dBm",
                    "package": "BGA 7x7mm",
                    "image": "bga_7x7.png",
                    "description": "Dual-polarization beamformer for 5G mmWave applications"
                },
                {
                    "name": "HMC1119",
                    "part_number": "HMC1119LP4E",
                    "type": "Power Amplifier",
                    "frequency": "20 - 31 GHz",
                    "applications": "Ka-Band, Satellite",
                    "channels": "1TX",
                    "gain": "22 dB",
                    "power": "25 dBm",
                    "package": "QFN 4x4mm",
                    "image": "qfn_4x4.png",
                    "description": "Ka-band power amplifier for satellite applications"
                }
            ],
            "NXP": [
                {
                    "name": "A2F18A050-00T",
                    "part_number": "A2F18A050-00T",
                    "type": "RF Power MOSFET",
                    "frequency": "1.8 - 2.2 GHz",
                    "applications": "Base Station, Repeater",
                    "channels": "1TX",
                    "gain": "16 dB",
                    "power": "50W",
                    "package": "SOT1322",
                    "image": "sot1322.png",
                    "description": "50W RF LDMOS transistor for base station applications"
                },
                {
                    "name": "MMZ1608",
                    "part_number": "MMZ1608B102A",
                    "type": "EMI Filter",
                    "frequency": "DC - 6 GHz",
                    "applications": "EMI Suppression",
                    "channels": "1",
                    "gain": "N/A",
                    "power": "N/A",
                    "package": "0603",
                    "image": "smd_0603.png",
                    "description": "Chip ferrite bead for high-frequency noise suppression"
                }
            ]
        }
    
    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left side - Vendor and chip list with search
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Search and filter section
        search_group = QGroupBox("Search & Filter")
        search_layout = QVBoxLayout(search_group)
        
        # Search field
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by name, part number, or application...")
        search_row.addWidget(self.search_field)
        search_layout.addLayout(search_row)
        
        # Type filter
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types",
            "RF Front-End Module",
            "Power Amplifier", 
            "Low Noise Amplifier",
            "RF Switch",
            "RF Filter",
            "Antenna Tuner",
            "Beamformer IC",
            "RF Power MOSFET",
            "EMI Filter",
            "Diversity Module",
            "Power Amplifier Module"
        ])
        # Fix dropdown not closing issue
        self.type_filter.setFocusPolicy(Qt.StrongFocus)
        filter_row.addWidget(self.type_filter)
        search_layout.addLayout(filter_row)
        
        left_layout.addWidget(search_group)
        
        # Vendor list
        vendor_group = QGroupBox("RF Device Vendors")
        vendor_layout = QVBoxLayout(vendor_group)
        self.vendor_list = QListWidget()
        self.vendor_list.setMaximumHeight(150)
        vendor_layout.addWidget(self.vendor_list)
        left_layout.addWidget(vendor_group)
        
        # Chip list
        chip_group = QGroupBox("Available Chips")
        chip_layout = QVBoxLayout(chip_group)
        self.chip_list = QListWidget()
        chip_layout.addWidget(self.chip_list)
        left_layout.addWidget(chip_group)
        
        main_splitter.addWidget(left_widget)
        
        # Right side - Chip details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Chip image area
        image_group = QGroupBox("Chip Package")
        image_layout = QVBoxLayout(image_group)
        
        # Create a horizontal layout to center the image
        image_center_layout = QHBoxLayout()
        image_center_layout.addStretch()  # Left spacer
        
        self.chip_image = QLabel()
        self.chip_image.setMinimumSize(250, 180)
        self.chip_image.setMaximumSize(250, 180)  # Set fixed size to prevent scaling issues
        self.chip_image.setScaledContents(True)  # Allow scaling to fill the area
        self.chip_image.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #f8f8f8;
                text-align: center;
            }
        """)
        self.chip_image.setAlignment(Qt.AlignCenter)
        self.chip_image.setText("Package Image\n(Preview)")
        
        image_center_layout.addWidget(self.chip_image)
        image_center_layout.addStretch()  # Right spacer
        
        image_layout.addLayout(image_center_layout)
        right_layout.addWidget(image_group)
        
        # Chip properties
        properties_group = QGroupBox("Chip Properties")
        properties_layout = QVBoxLayout(properties_group)
        
        # Create scrollable area for properties
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.properties_widget = QWidget()
        self.properties_layout = QGridLayout(self.properties_widget)
        self.properties_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.properties_widget)
        
        properties_layout.addWidget(scroll_area)
        right_layout.addWidget(properties_group)
        
        main_splitter.addWidget(right_widget)
        
        # Set splitter proportions: 25% for search/chips, 75% for details
        main_splitter.setStretchFactor(0, 1)  # Left side (search/chips)
        main_splitter.setStretchFactor(1, 3)  # Right side (details) - 3x larger
        main_splitter.setSizes([225, 675])  # Initial sizes in pixels
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("Add Chip")
        self.ok_button.setEnabled(False)
        self.ok_button.setMinimumSize(100, 35)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumSize(100, 35)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        
    def _connect_signals(self):
        """Connect widget signals"""
        self.vendor_list.currentItemChanged.connect(self._on_vendor_selection_changed)
        self.chip_list.currentItemChanged.connect(self._on_chip_selection_changed)
        self.search_field.textChanged.connect(self._on_search_changed)
        self.type_filter.currentTextChanged.connect(self._on_type_filter_changed)
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.reject)
        
    def _populate_vendor_list(self):
        """Populate the vendor list"""
        for vendor in self.chip_database.keys():
            item = QListWidgetItem(vendor)
            item.setFont(QFont("Arial", 10, QFont.Bold))
            self.vendor_list.addItem(item)
            
    def _on_vendor_selection_changed(self, current_item, previous_item):
        """Handle vendor selection change"""
        if not current_item:
            return
            
        vendor = current_item.text()
        self._populate_chip_list(vendor)
        self._clear_chip_details()
        
    def _populate_chip_list(self, vendor: str):
        """Populate chip list for selected vendor with filtering"""
        self.chip_list.clear()
        
        if vendor in self.chip_database:
            for chip in self.chip_database[vendor]:
                if self._chip_matches_filters(chip):
                    item = QListWidgetItem(f"{chip['name']} ({chip['part_number']})")
                    item.setData(Qt.UserRole, chip)
                    self.chip_list.addItem(item)
                    
    def _chip_matches_filters(self, chip: Dict) -> bool:
        """Check if chip matches current search and type filters"""
        # Check type filter
        if self.current_type_filter != "All Types":
            if chip.get('type', '') != self.current_type_filter:
                return False
                
        # Check search filter
        if self.current_search:
            search_lower = self.current_search.lower()
            searchable_fields = [
                chip.get('name', ''),
                chip.get('part_number', ''),
                chip.get('applications', ''),
                chip.get('type', ''),
                chip.get('frequency', '')
            ]
            
            if not any(search_lower in field.lower() for field in searchable_fields):
                return False
                
        return True
        
    def _on_search_changed(self, text: str):
        """Handle search text change"""
        self.current_search = text
        self._refresh_chip_list()
        
    def _on_type_filter_changed(self, filter_type: str):
        """Handle type filter change"""
        self.current_type_filter = filter_type
        self._refresh_chip_list()
        
    def _refresh_chip_list(self):
        """Refresh the chip list with current filters"""
        current_vendor_item = self.vendor_list.currentItem()
        if current_vendor_item:
            vendor = current_vendor_item.text()
            self._populate_chip_list(vendor)
                
    def _on_chip_selection_changed(self, current_item, previous_item):
        """Handle chip selection change"""
        if not current_item:
            self.selected_chip = None
            self.ok_button.setEnabled(False)
            self._clear_chip_details()
            return
            
        chip_data = current_item.data(Qt.UserRole)
        self.selected_chip = chip_data
        self.ok_button.setEnabled(True)
        self._update_chip_details(chip_data)
        
    def _update_chip_details(self, chip_data: Dict):
        """Update chip details display"""
        # Clear existing properties
        self._clear_chip_details()
        
        # Update chip image with actual package visualization
        image_name = chip_data.get('image', '')
        if image_name:
            pixmap = self.package_generator.get_or_create_package_image(image_name)
            if pixmap:
                # Scale image to fit the label with fixed size to prevent continuous scaling
                fixed_size = self.chip_image.minimumSize()
                scaled_pixmap = pixmap.scaled(
                    fixed_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.chip_image.setPixmap(scaled_pixmap)
                # Set scaled contents to prevent further scaling
                self.chip_image.setScaledContents(False)
            else:
                self.chip_image.setText(f"Package: {chip_data.get('package', 'N/A')}\n(Image Preview)")
        else:
            self.chip_image.setText(f"Package: {chip_data.get('package', 'N/A')}\n(Image Preview)")
        
        # Update properties
        properties = [
            ("Part Number", chip_data.get('part_number', 'N/A')),
            ("Type", chip_data.get('type', 'N/A')),
            ("Frequency Range", chip_data.get('frequency', 'N/A')),
            ("Applications", chip_data.get('applications', 'N/A')),
            ("Channels", chip_data.get('channels', 'N/A')),
            ("Gain", chip_data.get('gain', 'N/A')),
            ("Max Power", chip_data.get('power', 'N/A')),
            ("Package", chip_data.get('package', 'N/A')),
        ]
        
        for i, (label, value) in enumerate(properties):
            label_widget = QLabel(f"{label}:")
            label_widget.setFont(QFont("Arial", 9, QFont.Bold))
            value_widget = QLabel(str(value))
            value_widget.setWordWrap(True)
            
            self.properties_layout.addWidget(label_widget, i, 0, Qt.AlignTop)
            self.properties_layout.addWidget(value_widget, i, 1, Qt.AlignTop)
            
        # Add description
        if chip_data.get('description'):
            desc_label = QLabel("Description:")
            desc_label.setFont(QFont("Arial", 9, QFont.Bold))
            desc_value = QLabel(chip_data['description'])
            desc_value.setWordWrap(True)
            desc_value.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; border-radius: 4px; }")
            
            row = len(properties)
            self.properties_layout.addWidget(desc_label, row, 0, Qt.AlignTop)
            self.properties_layout.addWidget(desc_value, row, 1, Qt.AlignTop)
            
    def _clear_chip_details(self):
        """Clear chip details display"""
        self.chip_image.clear()
        self.chip_image.setText("Package Image\n(Preview)")
        
        # Clear properties layout
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def _on_ok_clicked(self):
        """Handle OK button click"""
        if self.selected_chip:
            self.chip_selected.emit(self.selected_chip)
            self.accept()
            
    def get_selected_chip(self) -> Optional[Dict]:
        """Get the currently selected chip data"""
        return self.selected_chip
