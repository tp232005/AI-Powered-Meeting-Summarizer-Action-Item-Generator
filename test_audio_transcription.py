import pytest

from transcription_engine import TranscriptionEngine


def test_validate_audio_file_rejects_unsupported_extension(tmp_path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not audio", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported audio format"):
        TranscriptionEngine().validate_audio_file(str(bad_file))


def test_validate_audio_file_rejects_large_file(tmp_path):
    large_file = tmp_path / "large.mp3"
    large_file.write_bytes(b"0" * (30 * 1024 * 1024 + 1))

    with pytest.raises(ValueError, match="too large"):
        TranscriptionEngine().validate_audio_file(str(large_file))
