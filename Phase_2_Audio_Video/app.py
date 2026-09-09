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
import re

import config
from nlp_engine import MeetingAnalyzer
from llm_engine import OllamaEngine
from knowledge_base import KnowledgeBase
from report_generator import ReportGenerator
from analytics import MeetingAnalytics
from transcription_engine import TranscriptionEngine
from auth import AuthManager
from calendar_manager import CalendarManager


st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded",
)

# ── Premium CSS Theme ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        font-family: 'DM Sans', sans-serif;
        background: #08111d;
        color: #edf4f1;
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

    /* ── Product surface refresh ── */
    :root {
        --canvas: #08111d;
        --panel: #101d2b;
        --panel-soft: #142536;
        --line: rgba(198, 220, 215, 0.13);
        --muted: #9aafb0;
        --ink: #edf4f1;
        --mint: #69e0bd;
        --coral: #ff8b75;
        --blue: #7bb8ff;
    }
    .stApp:before {
        content: '';
        position: fixed;
        inset: 0;
        pointer-events: none;
        background: radial-gradient(circle at 88% 4%, rgba(105, 224, 189, 0.09), transparent 28%),
                    radial-gradient(circle at 12% 90%, rgba(123, 184, 255, 0.08), transparent 30%);
    }
    .main .block-container {
        max-width: 1440px;
        padding: 2.2rem clamp(1rem, 4vw, 4rem) 4rem;
    }
    .stApp p, .stApp li, .stApp span, .stApp div { color: var(--ink); }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.02em; }
    .top-shell {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0 0 1.6rem;
        margin-bottom: 1.4rem;
        border-bottom: 1px solid var(--line);
    }
    .breadcrumb { color: var(--muted); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em; }
    .breadcrumb span { color: var(--mint); padding: 0 0.35rem; }
    .shell-title { color: var(--ink); font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 600; margin-top: 0.35rem; }
    .shell-actions { display: flex; align-items: center; gap: 0.55rem; color: var(--muted); font-size: 0.78rem; white-space: nowrap; }
    .engine-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--mint); box-shadow: 0 0 0 4px rgba(105,224,189,0.1), 0 0 14px rgba(105,224,189,0.65); }
    .shell-avatar { display: grid; place-items: center; width: 30px; height: 30px; margin-left: 0.7rem; border: 1px solid rgba(123,184,255,0.35); border-radius: 50%; background: rgba(123,184,255,0.15); color: #c7ddff !important; font-size: 0.68rem; font-weight: 700; }
    .eyebrow { color: var(--mint) !important; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; margin-bottom: 0.9rem; }
    .nav-group-label { color: #6e858b !important; font-size: 0.64rem; font-weight: 700; letter-spacing: 0.13em; margin: 1rem 0 0.5rem; padding-left: 0.2rem; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0b1724 !important;
        border-right: 1px solid var(--line);
        width: 288px !important;
        min-width: 288px !important;
        max-width: 288px !important;
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #c4b5fd; }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c4b5fd !important;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stRadio > div > label { border: 1px solid transparent; border-radius: 10px; padding: 0.22rem 0.35rem; transition: background 0.2s ease, border-color 0.2s ease; }
    section[data-testid="stSidebar"] .stRadio > div > label:hover { background: rgba(105,224,189,0.06); border-color: rgba(105,224,189,0.16); }

    /* ── Hero Header ── */
    .hero-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(2.2rem, 5vw, 4.5rem);
        font-weight: 900;
        color: #edf4f1;
        -webkit-background-clip: text;
        line-height: 1.1;
        margin: 0 0 10px;
        letter-spacing: -2px;
    }
    @keyframes gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }

    .hero-sub {
        color: var(--muted);
        font-size: 1.05rem;
        font-weight: 400;
        max-width: 780px;
        margin-bottom: 1.8rem;
        line-height: 1.6;
    }

    /* ── Glass Cards ── */
    .glass-card {
        background: rgba(16, 29, 43, 0.92);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: clamp(18px, 3vw, 30px);
        .stCaption, [data-testid="stCaptionContainer"] { color: #9ca3af !important; }
        /* ── MeetMind product system ── */
        :root {
            --canvas: #0a0f14;
            --panel: #111820;
            --panel-raised: #17212b;
            --line: #2a3946;
            --line-soft: rgba(160, 184, 193, 0.14);
            --ink: #eef4f3;
            --muted: #91a2aa;
            --accent: #63d5bd;
            --accent-strong: #3eb29e;
            --blue: #83b9e8;
            --warning: #e7b86d;
        }
        .stApp { background: var(--canvas) !important; color: var(--ink) !important; }
        .stApp:before {
            display: block;
            background: linear-gradient(135deg, rgba(99, 213, 189, 0.05), transparent 32%),
                        linear-gradient(315deg, rgba(131, 185, 232, 0.04), transparent 38%);
        }
        .main .block-container { max-width: 1280px; padding: 2.5rem clamp(1.25rem, 4vw, 4.5rem) 5rem; }
        h1, h2, h3, h4, .hero-header, .page-heading, .shell-title { font-family: 'Space Grotesk', sans-serif !important; }
        h1, h2, h3, h4 { letter-spacing: -0.01em !important; }
        .top-shell { border-bottom-color: var(--line); padding-bottom: 1.25rem; margin-bottom: 2.25rem; }
        .breadcrumb, .nav-group-label { color: #6f838d !important; letter-spacing: 0.11em; }
        .shell-title { color: var(--ink) !important; font-size: 1.08rem; }
        .hero-header { color: var(--ink) !important; font-size: clamp(2.35rem, 5vw, 4.2rem); line-height: 1.02; letter-spacing: -0.045em !important; max-width: 900px; }
        .hero-sub, .page-description { color: var(--muted) !important; max-width: 720px; line-height: 1.7; }
        section[data-testid="stSidebar"] { background: #0d141b !important; border-right: 1px solid var(--line) !important; width: 250px !important; min-width: 250px !important; max-width: 250px !important; }
        .logo-container { padding: 1.05rem 0.35rem 1.35rem; margin-bottom: 1.4rem; border-bottom-color: var(--line); }
        .logo-icon { width: 34px; height: 34px; border-radius: 9px; background: var(--accent); color: #09221d; font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 1rem; }
        .logo-text .name { color: var(--ink); font-family: 'Space Grotesk', sans-serif; font-size: 1.08rem; letter-spacing: -0.02em; }
        .logo-text .sub { color: var(--muted); font-size: 0.66rem; }
        section[data-testid="stSidebar"] .stRadio > div { gap: 0.24rem; }
        section[data-testid="stSidebar"] .stRadio > div > label { border-radius: 8px; padding: 0.45rem 0.65rem; border: 1px solid transparent; }
        section[data-testid="stSidebar"] .stRadio > div > label:hover { background: rgba(99, 213, 189, 0.07); border-color: rgba(99, 213, 189, 0.12); }
        section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] { background: rgba(99, 213, 189, 0.12); border-color: rgba(99, 213, 189, 0.25); }
        section[data-testid="stSidebar"] .stRadio label, .stRadio > div > label > div > p { color: #c7d4d7 !important; font-size: 0.88rem !important; font-weight: 600 !important; }
        .glass-card, .metric-card, .task-card, .participant-card, .history-card, .chart-container { background: var(--panel) !important; border: 1px solid var(--line-soft) !important; border-radius: 10px !important; }
        .glass-card { padding: 1.35rem; box-shadow: 0 18px 45px rgba(0, 0, 0, 0.12); }
        .glass-card:hover, .metric-card:hover, .history-card:hover { border-color: rgba(99, 213, 189, 0.38) !important; }
        .metric-row { gap: 0.75rem; margin: 1.4rem 0 2rem; }
        .metric-card { padding: 1.15rem; }
        .metric-card .value { color: var(--accent) !important; font-family: 'Space Grotesk', sans-serif; font-size: 1.65rem; }
        .metric-card .label { color: var(--muted) !important; }
        .section-header { color: var(--ink); font-size: 1.18rem; font-family: 'Space Grotesk', sans-serif; }
        .section-header .icon { display: none; }
        .decision-card, .risk-card { background: var(--panel-raised) !important; border-left: 3px solid var(--accent) !important; border-radius: 0 8px 8px 0 !important; }
        .task-card { padding: 1rem 1.1rem; }
        .task-card .task-text { color: var(--ink); }
        .task-card .task-meta span { color: var(--muted); }
        .stTextArea textarea, .stTextInput input, .stDateInput input, .stTimeInput input { background: #0d151d !important; border: 1px solid #334653 !important; border-radius: 8px !important; color: var(--ink) !important; }
        .stTextArea textarea:focus, .stTextInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 1px var(--accent) !important; }
        .stSelectbox > div > div { background: #0d151d !important; border: 1px solid #334653 !important; border-radius: 8px !important; }
        button[data-testid="stBaseButton-primary"] { background: var(--accent-strong) !important; color: #071713 !important; border: 0 !important; border-radius: 8px !important; font-weight: 800 !important; box-shadow: 0 8px 24px rgba(62, 178, 158, 0.16) !important; }
        button[data-testid="stBaseButton-primary"]:hover { background: var(--accent) !important; transform: translateY(-1px); }
        button[data-testid="stBaseButton-secondary"], .stDownloadButton button { background: transparent !important; border: 1px solid #3a4e5a !important; color: #dbe6e6 !important; border-radius: 8px !important; }
        button[data-testid="stBaseButton-secondary"]:hover, .stDownloadButton button:hover { background: rgba(99, 213, 189, 0.08) !important; border-color: var(--accent) !important; }
        .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--line); gap: 1.5rem; }
        .stTabs [data-baseweb="tab"] { color: var(--muted) !important; padding: 0.7rem 0.1rem; }
        .stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }
        .stExpander { background: var(--panel) !important; border: 1px solid var(--line) !important; border-radius: 9px !important; }
        div[data-testid="stMetric"] { background: var(--panel) !important; border: 1px solid var(--line-soft); border-radius: 9px; }
        div[data-testid="stMetricValue"] { color: var(--ink) !important; }
        div[data-testid="stMetricLabel"] { color: var(--muted) !important; }
        .stProgress > div > div > div { background: var(--accent) !important; }
        .stAlert { border-radius: 8px !important; }
        .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }
        @media (max-width: 760px) {
            section[data-testid="stSidebar"] { width: min(86vw, 280px) !important; min-width: min(86vw, 280px) !important; max-width: min(86vw, 280px) !important; }
            .main .block-container { padding: 1.4rem 1rem 3rem; }
            .hero-header { font-size: 2.55rem; }
            .metric-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.16);
    }
    .glass-card:hover {
        border-color: rgba(105, 224, 189, 0.32);
    }

    /* ── Metric Cards ── */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 14px;
        margin: 20px 0;
    }
    .metric-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: rgba(105, 224, 189, 0.38);
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.12);
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--mint);
        background: none;
        -webkit-background-clip: text;
        -webkit-text-fill-color: var(--mint);
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
        background: rgba(105, 224, 189, 0.08);
        border: 1px solid rgba(105, 224, 189, 0.2);
        color: #a8e8d4;
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
        color: var(--ink);
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
        background: var(--mint);
        color: #092019;
        border-radius: 10px;
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
        background: rgba(105, 224, 189, 0.08);
        border: 1px solid rgba(105, 224, 189, 0.2);
        color: #a8e8d4;
        padding: 6px 14px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        text-align: center;
        margin-top: 16px;
    }

    /* ── Plotly Chart Containers ── */
    .chart-container {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    @media (max-width: 760px) {
        section[data-testid="stSidebar"] {
            width: min(86vw, 288px) !important;
            min-width: min(86vw, 288px) !important;
            max-width: min(86vw, 288px) !important;
        }
        .main .block-container { padding: 1.4rem 1rem 3rem; }
        .hero-header { font-size: 2.35rem; letter-spacing: -1px; }
        .pill-row { gap: 6px; }
        .pill { font-size: 0.74rem; padding: 5px 9px; }
        .top-shell { align-items: flex-start; }
        .shell-actions { font-size: 0; }
        .shell-actions .engine-dot { font-size: initial; }
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

    /* ── Calm product theme ── */
    .stApp { background: #0b1118; font-family: 'DM Sans', sans-serif; }
    .stApp:before { display: none; }
    .main .block-container { max-width: 1180px; padding: 1.5rem 2.5rem 3.5rem; }
    .top-shell { padding: 0 0 1rem; margin-bottom: 1.8rem; border-bottom: 1px solid #263342; }
    .breadcrumb { color: #7f8b98; font-size: 0.72rem; letter-spacing: 0.02em; text-transform: none; }
    .breadcrumb span { color: #7f8b98; padding: 0 0.3rem; }
    .shell-title { color: #f3f4f6; font-size: 1rem; font-weight: 600; }
    .shell-actions { color: #9ca3af; }
    .engine-dot { width: 7px; height: 7px; background: #6f9f87; box-shadow: none; }
    .shell-avatar { display: none; }
    .eyebrow, .nav-group-label { color: #9ca3af !important; font-size: 0.72rem; letter-spacing: 0.03em; }
    .page-heading { color: #f3f4f6; font-family: 'DM Sans', sans-serif; font-size: 2rem; font-weight: 600; margin: 0 0 0.35rem; }
    .page-description { color: #9ca3af !important; font-size: 1rem; margin-bottom: 1.5rem; }
    .hero-header { color: #f3f4f6; font-family: 'DM Sans', sans-serif; font-size: 2rem; font-weight: 600; letter-spacing: -0.02em; }
    .hero-sub { color: #9ca3af; font-size: 1rem; max-width: 680px; }
    section[data-testid="stSidebar"] { background: #111a24 !important; border-right: 1px solid #263342; width: 230px !important; min-width: 230px !important; max-width: 230px !important; }
    .logo-container { padding: 0.8rem 0.2rem 1.2rem; margin-bottom: 1rem; border-bottom: 1px solid #263342; }
    .logo-icon { width: 30px; height: 30px; background: #7c5cfc; border-radius: 7px; font-size: 0; }
    .logo-icon:after { content: 'M'; color: #fff; font-size: 0.9rem; font-weight: 700; }
    .logo-text .name { font-size: 1rem; }
    .logo-text .sub { color: #9ca3af; font-size: 0.7rem; letter-spacing: 0; text-transform: none; }
    section[data-testid="stSidebar"] .stRadio > div > label { border-radius: 7px; padding: 0.12rem 0.25rem; }
    section[data-testid="stSidebar"] .stRadio > div > label:hover { background: #1a2633; border-color: transparent; }
    section[data-testid="stSidebar"] .stRadio label, .stRadio > div > label > div > p { color: #c9d1d9 !important; font-size: 0.9rem !important; font-weight: 500 !important; }
    .glass-card, .metric-card, .task-card, .participant-card, .history-card, .chart-container { background: #111a24; border: 1px solid #263342; border-radius: 8px; box-shadow: none; }
    .glass-card { padding: 1.25rem; }
    .glass-card:hover, .metric-card:hover, .history-card:hover { border-color: #3a4b5d; box-shadow: none; transform: none; }
    .metric-row { gap: 10px; margin: 1.25rem 0; }
    .metric-card { padding: 1rem; text-align: left; }
    .metric-card .value { color: #f3f4f6; font-size: 1.45rem; -webkit-text-fill-color: #f3f4f6; }
    .metric-card .label { color: #9ca3af; font-size: 0.82rem; text-transform: none; letter-spacing: 0; font-weight: 500; }
    .pill-row { display: none; }
    .section-header { color: #f3f4f6; font-size: 1.15rem; margin: 1.5rem 0 0.75rem; }
    .section-header .icon { display: none; }
    .decision-card, .risk-card { background: #141f2b; border-left: 2px solid #7c5cfc; border-radius: 4px; padding: 0.8rem 1rem; }
    .task-card { padding: 0.8rem 1rem; margin-bottom: 0.5rem; }
    .task-card .task-text { color: #f3f4f6; margin-bottom: 0.35rem; }
    .task-card .task-meta span { color: #9ca3af; }
    .stTextArea textarea, .stTextInput input { background: #0f1720 !important; border: 1px solid #334252 !important; border-radius: 6px !important; color: #f3f4f6 !important; }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #7c5cfc !important; box-shadow: 0 0 0 1px #7c5cfc !important; }
    .stSelectbox > div > div { background: #0f1720 !important; border: 1px solid #334252 !important; border-radius: 6px !important; }
    button[data-testid="stBaseButton-primary"] { background: #7c5cfc !important; border-radius: 6px !important; box-shadow: none !important; padding: 0.55rem 1rem !important; }
    button[data-testid="stBaseButton-primary"]:hover { background: #6d4ee8 !important; transform: none; }
    button[data-testid="stBaseButton-secondary"], .stDownloadButton button { background: #17222e !important; border: 1px solid #334252 !important; border-radius: 6px !important; color: #d7dee7 !important; }
    button[data-testid="stBaseButton-secondary"]:hover, .stDownloadButton button:hover { background: #202e3c !important; }
    .stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #263342; border-radius: 0; padding: 0; gap: 1.2rem; }
    .stTabs [data-baseweb="tab"] { border-radius: 0 !important; padding: 0.65rem 0.1rem; color: #9ca3af !important; }
    .stTabs [aria-selected="true"] { background: transparent !important; color: #f3f4f6 !important; border-bottom: 2px solid #7c5cfc; }
    .stExpander { background: #111a24 !important; border: 1px solid #263342 !important; border-radius: 8px !important; }
    .stDivider { border-color: #263342 !important; }
    div[data-testid="stMetric"] { background: #111a24; border: 1px solid #263342; border-radius: 8px; }
    div[data-testid="stMetricLabel"] { color: #9ca3af !important; }
    .stProgress > div > div > div { background: #7c5cfc !important; }
    .stCaption, [data-testid="stCaptionContainer"] { color: #9ca3af !important; }
    /* Final product pass: neutral workspace entry and teal actions. */
    .auth-intro { max-width: 1120px; margin: 0 auto; }
    .auth-intro .hero-header { max-width: 760px; font-size: clamp(2.5rem, 5vw, 4.4rem); letter-spacing: -0.045em; }
    .auth-intro .hero-sub { max-width: 650px; font-size: 1.05rem; }
    button[data-testid="stBaseButton-primary"], button[kind="primary"] { background: #3eb29e !important; color: #071713 !important; border: 0 !important; border-radius: 8px !important; font-weight: 800 !important; box-shadow: 0 8px 22px rgba(62, 178, 158, 0.18) !important; }
    button[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover { background: #63d5bd !important; }
    .stTabs [aria-selected="true"] { color: #63d5bd !important; border-bottom-color: #63d5bd !important; }
    .stApp { background: #0a0f14 !important; }
    @media (max-width: 760px) { .main .block-container { padding: 1rem 1rem 2.5rem; } .top-shell { margin-bottom: 1.2rem; } .shell-actions { display: none; } }
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

@st.cache_resource
def get_transcriber():
    return TranscriptionEngine()

@st.cache_resource
def get_auth():
    return AuthManager(config.DB_PATH)

@st.cache_resource
def get_calendar():
    return CalendarManager(config.DB_PATH)

analyzer = get_analyzer()
kb = get_kb()
llm = get_llm()
transcriber = get_transcriber()
report_gen = ReportGenerator()
analytics_engine = MeetingAnalytics(kb)
auth = get_auth()
calendar = get_calendar()


def render_authentication():
    """Render the public sign-in/register boundary for private meeting data."""
    st.markdown('<div class="auth-intro">', unsafe_allow_html=True)
    st.markdown('<div class="top-shell"><div><div class="breadcrumb">MEETMIND WORKSPACE</div><div class="shell-title">Meeting intelligence platform</div></div><div class="shell-actions"><span class="engine-dot"></span><span>Private workspace</span></div></div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-header">Bring every meeting into focus.</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">A secure workspace for multilingual transcripts, decisions, action items, deadlines and institutional memory.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    sign_in, sign_up = st.tabs(["Sign in", "Create account"])
    with sign_in:
        with st.form("sign_in_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            user = auth.authenticate(email, password)
            if user:
                st.session_state["current_user"] = user
                st.rerun()
            st.error("Invalid email or password.")
    with sign_up:
        with st.form("sign_up_form"):
            name = st.text_input("Name")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            organization = st.text_input("Organization name")
            organization_type = st.selectbox(
                "Organization type",
                ["Student Team", "Company", "College", "School", "University", "Hospital", "NGO", "Research Lab"],
            )
            submitted = st.form_submit_button("Create account", type="primary")
        if submitted:
            try:
                st.session_state["current_user"] = auth.register(name, email, password, organization, organization_type)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


current_user = st.session_state.get("current_user")
if not current_user:
    render_authentication()
    st.stop()
kb.set_actor(current_user["id"], current_user["organization_id"])
calendar.set_actor(current_user["id"], current_user["organization_id"])

# ── Plotly Dark Theme ──
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="rgba(124,58,237,0.08)", zerolinecolor="rgba(124,58,237,0.08)"),
    yaxis=dict(gridcolor="rgba(124,58,237,0.08)", zerolinecolor="rgba(124,58,237,0.08)"),
)


def safe_read_uploaded_audio(uploaded_file):
    """Validate and persist uploaded audio to a temp file for processing."""
    if uploaded_file is None:
        return None

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in config.SUPPORTED_AUDIO_EXTENSIONS:
        raise ValueError("Unsupported audio format. Please upload MP3, WAV, M4A, MP4, or WEBM.")

    try:
        file_size = uploaded_file.size
        max_size = config.MAX_AUDIO_FILE_SIZE_BYTES
        if file_size <= 0:
            raise ValueError("The uploaded audio file is empty or corrupted.")
        if file_size > max_size:
            raise ValueError(f"Audio file is too large ({file_size / (1024 * 1024):.1f} MB). Keep it under {config.MAX_AUDIO_FILE_SIZE_MB} MB.")
    except Exception:
        raise

    temp_dir = config.TEMP_DIR
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"upload_{uuid.uuid4().hex}{ext}")
    with open(temp_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())
    return temp_path


def retrieve_memory_matches(query: str, limit: int = 5) -> list:
    """Rank saved meetings by overlap with the user's question."""
    terms = set(re.findall(r"[a-z0-9]{3,}", query.lower()))
    matches = []
    for meeting in kb.list_meetings(limit=100):
        full = kb.get(meeting["id"])
        if not full:
            continue
        analysis = full.get("analysis", {})
        tasks = analysis.get("tasks", [])
        decisions = analysis.get("decisions", [])
        searchable = " ".join([
            full.get("title", ""), full.get("transcript", ""),
            full.get("short_summary", ""), full.get("detailed_summary", ""),
            " ".join(task.get("task", "") for task in tasks),
            " ".join(decisions),
        ]).lower()
        score = sum(searchable.count(term) for term in terms)
        if score:
            matches.append((score, full))
    matches.sort(key=lambda item: (item[0], item[1].get("date", "")), reverse=True)
    return [meeting for _, meeting in matches[:limit]]


def answer_memory_question(query: str, meetings: list) -> str:
    """Answer from retrieved meetings, with a deterministic offline fallback."""
    evidence = []
    for meeting in meetings:
        analysis = meeting.get("analysis", {})
        tasks = analysis.get("tasks", [])
        decisions = analysis.get("decisions", [])
        evidence.append(
            f"Meeting: {meeting.get('title', 'Untitled')} ({str(meeting.get('date', ''))[:10]})\n"
            f"Summary: {analysis.get('short_summary', meeting.get('short_summary', ''))}\n"
            f"Decisions: {'; '.join(decisions[:6]) or 'None detected'}\n"
            f"Action items: {'; '.join(task.get('task', '') for task in tasks[:6]) or 'None detected'}"
        )
    context = "\n\n".join(evidence)
    if ollama_ok:
        prompt = (
            "Answer the user's question using only the meeting records below. "
            "Cite meeting titles and dates in your answer. If the records do not contain "
            "the answer, say that clearly instead of guessing.\n\n"
            f"User question: {query}\n\nMeeting records:\n{context}"
        )
        response = llm._generate(prompt, "You are MeetMind's meeting memory assistant. Be precise and concise.")
        if response:
            return response
    return "No matching saved meeting contains enough information to answer that question.\n\n" + context


def get_accountability_tasks() -> list:
    """Flatten saved meeting tasks into tracker-friendly records."""
    records = []
    for meeting in kb.list_meetings(limit=100):
        full = kb.get(meeting["id"])
        if not full:
            continue
        for index, task in enumerate(full.get("analysis", {}).get("tasks", [])):
            deadline = str(task.get("deadline", "Not specified"))
            due_date = None
            if deadline.lower() not in {"not specified", "unknown", "none", ""}:
                due_date = ReportGenerator._parse_calendar_date(deadline, datetime.now()).date()
            records.append({
                "meeting_id": full["id"], "task_index": index,
                "meeting": full.get("title", "Untitled"), "task": task.get("task", ""),
                "assignee": task.get("assignee", "Team"), "deadline": deadline,
                "due_date": due_date, "priority": task.get("priority", "low"),
                "status": task.get("status", "pending"),
            })
    return records


def quality_recommendations(analysis: dict) -> list:
    """Generate explainable coaching advice from meeting measurements."""
    advice = []
    score = analysis.get("productivity_score", {})
    breakdown = score.get("breakdown", {})
    tasks = analysis.get("tasks", [])
    decisions = analysis.get("decisions", [])
    participants = analysis.get("participants", [])
    if not tasks:
        advice.append(("Follow-up gap", "No action items were detected. End the next meeting with an owner and deadline for every commitment."))
    elif sum(1 for task in tasks if task.get("deadline", "Not specified") in {"Not specified", "Unknown"}) > 0:
        advice.append(("Deadline clarity", "Some tasks have no deadline. Add a date before closing the meeting so the tracker can flag risk."))
    if not decisions:
        advice.append(("Decision clarity", "No firm decisions were detected. Use an explicit decision statement and record the decision owner."))
    if breakdown.get("participation_balance", 25) < 15:
        advice.append(("Participation balance", "One or more speakers dominated the discussion. Add a round-robin check-in or invite quieter participants directly."))
    if breakdown.get("clarity", 10) < 6:
        advice.append(("Communication clarity", "The transcript is difficult to follow. Use a short agenda, topic transitions, and a recap before moving on."))
    if analysis.get("risks") and not tasks:
        advice.append(("Risk ownership", "Risks were raised without follow-up tasks. Assign a mitigation owner and review date for each risk."))
    if score.get("total", 100) >= 80 and not advice:
        advice.append(("Keep the pattern", "This meeting has strong structure. Reuse its agenda and close with the same decision and action-item recap."))
    return advice


def get_governance_summary() -> dict:
    """Summarize follow-up and decision coverage across saved meetings."""
    meetings = kb.list_meetings(limit=100)
    needs_review = []
    meetings_with_tasks = 0
    meetings_with_decisions = 0

    for meeting in meetings:
        full = kb.get(meeting["id"])
        analysis = full.get("analysis", {}) if full else {}
        tasks = analysis.get("tasks", [])
        decisions = analysis.get("decisions", [])
        if tasks:
            meetings_with_tasks += 1
        if decisions:
            meetings_with_decisions += 1
        if not tasks or not decisions:
            needs_review.append({
                "title": meeting.get("title", "Untitled"),
                "date": str(meeting.get("date", ""))[:10],
                "reason": "No action items" if not tasks else "No decisions recorded",
            })

    tasks = get_accountability_tasks()
    today = datetime.now().date()
    open_tasks = [task for task in tasks if task["status"] != "done"]
    overdue_tasks = [
        task for task in open_tasks
        if task["due_date"] and task["due_date"] < today
    ]
    total = len(meetings)
    return {
        "total_meetings": total,
        "follow_up_rate": round(meetings_with_tasks / total * 100) if total else 0,
        "decision_rate": round(meetings_with_decisions / total * 100) if total else 0,
        "open_tasks": len(open_tasks),
        "overdue_tasks": len(overdue_tasks),
        "needs_review": needs_review[:8],
    }


# Need this at module scope for temp upload helper.
import uuid

COLORS = ["#a78bfa", "#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#fb923c", "#818cf8", "#2dd4bf"]


# ═══════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">M</div>
        <div class="logo-text">
            <div class="name">MeetMind</div>
            <div class="sub">Meeting Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-group-label">WORKSPACE</div>', unsafe_allow_html=True)
    navigation_labels = {
        "Analyze Meeting": "Analyze Meeting",
        "Meetings": "Meetings",
        "Calendar": "Calendar",
        "Knowledge Base": "Knowledge Base",
        "Dashboard": "Results Dashboard",
        "Analytics": "Analytics",
        "Memory Assistant": "Memory Assistant",
        "Quality Coach": "Quality Coach",
        "Action Items": "Accountability Center",
        "Reports": "Generate Report",
        "Settings": "Settings",
    }
    selected_navigation = st.radio(
        "Navigation",
        ["Analyze Meeting", "Meetings", "Calendar", "Knowledge Base", "Dashboard", "Analytics",
         "Memory Assistant", "Quality Coach", "Action Items", "Reports", "Settings"],
        label_visibility="collapsed",
    )
    page = navigation_labels[selected_navigation]

    st.markdown('<div class="nav-group-label">TOOLS & OUTPUT</div>', unsafe_allow_html=True)
    st.divider()

    # Ollama status
    ollama_ok = llm.is_available()
    meeting_count = len(kb.list_meetings())
    st.caption(f"{meeting_count} meetings")
    st.caption(f"{current_user['name']} · {current_user['role']}")
    if st.button("Sign out", type="secondary"):
        st.session_state.clear()
        st.rerun()


# ── Product shell ──
page_titles = {
    "Analyze Meeting": ("Analyze Meeting", "Workspace / New analysis"),
    "Meetings": ("Meetings", "Workspace / History"),
    "Calendar": ("Calendar", "Workspace / Deadlines"),
    "Results Dashboard": ("Meeting results", "Workspace / Results"),
    "Knowledge Base": ("Knowledge Base", "Workspace / Archive"),
    "Analytics": ("Analytics", "Insights / Trends"),
    "Memory Assistant": ("Memory Assistant", "AI tools / Recall"),
    "Accountability Center": ("Accountability Center", "Output / Action items"),
    "Quality Coach": ("Quality Coach", "AI tools / Coaching"),
    "Generate Report": ("Generate Report", "Output / Export"),
    "Settings": ("Settings", "System / Preferences"),
}
shell_title, shell_breadcrumb = page_titles.get(page, ("MeetMind", "Workspace"))
st.markdown(f"""
<div class="top-shell">
    <div>
        <div class="breadcrumb">MEETMIND <span>/</span> {shell_breadcrumb.upper()}</div>
        <div class="shell-title">{shell_title}</div>
    </div>
    <div class="shell-actions">
        <span class="engine-dot"></span><span>Ready</span>
        <span class="shell-avatar">DM</span>
    </div>
</div>
""", unsafe_allow_html=True)


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

if page == "Analyze Meeting":
    st.markdown('<h1 class="page-heading">Analyze a meeting</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-description">Upload a recording or paste a transcript to get a summary and action items.</p>', unsafe_allow_html=True)

    # Meeting input
    col1, col2 = st.columns([3, 1])
    with col1:
        default_title = st.session_state.get("_sample_title", "")
        meeting_title = st.text_input("Meeting title", value=default_title, placeholder="e.g., Product Strategy Meeting", label_visibility="visible")
    with col2:
        summary_len = st.slider("Summary length", 2, 12, 5)

    lang_col, output_col = st.columns(2)
    with lang_col:
        meeting_language = st.selectbox("Meeting language", list(config.SUPPORTED_LANGUAGES.keys()), index=0)
    with output_col:
        output_language = st.selectbox("Output language", ["English", "Hindi", "Marathi"], index=0)

    input_mode = st.radio(
        "Meeting input",
        ["Text transcript", "Audio recording", "Video recording"],
        horizontal=True,
        key="meeting_input_mode",
    )

    uploaded_file = None
    if input_mode == "Text transcript":
        st.markdown("<div class='section-header'>Text transcript</div>", unsafe_allow_html=True)
    else:
        is_video = input_mode == "Video recording"
        accepted_types = ["mp4", "mkv", "avi", "mov", "webm"] if is_video else ["mp3", "wav", "m4a", "flac", "ogg"]
        st.markdown(
            f"<div class='section-header'>{'Video' if is_video else 'Audio'} recording</div>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            f"Upload {('video' if is_video else 'audio')} recording",
            type=accepted_types,
            help="The recording is normalized, chunked, transcribed, and then analyzed.",
            key=f"{input_mode.lower().replace(' ', '_')}_uploader",
        )

    if uploaded_file is not None:
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            st.info(f"File uploaded: `{uploaded_file.name}` ({uploaded_file.size / (1024*1024):.2f} MB)")
        with col_u2:
            if st.button("Transcribe", type="secondary", use_container_width=True):
                try:
                    temp_file_path = safe_read_uploaded_audio(uploaded_file)
                    if temp_file_path is None:
                        st.error("No audio file was uploaded.")
                    else:
                        status = st.status("Uploading recording...\nTranscribing chunks...\nPreparing transcript...", expanded=True)
                        try:
                            with st.spinner("Converting audio to text and preparing the transcript..."):
                                transcription = transcriber.transcribe_file_detailed(temp_file_path)
                                transcribed_text = transcription["transcript"]
                            status.update(label="Completed", state="complete")
                            st.session_state["_sample_text"] = transcribed_text
                            st.session_state["_transcription_metadata"] = transcription
                            st.session_state["_sample_title"] = os.path.splitext(uploaded_file.name)[0]
                            detected = transcription["detected_language"]
                            st.success(f"Transcription complete. Detected language: {detected['language']} ({detected['confidence']} confidence).")
                            st.rerun()
                        except Exception as exc:
                            status.update(label="Failed", state="error")
                            st.error(f"Recording processing failed: {exc}")
                        finally:
                            if os.path.exists(temp_file_path):
                                try:
                                    os.remove(temp_file_path)
                                except Exception:
                                    pass
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error("Recording could not be processed. Please try another file or check the recording.")
                    st.caption(str(exc))

    default_text = st.session_state.get("_sample_text", "")
    transcript = ""
    if input_mode == "Text transcript":
        transcript = st.text_area(
            "Paste transcript",
            value=default_text,
            height=280,
            placeholder="Paste your meeting transcript here. Speaker format is supported, for example:\n\nSarah: Good morning everyone.\nJames: Let's start with the agenda.",
        )
    elif default_text:
        transcript = st.text_area(
            "Transcript preview",
            value=default_text,
            height=220,
            help="Review the generated transcript before analysis.",
        )

    col_s, col_l, col_a = st.columns([1, 1, 2])
    with col_s:
        if input_mode == "Text transcript" and st.button("Load text test", use_container_width=True, type="secondary"):
            sample_path = os.path.join(os.path.dirname(__file__), "samples", "text", "sample_meeting.txt")
            if os.path.exists(sample_path):
                with open(sample_path, "r", encoding="utf-8") as f:
                    st.session_state["_sample_text"] = f.read()
                    st.session_state["_sample_title"] = "Q1 2025 Product Strategy Meeting"
                st.rerun()

    with col_l:
        use_llm = st.checkbox("Use language model", value=False)

    with col_a:
        analyze_clicked = st.button("Analyze meeting", type="primary", use_container_width=True)

    # Run analysis
    if analyze_clicked and transcript.strip():
        progress = st.progress(0, text="Initializing analysis pipeline...")
        result = analyzer.analyze_hierarchical(transcript)

        if "error" in result:
            st.error(result["error"])
        else:
            progress.progress(60, text="Processing results...")

            if use_llm and ollama_ok:
                progress.progress(70, text="Enhancing with language model...")
                llm_context = "\n\n".join(
                    chunk["summary"] for chunk in result.get("chunk_summaries", [])
                ) or transcript
                llm_summary = llm.generate_summary(llm_context, "concise")
                if llm_summary:
                    result["llm_summary"] = llm_summary
                llm_tasks = llm.extract_tasks(llm_context)
                if llm_tasks:
                    result["llm_tasks"] = llm_tasks
                llm_risks = llm.analyze_risks(llm_context)
                if llm_risks:
                    result["llm_risks"] = llm_risks

            detected_language = transcriber.detect_language(transcript)
            result["input_language"] = meeting_language if meeting_language != "Auto Detect" else detected_language["language"]
            result["detected_language"] = detected_language
            result["output_language"] = output_language
            transcription_metadata = st.session_state.get("_transcription_metadata", {})
            result["transcript_segments"] = (
                transcription_metadata.get("segments", [])
                if transcription_metadata.get("transcript") == transcript else []
            )
            if output_language != "English":
                translation_source = result.get("llm_summary") or result.get("short_summary", "")
                translated = llm.translate_text(translation_source, output_language) if ollama_ok else None
                if translated:
                    result["translated_summary"] = translated
                else:
                    st.info("Output translation is unavailable offline; the original-language transcript and structured analysis are preserved.")

            title = meeting_title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            st.session_state["current_result"] = result
            st.session_state["current_title"] = title
            st.session_state["current_transcript"] = transcript

            progress.progress(85, text="Saving to Knowledge Base...")
            kb.save(title, transcript, result)

            progress.progress(100, text="Complete")
            st.success(f"Analysis complete. **{title}** was saved to the Knowledge Base. Open Results Dashboard to review it.")

    elif analyze_clicked:
        st.error("Please paste a meeting transcript first.")


# ═══════════════════════════════════════════
#  PAGE: RESULTS DASHBOARD
# ═══════════════════════════════════════════

elif page == "Results Dashboard":
    result = st.session_state.get("current_result")
    title = st.session_state.get("current_title", "Meeting Results")

    if not result:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">No results</div>
            <p>No analysis results yet.<br>Go to <strong>Analyze Meeting</strong> to process a transcript.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f'<h1 class="hero-header">{title}</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-sub">Summary, decisions, action items, and risks from this meeting.</p>', unsafe_allow_html=True)
        st.caption("Use this page to understand what was discussed and what needs to happen next.")
        detected = result.get("detected_language", {})
        st.info(
            f"Input language: {result.get('input_language', detected.get('language', 'Unknown'))} · "
            f"Detected: {detected.get('language', 'Unknown')} ({detected.get('confidence', 'low')} confidence) · "
            f"Output: {result.get('output_language', 'English')}"
        )

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
        sum_tabs = st.tabs(["Summary", "Detailed", "Key points", "Enhanced summary"])
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
            translated = result.get("translated_summary")
            if translated:
                st.markdown(f'<div class="glass-card">{translated}</div>', unsafe_allow_html=True)
            elif llm_s:
                st.markdown(f'<div class="glass-card">{llm_s}</div>', unsafe_allow_html=True)
            else:
                st.info("Enable Ollama LLM during analysis for AI-enhanced summaries.")

        with st.expander("Original transcript and timestamps"):
            segments = result.get("transcript_segments", [])
            if segments:
                for segment in segments:
                    st.markdown(
                        f"**[{segment['start']} - {segment['end']}] {segment.get('speaker', 'Unknown')}:** "
                        f"{segment['text']}"
                    )
            else:
                st.text_area("Original transcript", st.session_state.get("current_transcript", ""), height=260, disabled=True)

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
            st.caption("Longer bars mean the topic occupied more sentences in the transcript.")
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
            st.caption("This compares positive and negative language by speaker. It is a signal, not a final judgment.")
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
        st.caption("The chart shows each speaker's share of the words detected in the meeting.")
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
        st.caption("Higher scores indicate more decisions, clearer follow-up, balanced participation, and fewer unresolved risks.")
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
#  PAGE: MEETINGS
# ═══════════════════════════════════════════

elif page == "Meetings":
    st.markdown('<h1 class="hero-header">Meetings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Your complete meeting history. Open a meeting to review its analysis.</p>', unsafe_allow_html=True)

    meetings = kb.list_meetings(limit=100)
    if not meetings:
        st.info("No meetings have been analyzed yet.")
    else:
        meeting_query = st.text_input("Search meetings", placeholder="Search by meeting title...")
        if meeting_query.strip():
            query = meeting_query.lower()
            meetings = [meeting for meeting in meetings if query in meeting.get("title", "").lower()]

        st.caption(f"Showing {len(meetings)} meetings")
        for meeting in meetings:
            with st.container(border=True):
                title_col, stats_col, action_col = st.columns([3, 2, 1])
                title_col.markdown(f"**{meeting['title']}**")
                title_col.caption(str(meeting.get("date", ""))[:10])
                stats_col.caption(
                    f"{meeting.get('speakers_count', 0)} speakers · "
                    f"{meeting.get('tasks_count', 0)} tasks · "
                    f"Score {meeting.get('productivity_score', 0)}/100"
                )
                if action_col.button("Open", key=f"open_meeting_{meeting['id']}", use_container_width=True):
                    full = kb.get(meeting["id"])
                    if full:
                        st.session_state["current_result"] = full["analysis"]
                        st.session_state["current_title"] = full["title"]
                        st.session_state["current_transcript"] = full["transcript"]
                        st.success("Meeting loaded. Open Meeting results from the sidebar.")


# ═══════════════════════════════════════════
#  PAGE: CALENDAR
# ═══════════════════════════════════════════

elif page == "Calendar":
    st.markdown('<h1 class="hero-header">Calendar</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Turn deadlines and follow-ups into reminders you can track.</p>', unsafe_allow_html=True)

    with st.form("calendar_event_form"):
        title = st.text_input("Event title", placeholder="e.g., Submit project report")
        event_date = st.date_input("Date")
        event_time = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
        description = st.text_area("Description", height=90)
        assignee = st.text_input("Assignee", value=current_user["name"])
        reminder = st.selectbox("Reminder", {"No reminder": None, "1 hour before": 60, "1 day before": 1440}.keys())
        create_event = st.form_submit_button("Create event", type="primary")
    if create_event:
        if not title.strip():
            st.error("Enter an event title.")
        else:
            calendar.create_event(
                title, event_date.isoformat(), event_time.strftime("%H:%M"), description,
                assignee, reminder_minutes={"No reminder": None, "1 hour before": 60, "1 day before": 1440}[reminder],
            )
            st.success("Calendar event and reminder saved.")
            st.rerun()

    events = calendar.list_events()
    st.download_button("Download .ics calendar", calendar.export_ics(), "meetmind-calendar.ics", "text/calendar")
    if events:
        for event in events:
            with st.container(border=True):
                event_cols = st.columns([4, 2, 1])
                event_cols[0].markdown(f"**{event['title']}**")
                event_cols[0].caption(event["description"] or "No description")
                event_cols[1].write(f"{event['event_date']} {event['event_time']}")
                if event_cols[2].button("Delete", key=f"delete_event_{event['id']}"):
                    calendar.delete_event(event["id"])
                    st.rerun()
    else:
        st.info("No calendar events yet. Create one from a confirmed deadline or follow-up meeting.")


# ═══════════════════════════════════════════
#  PAGE: KNOWLEDGE BASE
# ═══════════════════════════════════════════

elif page == "Knowledge Base":
    st.markdown('<h1 class="hero-header">Knowledge Base</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Search inside meeting transcripts, summaries, decisions, and action items.</p>', unsafe_allow_html=True)

    search_query = st.text_input("Search meeting content", placeholder="Try: budget, James, launch date, API...")

    if search_query:
        meetings = kb.search(search_query)
        st.caption(f"Found **{len(meetings)}** results for \"{search_query}\"")
    else:
        meetings = []
        stored_count = len(kb.list_meetings())
        if stored_count:
            st.info(f"{stored_count} meetings are stored. Search for a topic, person, decision, or action item to find related records.")
        else:
            st.info("Analyze a meeting first to build your searchable knowledge base.")

    if search_query and not meetings:
        st.markdown("""
        <div class="empty-state">
            <div class="icon">⌕</div>
            <p>No matching meeting content was found.<br>Try another search term.</p>
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
#  PAGE: MEMORY ASSISTANT
# ═══════════════════════════════════════════

elif page == "Memory Assistant":
    st.markdown('<h1 class="hero-header">Meeting Memory Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Ask questions across your saved meeting history and discover what changed over time.</p>', unsafe_allow_html=True)

    examples = [
        "What decisions were made about the product launch?",
        "Who owns the unresolved tasks?",
        "What risks appeared in recent meetings?",
    ]
    st.caption("Example questions: " + " · ".join(examples))
    query = st.text_input("Ask your meeting history", placeholder="e.g. What did we agree to do about the API launch?")

    if st.button("🧠 Search Meeting Memory", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Searching saved meetings..."):
                matches = retrieve_memory_matches(query)
                st.session_state["memory_matches"] = matches
                st.session_state["memory_query"] = query
                st.session_state["memory_answer"] = answer_memory_question(query, matches) if matches else "No saved meetings matched your question."

    if st.session_state.get("memory_answer"):
        st.markdown('<div class="section-header"><span class="icon">💬</span> Answer</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="glass-card">{st.session_state["memory_answer"]}</div>', unsafe_allow_html=True)
        matches = st.session_state.get("memory_matches", [])
        if matches:
            st.markdown(f"**Sources ({len(matches)})**")
            for meeting in matches:
                st.caption(f"📌 {meeting.get('title', 'Untitled')} · {str(meeting.get('date', ''))[:10]}")


# ═══════════════════════════════════════════
#  PAGE: ACCOUNTABILITY CENTER
# ═══════════════════════════════════════════

elif page == "Accountability Center":
    st.markdown('<h1 class="hero-header">Accountability Center</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Track commitments across meetings and surface delivery risk before deadlines slip.</p>', unsafe_allow_html=True)
    tasks = get_accountability_tasks()
    today = datetime.now().date()
    overdue = [task for task in tasks if task["due_date"] and task["due_date"] < today and task["status"] != "done"]
    at_risk = [task for task in tasks if task["due_date"] and 0 <= (task["due_date"] - today).days <= 2 and task["status"] != "done"]
    done = [task for task in tasks if task["status"] == "done"]
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total tasks", len(tasks))
    metric_cols[1].metric("Completed", len(done))
    metric_cols[2].metric("Overdue", len(overdue), delta="Needs attention" if overdue else "On track", delta_color="inverse")
    metric_cols[3].metric("Due within 2 days", len(at_risk), delta="Plan now" if at_risk else "Clear", delta_color="inverse")

    if tasks:
        owners = sorted({task["assignee"] for task in tasks})
        status_filter = st.selectbox("Show tasks", ["All", "pending", "in progress", "done"])
        owner_filter = st.selectbox("Filter by owner", ["All"] + owners)
        visible = [task for task in tasks if (status_filter == "All" or task["status"] == status_filter) and (owner_filter == "All" or task["assignee"] == owner_filter)]
        st.caption(f"Showing {len(visible)} of {len(tasks)} tasks")
        for task in visible:
            risk = "OVERDUE" if task in overdue else ("DUE SOON" if task in at_risk else "")
            label = f"{task['priority'].upper()} · {task['assignee']} · {task['meeting']}"
            with st.container(border=True):
                st.markdown(f"**{label}** {f' · :red[{risk}]' if risk else ''}")
                st.write(task["task"])
                cols = st.columns([2, 2, 1])
                cols[0].caption(f"Deadline: {task['deadline']}")
                new_status = cols[1].selectbox("Status", ["pending", "in progress", "done"], index=["pending", "in progress", "done"].index(task["status"]) if task["status"] in {"pending", "in progress", "done"} else 0, key=f"status_{task['meeting_id']}_{task['task_index']}")
                if cols[2].button("Save", key=f"save_{task['meeting_id']}_{task['task_index']}"):
                    kb.update_task_status(task["meeting_id"], task["task_index"], new_status)
                    st.success("Task status saved.")
                    st.rerun()
    else:
        st.info("Analyze a meeting first to populate the accountability tracker.")


# ═══════════════════════════════════════════
#  PAGE: QUALITY COACH
# ═══════════════════════════════════════════

elif page == "Quality Coach":
    st.markdown('<h1 class="hero-header">Meeting Quality Coach</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Turn meeting analytics into specific improvements for your next conversation.</p>', unsafe_allow_html=True)
    meetings = kb.list_meetings()
    if meetings:
        selected = st.selectbox("Choose a meeting to review", meetings, format_func=lambda meeting: f"{meeting['title']} · {str(meeting.get('date', ''))[:10]}")
        full = kb.get(selected["id"]) if selected else None
        if full:
            analysis = full["analysis"]
            score = analysis.get("productivity_score", {})
            cols = st.columns(4)
            cols[0].metric("Productivity", f"{score.get('total', 0)}/100")
            cols[1].metric("Actions", len(analysis.get("tasks", [])))
            cols[2].metric("Decisions", len(analysis.get("decisions", [])))
            cols[3].metric("Speakers", analysis.get("stats", {}).get("speaker_count", 0))
            st.markdown('<div class="section-header"><span class="icon">🧭</span> Recommended improvements</div>', unsafe_allow_html=True)
            for title, recommendation in quality_recommendations(analysis):
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.write(recommendation)
    else:
        st.info("Analyze a meeting first to receive coaching recommendations.")


# ═══════════════════════════════════════════
#  PAGE: ANALYTICS
# ═══════════════════════════════════════════

elif page == "Analytics":
    st.markdown('<h1 class="hero-header">Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">A simple view of meeting patterns, follow-up, and team participation.</p>', unsafe_allow_html=True)
    st.caption("Use these numbers to decide which meetings need better agendas, clearer owners, or follow-up reviews.")

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
        st.caption("Meetings is the number analyzed. Total Tasks and Decisions count detected items. Avg Words indicates typical meeting length. Avg Score is the estimated productivity score out of 100.")

        governance = get_governance_summary()
        st.markdown('<div class="section-header">Meeting governance</div>', unsafe_allow_html=True)
        st.caption("A practical view of whether meetings produce clear decisions and follow-up work.")
        governance_cols = st.columns(4)
        governance_cols[0].metric("Meetings with follow-up", f"{governance['follow_up_rate']}%")
        governance_cols[1].metric("Meetings with decisions", f"{governance['decision_rate']}%")
        governance_cols[2].metric("Open action items", governance["open_tasks"])
        governance_cols[3].metric("Overdue action items", governance["overdue_tasks"])

        if governance["needs_review"]:
            with st.expander("Meetings that need review", expanded=False):
                for item in governance["needs_review"]:
                    st.markdown(f"**{item['title']}** · {item['date']}  ")
                    st.caption(item["reason"])

        st.divider()

        # Productivity Trend
        trend = data.get("productivity_trend", [])
        if trend:
            st.markdown('<div class="section-header"><span class="icon">📈</span> Productivity Trend</div>', unsafe_allow_html=True)
            st.caption("Each point is one meeting. A rising line suggests meetings are becoming clearer and more action-oriented; a falling line is a reason to review agendas and follow-up.")
            fig = px.line(trend, x="title", y="score", markers=True,
                          color_discrete_sequence=["#7c3aed"])
            fig.update_layout(**PLOTLY_LAYOUT, height=320, title="Estimated productivity score by meeting", yaxis_title="Score out of 100", xaxis_title="Meeting")
            fig.update_traces(line=dict(width=3), marker=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)

        # Action & Decision Trend
        action_trend = data.get("action_trend", [])
        if action_trend:
            st.markdown('<div class="section-header"><span class="icon">📊</span> Tasks & Decisions</div>', unsafe_allow_html=True)
            st.caption("Compare the number of follow-up tasks with formal decisions. Many tasks with few decisions may mean the meeting needs clearer conclusions.")
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Tasks", x=[a["title"] for a in action_trend], y=[a["tasks"] for a in action_trend],
                                 marker_color="#a78bfa", marker_line_width=0))
            fig.add_trace(go.Bar(name="Decisions", x=[a["title"] for a in action_trend], y=[a["decisions"] for a in action_trend],
                                 marker_color="#38bdf8", marker_line_width=0))
            fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=320, title="Tasks and decisions per meeting", yaxis_title="Count", xaxis_title="Meeting", legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            sentiments = data.get("sentiment_distribution", {})
            if sentiments:
                st.markdown('<div class="section-header"><span class="icon">💭</span> Sentiment</div>', unsafe_allow_html=True)
                st.caption("Shows the overall language tone across saved meetings. Use it as context when reviewing difficult or successful periods.")
                fig = px.pie(values=list(sentiments.values()), names=list(sentiments.keys()),
                             color_discrete_map={"positive": "#34d399", "neutral": "#64748b", "negative": "#f87171"},
                             hole=0.45)
                fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            pf = data.get("participant_frequency", {})
            if pf:
                st.markdown('<div class="section-header"><span class="icon">👥</span> Top Participants</div>', unsafe_allow_html=True)
                st.caption("Counts how many saved meetings included each speaker. It does not measure performance or contribution quality.")
                fig = px.bar(x=list(pf.values()), y=list(pf.keys()), orientation="h",
                             color=list(pf.values()), color_continuous_scale=[[0, "#4f46e5"], [1, "#a78bfa"]])
                fig.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, coloraxis_showscale=False)
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)

        tf = data.get("topic_frequency", {})
        if tf:
            st.markdown('<div class="section-header"><span class="icon">🗂️</span> Popular Topics</div>', unsafe_allow_html=True)
            st.caption("These are the most repeated topic keywords across saved meetings, useful for spotting recurring work or problems.")
            fig = px.bar(x=list(tf.keys())[:12], y=list(tf.values())[:12],
                         color=list(tf.values())[:12], color_continuous_scale=[[0, "#0ea5e9"], [1, "#38bdf8"]])
            fig.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False, coloraxis_showscale=False)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════
#  PAGE: GENERATE REPORT
# ═══════════════════════════════════════════

elif page == "Generate Report":
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
            report_type = st.selectbox("📄 Report Format", ["📧 Email Follow-Up", "📝 Detailed Markdown", "🌐 HTML Report", "📅 Calendar (.ics)"])
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
                elif "HTML" in report_type:
                    report = report_gen.generate_html(result, title)
                else:
                    report = report_gen.generate_ics(result, title)

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
                import html as _html
                escaped = _html.escape(report)
                st.markdown(f"""
<div style="
    background: rgba(10, 8, 30, 0.85);
    border: 1px solid rgba(124, 58, 237, 0.3);
    border-radius: 16px;
    padding: 28px 32px;
    margin: 8px 0 16px;
    max-height: 520px;
    overflow-y: auto;
    box-shadow: 0 4px 30px rgba(124,58,237,0.1);
">
<pre style="
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: 'Inter', 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9rem;
    line-height: 1.75;
    color: #e2e8f0;
">{escaped}</pre>
</div>
""", unsafe_allow_html=True)

            ext = "html" if "HTML" in r_type else ("md" if "Markdown" in r_type else ("ics" if "Calendar" in r_type else "txt"))
            mime = "text/calendar" if ext == "ics" else "text/plain"
            st.download_button(f"⬇️ Download .{ext}", report,
                               file_name=f"meeting_report_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}",
                               mime=mime, use_container_width=True)


# ═══════════════════════════════════════════
#  PAGE: SETTINGS
# ═══════════════════════════════════════════

elif page == "Settings":
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
    st.markdown('<div class="section-header"><span class="icon">🎙️</span> Speech-to-Text Configuration</div>', unsafe_allow_html=True)
    st.markdown("MeetMind transcribes English audio and video locally using Whisper.")
    
    whisper_model_options = [
        "openai/whisper-tiny.en",
        "openai/whisper-base.en",
        "openai/whisper-small.en",
        "openai/whisper-medium.en"
    ]
    current_model = config.WHISPER_MODEL
    default_index = whisper_model_options.index(current_model) if current_model in whisper_model_options else 0
    
    selected_whisper_model = st.selectbox(
        "Whisper Model (Tiny/Base are recommended for CPU)",
        whisper_model_options,
        index=default_index,
        help="Tiny.en is fastest for CPU. Base.en and Small.en can improve accuracy but require more memory and processing time."
    )
    
    if selected_whisper_model != config.WHISPER_MODEL:
        config.WHISPER_MODEL = selected_whisper_model
        st.success(f"Configured active model: `{selected_whisper_model}`")
        
    if st.button("📥 Download / Preload Model", use_container_width=True):
        with st.spinner("Downloading Whisper model and loading into memory... (This might take a minute on first run)"):
            try:
                # Preload pipeline
                transcriber.get_pipeline(selected_whisper_model)
                st.success(f"✅ Whisper model `{selected_whisper_model}` is ready and loaded!")
            except Exception as e:
                st.error(f"❌ Failed to load model: {e}")
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
