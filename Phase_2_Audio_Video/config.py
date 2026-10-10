"""Configuration for AI Meeting Summarizer"""
import os
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_setting(name, default=None):
    value = os.getenv(name)
    if value is not None:
        return value

    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


# ── Ollama LLM Configuration ──
OLLAMA_BASE_URL = _get_setting("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = _get_setting("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = 120  # seconds
OLLAMA_TRANSLATION_TIMEOUT = int(_get_setting("OLLAMA_TRANSLATION_TIMEOUT", "45"))

# ── API Keys ──
OPENAI_API_KEY = _get_setting("OPENAI_API_KEY") or _get_setting("SPEECH_TO_TEXT_API_KEY")
LLM_API_KEY = _get_setting("LLM_API_KEY")

# ── Database ──
DB_PATH = os.path.join(os.path.dirname(__file__), "meeting_knowledge_base.db")

# ── Speech-to-Text (ASR) Configuration ──
# Use the smallest reliable model by default to keep large meetings responsive on CPU.
WHISPER_MODEL = _get_setting("WHISPER_MODEL", "openai/whisper-tiny.en")
SPEECH_TO_TEXT_PROVIDER = _get_setting("SPEECH_TO_TEXT_PROVIDER", "openai")
AUDIO_CHUNK_SECONDS = int(_get_setting("AUDIO_CHUNK_SECONDS", "180"))
MAX_AUDIO_FILE_SIZE_MB = int(_get_setting("MAX_AUDIO_FILE_SIZE_MB", "30"))
MAX_AUDIO_FILE_SIZE_BYTES = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".mov", ".mkv", ".avi"}
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# English is the only supported output language across organizations, colleges,
# teams, and academic settings, keeping the workflow consistent and simple.
SUPPORTED_LANGUAGES = {"English": "en"}
DEFAULT_OUTPUT_LANGUAGE = _get_setting("DEFAULT_OUTPUT_LANGUAGE", "English")
TRANSCRIPT_CHUNK_CHARS = int(_get_setting("TRANSCRIPT_CHUNK_CHARS", "12000"))

# ── NLP Parameters ──
SHORT_SUMMARY_SENTENCES = 3
DETAILED_SUMMARY_SENTENCES = 10
BULLET_POINTS_COUNT = 8
TOP_KEYWORDS = 20
MAX_TOPICS = 10

# ── Risk Keywords ──
RISK_KEYWORDS = [
    "risk", "risky", "concern", "worried", "worry", "threat", "danger",
    "delay", "delayed", "blocking", "blocked", "blocker", "obstacle",
    "critical", "urgent", "fail", "failure", "problem", "issue",
    "budget overrun", "deadline", "miss", "missed", "behind schedule",
    "insufficient", "shortage", "turnover", "dependency", "vulnerable",
    "uncertain", "uncertainty", "escalate", "compliance", "security"
]

# ── Priority Keywords ──
HIGH_PRIORITY_KEYWORDS = ["urgent", "critical", "immediately", "asap", "must", "emergency", "blocker"]
MEDIUM_PRIORITY_KEYWORDS = ["soon", "this week", "important", "should", "priority"]

# ── Decision Patterns ──
DECISION_PATTERNS = [
    r"\b(decided|decision|agreed|agreement|approved|confirmed|resolved|concluded|determined|consensus)\b",
    r"\b(we('?ve)?\s+(decided|agreed|approved|confirmed|finalized))\b",
    r"\b(going forward|final decision|we will (proceed|move forward|go ahead|go with))\b",
    r"\b(let'?s\s+(go with|approve|proceed|finalize|confirm))\b",
    r"\b(motion (passed|approved|carried))\b",
]

# ── Action Patterns ──
ACTION_PATTERNS = [
    r"\b(will|shall|must|needs?\s+to|going\s+to|plan\s+to)\s+[^.!?]{5,100}",
    r"\b(action item|follow.?up|task|assigned to)\s*[:–]?\s*[^.!?]{5,100}",
    r"\b(please|can you|could you)\s+[^.!?]{5,100}",
    r"\b(complete|finish|deliver|submit|send|prepare|create|build|implement|review|approve|schedule|coordinate|update|draft|share|set up|organize)\s+[^.!?]{3,100}",
]

# ── Streamlit Theme ──
STREAMLIT_PAGE_TITLE = "MeetMind — AI Meeting Summarizer"
STREAMLIT_PAGE_ICON = "🧠"
STREAMLIT_LAYOUT = "wide"
