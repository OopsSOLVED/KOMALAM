"""
KOMALAM Configuration Manager
Reads/writes config.json, merging saved values over built-in defaults.
"""

import json
import os
import logging
from typing import Any, Optional

log = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)

DEFAULT_CONFIG: dict[str, Any] = {
    "theme": "dark",
    "model": "llama3.2",
    "gpu_backend": "auto",
    "temperature": 0.7,
    "context_window": 4096,
    "max_memory_results": 5,
    "auto_prune_days": 0,
    "system_prompt": (
        "You are KOMALAM, a helpful and friendly local AI assistant. "
        "You remember past conversations and use them to provide personalized responses. "
        "Be concise, accurate, and helpful."
    ),
}


class ConfigManager:
    """Manages application config with auto-save on every write."""

    def __init__(self):
        self._config: dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                # Merge: defaults first, saved values override
                self._config = {**DEFAULT_CONFIG, **saved}
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Config file corrupt, using defaults: %s", exc)
                self._config = dict(DEFAULT_CONFIG)
        else:
            self._config = dict(DEFAULT_CONFIG)
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
        except OSError as exc:
            log.error("Failed to write config: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self.save()

    def get_all(self) -> dict[str, Any]:
        return dict(self._config)

    def reset(self):
        self._config = dict(DEFAULT_CONFIG)
        self.save()
