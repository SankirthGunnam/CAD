from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QFormLayout,
)
from PySide6.QtCore import Qt
from apps.RBM5.BCF.source.models.chip_table_model import ChipTableModel


class ChipDialog(QDialog):
    """Dialog for adding and editing chips"""

    def __init__(self, model: ChipTableModel, chip_id: str = None):
        super().__init__()
        self.model = model
        self.chip_id = chip_id
        self.setup_ui()
        self.load_chip_data()

    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Edit Chip" if self.chip_id else "Add Chip")
        layout = QVBoxLayout()

        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Width
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 1000)
        self.width_spin.setDecimals(2)
        width_layout.addWidget(self.width_spin)
        layout.addLayout(width_layout)

        # Height
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0, 1000)
        self.height_spin.setDecimals(2)
        height_layout.addWidget(self.height_spin)
        layout.addLayout(height_layout)

        # Material
        material_layout = QHBoxLayout()
        material_layout.addWidget(QLabel("Material:"))
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Silicon", "GaAs", "InP", "Other"])
        material_layout.addWidget(self.material_combo)
        layout.addLayout(material_layout)

        # Thickness
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Thickness:"))
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0, 1000)
        self.thickness_spin.setDecimals(2)
        thickness_layout.addWidget(self.thickness_spin)
        layout.addLayout(thickness_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_chip)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_chip_data(self):
        """Load existing chip data if editing"""
        if self.chip_id:
            chip = next((c for c in self.model.chips if c["id"] == self.chip_id), None)
            if chip:
                self.name_edit.setText(chip["name"])
                self.width_spin.setValue(float(chip["width"]))
                self.height_spin.setValue(float(chip["height"]))
                self.material_combo.setCurrentText(chip["parameters"]["material"])
                self.thickness_spin.setValue(float(chip["parameters"]["thickness"]))

    def save_chip(self):
        """Save the chip data"""
        chip_data = {
            "name": self.name_edit.text(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value(),
            "parameters": {
                "material": self.material_combo.currentText(),
                "thickness": self.thickness_spin.value(),
            },
        }

        if self.chip_id:
            self.model.update_chip(self.chip_id, chip_data)
        else:
            self.model._add_chip(chip_data)

        self.accept()
