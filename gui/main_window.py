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

        # Add widgets to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

        # Set initial state
        self.current_app = None
        self.switch_app(0)  # Start with CAD app

    def add_app_button(self, name, icon, index):
        button = QPushButton(icon)
        button.setCheckable(True)
        button.setFixedSize(40, 40)
        button.setToolTip(name)
        button.clicked.connect(lambda: self.switch_app(index))
        self.app_buttons[name] = button
        self.sidebar.layout().addWidget(button)

    def switch_app(self, index):
        # Update button states
        for button in self.app_buttons.values():
            button.setChecked(False)
        list(self.app_buttons.values())[index].setChecked(True)

        # Switch content
        self.content_area.setCurrentIndex(index)
        self.current_app = index
