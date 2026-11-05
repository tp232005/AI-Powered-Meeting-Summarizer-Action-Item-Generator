import config
from knowledge_base import KnowledgeBase


def _analysis():
    return {
        "short_summary": "Approved the launch plan.",
        "detailed_summary": "The team agreed on an owner and a release date.",
        "decisions": ["Approved the launch plan."],
        "tasks": [{"task": "Maya will prepare the launch brief", "assignee": "Maya"}],
        "risks": [],
        "stats": {"speaker_count": 2, "word_count": 18},
        "sentiment": {"label": "positive"},
        "productivity_score": {"total": 82},
    }


def test_recording_is_saved_outside_sqlite_and_deleted_with_meeting(tmp_path, monkeypatch):
    recordings_dir = tmp_path / "recordings"
    monkeypatch.setattr(config, "RECORDINGS_DIR", str(recordings_dir))
    recording = tmp_path / "original.wav"
    recording.write_bytes(b"audio bytes")

    kb = KnowledgeBase(str(tmp_path / "meetings.db"))
    kb.set_actor(7, 3)
    meeting_id = kb.save(
        "Launch review",
        "The team discussed launch and approved the release plan.",
        _analysis(),
        recording_path=str(recording),
        recording_name="team meeting.wav",
        recording_type="audio",
        recording_duration=3600,
    )

    meeting = kb.get(meeting_id)
    stored_path = kb.get_recording_path(meeting_id)

    assert meeting["recording_type"] == "audio"
    assert meeting["recording_duration"] == 3600
    assert meeting["recording_name"] == "team meeting.wav"
    assert stored_path is not None
    assert stored_path.read_bytes() == recording.read_bytes()
    matches = kb.search("Maya")
    assert len(matches) == 1
    assert matches[0]["id"] == meeting_id

    assert kb.delete(meeting_id)
    assert not stored_path.exists()
    assert kb.get(meeting_id) is None


def test_recording_paths_cannot_escape_managed_media_directory(tmp_path, monkeypatch):
    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir()
    monkeypatch.setattr(config, "RECORDINGS_DIR", str(recordings_dir))
    kb = KnowledgeBase(str(tmp_path / "meetings.db"))
    kb.set_actor(7, 3)
    meeting_id = kb.save("Text only", "Transcript", _analysis())

    with kb._get_conn():
        kb._get_conn().execute(
            "UPDATE meetings SET recording_path = ? WHERE id = ?",
            ("../outside.wav", meeting_id),
        )

    try:
        kb.get_recording_path(meeting_id)
    except ValueError as exc:
        assert "path is invalid" in str(exc)
    else:
        raise AssertionError("A path outside the recordings directory was accepted.")


def test_recording_files_follow_meeting_actor_scope(tmp_path, monkeypatch):
    recordings_dir = tmp_path / "recordings"
    monkeypatch.setattr(config, "RECORDINGS_DIR", str(recordings_dir))
    recording = tmp_path / "private.wav"
    recording.write_bytes(b"private media")
    kb = KnowledgeBase(str(tmp_path / "meetings.db"))
    kb.set_actor(7, 3)
    meeting_id = kb.save(
        "Private recording",
        "Private transcript",
        _analysis(),
        recording_path=str(recording),
    )
    saved_path = kb.get_recording_path(meeting_id)

    kb.set_actor(8, 3)

    assert kb.get(meeting_id) is None
    assert kb.get_recording_path(meeting_id) is None
    assert not kb.delete(meeting_id)
    assert saved_path is not None and saved_path.is_file()


def test_search_can_be_limited_to_the_loaded_meeting(tmp_path):
    kb = KnowledgeBase(str(tmp_path / "meetings.db"))
    kb.set_actor(7, 3)
    selected_id = kb.save(
        "Launch review",
        "The team discussed the launch plan.",
        _analysis(),
    )
    kb.save(
        "Launch retrospective",
        "The team reviewed the launch outcome.",
        _analysis(),
    )

    selected_matches = kb.search("launch", meeting_id=selected_id)
    all_matches = kb.search("launch")

    assert [meeting["id"] for meeting in selected_matches] == [selected_id]
    assert len(all_matches) == 2


def test_save_migrates_existing_meetings_table(tmp_path):
    import sqlite3

    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE meetings (
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
            )"""
        )
        connection.execute(
            "INSERT INTO meetings (title, date, transcript, analysis) VALUES (?, ?, ?, ?)",
            ("Earlier", "2025-01-01", "Old transcript", "{}"),
        )

    kb = KnowledgeBase(str(database_path))

    assert kb.get(1)["title"] == "Earlier"
    assert kb.get(1)["recording_path"] is None
