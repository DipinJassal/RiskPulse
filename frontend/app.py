"""RiskPulse — Streamlit dashboard."""
from __future__ import annotations

import sys
from collections import Counter
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
    _severity,
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
  --teal:#06b6d4; --teal-soft:#0e3a4a; --red:#ef4444; --amber:#f59e0b;
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

/* top gradient accent line */
body::before {
  content: '';
  position: fixed; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, #ef4444 0%, #f59e0b 40%, #06b6d4 100%);
  z-index: 9999; pointer-events: none;
}

/* custom scrollbar */
* { scrollbar-width: thin; scrollbar-color: #1e2d45 transparent; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #253450; }

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
  display: flex; gap: 12px; margin: 0 4px 10px;
  padding: 6px 8px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.rp-side-stat {
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.4px;
  text-transform: uppercase;
}

/* sidebar filter radio */
[data-testid="stSidebar"] [data-baseweb="radio-group"] {
  flex-direction: row !important; gap: 6px !important;
  flex-wrap: wrap; margin: 0 4px 10px;
}
[data-testid="stSidebar"] [data-baseweb="radio"] {
  margin: 0 !important;
}
[data-testid="stSidebar"] [data-baseweb="radio"] label {
  padding: 3px 10px; border-radius: 12px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--muted) !important;
  cursor: pointer; transition: all 0.15s;
}
[data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) label {
  background: rgba(6,182,212,0.12) !important;
  border-color: var(--teal) !important;
  color: var(--teal) !important;
}

/* the wrapper div holds the severity-colored left stripe */
.rp-evt-wrap { position: relative; margin-bottom: 6px; }
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
.rp-pill-cat {
  display:inline-block; padding: 1px 7px; border-radius: 10px;
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
  text-shadow: 0 0 16px rgba(239, 68, 68, 0.7);
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

/* source status row */
.rp-src-row { display:flex; gap:14px; margin-top:6px; justify-content:flex-end; }
.rp-src { display:flex; align-items:center; gap:5px; font-size:10px; font-weight:600; letter-spacing:0.5px; color:var(--muted); text-transform:uppercase; }
.rp-src-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
.rp-src-dot.ok { background:#10b981; box-shadow:0 0 5px rgba(16,185,129,0.6); }
.rp-src-dot.off { background:#334155; }

/* Risk level pill */
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
  animation: rp-pulse 1.6s infinite;
}
@keyframes rp-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.7); }
  70%  { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
  100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}

.rp-divider {
  height: 1px; border: none; margin: 14px 0 6px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
}

/* ── Severity badges (shared) ─────────────────────────────────────────────── */
.rp-badge {
  display:inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.5px;
  vertical-align: middle; font-variant-numeric: tabular-nums;
}
.rp-badge-crit {
  box-shadow: 0 0 10px rgba(239,68,68,0.3);
}

