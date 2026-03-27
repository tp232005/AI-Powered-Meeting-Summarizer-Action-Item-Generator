"""Debug KB test"""
import traceback
from knowledge_base import KnowledgeBase

try:
    kb = KnowledgeBase(":memory:")
    print("DB initialized OK")
    mid = kb.save("Test Meeting", "Hello world transcript for testing the knowledge base functionality", {
        "short_summary": "Test summary",
        "detailed_summary": "Detailed test summary",
        "timestamp": "2025-01-01T00:00:00",
        "decisions": ["Decision 1"],
        "tasks": [{"task": "Do something", "assignee": "Team", "deadline": "Friday", "priority": "low"}],
        "stats": {"speaker_count": 2, "word_count": 100},
        "sentiment": {"label": "neutral"},
        "productivity_score": {"total": 50},
    })
    print(f"Saved meeting ID: {mid}")
    meetings = kb.list_meetings()
    print(f"Listed meetings: {len(meetings)}")
    results = kb.search("test")
    print(f"Search results: {len(results)}")
    print("ALL KB TESTS PASSED!")
except Exception as e:
    traceback.print_exc()
