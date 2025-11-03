import sys
from PySide6.QtCore import Qt, QPoint, QRect, QSize, Signal
from PySide6.QtGui import QIcon, QMouseEvent, QPainter, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QToolButton, QHBoxLayout,
    QVBoxLayout, QSizeGrip, QPushButton, QStyle, QFrame
)

IS_WINDOWS = sys.platform.startswith("win32")

# ---------- Custom Title Bar ----------
class TitleBar(QFrame):
    # Simple signal to initiate a system move from the parent
    requestSystemMove = Signal(object)   # emits QMouseEvent
    requestDoubleClick = Signal()
    requestContextMenu = Signal(object)  # emits QPoint (global)

    def __init__(self, parent=None, *, bg="#202937", fg="#FFFFFF"):
        super().__init__(parent)
        self.setObjectName("CustomTitleBar")
        self.setAutoFillBackground(True)
        self.bg = bg
        self.fg = fg
        self.setFixedHeight(40)

        # Left: window icon + title
        self.iconLabel = QLabel()
        self.iconLabel.setFixedSize(20, 20)
        self.titleLabel = QLabel("Custom Window")
        self.titleLabel.setStyleSheet(f"color:{self.fg}; font-weight:600;")

        left = QHBoxLayout()
        left.setContentsMargins(10, 0, 0, 0)
        left.setSpacing(8)
        left.addWidget(self.iconLabel)
        left.addWidget(self.titleLabel)
        left.addStretch(1)

        # Right: window buttons
        self.minBtn = QToolButton()
        self.maxBtn = QToolButton()
        self.closeBtn = QToolButton()
        for b in (self.minBtn, self.maxBtn, self.closeBtn):
            b.setCursor(Qt.ArrowCursor)
            b.setAutoRaise(True)
            b.setIconSize(QSize(14, 14))
            b.setStyleSheet("QToolButton{color:%s;}" % self.fg)

        style = self.style()
        self.minBtn.setIcon(style.standardIcon(QStyle.SP_TitleBarMinButton))
        self.maxBtn.setIcon(style.standardIcon(QStyle.SP_TitleBarMaxButton))
        self.closeBtn.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))

        right = QHBoxLayout()
        right.setContentsMargins(0, 0, 6, 0)
        right.setSpacing(2)
        right.addWidget(self.minBtn)
        right.addWidget(self.maxBtn)
        right.addWidget(self.closeBtn)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(left, 1)
        root.addLayout(right, 0)

        self.setStyleSheet(f"""
        QFrame#CustomTitleBar {{
            background: {self.bg};
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        """)

    def setWindowIcon(self, icon: QIcon):
        self.iconLabel.setPixmap(icon.pixmap(20, 20))

    def setWindowTitle(self, title: str):
        self.titleLabel.setText(title)

    # Mouse handling to start system move / support double click, context menu
    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton:
            self.requestSystemMove.emit(ev)
        elif ev.button() == Qt.RightButton:
            self.requestContextMenu.emit(ev.globalPosition().toPoint())
        super().mousePressEvent(ev)

    def mouseDoubleClickEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton:
            self.requestDoubleClick.emit()
        super().mouseDoubleClickEvent(ev)


