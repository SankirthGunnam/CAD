from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QTextEdit,
    QWidget,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from typing import Dict, Any, Optional


class ChipPropertiesDialog(QDialog):
    """Dialog for editing chip properties and parameters"""
    
    properties_updated = Signal(dict)  # Emits updated properties

    def __init__(self, chip_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chip Properties")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        self.original_chip_data = chip_data.copy()
        self.chip_data = chip_data.copy()
        
        self._setup_ui()
        self._populate_fields()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget for different property categories
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Basic Properties Tab
        self._create_basic_properties_tab()
        
        # RF Properties Tab  
        self._create_rf_properties_tab()
        
        # Physical Properties Tab
        self._create_physical_properties_tab()
        
        # Advanced Properties Tab
        self._create_advanced_properties_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("Reset")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Apply")
        
        # Style buttons
        for btn in [self.reset_button, self.cancel_button, self.ok_button]:
            btn.setMinimumSize(80, 35)
            
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        main_layout.addLayout(button_layout)
        
    def _create_basic_properties_tab(self):
        """Create basic properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)
        
        # Basic information group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.part_number_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems([
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
            "Power Amplifier Module",
            "Custom"
        ])
        self.manufacturer_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        
        basic_layout.addRow("Name:", self.name_edit)
        basic_layout.addRow("Part Number:", self.part_number_edit)
        basic_layout.addRow("Type:", self.type_combo)
        basic_layout.addRow("Manufacturer:", self.manufacturer_edit)
        basic_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Application information group
        app_group = QGroupBox("Application Information")
        app_layout = QFormLayout(app_group)
        
        self.applications_edit = QLineEdit()
        self.frequency_range_edit = QLineEdit()
        self.channels_edit = QLineEdit()
        
        app_layout.addRow("Applications:", self.applications_edit)
        app_layout.addRow("Frequency Range:", self.frequency_range_edit)
        app_layout.addRow("Channels:", self.channels_edit)
        
        scroll_layout.addWidget(app_group)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(widget, "Basic")
        
    def _create_rf_properties_tab(self):
        """Create RF properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)
        
        # RF Performance group
        rf_group = QGroupBox("RF Performance")
        rf_layout = QFormLayout(rf_group)
        
        self.gain_edit = QLineEdit()
        self.power_edit = QLineEdit()
        self.noise_figure_edit = QLineEdit()
        self.insertion_loss_edit = QLineEdit()
        self.isolation_edit = QLineEdit()
        self.vswr_edit = QLineEdit()
        self.p1db_edit = QLineEdit()
        self.ip3_edit = QLineEdit()
        
        rf_layout.addRow("Gain (dB):", self.gain_edit)
        rf_layout.addRow("Max Power (dBm):", self.power_edit)
        rf_layout.addRow("Noise Figure (dB):", self.noise_figure_edit)
        rf_layout.addRow("Insertion Loss (dB):", self.insertion_loss_edit)
        rf_layout.addRow("Isolation (dB):", self.isolation_edit)
        rf_layout.addRow("VSWR:", self.vswr_edit)
        rf_layout.addRow("P1dB (dBm):", self.p1db_edit)
        rf_layout.addRow("IP3 (dBm):", self.ip3_edit)
        
        scroll_layout.addWidget(rf_group)
        
        # Frequency characteristics group
        freq_group = QGroupBox("Frequency Characteristics")
        freq_layout = QFormLayout(freq_group)
        
        self.freq_min_edit = QDoubleSpinBox()
        self.freq_min_edit.setRange(0, 100000)
        self.freq_min_edit.setSuffix(" MHz")
        self.freq_max_edit = QDoubleSpinBox()
        self.freq_max_edit.setRange(0, 100000)
        self.freq_max_edit.setSuffix(" MHz")
        self.bandwidth_edit = QLineEdit()
        
        freq_layout.addRow("Min Frequency:", self.freq_min_edit)
        freq_layout.addRow("Max Frequency:", self.freq_max_edit)
        freq_layout.addRow("Bandwidth:", self.bandwidth_edit)
        
        scroll_layout.addWidget(freq_group)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(widget, "RF Properties")
        
    def _create_physical_properties_tab(self):
        """Create physical properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)
        
        # Package information group
        package_group = QGroupBox("Package Information")
        package_layout = QFormLayout(package_group)
        
        self.package_edit = QLineEdit()
        self.package_width_edit = QDoubleSpinBox()
        self.package_width_edit.setRange(0, 100)
        self.package_width_edit.setSuffix(" mm")
        self.package_height_edit = QDoubleSpinBox()
        self.package_height_edit.setRange(0, 100)
        self.package_height_edit.setSuffix(" mm")
        self.package_thickness_edit = QDoubleSpinBox()
        self.package_thickness_edit.setRange(0, 10)
        self.package_thickness_edit.setSuffix(" mm")
        self.pin_count_edit = QSpinBox()
        self.pin_count_edit.setRange(0, 1000)
        
        package_layout.addRow("Package Type:", self.package_edit)
        package_layout.addRow("Width:", self.package_width_edit)
        package_layout.addRow("Height:", self.package_height_edit)
        package_layout.addRow("Thickness:", self.package_thickness_edit)
        package_layout.addRow("Pin Count:", self.pin_count_edit)
        
        scroll_layout.addWidget(package_group)
        
        # Environmental specs group
        env_group = QGroupBox("Environmental Specifications")
        env_layout = QFormLayout(env_group)
        
        self.temp_min_edit = QSpinBox()
        self.temp_min_edit.setRange(-200, 200)
        self.temp_min_edit.setSuffix(" °C")
        self.temp_max_edit = QSpinBox()
        self.temp_max_edit.setRange(-200, 200)
        self.temp_max_edit.setSuffix(" °C")
        self.supply_voltage_edit = QLineEdit()
        self.supply_current_edit = QLineEdit()
        
        env_layout.addRow("Min Temperature:", self.temp_min_edit)
        env_layout.addRow("Max Temperature:", self.temp_max_edit)
        env_layout.addRow("Supply Voltage (V):", self.supply_voltage_edit)
        env_layout.addRow("Supply Current (mA):", self.supply_current_edit)
        
        scroll_layout.addWidget(env_group)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(widget, "Physical")
        
    def _create_advanced_properties_tab(self):
        """Create advanced properties tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Custom properties group
        custom_group = QGroupBox("Custom Properties")
        custom_layout = QFormLayout(custom_group)
        
        self.custom_prop1_key = QLineEdit()
        self.custom_prop1_value = QLineEdit()
        self.custom_prop2_key = QLineEdit()
        self.custom_prop2_value = QLineEdit()
        self.custom_prop3_key = QLineEdit()
        self.custom_prop3_value = QLineEdit()
        
        custom_layout.addRow("Property 1:", 
                           self._create_custom_prop_row(self.custom_prop1_key, self.custom_prop1_value))
        custom_layout.addRow("Property 2:",
                           self._create_custom_prop_row(self.custom_prop2_key, self.custom_prop2_value))
        custom_layout.addRow("Property 3:",
                           self._create_custom_prop_row(self.custom_prop3_key, self.custom_prop3_value))
        
        scroll_layout.addWidget(custom_group)
        
        # Features group
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout(features_group)
        
        self.feature_bypass = QCheckBox("Bypass Mode")
        self.feature_shutdown = QCheckBox("Shutdown Control")
        self.feature_temp_sensor = QCheckBox("Temperature Sensor")
        self.feature_digital_ctrl = QCheckBox("Digital Control Interface")
        self.feature_esd_protection = QCheckBox("ESD Protection")
        
        for checkbox in [self.feature_bypass, self.feature_shutdown, self.feature_temp_sensor,
                        self.feature_digital_ctrl, self.feature_esd_protection]:
            features_layout.addWidget(checkbox)
            
        scroll_layout.addWidget(features_group)
        
        # Notes group
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Additional notes, design considerations, or special requirements...")
        notes_layout.addWidget(self.notes_edit)
        
        scroll_layout.addWidget(notes_group)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(widget, "Advanced")
        
    def _create_custom_prop_row(self, key_edit: QLineEdit, value_edit: QLineEdit) -> QWidget:
        """Create a custom property key-value row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        key_edit.setPlaceholderText("Property name")
        value_edit.setPlaceholderText("Value")
        
        layout.addWidget(key_edit)
        layout.addWidget(QLabel("="))
        layout.addWidget(value_edit)
        
        return widget
        
    def _populate_fields(self):
        """Populate fields with current chip data"""
        # Basic properties
        self.name_edit.setText(self.chip_data.get('name', ''))
        self.part_number_edit.setText(self.chip_data.get('part_number', ''))
        chip_type = self.chip_data.get('type', '')
        if chip_type in [self.type_combo.itemText(i) for i in range(self.type_combo.count())]:
            self.type_combo.setCurrentText(chip_type)
        else:
            self.type_combo.setCurrentText('Custom')
        self.manufacturer_edit.setText(self.chip_data.get('manufacturer', ''))
        self.description_edit.setText(self.chip_data.get('description', ''))
        self.applications_edit.setText(self.chip_data.get('applications', ''))
        self.frequency_range_edit.setText(self.chip_data.get('frequency', ''))
        self.channels_edit.setText(self.chip_data.get('channels', ''))
        
        # RF properties
        self.gain_edit.setText(self.chip_data.get('gain', ''))
        self.power_edit.setText(self.chip_data.get('power', ''))
        self.noise_figure_edit.setText(self.chip_data.get('noise_figure', ''))
        self.insertion_loss_edit.setText(self.chip_data.get('insertion_loss', ''))
        self.isolation_edit.setText(self.chip_data.get('isolation', ''))
        self.vswr_edit.setText(self.chip_data.get('vswr', ''))
        self.p1db_edit.setText(self.chip_data.get('p1db', ''))
        self.ip3_edit.setText(self.chip_data.get('ip3', ''))
        
        # Physical properties
        self.package_edit.setText(self.chip_data.get('package', ''))
        self.supply_voltage_edit.setText(self.chip_data.get('supply_voltage', ''))
        self.supply_current_edit.setText(self.chip_data.get('supply_current', ''))
        
        # Advanced properties
        self.notes_edit.setText(self.chip_data.get('notes', ''))
        
    def _connect_signals(self):
        """Connect widget signals"""
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        
    def _on_ok_clicked(self):
        """Handle OK button click"""
        self._update_chip_data()
        self.properties_updated.emit(self.chip_data)
        self.accept()
        
    def _on_reset_clicked(self):
        """Handle reset button click"""
        self.chip_data = self.original_chip_data.copy()
        self._populate_fields()
        
    def _update_chip_data(self):
        """Update chip data from form fields"""
        # Basic properties
        self.chip_data['name'] = self.name_edit.text().strip()
        self.chip_data['part_number'] = self.part_number_edit.text().strip()
        self.chip_data['type'] = self.type_combo.currentText()
        self.chip_data['manufacturer'] = self.manufacturer_edit.text().strip()
        self.chip_data['description'] = self.description_edit.toPlainText().strip()
        self.chip_data['applications'] = self.applications_edit.text().strip()
        self.chip_data['frequency'] = self.frequency_range_edit.text().strip()
        self.chip_data['channels'] = self.channels_edit.text().strip()
        
        # RF properties
        if self.gain_edit.text().strip():
            self.chip_data['gain'] = self.gain_edit.text().strip()
        if self.power_edit.text().strip():
            self.chip_data['power'] = self.power_edit.text().strip()
        if self.noise_figure_edit.text().strip():
            self.chip_data['noise_figure'] = self.noise_figure_edit.text().strip()
        if self.insertion_loss_edit.text().strip():
            self.chip_data['insertion_loss'] = self.insertion_loss_edit.text().strip()
        if self.isolation_edit.text().strip():
            self.chip_data['isolation'] = self.isolation_edit.text().strip()
        if self.vswr_edit.text().strip():
            self.chip_data['vswr'] = self.vswr_edit.text().strip()
        if self.p1db_edit.text().strip():
            self.chip_data['p1db'] = self.p1db_edit.text().strip()
        if self.ip3_edit.text().strip():
            self.chip_data['ip3'] = self.ip3_edit.text().strip()
        
        # Physical properties
        if self.package_edit.text().strip():
            self.chip_data['package'] = self.package_edit.text().strip()
        if self.supply_voltage_edit.text().strip():
            self.chip_data['supply_voltage'] = self.supply_voltage_edit.text().strip()
        if self.supply_current_edit.text().strip():
            self.chip_data['supply_current'] = self.supply_current_edit.text().strip()
        
        # Frequency range
        if self.freq_min_edit.value() > 0 or self.freq_max_edit.value() > 0:
            self.chip_data['freq_min_mhz'] = self.freq_min_edit.value()
            self.chip_data['freq_max_mhz'] = self.freq_max_edit.value()
        
        # Temperature range
        if self.temp_min_edit.value() != 0 or self.temp_max_edit.value() != 0:
            self.chip_data['temp_min_c'] = self.temp_min_edit.value()
            self.chip_data['temp_max_c'] = self.temp_max_edit.value()
        
        # Package dimensions
        if self.package_width_edit.value() > 0:
            self.chip_data['package_width_mm'] = self.package_width_edit.value()
        if self.package_height_edit.value() > 0:
            self.chip_data['package_height_mm'] = self.package_height_edit.value()
        if self.package_thickness_edit.value() > 0:
            self.chip_data['package_thickness_mm'] = self.package_thickness_edit.value()
        if self.pin_count_edit.value() > 0:
            self.chip_data['pin_count'] = self.pin_count_edit.value()
        
        # Custom properties
        for i, (key_edit, value_edit) in enumerate([
            (self.custom_prop1_key, self.custom_prop1_value),
            (self.custom_prop2_key, self.custom_prop2_value),
            (self.custom_prop3_key, self.custom_prop3_value)
        ]):
            key = key_edit.text().strip()
            value = value_edit.text().strip()
            if key and value:
                self.chip_data[f'custom_{key}'] = value
        
        # Features
        features = []
        feature_checkboxes = [
            (self.feature_bypass, "Bypass Mode"),
            (self.feature_shutdown, "Shutdown Control"),
            (self.feature_temp_sensor, "Temperature Sensor"),
            (self.feature_digital_ctrl, "Digital Control Interface"),
            (self.feature_esd_protection, "ESD Protection")
        ]
        
        for checkbox, feature_name in feature_checkboxes:
            if checkbox.isChecked():
                features.append(feature_name)
        
        if features:
            self.chip_data['features'] = ", ".join(features)
        
        # Notes
        if self.notes_edit.toPlainText().strip():
            self.chip_data['notes'] = self.notes_edit.toPlainText().strip()
            
    def get_updated_chip_data(self) -> Dict[str, Any]:
        """Get the updated chip data"""
        return self.chip_data
