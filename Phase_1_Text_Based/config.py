"""Configuration for AI Meeting Summarizer"""
import os

# ── Ollama LLM Configuration ──
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = 120  # seconds

# ── Database ──
DB_PATH = os.path.join(os.path.dirname(__file__), "meeting_knowledge_base.db")

# ── NLP Parameters ──
SHORT_SUMMARY_SENTENCES = 3
DETAILED_SUMMARY_SENTENCES = 7
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
