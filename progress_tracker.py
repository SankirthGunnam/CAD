from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolTip, QScrollArea
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PySide6.QtCore import QRect, QPoint


class ProgressBubble(QWidget):
    """Individual progress bubble with hover tooltip"""

    def __init__(self, title="", completed=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.completed = completed
        self.setFixedSize(40, 40)
        self.setToolTip(title)
        self.setMouseTracking(True)

    def setCompleted(self, completed):
        self.completed = completed
        self.update()

    def setTitle(self, title):
        self.title = title
        self.setToolTip(title)

    def enterEvent(self, event):
        """Show tooltip on hover"""
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self.title)
        super().enterEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw bubble with gradient effect - centered in 40x40 widget
        rect = QRect(5, 5, 30, 30)

        if self.completed:
            # Completed bubble - green gradient
            gradient = QBrush(QColor(76, 175, 80))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(56, 142, 60), 2))
        else:
            # Incomplete bubble - gray gradient
            gradient = QBrush(QColor(240, 240, 240))
            painter.setBrush(gradient)
            painter.setPen(QPen(QColor(200, 200, 200), 2))

        painter.drawEllipse(rect)

        # Draw checkmark for completed bubbles
        if self.completed:
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            # Draw checkmark
            painter.drawLine(15, 20, 18, 23)
            painter.drawLine(18, 23, 25, 16)

        # Draw step number
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        step_num = str(len(self.parent().bubbles) if hasattr(self.parent(), 'bubbles') else "?")
        painter.drawText(rect, Qt.AlignCenter, step_num)


class ProgressArrow(QWidget):
    """Arrow connecting progress bubbles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 40)  # Narrower to connect bubbles seamlessly

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw arrow with better styling
        painter.setPen(QPen(QColor(100, 100, 100), 3))

        # Draw arrow line - centered vertically
        painter.drawLine(0, 20, 15, 20)

        # Draw arrow head
        painter.drawLine(10, 15, 15, 20)
        painter.drawLine(10, 25, 15, 20)


class ProgressTracker(QWidget):
    """Main progress tracker widget with scroll area"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QScrollArea.NoFrame)

        # Create content widget for the progress items
        self.content_widget = QWidget()
        self.layout = QHBoxLayout(self.content_widget)
        self.layout.setContentsMargins(10, 15, 10, 15)  # Reduced margins
        self.layout.setSpacing(0)  # No spacing between elements

        # Set the content widget in scroll area
        self.scroll_area.setWidget(self.content_widget)

        # Create main layout for this widget
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)

        self.bubbles = []
        self.arrows = []
        self.current_step = 0

        # Set minimum height for the widget to make bubbles clearly visible
        self.setMinimumHeight(70)
        self.setMaximumHeight(70)  # Fixed height to prevent vertical expansion

    def addStep(self, title):
        """Add a new step to the progress tracker"""
        # Add arrow if not the first step
        if len(self.bubbles) > 0:
            arrow = ProgressArrow()
            self.arrows.append(arrow)
            self.layout.addWidget(arrow)

        # Add bubble
        bubble = ProgressBubble(title, parent=self.content_widget)
        self.bubbles.append(bubble)
        self.layout.addWidget(bubble)

        # Update layout and ensure the new step is visible
        self.layout.update()
        self.scroll_area.ensureWidgetVisible(bubble)

    def completeCurrentStep(self):
        """Mark current step as completed and move to next"""
        if self.current_step < len(self.bubbles):
            self.bubbles[self.current_step].setCompleted(True)
            self.current_step += 1
            # Scroll to show the current step
            self.scrollToCurrentStep()

    def getCurrentStep(self):
        """Get current step number (0-based)"""
        return self.current_step

    def getTotalSteps(self):
        """Get total number of steps"""
        return len(self.bubbles)

    def reset(self):
        """Reset the progress tracker"""
        # Clear all widgets
        for bubble in self.bubbles:
            self.layout.removeWidget(bubble)
            bubble.deleteLater()
        for arrow in self.arrows:
            self.layout.removeWidget(arrow)
            arrow.deleteLater()

        self.bubbles.clear()
        self.arrows.clear()
        self.current_step = 0

        # Reset scroll position to beginning
        self.scroll_area.horizontalScrollBar().setValue(0)

    def scrollToCurrentStep(self):
        """Scroll to show the current step"""
        if self.current_step < len(self.bubbles):
            self.scroll_area.ensureWidgetVisible(self.bubbles[self.current_step])

    def scrollToEnd(self):
        """Scroll to show the last step"""
        if self.bubbles:
            self.scroll_area.ensureWidgetVisible(self.bubbles[-1])