"""
KOMALAM Settings Dialog
Theme, model parameters, GPU info, and memory management.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QPushButton, QGroupBox, QFormLayout, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, config: dict, gpu_info: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KOMALAM Settings")
        self.setMinimumSize(520, 480)
        self.config = config
        self.gpu_info = gpu_info or {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        tabs = QTabWidget()
        tabs.addTab(self._create_appearance_tab(), "🎨 Appearance")
        tabs.addTab(self._create_model_tab(), "🧠 Model")
        tabs.addTab(self._create_gpu_tab(), "⚡ Hardware")
        tabs.addTab(self._create_memory_tab(), "💾 Memory")
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(reset_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _create_appearance_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.config.get("theme", "dark"))
        layout.addRow("Theme:", self.theme_combo)

        return widget

    def _create_model_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self.temp_slider = QDoubleSpinBox()
        self.temp_slider.setRange(0.0, 2.0)
        self.temp_slider.setSingleStep(0.1)
        self.temp_slider.setValue(self.config.get("temperature", 0.7))
        layout.addRow("Temperature:", self.temp_slider)

        temp_hint = QLabel("Lower = more focused, Higher = more creative")
        temp_hint.setStyleSheet("font-size: 11px; color: #888;")
        layout.addRow("", temp_hint)

        self.ctx_spin = QSpinBox()
        self.ctx_spin.setRange(512, 32768)
        self.ctx_spin.setSingleStep(512)
        self.ctx_spin.setValue(self.config.get("context_window", 4096))
        layout.addRow("Context Window:", self.ctx_spin)

        self.memory_k_spin = QSpinBox()
        self.memory_k_spin.setRange(1, 20)
        self.memory_k_spin.setValue(self.config.get("max_memory_results", 5))
        layout.addRow("Memory Results (RAG):", self.memory_k_spin)

        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlainText(self.config.get("system_prompt", ""))
        self.system_prompt_edit.setMaximumHeight(100)
        layout.addRow("System Prompt:", self.system_prompt_edit)

        return widget

    def _create_gpu_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        info_group = QGroupBox("Detected Hardware")
        info_layout = QVBoxLayout(info_group)

        gpus = self.gpu_info.get("gpus", [])
        if gpus:
            for gpu in gpus:
                vram_gb = round(gpu.get("vram_mb", 0) / 1024, 1)
                label = QLabel(
                    f"• {gpu.get('name', 'Unknown')}  |  "
                    f"{vram_gb}GB VRAM  |  "
                    f"{gpu.get('backend', 'Unknown')} backend  |  "
                    f"Driver: {gpu.get('driver', 'Unknown')}"
                )
                label.setWordWrap(True)
                info_layout.addWidget(label)
        else:
            info_layout.addWidget(QLabel("No GPU detected. Running on CPU."))
        layout.addWidget(info_group)

        form = QFormLayout()
        self.gpu_combo = QComboBox()
        self.gpu_combo.addItems(["auto", "cuda", "directml", "cpu"])
        self.gpu_combo.setCurrentText(self.config.get("gpu_backend", "auto"))
        form.addRow("Compute Backend:", self.gpu_combo)
        layout.addLayout(form)

        layout.addStretch()
        return widget

    def _create_memory_tab(self):
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        self.prune_spin = QSpinBox()
        self.prune_spin.setRange(0, 365)
        self.prune_spin.setValue(self.config.get("auto_prune_days", 0))
        self.prune_spin.setSpecialValueText("Disabled")
        layout.addRow("Auto-prune (days):", self.prune_spin)

        prune_hint = QLabel("Set to 0 to keep all memories forever")
        prune_hint.setStyleSheet("font-size: 11px; color: #888;")
        layout.addRow("", prune_hint)

        clear_btn = QPushButton("🗑  Clear All Memories")
        clear_btn.clicked.connect(self._confirm_clear_memory)
        layout.addRow("", clear_btn)

        return widget

    def _confirm_clear_memory(self):
        reply = QMessageBox.question(
            self,
            "Clear All Memories",
            "This will permanently delete all vector memories.\n"
            "Chat history will be preserved.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings_changed.emit({"action": "clear_memory"})

    def _on_reset(self):
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings_changed.emit({"action": "reset"})
            self.accept()

    def _on_save(self):
        settings = {
            "theme": self.theme_combo.currentText(),
            "gpu_backend": self.gpu_combo.currentText(),
            "temperature": self.temp_slider.value(),
            "context_window": self.ctx_spin.value(),
            "max_memory_results": self.memory_k_spin.value(),
            "auto_prune_days": self.prune_spin.value(),
            "system_prompt": self.system_prompt_edit.toPlainText(),
        }
        self.settings_changed.emit(settings)
        self.accept()
