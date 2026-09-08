"""
Speech-to-Text Transcription Engine for MeetMind.
Supports secure audio validation, optional OpenAI transcription,
and a local Whisper fallback for the existing project workflow.
"""
import os
import uuid
from pathlib import Path

import soundfile as sf
from openai import OpenAI

try:
    from transformers import pipeline
except ImportError:  # pragma: no cover - optional local fallback
    pipeline = None

import config


class TranscriptionEngine:
    """Wrapper for audio validation and transcription with a safe fallback chain."""

    _pipeline = None
    _current_model = None

    @staticmethod
    def _mime_type(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".mp4": "video/mp4",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".mov": "video/quicktime",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
        }
        return mime_map.get(ext, "application/octet-stream")

    @classmethod
    def get_pipeline(cls, model_name=None):
        """Get or initialize the cached transformers ASR pipeline on CPU."""
        if pipeline is None:
            raise ValueError("Local Whisper is unavailable because the 'transformers' package is not installed. Configure an OpenAI speech-to-text API key or install the local transcription dependency set.")

        if model_name is None:
            model_name = config.WHISPER_MODEL

        if cls._pipeline is None or cls._current_model != model_name:
            print(f"Initializing local Whisper model '{model_name}' on CPU...")
            cls._pipeline = pipeline(
                "automatic-speech-recognition",
                model=model_name,
                device="cpu",
            )
            cls._current_model = model_name
        return cls._pipeline

    @staticmethod
    def validate_audio_file(file_path: str, max_size_bytes: int | None = None) -> bool:
        """Validate uploaded audio before transcription."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in config.SUPPORTED_AUDIO_EXTENSIONS:
            raise ValueError("Unsupported audio format. Please upload MP3, WAV, M4A, MP4, WEBM, OGG, FLAC, or similar meeting audio.")

        file_size = os.path.getsize(file_path)
        limit = max_size_bytes if max_size_bytes is not None else config.MAX_AUDIO_FILE_SIZE_BYTES
        if file_size <= 0:
            raise ValueError("The audio file is empty or corrupted. Please upload a valid recording.")
        if file_size > limit:
            size_mb = file_size / (1024 * 1024)
            raise ValueError(f"Audio file is too large ({size_mb:.1f} MB). Keep it under {config.MAX_AUDIO_FILE_SIZE_MB} MB.")

        return True

    @staticmethod
    def _get_openai_api_key() -> str:
        key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY") or os.getenv("SPEECH_TO_TEXT_API_KEY")
        if not key:
            raise ValueError("Speech-to-text API key is missing. Set SPEECH_TO_TEXT_API_KEY or OPENAI_API_KEY in your environment.")
        return key

    def _transcribe_with_openai(self, file_path: str) -> str:
        """Use the OpenAI transcription endpoint for reliable meeting audio conversion."""
        client = OpenAI(api_key=self._get_openai_api_key())
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=(os.path.basename(file_path), audio_file, self._mime_type(file_path)),
                response_format="text",
            )
        text = response.strip() if isinstance(response, str) else getattr(response, "text", "").strip()
        if not text:
            raise ValueError("The audio file produced an empty transcript. Please check the recording quality and try again.")
        return text

    @staticmethod
    def _estimate_duration(file_path: str) -> float:
        """Estimate audio duration for long-file chunking decisions."""
        try:
            from moviepy.audio.io.AudioFileClip import AudioFileClip

            clip = AudioFileClip(file_path)
            duration = float(clip.duration)
            clip.close()
            return duration
        except Exception:
            return 0.0

    def _segment_audio_file(self, file_path: str, max_duration_sec: int = 600) -> list[str]:
        """Split long recordings into manageable chunks in chronological order."""
        os.makedirs(config.TEMP_DIR, exist_ok=True)
        segment_paths: list[str] = []
        chunk_count = 0

        try:
            from moviepy.audio.io.AudioFileClip import AudioFileClip

            clip = AudioFileClip(file_path)
            total_duration = float(clip.duration)
            clip.close()

            for start in range(0, int(total_duration), max_duration_sec):
                end = min(start + max_duration_sec, total_duration)
                segment_path = os.path.join(config.TEMP_DIR, f"segment_{uuid.uuid4().hex}_{chunk_count}.wav")
                clip = AudioFileClip(file_path)
                chunk = clip.subclip(start, end)
                chunk.write_audiofile(segment_path, fps=16000, codec='pcm_s16le', logger=None)
                chunk.close()
                clip.close()
                segment_paths.append(segment_path)
                chunk_count += 1
        except Exception as exc:
            raise ValueError(f"Unable to segment the audio file for processing: {exc}") from exc

        if not segment_paths:
            segment_paths.append(file_path)
        return segment_paths

    def _transcribe_local_whisper(self, file_path: str, model_name: str = None) -> str:
        """Convert audio/video to normalized WAV and transcribe with Whisper."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        os.makedirs(config.TEMP_DIR, exist_ok=True)
        temp_wav_name = f"transcribe_{uuid.uuid4().hex}.wav"
        temp_wav_path = os.path.join(config.TEMP_DIR, temp_wav_name)

        ext = os.path.splitext(file_path)[1].lower()
        is_video = ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm']

        try:
            if is_video:
                from moviepy.video.io.VideoFileClip import VideoFileClip

                clip = VideoFileClip(file_path)
                if clip.audio is None:
                    raise ValueError("The uploaded video file has no audio channel.")
                clip.audio.write_audiofile(temp_wav_path, fps=16000, codec='pcm_s16le', logger=None)
                clip.close()
            else:
                from moviepy.audio.io.AudioFileClip import AudioFileClip

                clip = AudioFileClip(file_path)
                clip.write_audiofile(temp_wav_path, fps=16000, codec='pcm_s16le', logger=None)
                clip.close()

            audio_data, samplerate = sf.read(temp_wav_path)
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=-1)

            pipe = self.get_pipeline(model_name)
            result = pipe(
                {"raw": audio_data, "sampling_rate": samplerate},
                chunk_length_s=30,
                stride_length_s=5,
                return_timestamps=False,
            )
            transcription = result.get("text", "").strip()
            if not transcription:
                raise ValueError("The audio file produced an empty transcript. Please check the recording quality and try again.")
            return transcription
        finally:
            if os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except Exception:
                    pass

    def _transcribe_with_openai_chunked(self, file_path: str) -> str:
        """Fallback for large meetings: segment audio and combine transcripts chronologically."""
        segments = self._segment_audio_file(file_path, max_duration_sec=600)
        combined: list[str] = []

        try:
            for index, segment_path in enumerate(segments, start=1):
                transcript = self._transcribe_with_openai(segment_path)
                if transcript:
                    combined.append(transcript.strip())
        finally:
            for segment_path in segments:
                if segment_path != file_path and os.path.exists(segment_path):
                    try:
                        os.remove(segment_path)
                    except Exception:
                        pass

        combined_text = "\n\n".join(part for part in combined if part.strip())
        if not combined_text.strip():
            raise ValueError("The audio file produced an empty transcript after processing. Please ensure the recording is valid and audible.")
        return combined_text.strip()

    def transcribe_file(self, file_path: str, model_name: str = None) -> str:
        """Process the uploaded audio/video file and return a transcript for the existing summarization pipeline."""
        self.validate_audio_file(file_path)

        try:
            openai_key = self._get_openai_api_key()
        except ValueError:
            openai_key = None

        if openai_key:
            try:
                duration = self._estimate_duration(file_path)
                if duration > 0 and duration > 600:
                    return self._transcribe_with_openai_chunked(file_path)
                return self._transcribe_with_openai(file_path)
            except Exception as exc:
                if "40" in str(exc) or "too large" in str(exc).lower() or "exceeds" in str(exc).lower() or "size" in str(exc).lower():
                    try:
                        return self._transcribe_with_openai_chunked(file_path)
                    except Exception:
                        pass
                print(f"OpenAI transcription failed; falling back to local Whisper: {exc}")

        try:
            return self._transcribe_local_whisper(file_path, model_name)
        except ValueError as local_error:
            raise ValueError(f"Audio could not be transcribed. {local_error}") from local_error
