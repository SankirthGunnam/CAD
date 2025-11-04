import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PySide6.QtCore import Qt, QModelIndex

from apps.RBM5.BCF.source.RBM_Main import RBMMain


class LegacyBCFNavigationTest(QMainWindow):
    """Manual test window for legacy BCF parent/child navigation and breadcrumbs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Legacy BCF Navigation Test")
        self.setMinimumSize(1100, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QLabel("Legacy BCF: Parent → Children navigation with breadcrumbs")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 6px;")
        layout.addWidget(header)

        instructions = QLabel(
            "1) Click 'Show Bands children' to navigate to the children page.\n"
            "2) Breadcrumbs appear ABOVE the tabs in the Legacy pane (not on the children page).\n"
            "3) Click 'Back to Legacy' to view breadcrumbs like 'Legacy > Bands'.\n"
            "4) Click 'Open first child' to open its tab and remain in Legacy view; breadcrumbs should include the child."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        controls = QHBoxLayout()
        self.btn_show_bands = QPushButton("Show Bands children")
        self.btn_open_first = QPushButton("Open first child")
        self.btn_back_legacy = QPushButton("Back to Legacy")
        controls.addWidget(self.btn_show_bands)
        controls.addWidget(self.btn_open_first)
        controls.addWidget(self.btn_back_legacy)
        controls.addStretch(1)
        layout.addLayout(controls)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        self.main_widget = RBMMain()
        layout.addWidget(self.main_widget)

        self.controller = self.main_widget.gui_controller
        self.controller.switch_mode("legacy")

        self.btn_show_bands.clicked.connect(self._on_show_bands)
        self.btn_open_first.clicked.connect(self._on_open_first_child)
        self.btn_back_legacy.clicked.connect(self._on_back_to_legacy)

    def _on_show_bands(self) -> None:
        legacy = self.controller.legacy_manager
        model = legacy.tree_model
        target_name = "Bands"
        for row in range(model.rowCount(QModelIndex())):
            idx = model.index(row, 0, QModelIndex())
            if model.data(idx, Qt.DisplayRole) == target_name:
                legacy._on_tree_item_clicked(idx)
                self.status_label.setText(f"Navigated to children of '{target_name}'")
                return
        self.status_label.setText("Top-level 'Bands' not found")

    def _on_open_first_child(self) -> None:
        model = self.controller.legacy_children_model
        if model is None or model.rowCount() == 0:
            self.status_label.setText("No children loaded; click a parent first")
            return
        idx = model.index(0, 0)
        self.controller._on_legacy_child_clicked(idx)
        name = model.data(idx, Qt.DisplayRole)
        self.status_label.setText(f"Opened tab for '{name}' and returned to legacy view")

    def _on_back_to_legacy(self) -> None:
        self.controller.stacked_widget.setCurrentWidget(self.controller.legacy_manager)
        self.status_label.setText("Returned to legacy view")


def main() -> int:
    app = QApplication(sys.argv)
    window = LegacyBCFNavigationTest()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())


