import pytest

import config
from transcription_engine import TranscriptionEngine


def test_default_whisper_model_is_fast_tiny():
    assert config.WHISPER_MODEL == "openai/whisper-tiny.en"


def test_validate_audio_file_rejects_unsupported_extension(tmp_path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not audio", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported audio format"):
        TranscriptionEngine().validate_audio_file(str(bad_file))


def test_validate_audio_file_rejects_large_file(tmp_path):
    large_file = tmp_path / "large.mp3"
    large_file.write_bytes(b"0" * (config.MAX_AUDIO_FILE_SIZE_BYTES + 1))

    with pytest.raises(ValueError, match="too large"):
        TranscriptionEngine().validate_audio_file(str(large_file))


def test_audio_limit_is_30_mb():
    assert config.MAX_AUDIO_FILE_SIZE_MB == 30
