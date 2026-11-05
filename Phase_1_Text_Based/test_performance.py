import json
from pathlib import Path

import nlp_engine
from analytics import MeetingAnalytics
from knowledge_base import KnowledgeBase
from nlp_engine import MeetingAnalyzer
from report_generator import ReportGenerator


def test_analyze_tokenizes_sentences_once(monkeypatch):
    transcript = (
        Path(__file__).parent / "samples" / "sample_meeting.txt"
    ).read_text(encoding="utf-8")
    original_tokenizer = nlp_engine.sent_tokenize
    calls = []

    def track_tokenization(text):
        calls.append(text)
        return original_tokenizer(text)

    monkeypatch.setattr(nlp_engine, "sent_tokenize", track_tokenization)

    result = MeetingAnalyzer().analyze(transcript)

    assert len(calls) == 1
    assert result["short_summary"]
    assert result["detailed_summary"]
    assert result["tasks"]
    assert result["topics"]


def test_saved_analysis_and_analytics_avoid_duplicate_transcript_payload(tmp_path):
    analysis = {
        "short_summary": "The team approved a launch plan.",
        "detailed_summary": "The team approved a launch plan and assigned follow-up.",
        "timestamp": "2025-01-01T10:00:00",
        "decisions": ["Approve the launch plan."],
        "tasks": [{"task": "Prepare the launch brief"}],
        "topics": [{
            "topic": "Launch plan",
            "keywords": ["launch"],
            "sentences": ["First topic sentence.", "Second topic sentence."],
        }],
        "speakers": {"Alex": ["Long speaker transcript text."]},
        "utterances": [{"speaker": "Alex", "speech": "Long speaker transcript text."}],
        "risks": [{"severity": "medium", "keywords": ["deadline"]}],
        "stats": {"speaker_count": 1, "word_count": 130, "estimated_duration": 1},
        "sentiment": {"label": "positive"},
        "productivity_score": {
            "total": 80,
            "grade": "A",
            "label": "Excellent",
            "breakdown": {
                "action_density": 20,
                "decision_ratio": 20,
                "participation_balance": 20,
                "risk_awareness": 10,
                "clarity": 8,
            },
        },
    }

    kb = KnowledgeBase(str(tmp_path / "meeting.db"))
    meeting_id = kb.save(
        "Launch review",
        "The complete transcript remains stored separately.",
        analysis,
    )
    saved = kb.get(meeting_id)
    dashboard = MeetingAnalytics(kb).get_dashboard_data()

    assert saved is not None
    assert saved["analysis"]["speakers"] == {"Alex": []}
    assert "utterances" not in saved["analysis"]
    assert "sentences" not in saved["analysis"]["topics"][0]
    assert saved["analysis"]["topics"][0]["sentence_count"] == 2
    assert saved["analysis"]["topics"][0]["sample_sentence"] == "First topic sentence."
    assert analysis["topics"][0]["sentences"] == [
        "First topic sentence.",
        "Second topic sentence.",
    ]
    assert dashboard["overview"]["total"] == 1
    assert dashboard["action_trend"][0]["tasks"] == 1
    assert dashboard["action_trend"][0]["decisions"] == 1
    assert dashboard["participant_frequency"] == {"Alex": 1}
    assert dashboard["topic_frequency"] == {"launch": 1}
    assert dashboard["risk_summary"]["severity_distribution"] == {"medium": 1}
    report = ReportGenerator.generate_markdown(saved["analysis"], "Launch review")
    assert "2 sentences discussed" in report
    assert "First topic sentence." in report

    serialized = json.dumps(saved["analysis"])
    assert "Long speaker transcript text." not in serialized
