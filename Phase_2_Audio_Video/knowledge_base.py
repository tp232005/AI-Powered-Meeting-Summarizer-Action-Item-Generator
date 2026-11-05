"""
SQLite-based Knowledge Base for meeting storage and search.
Uses FTS5 for full-text search across meetings.
Thread-safe: each thread gets its own connection via threading.local().
"""
import json
import os
import re
import shutil
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import config


class KnowledgeBase:
    """Persistent meeting storage with full-text search."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._local = threading.local()   # Fix #1 & #3: thread-local storage
        self._actor = threading.local()
        self._init_db()

    def set_actor(self, user_id: int = None, organization_id: int = None):
        """Scope subsequent reads and writes to the authenticated actor."""
        self._actor.user_id = user_id
        self._actor.organization_id = organization_id

    def _scope(self, alias: str = "") -> tuple[str, tuple]:
        user_id = getattr(self._actor, "user_id", None)
        organization_id = getattr(self._actor, "organization_id", None)
        prefix = f"{alias}." if alias else ""
        if user_id is None:
            return "", ()
        return f" WHERE {prefix}user_id = ? AND {prefix}organization_id = ?", (user_id, organization_id)

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
                user_id INTEGER REFERENCES users(id),
                organization_id INTEGER REFERENCES organizations(id),
                visibility TEXT NOT NULL DEFAULT 'private',
                short_summary TEXT,
                detailed_summary TEXT,
                decisions_count INTEGER DEFAULT 0,
                tasks_count INTEGER DEFAULT 0,
                speakers_count INTEGER DEFAULT 0,
                sentiment TEXT,
                productivity_score INTEGER DEFAULT 0,
                word_count INTEGER DEFAULT 0,
                recording_path TEXT,
                recording_name TEXT,
                recording_type TEXT,
                recording_size INTEGER,
                recording_duration REAL,
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
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(meetings)")}
        for name, definition in (
            ("user_id", "INTEGER REFERENCES users(id)"),
            ("organization_id", "INTEGER REFERENCES organizations(id)"),
            ("visibility", "TEXT NOT NULL DEFAULT 'private'"),
            ("recording_path", "TEXT"),
            ("recording_name", "TEXT"),
            ("recording_type", "TEXT"),
            ("recording_size", "INTEGER"),
            ("recording_duration", "REAL"),
        ):
            if name not in columns:
                conn.execute(f"ALTER TABLE meetings ADD COLUMN {name} {definition}")
        conn.commit()

    # ── CRUD Operations ──

    def save(
        self,
        title: str,
        transcript: str,
        analysis: dict,
        recording_path: str = None,
        recording_name: str = None,
        recording_type: str = None,
        recording_duration: float = None,
    ) -> int:
        """Save meeting text and analysis, with an optional managed recording file."""
        conn = self._get_conn()
        stored_recording = None
        try:
            if recording_path:
                source = Path(recording_path)
                if not source.is_file():
                    raise FileNotFoundError(f"Meeting recording not found: {source}")
                extension = source.suffix.lower()
                if extension not in config.SUPPORTED_AUDIO_EXTENSIONS:
                    raise ValueError(f"Unsupported recording format: {extension or 'unknown'}")
                recording_size = source.stat().st_size
                if recording_size <= 0 or recording_size > config.MAX_AUDIO_FILE_SIZE_BYTES:
                    raise ValueError("Meeting recording is empty or exceeds the configured upload limit.")
                media_type = recording_type or ("video" if extension in {
                    ".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv"
                } else "audio")
                if media_type not in {"audio", "video"}:
                    raise ValueError("Recording type must be audio or video.")
                actor_id = getattr(self._actor, "user_id", None)
                actor_directory = f"user_{actor_id}" if actor_id is not None else "unassigned"
                relative_path = Path(actor_directory) / f"{uuid.uuid4().hex}{extension}"
                recordings_root = Path(config.RECORDINGS_DIR).resolve()
                destination = (recordings_root / relative_path).resolve()
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.is_relative_to(recordings_root):
                    raise ValueError("Invalid meeting recording destination.")
                temporary_destination = destination.with_suffix(destination.suffix + ".tmp")
                try:
                    shutil.copyfile(source, temporary_destination)
                    os.replace(temporary_destination, destination)
                finally:
                    if temporary_destination.exists():
                        temporary_destination.unlink()
                stored_recording = {
                    "path": relative_path.as_posix(),
                    "name": Path(recording_name or source.name).name,
                    "type": media_type,
                    "size": recording_size,
                    "duration": recording_duration,
                    "destination": destination,
                }

            cursor = conn.execute(
                """INSERT INTO meetings
                   (title, date, transcript, analysis, user_id, organization_id, visibility,
                    short_summary, detailed_summary,
                    decisions_count, tasks_count, speakers_count, sentiment,
                    productivity_score, word_count, recording_path, recording_name,
                    recording_type, recording_size, recording_duration)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    analysis.get("timestamp", datetime.now().isoformat()),
                    transcript,
                    json.dumps(analysis, default=str),
                    getattr(self._actor, "user_id", None),
                    getattr(self._actor, "organization_id", None),
                    analysis.get("visibility", "private"),
                    analysis.get("short_summary", ""),
                    analysis.get("detailed_summary", ""),
                    len(analysis.get("decisions", [])),
                    len(analysis.get("tasks", [])),
                    analysis.get("stats", {}).get("speaker_count", 0),
                    analysis.get("sentiment", {}).get("label", "neutral"),
                    analysis.get("productivity_score", {}).get("total", 0),
                    analysis.get("stats", {}).get("word_count", 0),
                    stored_recording["path"] if stored_recording else None,
                    stored_recording["name"] if stored_recording else None,
                    stored_recording["type"] if stored_recording else None,
                    stored_recording["size"] if stored_recording else None,
                    stored_recording["duration"] if stored_recording else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            conn.rollback()
            if stored_recording and stored_recording["destination"].exists():
                stored_recording["destination"].unlink()
            raise

    def get(self, meeting_id: int) -> Optional[dict]:
        """Get a single meeting by ID."""
        conn = self._get_conn()
        scope, params = self._scope()
        scope = scope.replace(" WHERE", " AND", 1) if scope else ""
        row = conn.execute(f"SELECT * FROM meetings WHERE id = ?{scope}", (meeting_id, *params)).fetchone()
        if row:
            result = dict(row)
            result["analysis"] = json.loads(result["analysis"])
            return result
        return None

    def list_meetings(self, limit: int = 50, offset: int = 0) -> list:
        """List all meetings, most recent first."""
        conn = self._get_conn()
        scope, params = self._scope()
        rows = conn.execute(
            """SELECT id, title, date, short_summary, decisions_count,
                      tasks_count, speakers_count, sentiment,
                      productivity_score, word_count, recording_path,
                      recording_name, recording_type, recording_size,
                      recording_duration, created_at
               FROM meetings""" + scope + " ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_recording_path(self, meeting_id: int) -> Optional[Path]:
        """Return a meeting's recording path after enforcing actor scope and path containment."""
        meeting = self.get(meeting_id)
        if not meeting or not meeting.get("recording_path"):
            return None
        recordings_root = Path(config.RECORDINGS_DIR).resolve()
        recording_path = (recordings_root / meeting["recording_path"]).resolve()
        if not recording_path.is_relative_to(recordings_root):
            raise ValueError("Stored meeting recording path is invalid.")
        return recording_path if recording_path.is_file() else None

    def delete(self, meeting_id: int) -> bool:
        """Delete a meeting by ID. Returns True only if a row was deleted (Fix #4)."""
        conn = self._get_conn()
        meeting = self.get(meeting_id)
        scope, params = self._scope()
        scope = scope.replace(" WHERE", " AND", 1) if scope else ""
        cursor = conn.execute(f"DELETE FROM meetings WHERE id = ?{scope}", (meeting_id, *params))
        conn.commit()
        if cursor.rowcount > 0 and meeting and meeting.get("recording_path"):
            recording_path = self.get_recording_path_for_record(meeting["recording_path"])
            if recording_path and recording_path.exists():
                recording_path.unlink()
        return cursor.rowcount > 0

    @staticmethod
    def get_recording_path_for_record(relative_path: str) -> Optional[Path]:
        """Resolve a database recording reference without allowing paths outside the media root."""
        recordings_root = Path(config.RECORDINGS_DIR).resolve()
        recording_path = (recordings_root / relative_path).resolve()
        if not recording_path.is_relative_to(recordings_root):
            raise ValueError("Stored meeting recording path is invalid.")
        return recording_path

    def update_task_status(self, meeting_id: int, task_index: int, status: str) -> bool:
        """Persist a task status inside a saved meeting analysis."""
        if status not in {"pending", "in progress", "done"}:
            raise ValueError("Unsupported task status")
        meeting = self.get(meeting_id)
        if not meeting:
            return False
        tasks = meeting["analysis"].get("tasks", [])
        if task_index < 0 or task_index >= len(tasks):
            return False
        tasks[task_index]["status"] = status
        conn = self._get_conn()
        scope, params = self._scope()
        scope = scope.replace(" WHERE", " AND", 1) if scope else ""
        conn.execute(
            f"UPDATE meetings SET analysis = ? WHERE id = ?{scope}",
            (json.dumps(meeting["analysis"], default=str), meeting_id, *params),
        )
        conn.commit()
        return True

    # ── Search ──

    def search(self, query: str, limit: int = 20, meeting_id: int = None) -> list:
        """Full-text search across meetings, optionally limited to one meeting."""
        conn = self._get_conn()
        scope, params = self._scope("m")
        scope = scope.replace(" WHERE", " AND") if scope else ""
        if meeting_id is not None:
            scope += " AND m.id = ?"
            params = (*params, meeting_id)
        terms = re.findall(r"[\w'-]+", query.strip(), flags=re.UNICODE)
        if not terms:
            return []
        fts_query = " OR ".join(f'"{term}"' for term in terms)
        like_terms = [f"%{term}%" for term in terms]
        analysis_conditions = " OR ".join("LOWER(m.analysis) LIKE LOWER(?)" for _ in terms)
        columns = """m.id, m.title, m.date, m.short_summary, m.detailed_summary,
                     m.decisions_count, m.tasks_count, m.speakers_count, m.sentiment,
                     m.productivity_score, m.word_count, m.recording_path,
                     m.recording_name, m.recording_type, m.recording_size,
                     m.recording_duration"""
        fts_rows = conn.execute(
            f"""SELECT {columns}
                FROM meetings_fts
                JOIN meetings m ON m.id = meetings_fts.rowid
                WHERE meetings_fts MATCH ?{scope}
                ORDER BY rank
                LIMIT ?""",
            (fts_query, *params, limit),
        ).fetchall()
        analysis_rows = conn.execute(
            f"""SELECT {columns}
                FROM meetings m
                WHERE ({analysis_conditions}){scope}
                ORDER BY m.created_at DESC
                LIMIT ?""",
            (*like_terms, *params, limit),
        ).fetchall()
        matches = {row["id"]: dict(row) for row in analysis_rows}
        matches.update({row["id"]: dict(row) for row in reversed(fts_rows)})
        return list(matches.values())[:limit]

    # ── Analytics Aggregation ──

    def get_stats(self) -> dict:
        """Aggregate stats across all meetings (Fix #5: returns safe empty dict)."""
        conn = self._get_conn()
        scope, params = self._scope()
        row = conn.execute(
            """SELECT
                  COUNT(*) as total,
                  SUM(tasks_count) as total_tasks,
                  SUM(decisions_count) as total_decisions,
                  AVG(word_count) as avg_words,
                  AVG(productivity_score) as avg_productivity,
                  SUM(speakers_count) as total_speakers
             FROM meetings""" + scope,
             params,
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
            "SELECT sentiment, COUNT(*) as cnt FROM meetings" + scope + " GROUP BY sentiment",
            params,
        ).fetchall()
        sentiments = {r["sentiment"]: r["cnt"] for r in sentiment_rows}

        trend_rows = conn.execute(
            """SELECT title, productivity_score, date, tasks_count, decisions_count
             FROM meetings""" + scope + " ORDER BY created_at DESC LIMIT 10",
             params,
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
        scope, params = self._scope()
        rows = conn.execute(
            "SELECT id, title, date, analysis, productivity_score FROM meetings" + scope + " ORDER BY created_at DESC LIMIT 100",
            params,
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["analysis"] = json.loads(d["analysis"])
            results.append(d)
        return results
