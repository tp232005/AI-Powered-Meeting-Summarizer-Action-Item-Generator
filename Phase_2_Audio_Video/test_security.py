"""Security regression checks for authentication and meeting isolation."""
import os
import tempfile

from auth import AuthManager
from knowledge_base import KnowledgeBase


def _analysis():
    return {
        "timestamp": "2026-09-09T10:00:00",
        "short_summary": "Private meeting",
        "detailed_summary": "Private meeting details",
        "decisions": [],
        "tasks": [],
        "stats": {"speaker_count": 0, "word_count": 4},
        "sentiment": {"label": "neutral"},
        "productivity_score": {"total": 0},
    }


def run_security_checks():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        database_path = os.path.join(directory, "security.db")
        auth = AuthManager(database_path)
        user_a = auth.register("Alice", "alice@example.com", "correct horse battery", "Alpha Org", "Company")
        user_b = auth.register("Bob", "bob@example.com", "correct horse battery", "Beta Org", "Company")
        assert auth.authenticate("alice@example.com", "correct horse battery")["id"] == user_a["id"]
        assert auth.authenticate("alice@example.com", "wrong password") is None

        kb = KnowledgeBase(database_path)
        kb.set_actor(user_a["id"], user_a["organization_id"])
        meeting_id = kb.save("Alice private meeting", "Private transcript for Alice", _analysis())
        assert kb.get(meeting_id)["title"] == "Alice private meeting"

        kb.set_actor(user_b["id"], user_b["organization_id"])
        assert kb.get(meeting_id) is None
        assert kb.list_meetings() == []
        assert kb.search("Alice") == []
        kb.close()

    print("Security checks passed")


if __name__ == "__main__":
    run_security_checks()
