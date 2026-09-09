"""Persistent calendar events, reminders, and iCalendar export."""
from datetime import datetime, timedelta
import sqlite3
import uuid


class CalendarManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.user_id = None
        self.organization_id = None
        self._init_db()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self):
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    organization_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    event_date TEXT NOT NULL,
                    event_time TEXT NOT NULL DEFAULT '',
                    assignee TEXT NOT NULL DEFAULT '',
                    meeting_id INTEGER,
                    reminder_minutes INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL,
                    remind_at TEXT NOT NULL,
                    sent INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                """
            )

    def set_actor(self, user_id: int, organization_id: int):
        self.user_id = user_id
        self.organization_id = organization_id

    def _require_actor(self):
        if self.user_id is None or self.organization_id is None:
            raise PermissionError("An authenticated user is required.")

    def create_event(self, title: str, event_date: str, event_time: str = "", description: str = "", assignee: str = "", meeting_id: int = None, reminder_minutes: int = None) -> int:
        self._require_actor()
        datetime.strptime(event_date, "%Y-%m-%d")
        if event_time:
            datetime.strptime(event_time, "%H:%M")
        now = datetime.now().isoformat()
        with self._connect() as connection:
            event_id = connection.execute(
                """INSERT INTO calendar_events
                   (user_id, organization_id, title, description, event_date, event_time,
                    assignee, meeting_id, reminder_minutes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.user_id, self.organization_id, title.strip(), description.strip(), event_date, event_time, assignee.strip(), meeting_id, reminder_minutes, now),
            ).lastrowid
            if reminder_minutes is not None:
                event_at = datetime.strptime(f"{event_date} {event_time or '09:00'}", "%Y-%m-%d %H:%M")
                remind_at = (event_at - timedelta(minutes=int(reminder_minutes))).isoformat()
                connection.execute(
                    "INSERT INTO reminders(event_id, user_id, remind_at, created_at) VALUES (?, ?, ?, ?)",
                    (event_id, self.user_id, remind_at, now),
                )
        return event_id

    def list_events(self) -> list[dict]:
        self._require_actor()
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM calendar_events
                   WHERE user_id = ? AND organization_id = ?
                   ORDER BY event_date, event_time, id""",
                (self.user_id, self.organization_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_event(self, event_id: int) -> bool:
        self._require_actor()
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM calendar_events WHERE id = ? AND user_id = ? AND organization_id = ?",
                (event_id, self.user_id, self.organization_id),
            )
        return cursor.rowcount == 1

    def export_ics(self) -> str:
        events = self.list_events()
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MeetMind//Calendar//EN"]
        for event in events:
            event_time = event["event_time"] or "09:00"
            start = datetime.strptime(f"{event['event_date']} {event_time}", "%Y-%m-%d %H:%M")
            end = start + timedelta(hours=1)
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:meetmind-{event['id']}-{uuid.uuid4().hex}@meetmind",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{self._escape(event['title'])}",
                f"DESCRIPTION:{self._escape(event['description'])}",
                "END:VEVENT",
            ])
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    @staticmethod
    def _escape(value: str) -> str:
        return str(value or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