/* ── Stats KPI strip ──────────────────────────────────────────────────────── */
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
  position: relative; overflow: hidden;
  transition: background 0.15s;
}
.rp-stat::after {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--accent), transparent);
  opacity: 0.4;
}
.rp-stat:hover { background: var(--panel-2); }
.rp-stat-num {
  font-size: 32px; font-weight: 800; line-height: 1;
  color: var(--accent); letter-spacing: -1.5px;
  font-variant-numeric: tabular-nums;
}
.rp-stat-lab {
  font-size: 10.5px; font-weight: 700; letter-spacing: 1.4px;
  color: var(--text); text-transform: uppercase;
  margin-top: 6px;
}
.rp-stat-sub { font-size: 10.5px; color: var(--muted); letter-spacing: 0.2px; }
.rp-stat-pct {
  font-size: 10.5px; font-weight: 700;
  color: var(--accent); opacity: 0.75;
  margin-top: 3px; font-variant-numeric: tabular-nums;
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
  border-radius: 0; border-bottom: 2px solid transparent;
  transition: color 0.15s;
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
.stTabs [data-baseweb="tab-panel"] ol,
.stTabs [data-baseweb="tab-panel"] ul { padding-left: 20px; }
.stTabs [data-baseweb="tab-panel"] li { margin: 4px 0; }
.stTabs [data-baseweb="tab-panel"] hr {
  border: none; border-top: 1px solid var(--border); margin: 14px 0;
}
.stTabs [data-baseweb="tab-panel"] strong { color: var(--text); }

/* alert cards */
.rp-alert {
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  padding: 12px 16px 8px; margin: 0 0 10px;
  transition: background 0.15s, transform 0.15s;
}
.rp-alert:hover { background: var(--panel-2); transform: translateX(2px); }
.rp-alert h3 {
  display: flex; align-items: center; gap: 8px;
  font-size: 13.5px !important; margin: 0 0 6px !important;
}
.rp-alert ul { margin: 4px 0 0; padding-left: 18px; }
.rp-alert li { margin: 2px 0; font-size: 12.5px !important; }
.rp-alert p { margin: 4px 0 6px !important; font-size: 12.5px !important; }

/* sector heatmap grid */
.rp-heat {
  display: flex; flex-direction: column; gap: 0;
  margin: 10px 0 12px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px; overflow: hidden;
}
.rp-heat-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 90px 2.5fr;
  gap: 12px; padding: 9px 14px;
  border-left: 3px solid var(--accent);
  border-bottom: 1px solid var(--border);
  align-items: center;
  transition: background 0.15s;
}
.rp-heat-row:last-child { border-bottom: none; }
.rp-heat-row:hover { background: var(--panel-2); }
.rp-heat-sector { font-size: 12.5px; font-weight: 600; color: var(--text); }
.rp-heat-level {
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.6px;
  text-align: center; padding: 3px 10px; border-radius: 4px;
  width: fit-content; font-variant-numeric: tabular-nums;
}
.rp-heat-driver { font-size: 11.5px; color: var(--muted-2); }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: var(--red) !important;
  border-color: var(--red) !important;
  color: #fff !important;
  font-weight: 700 !important; letter-spacing: 0.5px;
  border-radius: 6px !important; height: 38px !important;
  text-transform: uppercase; font-size: 12px !important;
  box-shadow: 0 1px 0 rgba(0,0,0,0.3), 0 0 0 0 rgba(239,68,68,0.4);
  transition: box-shadow 0.2s, background 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
  background: #dc2626 !important;
  border-color: #dc2626 !important;
  box-shadow: 0 0 12px rgba(239,68,68,0.4) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  color: var(--muted-2) !important;
  font-size: 11.5px !important; font-weight: 500 !important;
  border-radius: 16px !important;
  padding: 4px 12px !important; height: auto !important;
  letter-spacing: 0.2px; transition: all 0.15s !important;
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
  transition: background 0.15s;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
  background: var(--panel-2) !important;
  border-left: 2px solid #334155 !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
  background: rgba(6,182,212,0.05) !important;
  border-left: 2px solid rgba(6,182,212,0.35) !important;
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

