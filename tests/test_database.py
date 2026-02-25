"""Tests for core.database module."""

import os
import tempfile
import pytest

# Ensure project root is importable
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database


@pytest.fixture
def db(tmp_path):
    """Provide a fresh database in a temp directory."""
    db_path = os.path.join(str(tmp_path), "test.db")
    _db = Database(db_path=db_path)
    yield _db
    _db.close()


class TestConversations:
    def test_create_and_retrieve(self, db):
        conv_id = db.create_conversation("Test Chat")
        conv = db.get_conversation(conv_id)
        assert conv is not None
        assert conv["title"] == "Test Chat"

    def test_list_ordered_by_updated(self, db):
        id1 = db.create_conversation("First")
        id2 = db.create_conversation("Second")
        convs = db.get_conversations()
        # Most recently created should come first
        assert convs[0]["id"] == id2

    def test_delete(self, db):
        conv_id = db.create_conversation()
        db.delete_conversation(conv_id)
        assert db.get_conversation(conv_id) is None

    def test_update_title(self, db):
        conv_id = db.create_conversation("Old Title")
        db.update_conversation_title(conv_id, "New Title")
        assert db.get_conversation(conv_id)["title"] == "New Title"

    def test_auto_title_truncates(self, db):
        conv_id = db.create_conversation()
        long_msg = "A" * 100
        db.auto_title_conversation(conv_id, long_msg)
        conv = db.get_conversation(conv_id)
        assert len(conv["title"]) <= 63  # 60 chars + "…"
        assert conv["title"].endswith("…")


class TestMessages:
    def test_add_and_get(self, db):
        conv_id = db.create_conversation()
        db.add_message(conv_id, "user", "Hello")
        db.add_message(conv_id, "assistant", "Hi there!")
        msgs = db.get_messages(conv_id)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_cascade_delete(self, db):
        conv_id = db.create_conversation()
        db.add_message(conv_id, "user", "test message")
        db.delete_conversation(conv_id)
        # Messages should be gone too (foreign key cascade)
        msgs = db.get_messages(conv_id)
        assert len(msgs) == 0

    def test_embedding_update(self, db):
        conv_id = db.create_conversation()
        msg_id = db.add_message(conv_id, "user", "test")
        db.update_message_embedding(msg_id, 42)
        msgs = db.get_messages(conv_id)
        assert msgs[0]["embedding_id"] == 42


class TestSearch:
    def test_search_messages_like_fallback(self, db):
        conv_id = db.create_conversation("Chat about Python")
        db.add_message(conv_id, "user", "How do I use list comprehensions in Python?")
        db.add_message(conv_id, "assistant", "List comprehensions are a concise way...")
        results = db.search_messages("comprehensions")
        assert len(results) >= 1

    def test_search_conversations(self, db):
        db.create_conversation("Machine Learning Discussion")
        db.create_conversation("Grocery List")
        results = db.search_conversations("Machine")
        assert len(results) == 1
        assert "Machine Learning" in results[0]["title"]

    def test_search_no_results(self, db):
        db.create_conversation("Hello World")
        results = db.search_conversations("nonexistent_query_xyz")
        assert len(results) == 0


class TestTags:
    def test_add_and_get_tag(self, db):
        conv_id = db.create_conversation()
        msg_id = db.add_message(conv_id, "user", "Remember this")
        db.add_tag(msg_id, "important")
        tagged = db.get_tagged_messages("important")
        assert len(tagged) == 1
        assert tagged[0]["tag"] == "important"

    def test_remove_tag(self, db):
        conv_id = db.create_conversation()
        msg_id = db.add_message(conv_id, "user", "test")
        db.add_tag(msg_id, "temp")
        db.remove_tag(msg_id, "temp")
        assert len(db.get_tagged_messages("temp")) == 0

    def test_get_all_tags(self, db):
        conv_id = db.create_conversation()
        msg_id = db.add_message(conv_id, "user", "test")
        db.add_tag(msg_id, "alpha")
        db.add_tag(msg_id, "beta")
        tags = db.get_all_tags()
        assert "alpha" in tags
        assert "beta" in tags
