from analytics import MeetingAnalytics
from knowledge_base import KnowledgeBase


def _analysis(words, tasks, decisions, score, sentiment):
    return {
        "short_summary": f"Summary with {words} words",
        "detailed_summary": "Meeting-specific details",
        "decisions": decisions,
        "tasks": tasks,
        "topics": [{"topic": "planning", "keywords": ["planning"]}],
        "speakers": {"Alex": {"word_count": words}},
        "risks": [],
        "stats": {"speaker_count": 1, "word_count": words, "estimated_duration": 5},
        "sentiment": {"label": sentiment},
        "productivity_score": {"total": score},
    }


def test_selected_meeting_analytics_do_not_include_other_meetings(tmp_path):
    kb = KnowledgeBase(str(tmp_path / "analytics.db"))
    kb.set_actor(2, 4)
    first_id = kb.save(
        "Current meeting",
        "Current transcript",
        _analysis(120, [{"task": "Write notes"}], ["Approve timeline"], 80, "positive"),
    )
    kb.save(
        "Unrelated meeting",
        "Different transcript",
        _analysis(900, [{"task": "Ship product"}, {"task": "Prepare report"}], [], 30, "negative"),
    )

    analytics = MeetingAnalytics(kb)
    selected = analytics.get_dashboard_data(first_id)
    all_meetings = analytics.get_dashboard_data()

    assert selected["overview"]["total"] == 1
    assert selected["overview"]["total_tasks"] == 1
    assert selected["overview"]["avg_words"] == 120
    assert selected["overview"]["avg_productivity"] == 80
    assert selected["sentiment_distribution"] == {"positive": 1}
    assert selected["action_trend"][0]["title"] == "Current meeting"
    assert all_meetings["overview"]["total"] == 2
