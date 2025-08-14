import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Suppress Qt platform warnings
os.environ.setdefault('QT_LOGGING_RULES', 'qt.qpa.*=false;*.debug=false')

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
logger.debug(f"Added {current_dir} to Python path")

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QToolBar,
)
from PySide6.QtGui import QAction

logger.debug("Imported Qt modules")

try:
    from apps.RBM.BCF.src.RBM_Main import RBMMain

    logger.debug("Imported RBMMain")
except Exception as e:
    logger.error(f"Error importing RBMMain: {e}")
    raise


class SDTSMainWindow(QMainWindow):
    """Main window for SDTS that hosts various tools including RBM"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDTS - Schematic Design Tool Suite")
        self.setMinimumSize(1200, 800)

        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)

        try:
            # Create RBM main window
            self.rbm = RBMMain()
            self.stacked_widget.addWidget(self.rbm)

            # Add RBM action to toolbar
            rbm_action = QAction("RBM", self)
            rbm_action.triggered.connect(
                lambda: self.stacked_widget.setCurrentWidget(self.rbm)
            )
            self.toolbar.addAction(rbm_action)

            logger.debug("Created RBM main window")
        except Exception as e:
            logger.error(f"Error creating RBM main window: {e}")
            raise


def main():
    """Main entry point for the SDTS application"""
    try:
        app = QApplication(sys.argv)
        window = SDTSMainWindow()
        window.show()
        logger.debug("Showing main window")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
