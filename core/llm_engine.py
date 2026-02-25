"""
KOMALAM LLM Engine
Wraps the Ollama Python client for local inference with streaming support.
"""

import re
import subprocess
import time
import logging
from typing import Optional, Iterator

from PyQt5.QtCore import QThread, pyqtSignal

log = logging.getLogger(__name__)

try:
    import ollama
except ImportError:
    ollama = None

# Regex compiled once for stripping <think> blocks from Qwen3-style responses
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class OllamaEngine:
    """Interface to the local Ollama LLM service."""

    def __init__(self):
        self._model = "llama3.2"
        self._client = None
        self._connected = False
        self._options = {"num_ctx": 4096}

    def set_options(self, context_window: int = 4096, temperature: float = 0.7):
        self._options = {
            "num_ctx": context_window,
            "temperature": temperature,
        }

    def connect(self) -> bool:
        if ollama is None:
            raise RuntimeError("ollama package not installed — run: pip install ollama")

        try:
            self._client = ollama.Client()
            self._client.list()
            self._connected = True
            return True
        except Exception:
            pass

        # Ollama isn't running — try starting it
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            time.sleep(3)
            self._client = ollama.Client()
            self._client.list()
            self._connected = True
            return True
        except FileNotFoundError:
            self._connected = False
            raise RuntimeError(
                "Ollama binary not found. Install it from https://ollama.com"
            )
        except Exception as exc:
            self._connected = False
            raise RuntimeError(f"Cannot connect to Ollama: {exc}")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def list_models(self) -> list[dict]:
        if not self._connected:
            return []
        try:
            response = self._client.list()
            models = []
            for model in response.models:
                size_bytes = model.size or 0
                size_gb = round(size_bytes / (1024 ** 3), 1)
                models.append({
                    "name": model.model,
                    "size": f"{size_gb}GB",
                    "modified": str(model.modified_at) if model.modified_at else "",
                })
            return models
        except Exception as exc:
            log.warning("Failed to list models: %s", exc)
            return []

    def set_model(self, model_name: str):
        self._model = model_name

    @property
    def current_model(self) -> str:
        return self._model

    def _build_messages(self, prompt: str, context: str = "", system_prompt: str = "") -> list[dict]:
        """Assemble the messages list sent to Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant context from past conversations:\n{context}",
            })
        messages.append({"role": "user", "content": prompt})
        return messages

    def generate(self, prompt: str, context: str = "", system_prompt: str = "") -> str:
        """Blocking, non-streaming generation. For UI use, prefer GenerateWorker."""
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")

        messages = self._build_messages(prompt, context, system_prompt)
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                options=self._options,
            )
            return response.message.content if response.message else ""
        except Exception as exc:
            raise RuntimeError(f"Generation failed: {exc}")

    def stream_chat(self, prompt: str, context: str = "", system_prompt: str = "") -> Iterator:
        """Return a streaming iterator of chat chunks."""
        if not self._connected:
            raise RuntimeError("Not connected to Ollama")

        messages = self._build_messages(prompt, context, system_prompt)
        return self._client.chat(
            model=self._model,
            messages=messages,
            stream=True,
            options=self._options,
        )


class GenerateWorker(QThread):
    """
    Background thread for streaming LLM responses.
    Handles Qwen3-style <think>…</think> reasoning blocks.
    """

    token_received = pyqtSignal(str)
    thinking_started = pyqtSignal()
    thinking_finished = pyqtSignal()
    generation_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, engine: OllamaEngine, prompt: str, context: str = "", system_prompt: str = ""):
        super().__init__()
        self.engine = engine
        self.prompt = prompt
        self.context = context
        self.system_prompt = system_prompt

    def run(self):
        try:
            stream = self.engine.stream_chat(
                self.prompt, self.context, self.system_prompt
            )
        except RuntimeError as exc:
            self.error_occurred.emit(str(exc))
            return

        raw_stream = ""
        in_think = False
        think_notified = False

        try:
            for chunk in stream:
                token = chunk.message.content if chunk.message else ""
                if not token:
                    continue

                raw_stream += token

                # Detect <think> opening
                if "<think>" in raw_stream and not in_think:
                    in_think = True
                    if not think_notified:
                        self.thinking_started.emit()
                        think_notified = True

                # Detect </think> closing
                if "</think>" in raw_stream and in_think:
                    in_think = False
                    self.thinking_finished.emit()
                    after = raw_stream.split("</think>", 1)[-1]
                    if after.strip():
                        self.token_received.emit(after.strip())
                    continue

                if in_think:
                    continue

                self.token_received.emit(token)

        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return

        # Strip think blocks for storage
        clean = _THINK_RE.sub("", raw_stream).strip()
        self.generation_complete.emit(clean or raw_stream.strip())
