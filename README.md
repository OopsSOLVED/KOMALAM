# KOMALAM

A fully local, privacy-first AI chatbot for Windows. Everything runs on your machine — no cloud, no API keys, no telemetry.

Built with [Ollama](https://ollama.com) for LLM inference and PyQt5 for the desktop UI.

## Features

- **100% offline** after initial setup — works without internet
- **RAG memory** — remembers past conversations using FAISS + sentence-transformers
- **GPU acceleration** — auto-detects NVIDIA (CUDA) and AMD (DirectML) hardware
- **Multiple models** — switch between any locally installed Ollama model
- **Full-text search** across conversation history (FTS5)
- **System resource monitor** — live CPU, RAM, and GPU stats in the status bar

## Requirements

- Windows 10/11
- Python 3.10+
- ~4 GB disk space (for the default model + embeddings)
- A GPU is recommended but not required

## Quick Start

**One-time setup** — installs Ollama, creates a venv, pulls the default model, and downloads the embedding model:

```
setup.bat
```

**Launch the app:**

```
launch.bat
```

Or manually:

```bash
venv\Scripts\activate
python main.py
```

## Project Structure

```
├── main.py                 # Entry point
├── config.json             # User-editable settings
├── requirements.txt        # Python dependencies
├── setup.bat               # One-click setup script
├── launch.bat              # One-click launcher
├── Modelfile               # Custom Ollama model definition
├── core/
│   ├── config_manager.py   # Config read/write with defaults merge
│   ├── database.py         # SQLite storage + FTS5 search
│   ├── gpu_detector.py     # NVIDIA/AMD hardware detection
│   ├── llm_engine.py       # Ollama client wrapper + streaming
│   └── memory.py           # FAISS vector store for RAG
├── ui/
│   ├── chat_widget.py      # Chat bubbles + input bar
│   ├── main_window.py      # Application window
│   ├── resource_monitor.py # Status bar system stats
│   ├── settings_dialog.py  # Settings UI
│   ├── sidebar.py          # Conversation list + model picker
│   └── styles.py           # QSS themes (dark + light)
└── tests/
    ├── test_config.py
    └── test_database.py
```

## Configuration

Edit `config.json` or use the in-app Settings dialog (`Ctrl+,`):

| Key | Default | Description |
|-----|---------|-------------|
| `model` | `llama3.2` | Ollama model to use |
| `temperature` | `0.7` | Sampling temperature (0–2) |
| `context_window` | `4096` | Token context window size |
| `max_memory_results` | `5` | Number of RAG memories to retrieve |
| `auto_prune_days` | `0` | Auto-delete memories older than N days (0 = off) |
| `theme` | `dark` | UI theme (`dark` or `light`) |
| `gpu_backend` | `auto` | Compute backend (`auto`, `cuda`, `directml`, `cpu`) |

## Running Tests

```bash
venv\Scripts\activate
python -m pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).
