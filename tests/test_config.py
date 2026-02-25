"""Tests for core.config_manager module."""

import os
import json
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager, DEFAULT_CONFIG, CONFIG_FILE


@pytest.fixture(autouse=True)
def isolate_config(tmp_path, monkeypatch):
    """Point CONFIG_FILE at a temp directory so tests don't touch real config."""
    tmp_config = os.path.join(str(tmp_path), "config.json")
    monkeypatch.setattr("core.config_manager.CONFIG_FILE", tmp_config)
    yield tmp_config


class TestConfigManager:
    def test_creates_default_config(self, isolate_config):
        cm = ConfigManager()
        assert os.path.exists(isolate_config)
        assert cm.get("model") == "llama3.2"
        assert cm.get("theme") == "dark"

    def test_set_and_persist(self, isolate_config):
        cm = ConfigManager()
        cm.set("temperature", 1.2)
        # Read back from disk
        with open(isolate_config) as f:
            data = json.load(f)
        assert data["temperature"] == 1.2

    def test_get_with_default(self, isolate_config):
        cm = ConfigManager()
        assert cm.get("nonexistent_key", 42) == 42

    def test_merge_with_saved(self, isolate_config):
        # Write a partial config (simulating an older version)
        with open(isolate_config, "w") as f:
            json.dump({"model": "custom-model", "theme": "light"}, f)

        cm = ConfigManager()
        # Saved values should win
        assert cm.get("model") == "custom-model"
        assert cm.get("theme") == "light"
        # Missing keys should come from defaults
        assert cm.get("temperature") == DEFAULT_CONFIG["temperature"]

    def test_reset_restores_defaults(self, isolate_config):
        cm = ConfigManager()
        cm.set("temperature", 999)
        cm.reset()
        assert cm.get("temperature") == DEFAULT_CONFIG["temperature"]

    def test_get_all_returns_copy(self, isolate_config):
        cm = ConfigManager()
        all_config = cm.get_all()
        all_config["model"] = "tampered"
        # Original should be unaffected
        assert cm.get("model") != "tampered"

    def test_corrupt_config_falls_back(self, isolate_config):
        with open(isolate_config, "w") as f:
            f.write("not valid json {{{")
        cm = ConfigManager()
        # Should fall back to defaults without crashing
        assert cm.get("model") == DEFAULT_CONFIG["model"]
