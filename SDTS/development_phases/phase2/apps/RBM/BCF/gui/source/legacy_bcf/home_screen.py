from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QGridLayout,
    QToolButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon


class HomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Title bar
        title = QLabel("Welcome to SDTS")
        title.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(title)

        # Search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search tools or features...")
        search_bar.setFixedHeight(36)
        search_bar.setStyleSheet(
            "font-size: 16px; padding: 6px 12px; border-radius: 8px;"
        )
        layout.addWidget(search_bar)

        # Grid of tool buttons
        grid = QGridLayout()
        grid.setSpacing(32)
        tools = [
            ("CAD", "📐"),
            ("BCF", "📊"),
            ("DCF", "📈"),
            ("Simulator", "🖥️"),
            ("Reports", "📑"),
            ("Settings", "⚙️"),
        ]
        for i, (name, icon) in enumerate(tools):
            btn = QToolButton()
            btn.setText(name)
            btn.setIcon(QIcon())  # Replace with QIcon(path) for real icons
            btn.setIconSize(QSize(48, 48))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("font-size: 16px; padding: 12px; border-radius: 12px;")
            # For emoji icons, set as text if no QIcon is available
            if not btn.icon().isNull():
                pass
            else:
                btn.setText(f"{icon}\n{name}")
            grid.addWidget(btn, i // 3, i % 3)
        layout.addLayout(grid)
