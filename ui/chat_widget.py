"""
KOMALAM Chat Widget
Scrollable message area with styled bubbles and an input bar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QPushButton, QTextEdit, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeyEvent
from datetime import datetime


class MessageBubble(QFrame):
    """Single chat message bubble."""

    def __init__(self, text: str, role: str = "user", timestamp: str = None, parent=None):
        super().__init__(parent)
        self.role = role
        self.setObjectName("user_bubble" if role == "user" else "assistant_bubble")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.text_label = QLabel(text)
        self.text_label.setObjectName("bubble_text")
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.text_label)

        ts = timestamp or datetime.now().strftime("%I:%M %p")
        time_label = QLabel(ts)
        time_label.setObjectName("bubble_time")
        layout.addWidget(
            time_label,
            alignment=Qt.AlignRight if role == "user" else Qt.AlignLeft,
        )

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def update_text(self, text: str):
        self.text_label.setText(text)


class ChatInput(QTextEdit):
    """Text input that sends on Enter, inserts newline on Shift+Enter."""

    submit_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Type your message...")
        self.setMaximumHeight(120)
        self.setMinimumHeight(44)
        self.setAcceptRichText(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit_pressed.emit()
        else:
            super().keyPressEvent(event)


class ChatWidget(QWidget):
    """Main chat area: scrollable message list + input bar."""

    message_sent = pyqtSignal(str)

    # Throttle scroll-to-bottom during streaming to avoid flooding the event loop
    _SCROLL_INTERVAL_MS = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self._streaming_bubble = None
        self._scroll_pending = False
        self._setup_ui()

        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._do_scroll)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Message area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(16, 16, 16, 16)
        self.messages_layout.setSpacing(12)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Input bar
        input_frame = QFrame()
        input_frame.setStyleSheet("border-top: 1px solid palette(mid);")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(12)

        self.input_field = ChatInput()
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("➤")
        self.send_button.setObjectName("send_button")
        self.send_button.setToolTip("Send message (Enter)")
        self.send_button.setCursor(Qt.PointingHandCursor)
        input_layout.addWidget(self.send_button, alignment=Qt.AlignBottom)

        layout.addWidget(input_frame)

        self.send_button.clicked.connect(self._on_send)
        self.input_field.submit_pressed.connect(self._on_send)

    def _on_send(self):
        text = self.input_field.toPlainText().strip()
        if text:
            self.input_field.clear()
            self.message_sent.emit(text)

    def _request_scroll(self):
        """Schedule a scroll-to-bottom, coalescing rapid calls."""
        if not self._scroll_timer.isActive():
            self._scroll_timer.start(self._SCROLL_INTERVAL_MS)

    def _do_scroll(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_message(self, text: str, role: str = "user", timestamp: str = None) -> MessageBubble:
        bubble = MessageBubble(text, role, timestamp)

        wrapper = QHBoxLayout()
        if role == "user":
            wrapper.addStretch()
            wrapper.addWidget(bubble, stretch=0)
        else:
            wrapper.addWidget(bubble, stretch=0)
            wrapper.addStretch()

        count = self.messages_layout.count()
        self.messages_layout.insertLayout(count - 1, wrapper)

        # Scroll after the layout pass completes
        QApplication.processEvents()
        self._do_scroll()

        return bubble

    def start_streaming(self) -> MessageBubble:
        """Create an empty assistant bubble to stream tokens into."""
        self._streaming_bubble = self.add_message("", role="assistant")
        return self._streaming_bubble

    def append_token(self, token: str):
        if self._streaming_bubble:
            current = self._streaming_bubble.text_label.text()
            self._streaming_bubble.update_text(current + token)
            self._request_scroll()

    def finish_streaming(self):
        self._streaming_bubble = None

    def show_thinking(self):
        if self._streaming_bubble:
            self._streaming_bubble.update_text("🤔 Thinking...")

    def clear_thinking(self):
        if self._streaming_bubble:
            self._streaming_bubble.update_text("")

    def clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def set_input_enabled(self, enabled: bool):
        self.input_field.setEnabled(enabled)
        self.send_button.setEnabled(enabled)

    def show_welcome(self):
        self.add_message(
            "👋 Welcome to KOMALAM!\n\n"
            "I'm your local AI assistant — everything runs privately on your machine.\n\n"
            "Ask me anything to get started!",
            role="assistant",
        )
