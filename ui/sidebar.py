"""
KOMALAM Sidebar
Conversation history, search, model selector.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QComboBox, QFrame,
    QSizePolicy, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal


class Sidebar(QFrame):
    """Left sidebar with conversations, search, and model picker."""

    new_chat_requested = pyqtSignal()
    conversation_selected = pyqtSignal(str)
    conversation_delete_requested = pyqtSignal(str)
    model_changed = pyqtSignal(str)
    search_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(260)
        self.setMaximumWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(12)

        brand = QLabel("🤖 KOMALAM")
        brand.setObjectName("brand_title")
        brand.setAlignment(Qt.AlignCenter)
        layout.addWidget(brand)

        self.new_chat_btn = QPushButton("✦  New Chat")
        self.new_chat_btn.setObjectName("new_chat_button")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.new_chat_requested.emit)
        layout.addWidget(self.new_chat_btn)

        # Model selector
        model_label = QLabel("MODEL")
        model_label.setObjectName("section_title")
        layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setToolTip("Select AI model")
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        # Search
        search_label = QLabel("SEARCH")
        search_label.setObjectName("section_title")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search conversations...")
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input)

        # History
        history_label = QLabel("CONVERSATIONS")
        history_label.setObjectName("section_title")
        layout.addWidget(history_label)

        self.history_list = QListWidget()
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._show_context_menu)
        self.history_list.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self.history_list, stretch=1)

        self.memory_label = QLabel("Memory: 0 entries")
        self.memory_label.setObjectName("section_title")
        self.memory_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.memory_label)

    def _on_model_changed(self, text):
        if text:
            # Strip size suffix, e.g. "llama3.2 (2.0GB)" -> "llama3.2"
            model_name = text.split(" (")[0].strip()
            self.model_changed.emit(model_name)

    def _on_search(self, text):
        self.search_requested.emit(text)

    def _on_item_selected(self, current, previous):
        if current:
            conv_id = current.data(Qt.UserRole)
            if conv_id:
                self.conversation_selected.emit(conv_id)

    def _show_context_menu(self, position):
        item = self.history_list.itemAt(position)
        if not item:
            return
        conv_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        delete_action = QAction("🗑  Delete Conversation", self)
        delete_action.triggered.connect(lambda: self.conversation_delete_requested.emit(conv_id))
        menu.addAction(delete_action)
        menu.exec_(self.history_list.mapToGlobal(position))

    def set_models(self, models: list[dict]):
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for m in models:
            display = f"{m['name']} ({m['size']})" if m.get("size") else m["name"]
            self.model_combo.addItem(display)
        self.model_combo.blockSignals(False)

    def set_current_model(self, model_name: str):
        for i in range(self.model_combo.count()):
            if self.model_combo.itemText(i).startswith(model_name):
                self.model_combo.setCurrentIndex(i)
                break

    def set_conversations(self, conversations: list[dict]):
        self.history_list.blockSignals(True)
        self.history_list.clear()
        for conv in conversations:
            title = conv.get("title", "New Chat")
            updated = conv.get("updated_at", "")[:10]
            item = QListWidgetItem(f"{title}\n{updated}")
            item.setData(Qt.UserRole, conv["id"])
            self.history_list.addItem(item)
        self.history_list.blockSignals(False)

    def select_conversation(self, conv_id: str):
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            if item.data(Qt.UserRole) == conv_id:
                self.history_list.setCurrentItem(item)
                break

    def update_memory_stats(self, count: int):
        self.memory_label.setText(f"Memory: {count} entries")
