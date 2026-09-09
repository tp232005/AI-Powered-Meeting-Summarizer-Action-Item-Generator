"""Calendar persistence, reminder, export, and isolation checks."""
import os
import tempfile

from calendar_manager import CalendarManager


def run_calendar_checks():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        manager = CalendarManager(os.path.join(directory, "calendar.db"))
        manager.set_actor(1, 1)
        event_id = manager.create_event(
            "Submit report", "2026-09-15", "10:00", "Final project report", "Alice", reminder_minutes=1440
        )
        assert len(manager.list_events()) == 1
        assert "BEGIN:VCALENDAR" in manager.export_ics()
        assert "Submit report" in manager.export_ics()

        manager.set_actor(2, 2)
        assert manager.list_events() == []
        assert manager.delete_event(event_id) is False
    print("Calendar checks passed")


if __name__ == "__main__":
    run_calendar_checks()
