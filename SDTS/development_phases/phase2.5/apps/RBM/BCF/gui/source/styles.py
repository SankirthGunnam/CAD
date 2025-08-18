import os
import sys


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_stylesheet():
    """Load the stylesheet from CSS file or fall back to embedded styles"""
    css_path = get_resource_path("gui/assets/styles.css")

    # Try to load from file first
    if os.path.exists(css_path):
        try:
            with open(css_path, "r") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading CSS file: {e}")

    # Fall back to embedded styles if file not found
    return dark_theme


# Embedded styles as fallback
dark_theme = """
QMainWindow {
    background-color: #121212;
    padding: 10px;
}

QToolBar {
    background-color: #1e1e1e;
    border: none;
    border-radius: 10px;
    padding: 5px;
    alignment: center;
}

QPushButton {
    background-color: #2e2e2e;
    color: #ffffff;
    border: 1px solid #3e3e3e;
    border-radius: 8px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #3e3e3e;
}

QPushButton:pressed {
    background-color: #555555;
}

QGraphicsView {
    border: none;
    background-color: #121212;
    padding: 10px;
}

QGraphicsItem {
    color: #ffffff;
}

QGraphicsItem:selected {
    border: 1px solid #ffffff;
}
"""

# Apply with: app.setStyleSheet(dark_theme)
