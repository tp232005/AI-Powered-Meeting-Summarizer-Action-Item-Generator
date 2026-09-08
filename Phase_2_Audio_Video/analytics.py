"""
Cross-meeting Analytics Module.
Aggregates data from the knowledge base for trend analysis.
"""
from collections import Counter, defaultdict
from knowledge_base import KnowledgeBase


class MeetingAnalytics:
    """Generate cross-meeting analytics from the knowledge base."""

    def __init__(self, kb: KnowledgeBase = None):
        self.kb = kb or KnowledgeBase()

    def get_dashboard_data(self) -> dict | None:
        """Get all analytics data for the dashboard."""
        stats = self.kb.get_stats()
        if not stats:
            return None

        all_meetings = self.kb.get_all_analyses()
        if not all_meetings:
            return None

        return {
            "overview": stats,
            "productivity_trend": self._productivity_trend(all_meetings),
            "sentiment_distribution": stats.get("sentiments", {}),
            "participant_frequency": self._participant_frequency(all_meetings),
            "topic_frequency": self._topic_frequency(all_meetings),
            "action_trend": self._action_trend(all_meetings),
            "risk_summary": self._risk_summary(all_meetings),
            "meeting_durations": self._meeting_durations(all_meetings),
        }

    def _productivity_trend(self, meetings: list) -> list:
        """Productivity scores over time."""
        trend = []
        for m in reversed(meetings):  # chronological order
            analysis = m.get("analysis", {})
            ps = analysis.get("productivity_score", {})
            trend.append({
                "title": m.get("title", "Untitled")[:30],
                "score": ps.get("total", 0),
                "grade": ps.get("grade", "N/A"),
                "date": m.get("date", ""),
            })
        return trend

    def _participant_frequency(self, meetings: list) -> dict:
        """How often each participant appears across meetings."""
        freq = Counter()
        for m in meetings:
            analysis = m.get("analysis", {})
            speakers = analysis.get("speakers", {})
            for name in speakers:
                freq[name] += 1
        return dict(freq.most_common(20))

    def _topic_frequency(self, meetings: list) -> dict:
        """Most common topics across all meetings."""
        freq = Counter()
        for m in meetings:
            analysis = m.get("analysis", {})
            for topic in analysis.get("topics", []):
                for kw in topic.get("keywords", []):
                    freq[kw] += 1
        return dict(freq.most_common(20))

    def _action_trend(self, meetings: list) -> list:
        """Task and decision counts over time."""
        trend = []
        for m in reversed(meetings):
            analysis = m.get("analysis", {})
            trend.append({
                "title": m.get("title", "Untitled")[:30],
                "tasks": len(analysis.get("tasks", [])),
                "decisions": len(analysis.get("decisions", [])),
                "date": m.get("date", ""),
            })
        return trend

    def _risk_summary(self, meetings: list) -> dict:
        """Aggregate risk data across meetings."""
        total_risks = 0
        severity_counts = Counter()
        common_keywords = Counter()

        for m in meetings:
            analysis = m.get("analysis", {})
            risks = analysis.get("risks", [])
            total_risks += len(risks)
            for risk in risks:
                severity_counts[risk.get("severity", "low")] += 1
                for kw in risk.get("keywords", []):
                    common_keywords[kw] += 1

        return {
            "total_risks": total_risks,
            "severity_distribution": dict(severity_counts),
            "common_risk_keywords": dict(common_keywords.most_common(10)),
        }

    def _meeting_durations(self, meetings: list) -> list:
        """Estimated durations over time."""
        durations = []
        for m in reversed(meetings):
            analysis = m.get("analysis", {})
            stats = analysis.get("stats", {})
            durations.append({
                "title": m.get("title", "Untitled")[:30],
                "duration": stats.get("estimated_duration", 0),
                "word_count": stats.get("word_count", 0),
            })
        return durations
