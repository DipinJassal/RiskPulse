import streamlit as st
from schemas import AnalysisSchema, EventSchema


def severity_badge(score: int) -> str:
    if score >= 7:
        return f'<span style="background:#e53e3e;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">CRITICAL {score}</span>'
    elif score >= 4:
        return f'<span style="background:#dd6b20;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">WARNING {score}</span>'
    return f'<span style="background:#38a169;color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">INFO {score}</span>'


def render_event_sidebar(events: list[EventSchema], analyses: list[AnalysisSchema]):
    score_map = {a.event_id: a.severity_score for a in analyses}
    st.sidebar.markdown("## Live Event Feed")
    if not events:
        st.sidebar.info("No events loaded. Click Refresh.")
        return
    for event in events:
        score = score_map.get(event.event_id, 0)
        with st.sidebar.expander(f"{event.headline[:60]}..."):
            st.markdown(severity_badge(score), unsafe_allow_html=True)
            st.markdown(f"**Source:** {event.source}")
            st.markdown(f"**Category:** {event.category}")
            st.markdown(f"**Time:** {event.timestamp[:16]}")
            st.markdown(f"**Relevance:** {event.relevance_score:.2f}")


def render_risk_level(analyses: list[AnalysisSchema]):
    if not analyses:
        return
    top = analyses[0].severity_score
    color = "#e53e3e" if top >= 7 else "#dd6b20" if top >= 4 else "#38a169"
    label = "CRITICAL" if top >= 7 else "ELEVATED" if top >= 4 else "NORMAL"
    st.markdown(
        f'<div style="background:{color};color:#fff;padding:8px 16px;border-radius:6px;display:inline-block;font-weight:bold">'
        f"Risk Level: {label} ({top}/10)</div>",
        unsafe_allow_html=True,
    )