# ---------- Main Window with Frameless + Native Hit Test (Windows) ----------
class FramelessMainWindow(QMainWindow):
    BORDER_WIDTH = 8   # resize border thickness (will be scaled for HiDPI)

    def __init__(self):
        super().__init__()
        # Frameless, but keep system menu/min/max hints for OS features.
        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(1000, 650)
        self.setWindowTitle("Custom Window")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        # Title bar
        self.titleBar = TitleBar(self, bg="#1f2937", fg="#e5e7eb")  # Tailwind-ish slate/dove
        self.titleBar.setWindowIcon(self.windowIcon())
        self.titleBar.setWindowTitle(self.windowTitle())
        self.titleBar.minBtn.clicked.connect(self.showMinimized)
        self.titleBar.maxBtn.clicked.connect(self.toggleMaxRestore)
        self.titleBar.closeBtn.clicked.connect(self.close)
        self.titleBar.requestSystemMove.connect(self.beginSystemMove)
        self.titleBar.requestDoubleClick.connect(self.toggleMaxRestore)
        self.titleBar.requestContextMenu.connect(self.showSystemMenu)

        # Simple central content
        central = QWidget()
        central.setStyleSheet("background:#0b1220;")  # content bg
        v = QVBoxLayout(central)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(12)
        intro = QLabel(
            "<h2 style='color:#e5e7eb;margin:0'>Hello 👋</h2>"
            "<div style='color:#cbd5e1'>This window uses a custom title bar and keeps Windows snapping, "
            "dragging between monitors, and resize-from-edges.</div>"
        )
        intro.setTextFormat(Qt.RichText)
        intro.setWordWrap(True)
        v.addWidget(intro, 0)

        # A size grip (optional, still useful at bottom-right)
        grip = QSizeGrip(central)
        grip.setFixedSize(16, 16)
        v.addStretch(1)
        grip_wrap = QHBoxLayout()
        grip_wrap.addStretch(1)
        grip_wrap.addWidget(grip, 0, Qt.AlignBottom | Qt.AlignRight)
        v.addLayout(grip_wrap)

        # Layout: title bar on top, content below
        wrapper = QWidget()
        outer = QVBoxLayout(wrapper)
        outer.setContentsMargins(1, 1, 1, 1)  # subtle outer line
        outer.setSpacing(0)
        outer.addWidget(self.titleBar, 0)
        outer.addWidget(central, 1)

        self.setCentralWidget(wrapper)

        # Keep title bar text/icon in sync if window title/icon changes later
        self.windowTitleChanged.connect(self.titleBar.setWindowTitle)
        self.windowIconChanged.connect(self.titleBar.setWindowIcon)

        # Optional: a simple menu action to test Alt+Space system menu routing.
        act = QAction("Dummy", self)
        act.setShortcut("Ctrl+D")
        act.triggered.connect(lambda: None)
        self.addAction(act)

    # ---------- Title bar helpers ----------
    def toggleMaxRestore(self):
        if self.isMaximized():
            self.showNormal()
            self.titleBar.maxBtn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        else:
            self.showMaximized()
            self.titleBar.maxBtn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))

    def beginSystemMove(self, ev: QMouseEvent):
        """
        Use Qt's native system move to allow dragging across monitors and keep Aero snap.
        """
        if self.windowHandle():
            self.windowHandle().startSystemMove()

    def showSystemMenu(self, global_pos: QPoint):
        """
        On Windows, the OS system menu appears at the given point (Alt+Space equivalent).
        For simplicity, we just pass; Qt/Windows will still handle Alt+Space.
        """
        # You can add a custom right-click menu if you wish.
        pass

    # ---------- Windows native hit testing ----------
    def nativeEvent(self, eventType, message):
        """
        Return proper hit-test results so Windows treats our edges/corners like a normal resizable window.
        This preserves:
          - Edge/corner resizing
          - Maximize on double-click
          - Aero Snap (Win+Arrows), drag-to-top maximize, etc.
        """
        if not IS_WINDOWS:
            return super().nativeEvent(eventType, message)

        from ctypes import windll, POINTER, byref, sizeof, c_long
        from ctypes.wintypes import MSG, RECT, POINT, DWORD, HWND, LPARAM, WPARAM, LRESULT

        msg = MSG.from_address(message.__int__())

        WM_NCHITTEST = 0x0084
        HTNOWHERE = 0
        HTCLIENT = 1
        HTCAPTION = 2
        HTLEFT = 10
        HTRIGHT = 11
        HTTOP = 12
        HTTOPLEFT = 13
        HTTOPRIGHT = 14
        HTBOTTOM = 15
        HTBOTTOMLEFT = 16
        HTBOTTOMRIGHT = 17

        if msg.message == WM_NCHITTEST:
            # Get mouse position in screen coords
            x = c_long(msg.lParam & 0xffff if msg.lParam & 0x8000 == 0 else msg.lParam | ~0xffff).value
            y = c_long((msg.lParam >> 16) & 0xffff if msg.lParam & 0x80000000 == 0 else msg.lParam | ~0xffff0000).value

            # Map to this window
            gp = self.mapFromGlobal(QPoint(x, y))
            rect = self.rect()

            # Scale border for HiDPI
            dpr = self.devicePixelRatioF()
            bw = max(4, int(self.BORDER_WIDTH * dpr))

            # Title area regarded as caption so dragging works
            title_h = self.titleBar.height()

            # Corners
            on_left = gp.x() <= bw
            on_right = gp.x() >= rect.width() - bw
            on_top = gp.y() <= bw
            on_bottom = gp.y() >= rect.height() - bw

            # Edges & corners take priority
            if on_top and on_left:
                return True, HTTOPLEFT
            if on_top and on_right:
                return True, HTTOPRIGHT
            if on_bottom and on_left:
                return True, HTBOTTOMLEFT
            if on_bottom and on_right:
                return True, HTBOTTOMRIGHT
            if on_left:
                return True, HTLEFT
            if on_right:
                return True, HTRIGHT
            if on_top:
                # Still allow dragging from the very top strip
                return True, HTTOP
            if on_bottom:
                return True, HTBOTTOM

            # Inside title bar area -> caption (dragging + double click to maximize)
            if gp.y() <= title_h:
                # But ignore clicks on the buttons area (they should behave like client)
                btns_rect = self._buttonsRectInWindow()
                if not btns_rect.contains(gp):
                    return True, HTCAPTION

            # Otherwise, client area
            return True, HTCLIENT

        return super().nativeEvent(eventType, message)

    def _buttonsRectInWindow(self) -> QRect:
        """Return the rectangle (in window coords) that encloses the three window buttons."""
        # Map titleBar's right container area roughly; simplest is to take the geometry of the whole titlebar
        # minus a fixed width on the left. For precision, map actual buttons.
        g = QRect()
        for b in (self.titleBar.minBtn, self.titleBar.maxBtn, self.titleBar.closeBtn):
            g = g.united(self._mapToWindow(b))
        return g

    def _mapToWindow(self, widget: QWidget) -> QRect:
        top_left = widget.mapTo(self, QPoint(0, 0))
        return QRect(top_left, widget.size())

    # Keep title bar state in sync when maximized/restored (icon toggles)
    def changeEvent(self, ev):
        super().changeEvent(ev)
        if ev.type() == ev.WindowStateChange:
            if self.isMaximized():
                self.titleBar.maxBtn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
            else:
                self.titleBar.maxBtn.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))


def main():
    app = QApplication(sys.argv)
    w = FramelessMainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
