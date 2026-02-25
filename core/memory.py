"""
KOMALAM Memory Manager — FAISS vector store + sentence-transformers for RAG.
All processing runs locally, zero external API calls.
"""

import os
import json
import logging
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
FAISS_DIR = os.path.join(DATA_DIR, "faiss_index")
META_FILE = os.path.join(FAISS_DIR, "metadata.json")
INDEX_FILE = os.path.join(FAISS_DIR, "index.faiss")

# Lazy-loaded at first use to keep startup fast
faiss = None
SentenceTransformer = None


def _load_deps():
    global faiss, SentenceTransformer
    if faiss is None:
        import faiss as _faiss
        faiss = _faiss
    if SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer as _ST
        SentenceTransformer = _ST


class MemoryManager:
    """
    Long-term memory backed by a FAISS flat-L2 index.

    Each message is embedded with all-MiniLM-L6-v2 (384-dim) and stored
    alongside JSON metadata for retrieval during inference.
    """

    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2

    def __init__(self):
        _load_deps()
        os.makedirs(FAISS_DIR, exist_ok=True)

        self._index = None
        self._metadata: list[dict] = []
        self._model = None
        self._available = True
        self._load_index()

    def _get_model(self):
        """Load the embedding model, trying cached (offline) first."""
        if self._model is not None or not self._available:
            return self._model

        model_name = "all-MiniLM-L6-v2"

        # Prefer local cache so the app works offline after initial setup
        try:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            self._model = SentenceTransformer(model_name, local_files_only=True)
            return self._model
        except OSError:
            pass
        finally:
            os.environ.pop("HF_HUB_OFFLINE", None)
            os.environ.pop("TRANSFORMERS_OFFLINE", None)

        # Fallback: download from HuggingFace
        try:
            self._model = SentenceTransformer(model_name)
        except Exception:
            log.warning(
                "Embedding model unavailable. Run setup.bat with internet to download it."
            )
            self._available = False
            return None

        return self._model

    def _load_index(self):
        if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
            try:
                self._index = faiss.read_index(INDEX_FILE)
                with open(META_FILE, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                log.warning("Corrupted index, rebuilding: %s", exc)
                self._create_empty_index()
        else:
            self._create_empty_index()

    def _create_empty_index(self):
        self._index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
        self._metadata = []

    def _save_index(self):
        try:
            faiss.write_index(self._index, INDEX_FILE)
            with open(META_FILE, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False)
        except OSError as exc:
            log.error("Failed to persist index: %s", exc)

    def _embed(self, text: str) -> Optional[np.ndarray]:
        model = self._get_model()
        if model is None:
            return None
        return model.encode([text], convert_to_numpy=True).astype("float32")

    def add_to_memory(
        self,
        text: str,
        message_id: str = "",
        conversation_id: str = "",
        timestamp: str = "",
        tags: Optional[list[str]] = None,
    ) -> int:
        """Embed and store text. Returns the embedding index, or -1 if skipped."""
        if not text or len(text.strip()) < 5:
            return -1

        embedding = self._embed(text)
        if embedding is None:
            return -1

        embedding_id = self._index.ntotal
        self._index.add(embedding)

        self._metadata.append({
            "text": text,
            "message_id": message_id,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "tags": tags or [],
            "embedding_id": embedding_id,
        })

        self._save_index()
        return embedding_id

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic nearest-neighbour search over stored memories."""
        if self._index.ntotal == 0:
            return []

        query_embedding = self._embed(query)
        if query_embedding is None:
            return []

        k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(query_embedding, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            meta = self._metadata[idx]
            # TODO: add a configurable distance threshold to filter weak matches
            results.append({
                "text": meta["text"],
                "score": float(distances[0][i]),
                "message_id": meta.get("message_id", ""),
                "conversation_id": meta.get("conversation_id", ""),
                "timestamp": meta.get("timestamp", ""),
                "tags": meta.get("tags", []),
            })

        return results

    def build_context(self, query: str, top_k: int = 5) -> str:
        """Format retrieved memories as a context block for the LLM prompt."""
        results = self.retrieve(query, top_k)
        if not results:
            return ""
        return "\n".join(
            f"[Memory {i}] {r['text']}" for i, r in enumerate(results, 1)
        )

    def tag_memory(self, embedding_id: int, tag: str):
        if 0 <= embedding_id < len(self._metadata):
            tags = self._metadata[embedding_id].setdefault("tags", [])
            if tag not in tags:
                tags.append(tag)
                self._save_index()

    def untag_memory(self, embedding_id: int, tag: str):
        if 0 <= embedding_id < len(self._metadata):
            tags = self._metadata[embedding_id].get("tags", [])
            if tag in tags:
                tags.remove(tag)
                self._save_index()

    def prune(self, older_than_days: int = 0) -> int:
        """
        Drop memories older than *older_than_days* and rebuild the index.
        Returns the number of entries removed.
        """
        if older_than_days <= 0 or not self._metadata:
            return 0

        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()

        keep = [m for m in self._metadata if not m.get("timestamp") or m["timestamp"] >= cutoff]
        removed = len(self._metadata) - len(keep)
        if removed == 0:
            return 0

        self._create_empty_index()
        for meta in keep:
            embedding = self._embed(meta["text"])
            meta["embedding_id"] = self._index.ntotal
            self._index.add(embedding)
        self._metadata = keep
        self._save_index()

        log.info("Pruned %d memories older than %d days", removed, older_than_days)
        return removed

    def get_stats(self) -> dict:
        return {
            "total_memories": self._index.ntotal if self._index else 0,
            "index_file_size": (
                os.path.getsize(INDEX_FILE) if os.path.exists(INDEX_FILE) else 0
            ),
        }

    def clear_all(self):
        self._create_empty_index()
        self._save_index()
        log.info("All memories cleared")
