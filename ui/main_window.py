"""
KOMALAM Main Window
Wires UI components to the backend engine.
"""

import os
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QWidget, QVBoxLayout, QAction,
    QMessageBox, QStatusBar, QApplication, QLabel
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from ui.chat_widget import ChatWidget
from ui.sidebar import Sidebar
from ui.settings_dialog import SettingsDialog
from ui.resource_monitor import ResourceMonitor
from ui.styles import DARK_THEME, LIGHT_THEME
from core.config_manager import ConfigManager
from core.llm_engine import OllamaEngine, GenerateWorker
from core.database import Database
from core.gpu_detector import GPUDetector

# Heavy deps loaded lazily so the window appears fast
MemoryManager = None


def _load_memory():
    global MemoryManager
    if MemoryManager is None:
        from core.memory import MemoryManager as _MM
        MemoryManager = _MM


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(_PROJECT_ROOT, "data")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "komalam.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("KOMALAM")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KOMALAM — Local AI Assistant")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        # Backend objects
        self.config = ConfigManager()
        self.db = Database()
        self.gpu_detector = GPUDetector()
        self.gpu_detector.detect()
        self.llm = OllamaEngine()
        self.memory = None
        self._current_conv_id = None
        self._worker = None

        self._apply_theme(self.config.get("theme", "dark"))

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

        # Defer heavy init so the window paints immediately
        QTimer.singleShot(500, self._connect_ollama)
        QTimer.singleShot(1000, self._init_memory)

        self._refresh_conversations()
        log.info("Application started")

    # ------------------------------------------------------------------ #
    #  UI Setup                                                           #
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        self.sidebar = Sidebar()
        self.sidebar.new_chat_requested.connect(self._new_chat)
        self.sidebar.conversation_selected.connect(self._load_conversation)
        self.sidebar.conversation_delete_requested.connect(self._delete_conversation)
        self.sidebar.model_changed.connect(self._change_model)
        self.sidebar.search_requested.connect(self._search_conversations)
        splitter.addWidget(self.sidebar)

        self.chat = ChatWidget()
        self.chat.message_sent.connect(self._on_user_message)
        splitter.addWidget(self.chat)

        splitter.setSizes([280, 920])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        new_action = QAction("New Chat", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_chat)
        file_menu.addAction(new_action)
        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        menubar.addAction(settings_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About KOMALAM", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.model_status = QLabel("Connecting...")
        self.status_bar.addWidget(self.model_status)

        spacer = QWidget()
        spacer.setFixedWidth(20)
        self.status_bar.addWidget(spacer)

        self.resource_monitor = ResourceMonitor(self.gpu_detector)
        self.status_bar.addPermanentWidget(self.resource_monitor)

    def _apply_theme(self, theme: str):
        if theme == "light":
            QApplication.instance().setStyleSheet(LIGHT_THEME)
        else:
            QApplication.instance().setStyleSheet(DARK_THEME)

    # ------------------------------------------------------------------ #
    #  Backend init                                                       #
    # ------------------------------------------------------------------ #

    def _connect_ollama(self):
        try:
            self.llm.connect()
            models = self.llm.list_models()
            if models:
                self.sidebar.set_models(models)

                # Use configured model if available, otherwise take the first one
                model = self.config.get("model", "llama3.2")
                available = [m["name"] for m in models]
                if model not in available:
                    model = available[0]
                    self.config.set("model", model)

                self.llm.set_model(model)
                self.llm.set_options(
                    context_window=self.config.get("context_window", 4096),
                    temperature=self.config.get("temperature", 0.7),
                )
                self.sidebar.set_current_model(model)
                self.model_status.setText(f"✅ Model: {model}")
            else:
                self.model_status.setText("⚠ No models found — run: ollama pull llama3.2")

            log.info("Connected to Ollama, model=%s", self.llm.current_model)
        except RuntimeError as exc:
            self.model_status.setText("❌ Ollama not connected")
            log.error("Ollama connection failed: %s", exc)
            QMessageBox.warning(
                self,
                "Ollama Not Found",
                f"Could not connect to Ollama.\n\n{exc}\n\n"
                "Please run setup.bat first, or install Ollama from ollama.com",
            )

    def _init_memory(self):
        """Load the RAG memory system (deferred because it pulls in torch + transformers)."""
        try:
            _load_memory()
            self.memory = MemoryManager()
            stats = self.memory.get_stats()
            self.sidebar.update_memory_stats(stats["total_memories"])
            log.info("Memory system ready (%d entries)", stats["total_memories"])
        except Exception as exc:
            log.error("Memory init failed: %s", exc)
            self.memory = None

    # ------------------------------------------------------------------ #
    #  Chat                                                               #
    # ------------------------------------------------------------------ #

    def _new_chat(self):
        self._current_conv_id = None
        self.chat.clear_messages()
        self.chat.show_welcome()
        self.sidebar.history_list.clearSelection()

    def _on_user_message(self, text: str):
        if self._current_conv_id is None:
            self._current_conv_id = self.db.create_conversation()
            self.db.auto_title_conversation(self._current_conv_id, text)
            self._refresh_conversations()

        self.chat.add_message(text, role="user")

        msg_id = self.db.add_message(self._current_conv_id, "user", text)

        if self.memory:
            try:
                emb_id = self.memory.add_to_memory(
                    text,
                    message_id=msg_id,
                    conversation_id=self._current_conv_id,
                    timestamp=datetime.now().isoformat(),
                )
                self.db.update_message_embedding(msg_id, emb_id)
            except Exception as exc:
                log.warning("Memory store failed for user msg: %s", exc)

        self._generate_response(text)

    def _generate_response(self, user_text: str):
        self.chat.set_input_enabled(False)

        context = ""
        if self.memory:
            try:
                context = self.memory.build_context(
                    user_text,
                    top_k=self.config.get("max_memory_results", 5),
                )
            except Exception as exc:
                log.warning("Memory retrieval failed: %s", exc)

        self.chat.start_streaming()

        system_prompt = self.config.get("system_prompt", "")
        self._worker = GenerateWorker(self.llm, user_text, context, system_prompt)
        self._worker.token_received.connect(self.chat.append_token)
        self._worker.thinking_started.connect(self._on_thinking_started)
        self._worker.thinking_finished.connect(self._on_thinking_finished)
        self._worker.generation_complete.connect(self._on_generation_complete)
        self._worker.error_occurred.connect(self._on_generation_error)
        self._worker.start()

    def _on_thinking_started(self):
        self.chat.show_thinking()

    def _on_thinking_finished(self):
        self.chat.clear_thinking()

    def _on_generation_complete(self, full_response: str):
        self.chat.finish_streaming()
        self.chat.set_input_enabled(True)

        if self._current_conv_id and full_response:
            msg_id = self.db.add_message(
                self._current_conv_id, "assistant", full_response
            )
            if self.memory:
                try:
                    emb_id = self.memory.add_to_memory(
                        full_response,
                        message_id=msg_id,
                        conversation_id=self._current_conv_id,
                        timestamp=datetime.now().isoformat(),
                    )
                    self.db.update_message_embedding(msg_id, emb_id)
                    stats = self.memory.get_stats()
                    self.sidebar.update_memory_stats(stats["total_memories"])
                except Exception as exc:
                    log.warning("Memory store failed for assistant msg: %s", exc)

        self._refresh_conversations()
        self._worker = None

    def _on_generation_error(self, error: str):
        self.chat.finish_streaming()
        self.chat.set_input_enabled(True)
        self.chat.add_message(f"⚠ Error: {error}", role="assistant")
        log.error("Generation error: %s", error)
        self._worker = None

    # ------------------------------------------------------------------ #
    #  Conversation management                                            #
    # ------------------------------------------------------------------ #

    def _load_conversation(self, conv_id: str):
        self._current_conv_id = conv_id
        self.chat.clear_messages()

        messages = self.db.get_messages(conv_id)
        for msg in messages:
            ts = msg.get("timestamp", "")[:16].replace("T", " ")
            self.chat.add_message(msg["content"], role=msg["role"], timestamp=ts)

    def _delete_conversation(self, conv_id: str):
        reply = QMessageBox.question(
            self, "Delete Conversation",
            "Delete this conversation permanently?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.db.delete_conversation(conv_id)
            if self._current_conv_id == conv_id:
                self._new_chat()
            self._refresh_conversations()

    def _refresh_conversations(self):
        convs = self.db.get_conversations()
        self.sidebar.set_conversations(convs)
        if self._current_conv_id:
            self.sidebar.select_conversation(self._current_conv_id)

    def _search_conversations(self, query: str):
        if query.strip():
            convs = self.db.search_conversations(query)
        else:
            convs = self.db.get_conversations()
        self.sidebar.set_conversations(convs)

    def _change_model(self, model_name: str):
        self.llm.set_model(model_name)
        self.llm.set_options(
            context_window=self.config.get("context_window", 4096),
            temperature=self.config.get("temperature", 0.7),
        )
        self.config.set("model", model_name)
        self.model_status.setText(f"✅ Model: {model_name}")
        log.info("Switched model to %s", model_name)

    # ------------------------------------------------------------------ #
    #  Settings                                                           #
    # ------------------------------------------------------------------ #

    def _open_settings(self):
        dialog = SettingsDialog(
            self.config.get_all(),
            self.gpu_detector.get_gpu_info(),
            self,
        )
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec_()

    def _apply_settings(self, settings: dict):
        if settings.get("action") == "clear_memory":
            if self.memory:
                self.memory.clear_all()
                self.sidebar.update_memory_stats(0)
            return

        if settings.get("action") == "reset":
            self.config.reset()
            self._apply_theme("dark")
            return

        for key, value in settings.items():
            self.config.set(key, value)

        if "theme" in settings:
            self._apply_theme(settings["theme"])

        if "context_window" in settings or "temperature" in settings:
            self.llm.set_options(
                context_window=self.config.get("context_window", 4096),
                temperature=self.config.get("temperature", 0.7),
            )

    def _show_about(self):
        QMessageBox.about(
            self,
            "About KOMALAM",
            "<h2>🤖 KOMALAM v1.0</h2>"
            "<p>A fully local, privacy-first AI chatbot.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>100% offline — no cloud, no API calls</li>"
            "<li>Persistent memory with RAG</li>"
            "<li>NVIDIA & AMD GPU support</li>"
            "</ul>"
            "<p>All your data stays on your machine.</p>",
        )

    # ------------------------------------------------------------------ #
    #  Shutdown                                                           #
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        log.info("Shutting down")
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
        if self.resource_monitor:
            self.resource_monitor.stop()
        self.db.close()
        event.accept()
