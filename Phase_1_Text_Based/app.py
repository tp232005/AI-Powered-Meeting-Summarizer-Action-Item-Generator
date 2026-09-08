"""
MeetMind — AI Meeting Summarizer
Premium Streamlit Dashboard with Advanced NLP + LLM Integration
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

import config
from nlp_engine import MeetingAnalyzer
from llm_engine import OllamaEngine
from knowledge_base import KnowledgeBase
from report_generator import ReportGenerator
from analytics import MeetingAnalytics

# ═══════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════

st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded",
)

# ── Premium CSS Theme ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #0a0a1a 0%, #0f0c29 25%, #1a1145 50%, #0d0b21 100%);
        color: #e2e8f0;
    }

    /* ── Hide Streamlit header/decoration bar ── */
    header[data-testid="stHeader"] {
        background: transparent !important;
        backdrop-filter: none !important;
    }
    .stDeployButton, #MainMenu {
        visibility: hidden;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    .stApp > header {
        background: transparent !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0a1e 0%, #15112b 50%, #1a1333 100%) !important;
        border-right: 1px solid rgba(124,58,237,0.15);
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #c4b5fd; }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c4b5fd !important;
        font-weight: 500;
    }

    /* ── Hero Header ── */
    .hero-header {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #a78bfa, #7c3aed, #38bdf8, #34d399);
        background-size: 300% 300%;
        animation: gradient-shift 6s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 4px;
        letter-spacing: -1px;
    }
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    .hero-sub {
        color: #94a3b8;
        font-size: 1.15rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    /* ── Glass Cards ── */
    .glass-card {
        background: rgba(15, 12, 41, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(124, 58, 237, 0.4);
        box-shadow: 0 8px 40px rgba(124, 58, 237, 0.1);
    }

    /* ── Metric Cards ── */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 14px;
        margin: 20px 0;
    }
    .metric-card {
        background: rgba(15, 12, 41, 0.7);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(124, 58, 237, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.12);
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card .label {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    .metric-card.accent-green .value { background: linear-gradient(135deg, #34d399, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card.accent-amber .value { background: linear-gradient(135deg, #fbbf24, #f59e0b); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card.accent-rose .value { background: linear-gradient(135deg, #f472b6, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card.accent-sky .value { background: linear-gradient(135deg, #38bdf8, #0ea5e9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

    /* ── Feature Pills ── */
    .pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 24px; }
    .pill {
        background: rgba(124, 58, 237, 0.12);
        border: 1px solid rgba(124, 58, 237, 0.25);
        color: #c4b5fd;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    .pill:hover { background: rgba(124, 58, 237, 0.25); border-color: rgba(124, 58, 237, 0.5); }

    /* ── Section Headers ── */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section-header .icon {
        font-size: 1.5rem;
    }

    /* ── Decision & Task Cards ── */
    .decision-card {
        background: rgba(124, 58, 237, 0.08);
        border-left: 3px solid #7c3aed;
        padding: 14px 18px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 10px;
        font-size: 0.95rem;
        color: #e2e8f0;
    }

    .task-card {
        background: rgba(15, 12, 41, 0.5);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 10px;
        transition: all 0.2s;
    }
    .task-card:hover { border-color: rgba(124, 58, 237, 0.35); }
    .task-card .task-text { color: #e2e8f0; font-weight: 500; margin-bottom: 8px; }
    .task-card .task-meta { display: flex; gap: 16px; flex-wrap: wrap; }
    .task-card .task-meta span {
        font-size: 0.8rem;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .priority-high { color: #f87171 !important; }
    .priority-medium { color: #fbbf24 !important; }
    .priority-low { color: #34d399 !important; }

    .priority-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .priority-dot.high { background: #f87171; box-shadow: 0 0 8px rgba(248,113,113,0.5); }
    .priority-dot.medium { background: #fbbf24; box-shadow: 0 0 8px rgba(251,191,36,0.5); }
    .priority-dot.low { background: #34d399; box-shadow: 0 0 8px rgba(52,211,153,0.5); }

    /* ── Risk Cards ── */
    .risk-card {
        padding: 14px 18px;
        border-radius: 0 12px 12px 0;
        margin-bottom: 10px;
        font-size: 0.95rem;
        color: #e2e8f0;
    }
    .risk-card.high { background: rgba(239,68,68,0.1); border-left: 3px solid #ef4444; }
    .risk-card.medium { background: rgba(245,158,11,0.1); border-left: 3px solid #f59e0b; }
    .risk-card.low { background: rgba(16,185,129,0.1); border-left: 3px solid #10b981; }

    /* ── Participant Cards ── */
    .participant-card {
        display: flex;
        align-items: center;
        gap: 14px;
        background: rgba(15, 12, 41, 0.5);
        border: 1px solid rgba(124, 58, 237, 0.12);
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 8px;
    }
    .participant-avatar {
        width: 44px; height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
        flex-shrink: 0;
    }
    .participant-info { flex: 1; }
    .participant-name { font-weight: 600; color: #e2e8f0; }
    .participant-stats { font-size: 0.8rem; color: #94a3b8; }

    /* ── History Cards ── */
    .history-card {
        background: rgba(15, 12, 41, 0.5);
        border: 1px solid rgba(124, 58, 237, 0.12);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.2s;
        cursor: pointer;
    }
    .history-card:hover {
        border-color: rgba(124, 58, 237, 0.35);
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.1);
    }

    /* ── Empty State ── */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #64748b;
    }
    .empty-state .icon { font-size: 3.5rem; margin-bottom: 16px; opacity: 0.5; }
    .empty-state p { font-size: 1.05rem; max-width: 400px; margin: 0 auto; }

    /* ── Logo ── */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding: 12px 8px;
    }
    .logo-icon {
        width: 42px; height: 42px;
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
    }
    .logo-text .name { font-weight: 800; font-size: 1.2rem; color: #f1f5f9; }
    .logo-text .sub { font-size: 0.7rem; color: #64748b; letter-spacing: 1px; text-transform: uppercase; }

    /* ── Score Badge ── */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(56,189,248,0.2));
        border: 1px solid rgba(124,58,237,0.3);
        border-radius: 14px;
        padding: 8px 18px;
        font-weight: 700;
        font-size: 1.1rem;
    }

    /* ── Version Badge ── */
    .version-badge {
        background: rgba(124, 58, 237, 0.1);
        border: 1px solid rgba(124, 58, 237, 0.2);
        color: #a78bfa;
        padding: 6px 14px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        text-align: center;
        margin-top: 16px;
    }

    /* ── Plotly Chart Containers ── */
    .chart-container {
        background: rgba(15, 12, 41, 0.5);
        border: 1px solid rgba(124, 58, 237, 0.12);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* ── Keyword Tags ── */
    .keyword-tag {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 3px;
    }

    /* ── Override Streamlit defaults for READABILITY ── */

    /* All body text bright */
    .stApp p, .stApp li, .stApp span, .stApp div {
        color: #e2e8f0;
    }

    /* Form labels - MUCH brighter and bigger */
    .stTextArea label, .stTextInput label, .stSelectbox label,
    .stSlider label, .stCheckbox label, .stRadio label,
    .stNumberInput label, .stDateInput label, .stTimeInput label,
    .stFileUploader label, .stMultiSelect label {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    /* Placeholder text - more visible */
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #8b8da3 !important;
        opacity: 1 !important;
    }

    /* Text inputs */
    .stTextArea textarea {
        background: rgba(15, 12, 41, 0.7) !important;
        border: 1px solid rgba(124, 58, 237, 0.25) !important;
        border-radius: 14px !important;
        color: #f1f5f9 !important;
        font-family: 'Inter', monospace !important;
        font-size: 0.95rem !important;
    }
    .stTextArea textarea:focus {
        border-color: rgba(124, 58, 237, 0.6) !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.15) !important;
    }
    .stTextInput input {
        background: rgba(15, 12, 41, 0.7) !important;
        border: 1px solid rgba(124, 58, 237, 0.25) !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input:focus {
        border-color: rgba(124, 58, 237, 0.6) !important;
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.15) !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(15, 12, 41, 0.7) !important;
        border: 1px solid rgba(124, 58, 237, 0.25) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    .stSelectbox [data-baseweb="select"] span {
        color: #e2e8f0 !important;
    }

    /* Checkbox text - bright */
    .stCheckbox label span {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
    }

    /* Slider - bright label + value */
    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"] {
        color: #c4b5fd !important;
        font-weight: 600 !important;
    }
    .stSlider [data-baseweb="slider"] div {
        color: #e2e8f0 !important;
    }

    /* Sidebar nav text - MUCH brighter */
    section[data-testid="stSidebar"] .stRadio label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stCaption, 
    section[data-testid="stSidebar"] small {
        color: #a5b4fc !important;
        font-size: 0.85rem !important;
    }

    /* Buttons */
    button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px;
        padding: 12px 28px !important;
        transition: all 0.3s !important;
        color: #ffffff !important;
    }
    button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
        box-shadow: 0 6px 25px rgba(124, 58, 237, 0.35) !important;
        transform: translateY(-1px);
    }
    button[data-testid="stBaseButton-secondary"] {
        background: rgba(124, 58, 237, 0.15) !important;
        border: 1px solid rgba(124, 58, 237, 0.4) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(124, 58, 237, 0.25) !important;
        color: #ffffff !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 12, 41, 0.5);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 20px;
        font-weight: 600;
        color: #c4b5fd !important;
        font-size: 0.9rem !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(124, 58, 237, 0.2) !important;
        color: #ffffff !important;
    }

    /* Expander */
    .stExpander {
        background: rgba(15, 12, 41, 0.5) !important;
        border: 1px solid rgba(124, 58, 237, 0.12) !important;
        border-radius: 14px !important;
    }
    .stExpander summary span {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
    }

    /* Divider */
    .stDivider { border-color: rgba(124, 58, 237, 0.15) !important; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(15, 12, 41, 0.6);
        border: 1px solid rgba(124, 58, 237, 0.15);
        border-radius: 14px;
        padding: 16px;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #f1f5f9 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #c4b5fd !important;
        font-weight: 600 !important;
    }

    /* Progress bars */
    .stProgress > div > div {
        background: rgba(124, 58, 237, 0.15) !important;
        border-radius: 10px;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #38bdf8) !important;
        border-radius: 10px;
    }

    /* Download button */
    .stDownloadButton button {
        background: rgba(124, 58, 237, 0.15) !important;
        border: 1px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    /* Captions everywhere */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #a5b4fc !important;
        font-size: 0.85rem !important;
    }

    /* Info/Success/Error boxes - readable text */
    .stAlert p, .stAlert span {
        font-size: 0.95rem !important;
    }

    /* st.info, st.success etc readable */
    div[data-testid="stNotification"] p {
        color: inherit !important;
        font-size: 0.95rem !important;
    }

    /* Radio label text in sidebar */
    .stRadio > div > label > div > p {
        color: #e2e8f0 !important;
        font-size: 0.95rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  INITIALIZE COMPONENTS
# ═══════════════════════════════════════════

@st.cache_resource
def get_analyzer():
    return MeetingAnalyzer()

@st.cache_resource
def get_kb():
    return KnowledgeBase()

@st.cache_resource
def get_llm():
    return OllamaEngine()

analyzer = get_analyzer()
kb = get_kb()
llm = get_llm()
report_gen = ReportGenerator()
analytics_engine = MeetingAnalytics(kb)

# ── Plotly Dark Theme ──
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(124,58,237,0.08)", zerolinecolor="rgba(124,58,237,0.08)"),
    yaxis=dict(gridcolor="rgba(124,58,237,0.08)", zerolinecolor="rgba(124,58,237,0.08)"),
)

COLORS = ["#a78bfa", "#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#fb923c", "#818cf8", "#2dd4bf"]


# ═══════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">🧠</div>
        <div class="logo-text">
            <div class="name">MeetMind</div>
            <div class="sub">AI Summarizer</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Analyze Meeting", "📊 Results Dashboard", "📚 Knowledge Base",
         "📈 Analytics", "📧 Generate Report", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.divider()

    # Ollama status
    ollama_ok = llm.is_available()
    if ollama_ok:
        st.markdown(f"✅ **Ollama**: `{config.OLLAMA_MODEL}`")
    else:
        st.markdown("⚠️ **Ollama**: Offline")
        st.caption("Using rule-based NLP engine")

    meeting_count = len(kb.list_meetings())
    st.markdown(f"📂 **{meeting_count}** meetings stored")

    st.markdown('<div class="version-badge">v3.0 · Research Edition</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════

def render_metric_row(metrics):
    """Render a row of beautiful metric cards."""
    cols_html = ""
    accents = ["", "accent-green", "accent-sky", "accent-amber", "accent-rose", ""]
    for i, (val, label) in enumerate(metrics):
        accent = accents[i % len(accents)]
        cols_html += f'<div class="metric-card {accent}"><div class="value">{val}</div><div class="label">{label}</div></div>'
    st.markdown(f'<div class="metric-row">{cols_html}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  PAGE: ANALYZE MEETING
# ═══════════════════════════════════════════

if page == "🏠 Analyze Meeting":
    st.markdown('<h1 class="hero-header">Turn Meetings Into<br>Actionable Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Advanced NLP engine with TF-IDF summarization, smart task extraction, risk detection, topic segmentation, and productivity scoring — powered by spaCy, NLTK & optional Ollama LLM.</p>', unsafe_allow_html=True)

    # Feature pills
    pills = ["Multi-Level Summaries", "Decision Detection", "Smart Task Extraction",
             "Risk Analysis", "Topic Segmentation", "Participant Analysis",
             "Productivity Score", "LLM Enhancement", "Knowledge Base", "Auto Reports"]
    pills_html = "".join(f'<span class="pill">✦ {p}</span>' for p in pills)
    st.markdown(f'<div class="pill-row">{pills_html}</div>', unsafe_allow_html=True)

    # Input card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        default_title = st.session_state.get("_sample_title", "")
        meeting_title = st.text_input("📝 Meeting Title", value=default_title, placeholder="e.g., Q1 2025 Product Strategy Meeting", label_visibility="visible")
    with col2:
        summary_len = st.slider("Summary length", 2, 12, 5)

    default_text = st.session_state.get("_sample_text", "")
    transcript = st.text_area(
        "📄 Meeting Transcript",
        value=default_text,
        height=280,
        placeholder="Paste your meeting transcript here...\n\nSupports speaker diarization:\n  Sarah: Good morning everyone...\n  James: Let's start with the agenda...\n  [Speaker Name] text also works\n\nOr paste unformatted meeting minutes.",
    )

    col_s, col_l, col_a = st.columns([1, 1, 2])
    with col_s:
        if st.button("📋 Load Sample", use_container_width=True, type="secondary"):
            sample_path = os.path.join(os.path.dirname(__file__), "samples", "sample_meeting.txt")
            if os.path.exists(sample_path):
                with open(sample_path, "r", encoding="utf-8") as f:
                    st.session_state["_sample_text"] = f.read()
                    st.session_state["_sample_title"] = "Q1 2025 Product Strategy Meeting"
                st.rerun()

    with col_l:
        use_llm = st.checkbox("🤖 Use LLM", value=False)

    with col_a:
        analyze_clicked = st.button("🔍  Analyze Meeting", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Run analysis
    if analyze_clicked and transcript.strip():
        progress = st.progress(0, text="🧠 Initializing NLP pipeline...")
        result = analyzer.analyze(transcript)

        if "error" in result:
            st.error(result["error"])
        else:
            progress.progress(60, text="📊 Processing results...")

            if use_llm and ollama_ok:
                progress.progress(70, text="🤖 Enhancing with LLM...")
                llm_summary = llm.generate_summary(transcript, "concise")
                if llm_summary:
                    result["llm_summary"] = llm_summary
                llm_tasks = llm.extract_tasks(transcript)
                if llm_tasks:
                    result["llm_tasks"] = llm_tasks
                llm_risks = llm.analyze_risks(transcript)
                if llm_risks:
                    result["llm_risks"] = llm_risks

            title = meeting_title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            st.session_state["current_result"] = result
            st.session_state["current_title"] = title
            st.session_state["current_transcript"] = transcript

            progress.progress(85, text="💾 Saving to Knowledge Base...")
            kb.save(title, transcript, result)

            progress.progress(100, text="✅ Complete!")
            st.balloons()
            st.success(f"✅ Analysis complete — **{title}** saved to Knowledge Base! Navigate to **Results Dashboard** to see the full analysis.", icon="🎉")

    elif analyze_clicked:
        st.error("Please paste a meeting transcript first.")


# ═══════════════════════════════════════════
#  PAGE: RESULTS DASHBOARD
# ═══════════════════════════════════════════

elif page == "📊 Results Dashboard":
    result = st.session_state.get("current_result")
    title = st.session_state.get("current_title", "Meeting Results")

    if not result:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📊</div>
            <p>No analysis results yet.<br>Go to <strong>Analyze Meeting</strong> to process a transcript.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<h1 class="hero-header">{title}</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-sub">AI-powered meeting intelligence dashboard</p>', unsafe_allow_html=True)

        # Stats bar
        stats = result.get("stats", {})
        ps = result.get("productivity_score", {})
        render_metric_row([
            (f"{stats.get('word_count', 0):,}", "Words"),
            (f"~{stats.get('estimated_duration', 0)} min", "Duration"),
            (str(stats.get("speaker_count", 0)), "Speakers"),
            (str(len(result.get("tasks", []))), "Tasks"),
            (str(len(result.get("decisions", []))), "Decisions"),
            (f"{ps.get('total', 0)}% {ps.get('grade', '')}", "Score"),
        ])

        st.divider()

        # ── Multi-Level Summaries ──
        st.markdown('<div class="section-header"><span class="icon">📝</span> Meeting Summaries</div>', unsafe_allow_html=True)
        sum_tabs = st.tabs(["✨ Short", "📄 Detailed", "📌 Bullet Points", "🤖 LLM Summary"])
        with sum_tabs[0]:
            st.markdown(f'<div class="glass-card">{result.get("short_summary", "N/A")}</div>', unsafe_allow_html=True)
        with sum_tabs[1]:
            st.markdown(f'<div class="glass-card">{result.get("detailed_summary", "N/A")}</div>', unsafe_allow_html=True)
        with sum_tabs[2]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            for bp in result.get("bullet_points", []):
                st.markdown(f"• {bp}")
            st.markdown('</div>', unsafe_allow_html=True)
        with sum_tabs[3]:
            llm_s = result.get("llm_summary")
            if llm_s:
                st.markdown(f'<div class="glass-card">{llm_s}</div>', unsafe_allow_html=True)
            else:
                st.info("Enable Ollama LLM during analysis for AI-enhanced summaries.")

        st.divider()

        # ── Decisions & Tasks ──
        col_d, col_t = st.columns(2)
        with col_d:
            st.markdown('<div class="section-header"><span class="icon">⚖️</span> Decisions Made</div>', unsafe_allow_html=True)
            decisions = result.get("decisions", [])
            if decisions:
                for d in decisions:
                    st.markdown(f'<div class="decision-card">{d}</div>', unsafe_allow_html=True)
            else:
                st.caption("No formal decisions detected.")

        with col_t:
            st.markdown(f'<div class="section-header"><span class="icon">✅</span> Action Items ({len(result.get("tasks", []))})</div>', unsafe_allow_html=True)
            tasks = result.get("tasks", [])
            if tasks:
                for t in tasks:
                    p = t.get("priority", "low")
                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-text"><span class="priority-dot {p}"></span> {t['task'][:120]}</div>
                        <div class="task-meta">
                            <span>👤 {t['assignee']}</span>
                            <span>📅 {t['deadline']}</span>
                            <span class="priority-{p}">● {p.upper()}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No action items detected.")

        st.divider()

        # ── Risks ──
        st.markdown('<div class="section-header"><span class="icon">⚠️</span> Risks & Concerns</div>', unsafe_allow_html=True)
        risks = result.get("llm_risks") or result.get("risks", [])
        if risks:
            for r in risks:
                sev = r.get("severity", "low")
                st.markdown(f"""
                <div class="risk-card {sev}">
                    <strong>[{sev.upper()}]</strong> {r['description']}
                    {f"<br><small style='color:#94a3b8'>💡 {r['mitigation']}</small>" if r.get('mitigation') and r['mitigation'] != 'Not discussed' else ''}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No significant risks detected. ✅")

        st.divider()

        # ── Topics ──
        col_topics, col_sentiment = st.columns(2)
        with col_topics:
            st.markdown('<div class="section-header"><span class="icon">🗂️</span> Discussion Topics</div>', unsafe_allow_html=True)
            topics = result.get("topics", [])
            if topics:
                fig = px.bar(
                    x=[len(t.get("sentences", [])) for t in topics],
                    y=[f"{i+1}. {t['topic'][:25]}" for i, t in enumerate(topics)],
                    orientation="h",
                    color=[len(t.get("sentences", [])) for t in topics],
                    color_continuous_scale=[[0, "#4f46e5"], [0.5, "#7c3aed"], [1, "#a78bfa"]],
                )
                fig.update_layout(**PLOTLY_LAYOUT, height=max(200, len(topics) * 50), showlegend=False, coloraxis_showscale=False)
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)

        with col_sentiment:
            st.markdown('<div class="section-header"><span class="icon">💭</span> Speaker Sentiment</div>', unsafe_allow_html=True)
            speaker_sents = result.get("speaker_sentiments", {})
            if speaker_sents:
                fig = go.Figure()
                names = list(speaker_sents.keys())
                fig.add_trace(go.Bar(name="Positive", x=names, y=[s["positive"] for s in speaker_sents.values()],
                                     marker_color="#34d399", marker_line_width=0))
                fig.add_trace(go.Bar(name="Negative", x=names, y=[s["negative"] for s in speaker_sents.values()],
                                     marker_color="#f87171", marker_line_width=0))
                fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=300, legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)
            else:
                sentiment = result.get("sentiment", {})
                st.metric("Overall Sentiment", sentiment.get("label", "neutral").capitalize())

        st.divider()

        # ── Participants ──
        st.markdown('<div class="section-header"><span class="icon">👥</span> Participant Contributions</div>', unsafe_allow_html=True)
        participants = result.get("participants", [])
        if participants:
            col_pie, col_cards = st.columns([1, 1])
            with col_pie:
                fig = px.pie(
                    values=[p["contribution_pct"] for p in participants],
                    names=[p["name"] for p in participants],
                    color_discrete_sequence=COLORS,
                    hole=0.45,
                )
                fig.update_layout(**PLOTLY_LAYOUT, height=350, showlegend=True,
                                  legend=dict(orientation="h", y=-0.1, font=dict(size=11)))
                fig.update_traces(textinfo="percent+label", textfont_size=11)
                st.plotly_chart(fig, use_container_width=True)

            with col_cards:
                for i, p in enumerate(participants):
                    color = COLORS[i % len(COLORS)]
                    initials = "".join(w[0] for w in p["name"].split()[:2]).upper()
                    sent_icon = {"positive": "😊", "negative": "😟", "neutral": "😐"}.get(p["sentiment"]["label"], "😐")
                    st.markdown(f"""
                    <div class="participant-card">
                        <div class="participant-avatar" style="background:{color}22;color:{color}">{initials}</div>
                        <div class="participant-info">
                            <div class="participant-name">{p['name']}</div>
                            <div class="participant-stats">{p['utterance_count']} utterances · {p['word_count']} words · {p['contribution_pct']}% {sent_icon}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info('No speaker data. Use "Name: text" format in transcript.')

        st.divider()

        # ── Productivity Score ──
        st.markdown('<div class="section-header"><span class="icon">🎯</span> Meeting Productivity Score</div>', unsafe_allow_html=True)
        ps = result.get("productivity_score", {})
        breakdown = ps.get("breakdown", {})

        col_gauge, col_breakdown = st.columns([1, 1])
        with col_gauge:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=ps.get("total", 0),
                number={"suffix": "%", "font": {"size": 48, "color": "#e2e8f0", "family": "Inter"}},
                title={"text": f"<b>{ps.get('grade', 'N/A')}</b> — {ps.get('label', '')}", "font": {"size": 16, "color": "#94a3b8"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#334155"},
                    "bar": {"color": "#7c3aed", "thickness": 0.25},
                    "bgcolor": "rgba(15,12,41,0.3)",
                    "bordercolor": "rgba(124,58,237,0.2)",
                    "steps": [
                        {"range": [0, 30], "color": "rgba(239,68,68,0.15)"},
                        {"range": [30, 60], "color": "rgba(251,191,36,0.15)"},
                        {"range": [60, 100], "color": "rgba(52,211,153,0.15)"},
                    ],
                    "threshold": {"line": {"color": "#a78bfa", "width": 3}, "thickness": 0.8, "value": ps.get("total", 0)},
                },
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"), height=280, margin=dict(l=30, r=30, t=60, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_breakdown:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            components = [
                ("⚡ Action Density", breakdown.get("action_density", 0), 25, "#a78bfa"),
                ("⚖️ Decision Ratio", breakdown.get("decision_ratio", 0), 25, "#38bdf8"),
                ("👥 Participation", breakdown.get("participation_balance", 0), 25, "#34d399"),
                ("⚠️ Risk Awareness", breakdown.get("risk_awareness", 0), 15, "#fbbf24"),
                ("📖 Clarity", breakdown.get("clarity", 0), 10, "#f472b6"),
            ]
            for name, val, max_val, color in components:
                pct = val / max_val if max_val > 0 else 0
                st.markdown(f"**{name}** — {val:.1f}/{max_val}")
                st.progress(min(pct, 1.0))
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Keywords ──
        st.divider()
        st.markdown('<div class="section-header"><span class="icon">🏷️</span> Top Keywords</div>', unsafe_allow_html=True)
        keywords = result.get("keywords", [])
        if keywords:
            kw_html = ""
            for i, k in enumerate(keywords[:20]):
                color = COLORS[i % len(COLORS)]
                size = max(13, min(22, k["count"] * 2 + 12))
                kw_html += f'<span class="keyword-tag" style="background:{color}1a;color:{color};font-size:{size}px">{k["word"]}</span>'
            st.markdown(kw_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  PAGE: KNOWLEDGE BASE
# ═══════════════════════════════════════════

elif page == "📚 Knowledge Base":
    st.markdown('<h1 class="hero-header">Knowledge Base</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Browse, search, and manage your analyzed meetings</p>', unsafe_allow_html=True)

    search_query = st.text_input("🔍 Search meetings", placeholder="Search by title, content, or keywords...")

    if search_query:
        meetings = kb.search(search_query)
        st.caption(f"Found **{len(meetings)}** results for \"{search_query}\"")
    else:
        meetings = kb.list_meetings()

    if not meetings:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📚</div>
            <p>No meetings stored yet.<br>Analyze your first meeting to see it here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for m in meetings:
            score = m.get("productivity_score", 0)
            sentiment = m.get("sentiment", "neutral")
            sent_icon = {"positive": "😊", "negative": "😟", "neutral": "😐"}.get(sentiment, "😐")

            with st.expander(f"📄 {m['title']} — {str(m.get('date', ''))[:10]}", expanded=False):
                cols = st.columns(4)
                cols[0].metric("✅ Tasks", m.get("tasks_count", 0))
                cols[1].metric("⚖️ Decisions", m.get("decisions_count", 0))
                cols[2].metric("🎯 Score", f"{score}/100")
                cols[3].metric(f"{sent_icon} Sentiment", sentiment.capitalize())

                summary = m.get("short_summary", "")
                if summary:
                    st.markdown(f"**Summary:** {summary}")
                st.caption(f"📝 {m.get('word_count', 0)} words · 👥 {m.get('speakers_count', 0)} speakers")

                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("📂 Load Analysis", key=f"view_{m['id']}", use_container_width=True):
                        full = kb.get(m["id"])
                        if full:
                            st.session_state["current_result"] = full["analysis"]
                            st.session_state["current_title"] = full["title"]
                            st.session_state["current_transcript"] = full["transcript"]
                            st.success("✅ Loaded! Go to Results Dashboard.")
                with btn2:
                    if st.button("🗑️ Delete", key=f"del_{m['id']}", use_container_width=True, type="secondary"):
                        kb.delete(m["id"])
                        st.rerun()


# ═══════════════════════════════════════════
#  PAGE: ANALYTICS
# ═══════════════════════════════════════════

elif page == "📈 Analytics":
    st.markdown('<h1 class="hero-header">Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Cross-meeting insights and trends</p>', unsafe_allow_html=True)

    data = analytics_engine.get_dashboard_data()
    if not data:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">📈</div>
            <p>No meeting data yet.<br>Analyze a few meetings to see trends here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        overview = data["overview"]

        render_metric_row([
            (str(overview["total"]), "Meetings"),
            (str(overview["total_tasks"]), "Total Tasks"),
            (str(overview["total_decisions"]), "Decisions"),
            (f"{overview['avg_words']:,}", "Avg Words"),
            (f"{overview['avg_productivity']}", "Avg Score"),
        ])

        st.divider()

        # Productivity Trend
        trend = data.get("productivity_trend", [])
        if trend:
            st.markdown('<div class="section-header"><span class="icon">📈</span> Productivity Trend</div>', unsafe_allow_html=True)
            fig = px.line(trend, x="title", y="score", markers=True,
                          color_discrete_sequence=["#7c3aed"])
            fig.update_layout(**PLOTLY_LAYOUT, height=320)
            fig.update_traces(line=dict(width=3), marker=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)

        # Action & Decision Trend
        action_trend = data.get("action_trend", [])
        if action_trend:
            st.markdown('<div class="section-header"><span class="icon">📊</span> Tasks & Decisions</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Tasks", x=[a["title"] for a in action_trend], y=[a["tasks"] for a in action_trend],
                                 marker_color="#a78bfa", marker_line_width=0))
            fig.add_trace(go.Bar(name="Decisions", x=[a["title"] for a in action_trend], y=[a["decisions"] for a in action_trend],
                                 marker_color="#38bdf8", marker_line_width=0))
            fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=320, legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            sentiments = data.get("sentiment_distribution", {})
            if sentiments:
                st.markdown('<div class="section-header"><span class="icon">💭</span> Sentiment</div>', unsafe_allow_html=True)
                fig = px.pie(values=list(sentiments.values()), names=list(sentiments.keys()),
                             color_discrete_map={"positive": "#34d399", "neutral": "#64748b", "negative": "#f87171"},
                             hole=0.45)
                fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            pf = data.get("participant_frequency", {})
            if pf:
                st.markdown('<div class="section-header"><span class="icon">👥</span> Top Participants</div>', unsafe_allow_html=True)
                fig = px.bar(x=list(pf.values()), y=list(pf.keys()), orientation="h",
                             color=list(pf.values()), color_continuous_scale=[[0, "#4f46e5"], [1, "#a78bfa"]])
                fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, coloraxis_showscale=False)
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)

        tf = data.get("topic_frequency", {})
        if tf:
            st.markdown('<div class="section-header"><span class="icon">🗂️</span> Popular Topics</div>', unsafe_allow_html=True)
            fig = px.bar(x=list(tf.keys())[:12], y=list(tf.values())[:12],
                         color=list(tf.values())[:12], color_continuous_scale=[[0, "#0ea5e9"], [1, "#38bdf8"]])
            fig.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False, coloraxis_showscale=False)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════
#  PAGE: GENERATE REPORT
# ═══════════════════════════════════════════

elif page == "📧 Generate Report":
    st.markdown('<h1 class="hero-header">Generate Report</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Auto-generate professional follow-up emails and meeting reports</p>', unsafe_allow_html=True)

    source = st.radio("Meeting source", ["Current Analysis", "From Knowledge Base"], horizontal=True)

    result = None
    title = "Meeting"

    if source == "Current Analysis":
        result = st.session_state.get("current_result")
        title = st.session_state.get("current_title", "Meeting")
        if not result:
            st.info("No current analysis. Analyze a meeting first or select from Knowledge Base.")
    else:
        meetings = kb.list_meetings()
        if meetings:
            selected = st.selectbox("Select meeting",
                                    meetings,
                                    format_func=lambda m: f"{m['title']} ({str(m.get('date', ''))[:10]})")
            if selected:
                full = kb.get(selected["id"])
                if full:
                    result = full["analysis"]
                    title = full["title"]
        else:
            st.info("No meetings in Knowledge Base.")

    if result:
        st.divider()

        col_fmt, col_llm_opt = st.columns([2, 1])
        with col_fmt:
            report_type = st.selectbox("📄 Report Format", ["📧 Email Follow-Up", "📝 Detailed Markdown", "🌐 HTML Report"])
        with col_llm_opt:
            use_llm_report = st.checkbox("🤖 Enhance with LLM", value=ollama_ok, disabled=not ollama_ok)

        if st.button("📧 Generate Report", type="primary", use_container_width=True):
            with st.spinner("✨ Generating report..."):
                if "Email" in report_type:
                    if use_llm_report and ollama_ok:
                        report = llm.generate_email_report(result, title)
                        if not report:
                            report = report_gen.generate_email(result, title)
                    else:
                        report = report_gen.generate_email(result, title)
                elif "Markdown" in report_type:
                    report = report_gen.generate_markdown(result, title)
                else:
                    report = report_gen.generate_html(result, title)

                st.session_state["generated_report"] = report
                st.session_state["report_type"] = report_type

        if "generated_report" in st.session_state:
            report = st.session_state["generated_report"]
            r_type = st.session_state.get("report_type", "")
            st.divider()
            st.markdown('<div class="section-header"><span class="icon">📄</span> Generated Report</div>', unsafe_allow_html=True)

            if "HTML" in r_type:
                st.components.v1.html(report, height=700, scrolling=True)
            else:
                st.code(report, language="markdown" if "Markdown" in r_type else "text")

            ext = "html" if "HTML" in r_type else ("md" if "Markdown" in r_type else "txt")
            st.download_button(f"⬇️ Download .{ext}", report,
                               file_name=f"meeting_report_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}",
                               mime="text/plain", use_container_width=True)


# ═══════════════════════════════════════════
#  PAGE: SETTINGS
# ═══════════════════════════════════════════

elif page == "⚙️ Settings":
    st.markdown('<h1 class="hero-header">Settings</h1>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="icon">🤖</span> Ollama LLM Configuration</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ollama_url = st.text_input("Ollama URL", value=config.OLLAMA_BASE_URL)
    with col2:
        ollama_model = st.text_input("Model Name", value=config.OLLAMA_MODEL)

    if st.button("🔌 Test Connection", use_container_width=True):
        test_llm = OllamaEngine(ollama_url, ollama_model)
        if test_llm.is_available():
            st.success(f"✅ Connected! Model `{ollama_model}` is available.")
            models = test_llm.list_models()
            if models:
                st.info(f"Available models: `{'`, `'.join(models)}`")
        else:
            st.error("❌ Cannot connect to Ollama.")
            st.code(f"# Install: https://ollama.ai\n# Then:\nollama pull {ollama_model}", language="bash")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="icon">📚</span> Knowledge Base</div>', unsafe_allow_html=True)
    mc = len(kb.list_meetings())
    st.metric("Stored Meetings", mc)
    if mc > 0:
        if st.button("🗑️ Clear All Meetings", type="secondary", use_container_width=True):
            for m in kb.list_meetings():
                kb.delete(m["id"])
            st.success("✅ All meetings cleared.")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="icon">ℹ️</span> About MeetMind</div>', unsafe_allow_html=True)
    st.markdown("""
    **MeetMind v3.0** — AI Meeting Summarizer with Advanced NLP

    | Component | Technology |
    |-----------|-----------|
    | NLP Engine | spaCy + NLTK + scikit-learn |
    | LLM | Ollama (local, optional) |
    | Summarization | TF-IDF + positional weighting |
    | Task Extraction | Pattern + spaCy NER |
    | Knowledge Base | SQLite + FTS5 |
    | Charts | Plotly |
    | Reports | Jinja2 templates |
    | Dashboard | Streamlit |
    """)
    st.caption("🎓 Built for semester research · AI-Powered NLP")
    st.markdown('</div>', unsafe_allow_html=True)
