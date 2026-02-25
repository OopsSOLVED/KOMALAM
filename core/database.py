"""
KOMALAM Database Layer
SQLite storage for conversations and messages, with FTS5 full-text search.
"""

import sqlite3
import os
import uuid
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "komalam.db")


class Database:
    """SQLite database manager for chat storage and search."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # TODO: consider a connection-per-thread pool if we ever go multi-threaded on writes
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                embedding_id INTEGER DEFAULT -1,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS memory_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
            CREATE INDEX IF NOT EXISTS idx_memory_tags_tag ON memory_tags(tag);
        """)

        # FTS5 virtual table for full-text search
        try:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content,
                    content_rowid='rowid',
                    tokenize='porter'
                );
            """)
        except sqlite3.OperationalError:
            pass  # already exists or FTS5 not compiled in

        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  Conversations                                                      #
    # ------------------------------------------------------------------ #

    def create_conversation(self, title: str = "New Chat") -> str:
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now),
        )
        self.conn.commit()
        return conv_id

    def get_conversations(self, limit: int = 50) -> list[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_conversation_title(self, conv_id: str, title: str):
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conv_id),
        )
        self.conn.commit()

    def delete_conversation(self, conv_id: str):
        self.conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  Messages                                                           #
    # ------------------------------------------------------------------ #

    def add_message(self, conversation_id: str, role: str, content: str, embedding_id: int = -1) -> str:
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO messages (id, conversation_id, role, content, timestamp, embedding_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, now, embedding_id),
        )
        self.conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )

        # Keep FTS index in sync
        try:
            self.conn.execute(
                "INSERT INTO messages_fts (rowid, content) VALUES (last_insert_rowid(), ?)",
                (content,),
            )
        except sqlite3.OperationalError:
            log.debug("FTS insert skipped (table may not exist)")

        self.conn.commit()
        return msg_id

    def get_messages(self, conversation_id: str) -> list[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_messages(self, limit: int = 1000) -> list[dict]:
        """All messages across conversations (used for bulk memory re-indexing)."""
        cursor = self.conn.execute(
            "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_message_embedding(self, msg_id: str, embedding_id: int):
        self.conn.execute(
            "UPDATE messages SET embedding_id = ? WHERE id = ?",
            (embedding_id, msg_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    #  Search                                                             #
    # ------------------------------------------------------------------ #

    def search_messages(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search messages using FTS5 when available, falling back to LIKE.
        """
        # Try FTS5 first — much faster on larger datasets
        try:
            cursor = self.conn.execute(
                """
                SELECT m.*, c.title as conversation_title
                FROM messages_fts fts
                JOIN messages m ON m.rowid = fts.rowid
                JOIN conversations c ON m.conversation_id = c.id
                WHERE messages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            )
            results = [dict(row) for row in cursor.fetchall()]
            if results:
                return results
        except sqlite3.OperationalError:
            pass  # FTS5 table missing or query syntax issue

        # Fallback: plain LIKE
        cursor = self.conn.execute(
            """
            SELECT m.*, c.title as conversation_title
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.content LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT ?
            """,
            (f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def search_conversations(self, query: str, limit: int = 20) -> list[dict]:
        cursor = self.conn.execute(
            """
            SELECT DISTINCT c.*
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.title LIKE ? OR m.content LIKE ?
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------ #
    #  Memory Tags                                                        #
    # ------------------------------------------------------------------ #

    def add_tag(self, message_id: str, tag: str):
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO memory_tags (message_id, tag, created_at) VALUES (?, ?, ?)",
            (message_id, tag, now),
        )
        self.conn.commit()

    def remove_tag(self, message_id: str, tag: str):
        self.conn.execute(
            "DELETE FROM memory_tags WHERE message_id = ? AND tag = ?",
            (message_id, tag),
        )
        self.conn.commit()

    def get_tagged_messages(self, tag: Optional[str] = None) -> list[dict]:
        if tag:
            cursor = self.conn.execute(
                """
                SELECT m.*, mt.tag FROM messages m
                JOIN memory_tags mt ON m.id = mt.message_id
                WHERE mt.tag = ?
                ORDER BY m.timestamp DESC
                """,
                (tag,),
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT m.*, mt.tag FROM messages m
                JOIN memory_tags mt ON m.id = mt.message_id
                ORDER BY m.timestamp DESC
                """
            )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_tags(self) -> list[str]:
        cursor = self.conn.execute("SELECT DISTINCT tag FROM memory_tags ORDER BY tag")
        return [row["tag"] for row in cursor.fetchall()]

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def auto_title_conversation(self, conv_id: str, first_message: str):
        """Set the conversation title from the first user message (truncated)."""
        title = first_message[:60].strip()
        if len(first_message) > 60:
            title += "…"
        self.update_conversation_title(conv_id, title)

    def close(self):
        self.conn.close()
