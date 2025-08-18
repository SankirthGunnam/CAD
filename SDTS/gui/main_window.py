from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from apps.RBM.BCF.gui.source.legacy_bcf.home_screen import HomeScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTS - System Design Tool Suite")
        self.setMinimumSize(1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(50)
        self.sidebar.setStyleSheet(
            """
            QFrame {
                background-color: #252526;
                border-right: 1px solid #1e1e1e;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                margin: 4px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2a2d2e;
            }
            QPushButton:checked {
                background-color: #37373d;
            }
        """
        )

        # Create sidebar layout
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setAlignment(Qt.AlignTop)

        # Add application buttons
        self.app_buttons = {}
        self.add_app_button("CAD", "📐", 0)
        self.add_app_button("BCF", "📊", 1)
        self.add_app_button("DCF", "📈", 2)

        # Add spacer to push buttons to top
        sidebar_layout.addStretch()

        # Create content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(
            """
            QStackedWidget {
                background-color: #1e1e1e;
            }
        """
        )

        # Add HomeScreen as the first page
        self.home_screen = HomeScreen()
        self.content_area.addWidget(self.home_screen)
        # TODO: Add other app widgets here, e.g. self.content_area.addWidget(CADWidget())

        # Add widgets to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

        # Set initial state
        self.current_app = None
        self.switch_app(0)  # Start with HomeScreen

    def add_app_button(self, name, icon, index):
        button = QPushButton(icon)
        button.setCheckable(True)
        button.setFixedSize(40, 40)
        button.setToolTip(name)
        button.clicked.connect(
            lambda: self.switch_app(index + 1)
        )  # +1 to skip HomeScreen
        self.app_buttons[name] = button
        self.sidebar.layout().addWidget(button)

    def switch_app(self, index):
        # Update button states
        for button in self.app_buttons.values():
            button.setChecked(False)
        if index > 0:
            list(self.app_buttons.values())[index - 1].setChecked(True)

        # Switch content
        self.content_area.setCurrentIndex(index)
        self.current_app = index
