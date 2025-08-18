"""
RFIC (Radio Frequency Integrated Circuit) chip model.
Extends the base ChipModel with RF-specific properties and pin configurations.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from apps.RBM.BCF.src.models.chip import ChipModel
from apps.RBM.BCF.src.models.pin import Pin


@dataclass
class RFICChipModel(ChipModel):
    """RFIC chip model with RF-specific properties and configurations"""
    
    def __init__(self, name: str = "RFIC", width: float = 200, height: float = 150):
        super().__init__(name, width, height)
        
        # Override properties with RFIC-specific values
        self.properties.update({
            "type": "RFIC",
            "function": "Radio Frequency Integrated Circuit",
            "frequency_range": "600MHz - 6GHz",
            "technology": "CMOS",
            "package": "BGA",
            "power_supply": "1.8V/2.8V",
            "operating_temp": "-40°C to +85°C",
            "rf_bands": ["B1", "B2", "B3", "B4", "B5", "B7", "B8", "B20", "B28", "B38", "B40", "B41"],
            "tx_ports": 4,
            "rx_ports": 4,
            "mimo_support": "4x4",
            "carrier_aggregation": "5CA",
        })
        
        # Initialize default RFIC pin configuration
        self._setup_default_pins()
    
    def _setup_default_pins(self) -> None:
        """Setup default pin configuration for RFIC"""
        # Clear any existing pins
        self.pins.clear()
        
        # RF TX ports (Left side)
        tx_spacing = self.height / 5
        for i in range(4):
            y_pos = tx_spacing * (i + 1)
            pin_name = f"TX{i+1}"
            self.add_pin(0, y_pos, pin_name)
        
        # RF RX ports (Right side)
        rx_spacing = self.height / 5
        for i in range(4):
            y_pos = rx_spacing * (i + 1)
            pin_name = f"RX{i+1}"
            self.add_pin(self.width, y_pos, pin_name)
        
        # Control interfaces (Top side)
        control_spacing = self.width / 4
        control_pins = ["SPI_CLK", "SPI_DATA", "ENABLE"]
        for i, pin_name in enumerate(control_pins):
            x_pos = control_spacing * (i + 1)
            self.add_pin(x_pos, 0, pin_name)
        
        # Power/Ground (Bottom side)
        power_spacing = self.width / 4
        power_pins = ["VDD", "GND", "VCC"]
        for i, pin_name in enumerate(power_pins):
            x_pos = power_spacing * (i + 1)
            self.add_pin(x_pos, self.height, pin_name)
    
    def get_tx_pins(self) -> List[Pin]:
        """Get all TX (transmit) pins"""
        return [pin for pin in self.pins if pin.name.startswith("TX")]
    
    def get_rx_pins(self) -> List[Pin]:
        """Get all RX (receive) pins"""
        return [pin for pin in self.pins if pin.name.startswith("RX")]
    
    def get_control_pins(self) -> List[Pin]:
        """Get all control pins"""
        control_names = ["SPI_CLK", "SPI_DATA", "ENABLE"]
        return [pin for pin in self.pins if pin.name in control_names]
    
    def get_power_pins(self) -> List[Pin]:
        """Get all power/ground pins"""
        power_names = ["VDD", "GND", "VCC"]
        return [pin for pin in self.pins if pin.name in power_names]
    
    def set_rf_band_support(self, bands: List[str]) -> None:
        """Set supported RF bands"""
        self.properties["rf_bands"] = bands
    
    def get_rf_band_support(self) -> List[str]:
        """Get supported RF bands"""
        return self.properties.get("rf_bands", [])
    
    def set_frequency_range(self, freq_range: str) -> None:
        """Set frequency range"""
        self.properties["frequency_range"] = freq_range
    
    def get_frequency_range(self) -> str:
        """Get frequency range"""
        return self.properties.get("frequency_range", "Unknown")
    
    def configure_mimo(self, mimo_config: str) -> None:
        """Configure MIMO support (e.g., '2x2', '4x4')"""
        self.properties["mimo_support"] = mimo_config
    
    def get_mimo_support(self) -> str:
        """Get MIMO configuration"""
        return self.properties.get("mimo_support", "1x1")
    
    def set_carrier_aggregation(self, ca_config: str) -> None:
        """Set carrier aggregation capability"""
        self.properties["carrier_aggregation"] = ca_config
    
    def get_carrier_aggregation(self) -> str:
        """Get carrier aggregation capability"""
        return self.properties.get("carrier_aggregation", "No CA")
    
    def get_detailed_info(self) -> Dict[str, str]:
        """Get detailed RFIC information"""
        return {
            "Name": self.name,
            "Type": self.properties["type"],
            "Function": self.properties["function"],
            "Frequency Range": self.get_frequency_range(),
            "Technology": self.properties.get("technology", "Unknown"),
            "Package": self.properties.get("package", "Unknown"),
            "Power Supply": self.properties.get("power_supply", "Unknown"),
            "Operating Temperature": self.properties.get("operating_temp", "Unknown"),
            "MIMO Support": self.get_mimo_support(),
            "Carrier Aggregation": self.get_carrier_aggregation(),
            "RF Bands": ", ".join(self.get_rf_band_support()),
            "TX Ports": str(len(self.get_tx_pins())),
            "RX Ports": str(len(self.get_rx_pins())),
            "Control Pins": str(len(self.get_control_pins())),
            "Power Pins": str(len(self.get_power_pins())),
        }