/* ── Analytics tab ────────────────────────────────────────────────────────── */
.rp-ana-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16px; margin-bottom: 16px;
}
@media (max-width: 900px) { .rp-ana-grid { grid-template-columns: 1fr; } }
.rp-ana-card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 16px;
}
.rp-ana-card-full {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 16px; margin-bottom: 16px;
}
.rp-ana-title {
  font-size: 10.5px; font-weight: 700; letter-spacing: 1.6px;
  color: var(--teal); text-transform: uppercase;
  margin: 0 0 14px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.rp-ana-bar-row {
  display: grid; grid-template-columns: 100px 1fr 36px;
  align-items: center; gap: 10px; margin-bottom: 10px;
}
.rp-ana-label { font-size: 11px; font-weight: 600; color: var(--muted-2); letter-spacing: 0.3px; }
.rp-ana-track {
  background: var(--panel-2); border-radius: 3px; height: 8px;
  overflow: hidden; border: 1px solid var(--border);
}
.rp-ana-fill { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.rp-ana-count { font-size: 12px; font-weight: 700; color: var(--text); text-align: right; font-variant-numeric: tabular-nums; }
.rp-sector-row {
  display: grid; grid-template-columns: 1fr auto;
  align-items: center; gap: 12px;
  padding: 7px 0; border-bottom: 1px solid var(--border);
}
.rp-sector-row:last-child { border-bottom: none; }
.rp-sector-name { font-size: 12px; font-weight: 500; color: var(--text); }
.rp-sector-count {
  font-size: 11px; font-weight: 700; color: var(--teal);
  background: rgba(6,182,212,0.1); border: 1px solid var(--teal-soft);
  padding: 1px 8px; border-radius: 10px;
  font-variant-numeric: tabular-nums;
}
.rp-src-card {
  display: inline-flex; align-items: center; gap: 10px;
  background: var(--panel-2); border: 1px solid var(--border);
  border-radius: 6px; padding: 10px 14px; margin: 4px;
}
.rp-src-name { font-size: 11.5px; font-weight: 600; color: var(--muted-2); }
.rp-src-num { font-size: 20px; font-weight: 800; color: var(--text); letter-spacing: -0.5px; font-variant-numeric: tabular-nums; }

/* spinner */
[data-testid="stSpinner"] > div { border-top-color: var(--teal) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Session state ───────────────────────────────────────────────────────────
def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("sev_filter", "ALL")
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
    is_live = st.session_state.data_source == "live"
    src_label = "Live pipeline" if is_live else "Mock data"
    st.markdown(
        f'<div class="rp-meta-line">'
        f"<b>Updated</b> {st.session_state.last_updated}"
        f'<span class="rp-meta-dot">·</span>'
        f"<b>{len(st.session_state.events)}</b> events"
        f'<br><span style="font-size:10.5px;letter-spacing:1px">{src_label.upper()}</span>'
        f"</div>"
        f'<div class="rp-src-row">'
        f'<span class="rp-src"><span class="rp-src-dot {"ok" if is_live else "off"}"></span>NewsAPI</span>'
        f'<span class="rp-src"><span class="rp-src-dot {"ok" if is_live else "off"}"></span>SEC EDGAR</span>'
        f'<span class="rp-src"><span class="rp-src-dot {"ok" if is_live else "off"}"></span>yfinance</span>'
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
sev_filter = st.sidebar.radio(
    "",
    ["ALL", "CRITICAL", "WARNING", "INFO"],
    horizontal=True,
    index=["ALL", "CRITICAL", "WARNING", "INFO"].index(st.session_state.sev_filter),
    label_visibility="collapsed",
    key="sev_filter_radio",
)
st.session_state.sev_filter = sev_filter
render_event_sidebar(st.session_state.events, st.session_state.analyses, sev_filter)

# ── Main tabs ───────────────────────────────────────────────────────────────
tab_briefing, tab_analytics, tab_chat = st.tabs(["Risk Briefing", "Analytics", "Chat"])

with tab_briefing:
    render_severity_strip(st.session_state.analyses)
    render_briefing(st.session_state.briefing)

with tab_analytics:
    analyses = st.session_state.analyses
    events = st.session_state.events

    if not analyses:
        st.info("Click **Refresh** to load analysis data.")
    else:
        # ── Compute ────────────────────────────────────────────────────────
        counts: dict[str, int] = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        for a in analyses:
            _, lab = _severity(a.severity_score)
            counts[lab] += 1
        total = len(analyses) or 1

        sector_counts: dict[str, int] = {}
        for a in analyses:
            for s in (a.affected_sectors or []):
                sector_counts[s] = sector_counts.get(s, 0) + 1
        top_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        source_counts = Counter(e.source for e in events)
        cat_counts = Counter(e.category for e in events)

        sev_colors = {"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "INFO": "#10b981"}
        max_sector = top_sectors[0][1] if top_sectors else 1

        # ── Severity distribution + Sector exposure (2-col grid) ──────────
        sev_bars = "".join(
            f'<div class="rp-ana-bar-row">'
            f'<span class="rp-ana-label">{lab}</span>'
            f'<div class="rp-ana-track"><div class="rp-ana-fill" style="width:{counts[lab]/total*100:.0f}%;background:{sev_colors[lab]}"></div></div>'
            f'<span class="rp-ana-count">{counts[lab]}</span>'
            f"</div>"
            for lab in ["CRITICAL", "WARNING", "INFO"]
        )
        sector_rows = "".join(
            f'<div class="rp-sector-row">'
            f'<span class="rp-sector-name">{name}</span>'
            f'<span class="rp-sector-count">{cnt}</span>'
            f"</div>"
            for name, cnt in top_sectors
        )

        st.markdown(
            f'<div class="rp-ana-grid">'
            f'<div class="rp-ana-card">'
            f'<div class="rp-ana-title">Severity Distribution</div>'
            f"{sev_bars}"
            f"</div>"
            f'<div class="rp-ana-card">'
            f'<div class="rp-ana-title">Top Affected Sectors</div>'
            f"{sector_rows}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Source & Category breakdown ────────────────────────────────────
        CAT_COLORS = {
            "fraud": "#ef4444", "macro": "#f59e0b", "earnings": "#f97316",
            "regulatory": "#3b82f6", "geopolitical": "#a855f7",
            "credit": "#ec4899", "market": "#06b6d4", "bankruptcy": "#84cc16",
        }
        src_cards = "".join(
            f'<div class="rp-src-card">'
            f'<div><div class="rp-src-num">{cnt}</div>'
            f'<div class="rp-src-name">{src}</div></div>'
            f"</div>"
            for src, cnt in source_counts.most_common(8)
        )
        cat_bars = "".join(
            f'<div class="rp-ana-bar-row">'
            f'<span class="rp-ana-label">{cat.upper()}</span>'
            f'<div class="rp-ana-track"><div class="rp-ana-fill" style="width:{cnt/len(events)*100:.0f}%;background:{CAT_COLORS.get(cat, "#7c8aa1")}"></div></div>'
            f'<span class="rp-ana-count">{cnt}</span>'
            f"</div>"
            for cat, cnt in cat_counts.most_common()
        )

        st.markdown(
            f'<div class="rp-ana-grid">'
            f'<div class="rp-ana-card">'
            f'<div class="rp-ana-title">Events by Category</div>'
            f"{cat_bars}"
            f"</div>"
            f'<div class="rp-ana-card">'
            f'<div class="rp-ana-title">Events by Source</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px">{src_cards}</div>'
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Avg severity per sector ────────────────────────────────────────
        sector_scores: dict[str, list[int]] = {}
        for a in analyses:
            for s in (a.affected_sectors or []):
                sector_scores.setdefault(s, []).append(a.severity_score)
        sector_avgs = sorted(
            ((s, sum(v) / len(v)) for s, v in sector_scores.items()),
            key=lambda x: x[1], reverse=True,
        )[:8]

        def _sev_color(score: float) -> str:
            if score >= 7: return "#ef4444"
            if score >= 4: return "#f59e0b"
            return "#10b981"

        avg_rows = "".join(
            f'<div class="rp-ana-bar-row">'
            f'<span class="rp-ana-label" style="font-size:10.5px">{s[:18]}</span>'
            f'<div class="rp-ana-track"><div class="rp-ana-fill" style="width:{avg/10*100:.0f}%;background:{_sev_color(avg)}"></div></div>'
            f'<span class="rp-ana-count" style="color:{_sev_color(avg)}">{avg:.1f}</span>'
            f"</div>"
            for s, avg in sector_avgs
        )
        st.markdown(
            f'<div class="rp-ana-card-full">'
            f'<div class="rp-ana-title">Average Severity by Sector (1–10 scale)</div>'
            f"{avg_rows}"
            f"</div>",
            unsafe_allow_html=True,
        )

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
