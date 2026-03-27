"""
SQLite-based Knowledge Base for meeting storage and search.
Uses FTS5 for full-text search across meetings.
Thread-safe: each thread gets its own connection via threading.local().
"""
import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional
import config


class KnowledgeBase:
    """Persistent meeting storage with full-text search."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._local = threading.local()   # Fix #1 & #3: thread-local storage
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Return a per-thread SQLite connection (Fix #1)."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            if self.db_path != ":memory:":
                conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return self._local.conn

    def close(self):
        """Close this thread's database connection (Fix #2)."""
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                transcript TEXT NOT NULL,
                analysis TEXT NOT NULL,
                short_summary TEXT,
                detailed_summary TEXT,
                decisions_count INTEGER DEFAULT 0,
                tasks_count INTEGER DEFAULT 0,
                speakers_count INTEGER DEFAULT 0,
                sentiment TEXT,
                productivity_score INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS meetings_fts USING fts5(
                title, transcript, short_summary, detailed_summary,
                content='meetings',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS meetings_ai AFTER INSERT ON meetings BEGIN
                INSERT INTO meetings_fts(rowid, title, transcript, short_summary, detailed_summary)
                VALUES (new.id, new.title, new.transcript, new.short_summary, new.detailed_summary);
            END;

            CREATE TRIGGER IF NOT EXISTS meetings_ad AFTER DELETE ON meetings BEGIN
                INSERT INTO meetings_fts(meetings_fts, rowid, title, transcript, short_summary, detailed_summary)
                VALUES('delete', old.id, old.title, old.transcript, old.short_summary, old.detailed_summary);
            END;

            CREATE TRIGGER IF NOT EXISTS meetings_au AFTER UPDATE ON meetings BEGIN
                INSERT INTO meetings_fts(meetings_fts, rowid, title, transcript, short_summary, detailed_summary)
                VALUES('delete', old.id, old.title, old.transcript, old.short_summary, old.detailed_summary);
                INSERT INTO meetings_fts(rowid, title, transcript, short_summary, detailed_summary)
                VALUES (new.id, new.title, new.transcript, new.short_summary, new.detailed_summary);
            END;
        """)
        conn.commit()

    # ── CRUD Operations ──

    def save(self, title: str, transcript: str, analysis: dict) -> int:
        """Save a meeting and its analysis. Returns the meeting ID (Fix #6)."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO meetings
                   (title, date, transcript, analysis, short_summary, detailed_summary,
                    decisions_count, tasks_count, speakers_count, sentiment,
                    productivity_score, word_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    analysis.get("timestamp", datetime.now().isoformat()),
                    transcript,
                    json.dumps(analysis, default=str),
                    analysis.get("short_summary", ""),
                    analysis.get("detailed_summary", ""),
                    len(analysis.get("decisions", [])),
                    len(analysis.get("tasks", [])),
                    analysis.get("stats", {}).get("speaker_count", 0),
                    analysis.get("sentiment", {}).get("label", "neutral"),
                    analysis.get("productivity_score", {}).get("total", 0),
                    analysis.get("stats", {}).get("word_count", 0),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            raise

    def get(self, meeting_id: int) -> Optional[dict]:
        """Get a single meeting by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if row:
            result = dict(row)
            result["analysis"] = json.loads(result["analysis"])
            return result
        return None

    def list_meetings(self, limit: int = 50, offset: int = 0) -> list:
        """List all meetings, most recent first."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT id, title, date, short_summary, decisions_count,
                      tasks_count, speakers_count, sentiment,
                      productivity_score, word_count, created_at
               FROM meetings ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def delete(self, meeting_id: int) -> bool:
        """Delete a meeting by ID. Returns True only if a row was deleted (Fix #4)."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ── Search ──

    def search(self, query: str, limit: int = 20) -> list:
        """Full-text search across meetings."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """SELECT m.id, m.title, m.date, m.short_summary,
                          m.decisions_count, m.tasks_count, m.sentiment,
                          m.productivity_score, m.word_count,
                          rank
                   FROM meetings_fts fts
                   JOIN meetings m ON m.id = fts.rowid
                   WHERE meetings_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            like_q = f"%{query}%"
            rows = conn.execute(
                """SELECT id, title, date, short_summary,
                          decisions_count, tasks_count, sentiment,
                          productivity_score, word_count
                   FROM meetings
                   WHERE title LIKE ? OR short_summary LIKE ? OR transcript LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (like_q, like_q, like_q, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Analytics Aggregation ──

    def get_stats(self) -> dict:
        """Aggregate stats across all meetings (Fix #5: returns safe empty dict)."""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT
                  COUNT(*) as total,
                  SUM(tasks_count) as total_tasks,
                  SUM(decisions_count) as total_decisions,
                  AVG(word_count) as avg_words,
                  AVG(productivity_score) as avg_productivity,
                  SUM(speakers_count) as total_speakers
               FROM meetings"""
        ).fetchone()

        if not row or row["total"] == 0:
            # Fix #5: return safe empty defaults instead of None
            return {
                "total": 0,
                "total_tasks": 0,
                "total_decisions": 0,
                "avg_words": 0,
                "avg_productivity": 0,
                "sentiments": {},
                "productivity_trend": [],
            }

        sentiment_rows = conn.execute(
            "SELECT sentiment, COUNT(*) as cnt FROM meetings GROUP BY sentiment"
        ).fetchall()
        sentiments = {r["sentiment"]: r["cnt"] for r in sentiment_rows}

        trend_rows = conn.execute(
            """SELECT title, productivity_score, date, tasks_count, decisions_count
               FROM meetings ORDER BY created_at DESC LIMIT 10"""
        ).fetchall()

        return {
            "total": row["total"],
            "total_tasks": row["total_tasks"] or 0,
            "total_decisions": row["total_decisions"] or 0,
            "avg_words": round(row["avg_words"] or 0),
            "avg_productivity": round(row["avg_productivity"] or 0),
            "sentiments": sentiments,
            "productivity_trend": [dict(r) for r in trend_rows],
        }

    def get_all_analyses(self) -> list:
        """Get all meeting analyses for cross-meeting analytics (Fix #7: LIMIT added)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, title, date, analysis, productivity_score FROM meetings ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["analysis"] = json.loads(d["analysis"])
            results.append(d)
        return results
