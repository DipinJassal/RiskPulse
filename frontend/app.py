"""RiskPulse — Streamlit dashboard (Member 4 Step 1).

Compact, dark-themed risk intelligence dashboard with a live event feed,
formatted briefing, and conversational chat. Seeds from `frontend.mock_data`
and transparently swaps to `pipeline.run_pipeline()` once the agents are wired.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from frontend.components import (  # noqa: E402
    render_briefing,
    render_event_sidebar,
    render_risk_level,
    render_severity_strip,
)
from frontend.mock_data import get_mock_payload  # noqa: E402

st.set_page_config(
    page_title="RiskPulse — Risk Intelligence Dashboard",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
:root {
  --bg:#070b13; --panel:#0e1623; --panel-2:#142033; --panel-3:#1a2638;
  --teal:#06b6d4; --teal-soft:#0e3a4a; --red:#ef4444;
  --text:#e8edf5; --muted:#7c8aa1; --muted-2:#9aa8c0; --border:#1c2738;
}
html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif;
  font-feature-settings: "ss01", "cv11";
  -webkit-font-smoothing: antialiased;
}
.stApp { background: var(--bg); color: var(--text); }
.block-container {
  padding-top: 1.2rem !important;
  padding-bottom: 2rem !important;
  max-width: 1400px;
}

/* hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton, [data-testid="stToolbar"] { display: none !important; }
.stAppHeader, [data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: #050911;
  border-right: 1px solid var(--border);
  width: 360px !important;
}
section[data-testid="stSidebar"] > div:first-child {
  padding: 16px 12px 12px;
}
.rp-side-h {
  font-size: 10.5px; font-weight: 700; letter-spacing: 1.6px;
  color: var(--muted); text-transform: uppercase;
  display:flex; align-items:center; justify-content:space-between;
  margin: 0 4px 6px;
}
.rp-side-count {
  background: var(--panel-2); color: var(--teal);
  padding: 2px 8px; border-radius: 10px; font-size: 10.5px;
  letter-spacing: 0.5px;
}
.rp-side-stats {
  display: flex; gap: 12px; margin: 0 4px 14px;
  padding: 6px 8px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.rp-side-stat {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.4px;
  text-transform: uppercase;
}

/* the wrapper div holds the severity-colored left stripe */
.rp-evt-wrap { position: relative; margin-bottom: 6px; }
.rp-evt-wrap + div[data-testid="stExpander"] {
  border-left: 3px solid var(--sev) !important;
}
section[data-testid="stSidebar"] details {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-left-width: 3px !important;
  border-radius: 6px !important;
  margin-bottom: 6px !important;
  transition: background 0.15s ease;
}
section[data-testid="stSidebar"] details:hover {
  background: var(--panel-2) !important;
}
section[data-testid="stSidebar"] details summary {
  padding: 8px 10px !important;
  font-size: 12.5px !important;
  font-weight: 500 !important;
  color: var(--text) !important;
  letter-spacing: 0.1px;
  font-variant-numeric: tabular-nums;
}
section[data-testid="stSidebar"] details[open] summary {
  border-bottom: 1px solid var(--border);
  background: rgba(6, 182, 212, 0.05);
}
.rp-evt-meta { display:flex; gap:5px; flex-wrap:wrap; margin: 4px 0 6px; }
.rp-pill {
  display:inline-block; padding: 1px 7px; border-radius: 10px;
  background: var(--panel-2); color: var(--muted-2);
  border: 1px solid var(--border);
  font-size: 10px; font-weight: 600; letter-spacing: 0.3px;
  text-transform: uppercase;
}
.rp-evt-time { color: var(--muted); font-size: 10.5px; margin-bottom: 6px; letter-spacing: 0.2px; }
.rp-evt-body { font-size: 12.5px; line-height: 1.55; color: #cbd5e1; margin-bottom: 8px; }
.rp-chips { display:flex; gap:4px; flex-wrap:wrap; margin-top: 6px; }
.rp-chip {
  background: rgba(6,182,212,0.08); color: var(--teal);
  border: 1px solid var(--teal-soft);
  padding: 1px 7px; border-radius: 4px;
  font-size: 10.5px; font-weight: 500;
}

/* ── Header bar ────────────────────────────────────────────────────────────── */
.rp-brand { display:flex; align-items:baseline; gap:12px; }
.rp-brand .rp-mark {
  color: var(--red); font-size: 22px; line-height: 1;
  text-shadow: 0 0 12px rgba(239, 68, 68, 0.6);
}
.rp-brand h1 {
  margin: 0; font-size: 24px; font-weight: 800;
  letter-spacing: -0.6px; color: var(--text);
}
.rp-brand .rp-tag {
  color: var(--muted); font-size: 11.5px; letter-spacing: 0.4px;
  border-left: 1px solid var(--border); padding-left: 12px;
  text-transform: uppercase; font-weight: 600;
}
.rp-meta-line {
  color: var(--muted); font-size: 11.5px; letter-spacing: 0.3px;
  text-align: right; line-height: 1.6;
  font-variant-numeric: tabular-nums;
}
.rp-meta-line b { color: #cbd5e1; font-weight: 600; }
.rp-meta-dot { color: #334155; margin: 0 6px; }

/* Risk level pill — bigger, with optional pulsing dot */
.rp-risk {
  display:inline-flex; align-items:center; gap:10px;
  padding: 7px 14px; border-radius: 8px;
  font-weight: 700; letter-spacing: 0.3px;
}
.rp-risk-k { font-size: 9px; opacity: 0.7; letter-spacing: 1.6px; display:block; }
.rp-risk-v { font-size: 14px; line-height: 1.1; }
.rp-risk-s { opacity: 0.7; font-weight: 500; }
.rp-pulse {
  width: 8px; height: 8px; border-radius: 50%;
  box-shadow: 0 0 0 0 currentColor;
  animation: rp-pulse 1.6s infinite;
}
@keyframes rp-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.7); }
  70%  { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
  100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}

.rp-divider {
  border-top: 1px solid var(--border);
  margin: 14px 0 6px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  height: 1px; border: none;
}

/* ── Severity badges (shared) ─────────────────────────────────────────────── */
.rp-badge {
  display:inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px;
  vertical-align: middle;
  font-variant-numeric: tabular-nums;
}

/* ── Stats KPI strip (top of briefing) ────────────────────────────────────── */
.rp-stats {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 10px; margin: 6px 0 22px;
}
.rp-stat {
  background: var(--panel);
  border: 1px solid var(--border);
  border-top: 2px solid var(--accent);
  padding: 12px 14px; border-radius: 6px;
  display: flex; flex-direction: column; gap: 2px;
}
.rp-stat-num {
  font-size: 28px; font-weight: 800; line-height: 1;
  color: var(--accent); letter-spacing: -1px;
  font-variant-numeric: tabular-nums;
}
.rp-stat-lab {
  font-size: 10.5px; font-weight: 700; letter-spacing: 1.4px;
  color: var(--text); text-transform: uppercase;
  margin-top: 6px;
}
.rp-stat-sub {
  font-size: 10.5px; color: var(--muted);
  letter-spacing: 0.2px;
}

/* ── Tabs ──────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0; border-bottom: 1px solid var(--border);
  background: transparent; margin-bottom: 8px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent; color: var(--muted);
  padding: 10px 18px; font-size: 12.5px; font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase;
  border-radius: 0;
  border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text); }
.stTabs [aria-selected="true"] {
  color: var(--teal) !important;
  border-bottom: 2px solid var(--teal) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 12px; }

/* ── Briefing content ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-panel"] h2 {
  font-size: 12.5px; font-weight: 700; letter-spacing: 1.6px;
  color: var(--teal); text-transform: uppercase;
  margin: 22px 0 10px; padding: 0 0 6px;
  border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab-panel"] h2:first-child { margin-top: 4px; }
.stTabs [data-baseweb="tab-panel"] h3 {
  font-size: 14px; font-weight: 600; color: var(--text);
  margin: 0 0 6px; letter-spacing: -0.1px;
}
.stTabs [data-baseweb="tab-panel"] p,
.stTabs [data-baseweb="tab-panel"] li {
  font-size: 13px; line-height: 1.65; color: #cbd5e1;
}
.stTabs [data-baseweb="tab-panel"] hr {
  border: none; border-top: 1px solid var(--border); margin: 14px 0;
}
.stTabs [data-baseweb="tab-panel"] strong { color: var(--text); }

/* alert cards (wrapper added by _wrap_alert_cards in components.py) */
.rp-alert {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 12px 16px 8px;
  margin: 0 0 10px;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.rp-alert:hover {
  background: var(--panel-2);
}
.rp-alert h3 {
  display: flex; align-items: center; gap: 8px;
  font-size: 13.5px !important;
  margin: 0 0 6px !important;
}
.rp-alert ul { margin: 4px 0 0; padding-left: 18px; }
.rp-alert li { margin: 2px 0; font-size: 12.5px !important; }
.rp-alert p { margin: 4px 0 6px !important; font-size: 12.5px !important; }

/* sector heatmap grid (replaces the markdown table) */
.rp-heat {
  display: flex; flex-direction: column; gap: 4px;
  margin: 10px 0 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.rp-heat-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 90px 2.5fr;
  gap: 12px; padding: 9px 14px;
  border-left: 3px solid var(--accent);
  border-bottom: 1px solid var(--border);
  align-items: center;
  transition: background 0.15s ease;
}
.rp-heat-row:last-child { border-bottom: none; }
.rp-heat-row:hover { background: var(--panel-2); }
.rp-heat-sector {
  font-size: 12.5px; font-weight: 600; color: var(--text);
}
.rp-heat-level {
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.6px;
  text-align: center; padding: 3px 10px; border-radius: 4px;
  width: fit-content;
  font-variant-numeric: tabular-nums;
}
.rp-heat-driver { font-size: 11.5px; color: var(--muted-2); }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: var(--red) !important;
  border-color: var(--red) !important;
  color: #fff !important;
  font-weight: 700 !important; letter-spacing: 0.5px;
  border-radius: 6px !important;
  height: 38px !important;
  text-transform: uppercase;
  font-size: 12px !important;
  box-shadow: 0 1px 0 rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
}
.stButton > button[kind="primary"]:hover {
  background: #dc2626 !important;
  border-color: #dc2626 !important;
}
.stButton > button[kind="secondary"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted-2) !important;
  font-size: 11.5px !important; font-weight: 500 !important;
  border-radius: 16px !important;
  padding: 4px 12px !important; height: auto !important;
  letter-spacing: 0.2px;
}
.stButton > button[kind="secondary"]:hover {
  background: var(--panel-2) !important;
  color: var(--teal) !important;
  border-color: var(--teal-soft) !important;
}

/* ── Chat ─────────────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 10px 14px !important;
  margin-bottom: 8px !important;
}
[data-testid="stChatMessage"] p { font-size: 13px !important; line-height: 1.6 !important; }
[data-testid="stChatInput"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
.rp-chat-hint {
  color: var(--muted); font-size: 10.5px;
  letter-spacing: 1.4px; margin: 4px 0 8px;
  text-transform: uppercase; font-weight: 700;
}

/* alerts / toasts */
[data-testid="stAlert"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Session state ───────────────────────────────────────────────────────────
def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)
    if "events" not in st.session_state:
        events, analyses, briefing, chat = get_mock_payload()
        st.session_state.events = events
        st.session_state.analyses = analyses
        st.session_state.briefing = briefing
        st.session_state.chat_instance = chat
        st.session_state.last_updated = datetime.now().strftime("%H:%M:%S")
        st.session_state.data_source = "mock"


_init_state()


def _refresh() -> None:
    try:
        from pipeline import run_pipeline  # type: ignore

        events, analyses, briefing_text, chat = run_pipeline()
        st.session_state.data_source = "live"
    except Exception as e:
        events, analyses, briefing_text, chat = get_mock_payload()
        st.session_state.data_source = "mock"
        st.toast(f"Pipeline unavailable — using mock data ({type(e).__name__})", icon="⚠️")

    st.session_state.events = events
    st.session_state.analyses = analyses
    st.session_state.briefing = briefing_text
    st.session_state.chat_instance = chat
    st.session_state.messages = []
    st.session_state.last_updated = datetime.now().strftime("%H:%M:%S")


def _ask(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    response = st.session_state.chat_instance.chat(question)
    st.session_state.messages.append({"role": "assistant", "content": response})


# ── Header bar ──────────────────────────────────────────────────────────────
col_brand, col_risk, col_meta, col_btn = st.columns([3, 2, 2, 1], gap="medium")

with col_brand:
    st.markdown(
        '<div class="rp-brand">'
        '<span class="rp-mark">◆</span>'
        "<h1>RiskPulse</h1>"
        '<span class="rp-tag">Real-Time Financial Risk Intelligence</span>'
        "</div>",
        unsafe_allow_html=True,
    )

with col_risk:
    render_risk_level(st.session_state.analyses)

with col_meta:
    src = "Live pipeline" if st.session_state.data_source == "live" else "Mock data"
    st.markdown(
        f'<div class="rp-meta-line">'
        f"<b>Updated</b> {st.session_state.last_updated}"
        f'<span class="rp-meta-dot">·</span>'
        f"<b>{len(st.session_state.events)}</b> events"
        f'<br><span style="font-size:10.5px;letter-spacing:1px">{src.upper()}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

with col_btn:
    if st.button("↻ Refresh", type="primary", use_container_width=True):
        with st.spinner("Agents analyzing..."):
            _refresh()
        st.rerun()

st.markdown('<hr class="rp-divider"/>', unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
render_event_sidebar(st.session_state.events, st.session_state.analyses)

# ── Main tabs ───────────────────────────────────────────────────────────────
tab_briefing, tab_chat = st.tabs(["Risk Briefing", "Chat"])

with tab_briefing:
    render_severity_strip(st.session_state.analyses)
    render_briefing(st.session_state.briefing)

with tab_chat:
    if not st.session_state.chat_instance:
        st.info("Click **Refresh** to generate a briefing first.")
    else:
        if not st.session_state.messages:
            st.markdown('<div class="rp-chat-hint">Try asking</div>', unsafe_allow_html=True)
            sugg = [
                "Which sector has the highest risk today?",
                "How does today compare to 2008?",
                "What actions should I take this week?",
            ]
            cols = st.columns(len(sugg))
            for col, q in zip(cols, sugg):
                if col.button(q, key=f"sugg-{q}", use_container_width=True):
                    st.session_state.pending_question = q

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.pending_question:
            q = st.session_state.pending_question
            st.session_state.pending_question = None
            _ask(q)
            st.rerun()

        user_input = st.chat_input("Ask about today's risk landscape...")
        if user_input:
            with st.spinner("Analyzing..."):
                _ask(user_input)
            st.rerun()
