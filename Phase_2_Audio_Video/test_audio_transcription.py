from pathlib import Path

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


def test_validate_audio_file_rejects_large_file(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "MAX_AUDIO_FILE_SIZE_BYTES", 100)
    monkeypatch.setattr(config, "MAX_AUDIO_FILE_SIZE_MB", 1)
    large_file = tmp_path / "large.mp3"
    large_file.write_bytes(b"0" * 101)

    with pytest.raises(ValueError, match="too large"):
        TranscriptionEngine().validate_audio_file(str(large_file))


def test_audio_limit_supports_long_meeting_recordings():
    assert config.MAX_AUDIO_FILE_SIZE_MB >= 1024


def test_long_recording_is_transcribed_in_ordered_chunks(monkeypatch, tmp_path):
    engine = TranscriptionEngine()
    source = tmp_path / "meeting.wav"
    source.write_bytes(b"recording")
    chunk_paths = []
    for index in range(20):
        chunk = tmp_path / f"chunk_{index}.wav"
        chunk.write_bytes(b"chunk")
        chunk_paths.append(str(chunk))

    monkeypatch.setattr(engine, "_estimate_duration", lambda path: 3600)
    monkeypatch.setattr(engine, "_segment_audio_file", lambda path, seconds: chunk_paths)
    monkeypatch.setattr(engine, "_has_openai_api_key", lambda: False)
    monkeypatch.setattr(
        engine,
        "_transcribe_local_whisper",
        lambda path, model_name=None: f"chunk {chunk_paths.index(path)}",
    )

    result = engine.transcribe_file_detailed(str(source))

    assert result["duration_seconds"] == 3600
    assert result["chunk_count"] == 20
    assert result["transcript"].startswith("chunk 0")
    assert result["transcript"].endswith("chunk 19")
    assert result["segments"][0]["start"] == "00:00:00"
    assert result["segments"][-1]["start"] == "00:57:00"
    assert result["segments"][-1]["end"] == "01:00:00"


def test_one_hour_wav_is_physically_split_into_chronological_chunks(monkeypatch, tmp_path):
    class FakeSoundFile:
        samplerate = 1

        def __init__(self):
            self.position = 0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def __len__(self):
            return 3600

        def seek(self, frame):
            self.position = frame

        def read(self, frames, **kwargs):
            import numpy as np

            data = np.array([[self.position]], dtype="float32")
            self.position += min(frames, 3600 - self.position)
            return data

    segments_directory = tmp_path / "chunks"
    written_sample_rates = []
    monkeypatch.setattr(config, "TEMP_DIR", str(segments_directory))
    monkeypatch.setattr("transcription_engine.sf.SoundFile", lambda path: FakeSoundFile())
    monkeypatch.setattr("scipy.signal.resample_poly", lambda data, up, down: data)

    def write_chunk(path, data, samplerate, subtype):
        written_sample_rates.append(samplerate)
        Path(path).write_text(str(int(data[0])))

    monkeypatch.setattr(
        "transcription_engine.sf.write",
        write_chunk,
    )
    source = tmp_path / "one-hour.wav"
    source.write_bytes(b"placeholder")

    segments = TranscriptionEngine()._segment_audio_file(str(source), max_duration_sec=600)

    assert len(segments) == 6
    assert [Path(path).read_text() for path in segments] == [
        "0", "600", "1200", "1800", "2400", "3000",
    ]
    assert written_sample_rates == [16000] * 6


def test_video_audio_chunks_remain_readable_and_normalized(monkeypatch, tmp_path):
    import soundfile as sf

    video_file = Path(__file__).parent / "samples" / "video" / "Project_Planning_Video.mp4"
    if not video_file.exists():
        pytest.skip("Project_Planning_Video.mp4 sample is unavailable")

    monkeypatch.setattr(config, "TEMP_DIR", str(tmp_path))
    segments = TranscriptionEngine()._segment_audio_file(str(video_file), max_duration_sec=10)

    try:
        assert len(segments) >= 2
        assert all(
            (info := sf.info(segment)).samplerate == 16000 and info.channels == 1
            for segment in segments
        )
    finally:
        for segment in segments:
            if segment != str(video_file) and Path(segment).exists():
                Path(segment).unlink()


def test_api_chunk_size_is_reduced_for_large_uncompressed_recordings(monkeypatch):
    monkeypatch.setattr("transcription_engine.os.path.getsize", lambda path: 800 * 1024 * 1024)

    chunk_seconds = TranscriptionEngine._api_chunk_duration(
        "one-hour.wav",
        duration=3600,
        preferred_seconds=180,
    )

    assert 30 <= chunk_seconds < 180


def test_openai_failure_does_not_fall_back_to_slow_local_transcription(monkeypatch, tmp_path):
    engine = TranscriptionEngine()
    audio_file = tmp_path / "meeting.wav"
    audio_file.write_bytes(b"audio")
    local_transcription_called = False

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(engine, "validate_audio_file", lambda path: True)
    monkeypatch.setattr(engine, "_estimate_duration", lambda path: 60)
    monkeypatch.setattr(engine, "_segment_audio_file", lambda path, seconds: [path])
    monkeypatch.setattr(
        engine,
        "_transcribe_with_openai",
        lambda path: (_ for _ in ()).throw(RuntimeError("API unavailable")),
    )

    def local_transcription(*args, **kwargs):
        nonlocal local_transcription_called
        local_transcription_called = True
        return "slow local transcript"

    monkeypatch.setattr(engine, "_transcribe_local_whisper", local_transcription)

    with pytest.raises(RuntimeError, match="OpenAI transcription failed"):
        engine.transcribe_file_detailed(str(audio_file))

    assert not local_transcription_called
