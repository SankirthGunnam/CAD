import os
from typing import Tuple, Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap
from PySide6.QtCore import Qt, QRect

class PackageImageGenerator:
    """Generator for creating chip package visualization images"""

    def __init__(self, image_dir: str = None):
        if image_dir is None:
            # Default to resource/package_images directory relative to this
            # file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.image_dir = os.path.join(
                current_dir, '../../../resource/package_images')
        else:
            self.image_dir = image_dir

        # Ensure directory exists
        os.makedirs(self.image_dir, exist_ok=True)

    def generate_qfn_image(
            self,
            width_mm: float,
            height_mm: float,
            pin_count: int = 0) -> QPixmap:
        """Generate QFN (Quad Flat No-leads) package image"""
        pixmap = QPixmap(200, 150)
        pixmap.fill(Qt.white)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Package body (dark green/black)
        body_color = QColor(20, 40, 20)
        painter.fillRect(40, 30, 120, 90, QBrush(body_color))

        # Package outline
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(40, 30, 120, 90)

        # Draw pins around the package
        pin_color = QColor(200, 200, 180)  # Silver color
        painter.setBrush(QBrush(pin_color))
        painter.setPen(QPen(Qt.darkGray, 1))

        # Estimate pins per side (simplified)
        pins_per_side = max(1, pin_count // 4) if pin_count > 0 else 6

        # Top pins
        pin_width = 100 // max(1, pins_per_side)
        for i in range(pins_per_side):
            x = 50 + i * pin_width
            painter.drawRect(x, 25, pin_width - 2, 8)

        # Bottom pins
        for i in range(pins_per_side):
            x = 50 + i * pin_width
            painter.drawRect(x, 117, pin_width - 2, 8)

        # Left pins
        pin_height = 80 // max(1, pins_per_side)
        for i in range(pins_per_side):
            y = 35 + i * pin_height
            painter.drawRect(32, y, 8, pin_height - 2)

        # Right pins
        for i in range(pins_per_side):
            y = 35 + i * pin_height
            painter.drawRect(160, y, 8, pin_height - 2)

        # Add package marking (pin 1 indicator)
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(45, 35, 8, 8)

        # Add text
        painter.setPen(QPen(Qt.white))
        painter.setFont(QFont("Arial", 8))
        painter.drawText(50, 80, f"QFN")
        painter.drawText(50, 95, f"{width_mm:.1f}x{height_mm:.1f}mm")

        painter.end()
        return pixmap

    def get_or_create_package_image(
            self,
            image_name: str,
            package_info: str = "") -> Optional[QPixmap]:
        """Get existing package image or create a new one"""
        image_path = os.path.join(self.image_dir, image_name)

        # Check if image already exists
        if os.path.exists(image_path):
            return QPixmap(image_path)

        # Generate image based on package type - simplified version
        pixmap = None

        if "qfn" in image_name.lower():
            # Extract dimensions from filename if possible
            try:
                parts = image_name.lower().replace('.png', '').split('_')
                if len(parts) >= 2:
                    dims = parts[1].replace('p', '.').split('x')
                    width = float(dims[0]) if len(dims) > 0 else 4.0
                    height = float(dims[1]) if len(dims) > 1 else width
                    pixmap = self.generate_qfn_image(width, height)
            except BaseException:
                pixmap = self.generate_qfn_image(4.0, 4.0)
        else:
            # Generic package - default to QFN style
            pixmap = self.generate_qfn_image(4.0, 4.0)

        # Save the generated image
        if pixmap:
            pixmap.save(image_path)
            return pixmap

        return None
