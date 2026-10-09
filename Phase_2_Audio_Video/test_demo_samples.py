from pathlib import Path
import wave

import config


DEMO_DIRECTORY = Path(__file__).parent / "samples" / "demo_meetings"
SHORT_DEMOS = (
    "01_campus_event_checkin",
    "02_product_launch_standup",
    "03_student_project_review",
    "04_department_budget_review",
)
LONG_DEMO = "05_sustainability_program_planning_10_min"


def _duration_seconds(audio_path: Path) -> float:
    with wave.open(str(audio_path), "rb") as recording:
        return recording.getnframes() / recording.getframerate()


def test_demo_collection_has_five_audio_transcript_pairs():
    recordings = list(DEMO_DIRECTORY.glob("*.wav"))

    assert len(recordings) == 5
    for recording in recordings:
        transcript = recording.with_suffix(".txt")
        assert transcript.is_file()
        assert transcript.stat().st_size > 0
        assert recording.stat().st_size <= config.MAX_AUDIO_FILE_SIZE_BYTES


def test_short_demo_recordings_are_under_two_minutes():
    for name in SHORT_DEMOS:
        duration = _duration_seconds(DEMO_DIRECTORY / f"{name}.wav")
        assert 0 < duration <= 120


def test_long_demo_recording_is_about_ten_minutes():
    duration = _duration_seconds(DEMO_DIRECTORY / f"{LONG_DEMO}.wav")
    assert 600 <= duration <= 605
