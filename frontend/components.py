"""UI helpers for the RiskPulse Streamlit dashboard."""
from __future__ import annotations

import re

import streamlit as st

from schemas import AnalysisSchema, EventSchema


def _severity(score: int) -> tuple[str, str]:
    """(hex_color, label) for a 1-10 severity score."""
    if score >= 7:
        return "#ef4444", "CRITICAL"
    if score >= 4:
        return "#f59e0b", "WARNING"
    return "#10b981", "INFO"


def severity_badge(score: int) -> str:
    color, label = _severity(score)
    return (
        f'<span class="rp-badge" style="background:{color}1f;color:{color};'
        f'border:1px solid {color}55">{label} {score}</span>'
    )


def _format_ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""


def render_event_sidebar(events: list[EventSchema], analyses: list[AnalysisSchema]) -> None:
    """Compact left-stripe event list. Headline + sev number on one line; details on expand."""
    score_map = {a.event_id: a.severity_score for a in analyses}
    sector_map = {a.event_id: a.affected_sectors for a in analyses}

    counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for a in analyses:
        _, lab = _severity(a.severity_score)
        counts[lab] += 1

    st.sidebar.markdown(
        f'<div class="rp-side-h">'
        f"<span>Live Event Feed</span>"
        f'<span class="rp-side-count">{len(events)}</span>'
        f"</div>"
        f'<div class="rp-side-stats">'
        f'<span class="rp-side-stat" style="color:#ef4444">● {counts["CRITICAL"]} crit</span>'
        f'<span class="rp-side-stat" style="color:#f59e0b">● {counts["WARNING"]} warn</span>'
        f'<span class="rp-side-stat" style="color:#10b981">● {counts["INFO"]} info</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    if not events:
        st.sidebar.info("No events. Click **Refresh**.")
        return

    ordered = sorted(events, key=lambda e: score_map.get(e.event_id, 0), reverse=True)
    for event in ordered:
        score = score_map.get(event.event_id, 0)
        color, _ = _severity(score)
        title = event.headline if len(event.headline) <= 70 else event.headline[:67] + "..."

        # Custom-styled wrapper that gives the expander its left color stripe
        st.sidebar.markdown(
            f'<div class="rp-evt-wrap" style="--sev:{color}">', unsafe_allow_html=True
        )
        with st.sidebar.expander(f"{score}   {title}"):
            st.markdown(
                f'<div class="rp-evt-meta">'
                f'<span class="rp-pill" style="background:{color}1f;color:{color};border-color:{color}55">'
                f"sev {score}</span>"
                f'<span class="rp-pill">{event.category}</span>'
                f'<span class="rp-pill">{event.source}</span>'
                f"</div>"
                f'<div class="rp-evt-time">{_format_ts(event.timestamp)} · '
                f"relevance {event.relevance_score:.2f}</div>"
                f'<div class="rp-evt-body">{event.raw_text}</div>',
                unsafe_allow_html=True,
            )
            sectors = sector_map.get(event.event_id) or []
            if sectors:
                chips = "".join(f'<span class="rp-chip">{s}</span>' for s in sectors)
                st.markdown(f'<div class="rp-chips">{chips}</div>', unsafe_allow_html=True)
        st.sidebar.markdown("</div>", unsafe_allow_html=True)


def render_risk_level(analyses: list[AnalysisSchema]) -> None:
    if not analyses:
        color, label, score = "#475569", "—", "—"
        pulse = ""
    else:
        top = max(a.severity_score for a in analyses)
        color, label = _severity(top)
        score = f"{top}/10"
        pulse = (
            f'<span class="rp-pulse" style="background:{color}"></span>' if top >= 7 else ""
        )
    st.markdown(
        f'<div class="rp-risk" style="background:{color}14;color:{color};border:1px solid {color}55">'
        f"{pulse}"
        f'<div><span class="rp-risk-k">RISK LEVEL</span>'
        f'<div class="rp-risk-v">{label} <span class="rp-risk-s">· {score}</span></div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_severity_strip(analyses: list[AnalysisSchema]) -> None:
    """Quick KPI bar: counts by severity bucket."""
    counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for a in analyses:
        _, lab = _severity(a.severity_score)
        counts[lab] += 1
    spec = [
        ("CRITICAL", counts["CRITICAL"], "#ef4444", "severity ≥ 7"),
        ("WARNING", counts["WARNING"], "#f59e0b", "severity 4–6"),
        ("INFO", counts["INFO"], "#10b981", "severity 1–3"),
        ("TOTAL", len(analyses), "#06b6d4", "events tracked"),
    ]
    cards = "".join(
        f'<div class="rp-stat" style="--accent:{color}">'
        f'<div class="rp-stat-num">{n}</div>'
        f'<div class="rp-stat-lab">{lab}</div>'
        f'<div class="rp-stat-sub">{sub}</div>'
        f"</div>"
        for lab, n, color, sub in spec
    )
    st.markdown(f'<div class="rp-stats">{cards}</div>', unsafe_allow_html=True)


_TAG_RE = re.compile(r"\[(CRITICAL|WARNING|INFO)(?:\s+(\d+))?\]")


def _colorize_tags(text: str) -> str:
    color_for = {"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "INFO": "#10b981"}

    def _sub(m: re.Match) -> str:
        label = m.group(1)
        num = m.group(2)
        body = f"{label} {num}" if num else label
        c = color_for[label]
        return (
            f'<span class="rp-badge" style="background:{c}1f;color:{c};'
            f'border:1px solid {c}55">{body}</span>'
        )

    return _TAG_RE.sub(_sub, text)


# Match a "### [CRITICAL N] Title" or "### [WARNING N] Title" block.
# Captures the inline tag color so we can style the wrapping card.
_ALERT_BLOCK_RE = re.compile(
    r"^###\s+\[(CRITICAL|WARNING|INFO)\s+(\d+)\]\s+(.+?)(?=^###\s|^##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _wrap_alert_cards(markdown: str) -> str:
    """Convert each `### [SEV N] ... ` block into a styled card div containing markdown.

    We wrap the heading + body in a div whose left border picks up the severity
    color. Streamlit's markdown renderer processes content inside divs as long
    as we leave blank lines around the markup.
    """
    color_for = {"CRITICAL": "#ef4444", "WARNING": "#f59e0b", "INFO": "#10b981"}

    def _sub(m: re.Match) -> str:
        label = m.group(1)
        block = m.group(0).rstrip()
        c = color_for[label]
        return (
            f'\n<div class="rp-alert" style="--accent:{c}">\n\n'
            f"{block}\n\n"
            f"</div>\n"
        )

    return _ALERT_BLOCK_RE.sub(_sub, markdown)


_HEATMAP_RE = re.compile(
    r"## Sector Exposure Heat Map\s*\n+(\|.+?\|)\s*\n\s*(?:\|[\s\-:|]+\|\s*\n)?((?:\|.*\|\s*\n?)+)",
    re.DOTALL,
)


def _render_heatmap(markdown: str) -> str:
    """Replace the heatmap markdown table with a styled grid."""

    def _sub(m: re.Match) -> str:
        rows_block = m.group(2).strip()
        cells_html = []
        for line in rows_block.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            sector, level, driver = cells[0], cells[1], cells[2]
            level_clean = re.sub(r"\*+", "", level).strip().upper()
            color = {
                "HIGH": "#ef4444",
                "MEDIUM": "#f59e0b",
                "LOW": "#10b981",
            }.get(level_clean, "#7c8aa1")
            cells_html.append(
                f'<div class="rp-heat-row" style="--accent:{color}">'
                f'<div class="rp-heat-sector">{sector}</div>'
                f'<div class="rp-heat-level" style="background:{color}1f;color:{color};border:1px solid {color}55">{level_clean}</div>'
                f'<div class="rp-heat-driver">{driver}</div>'
                f"</div>"
            )
        return (
            "## Sector Exposure Heat Map\n\n"
            f'<div class="rp-heat">{"".join(cells_html)}</div>\n'
        )

    return _HEATMAP_RE.sub(_sub, markdown)


def render_briefing(briefing_text: str) -> None:
    if not briefing_text:
        st.info("Click **Refresh** to generate a risk briefing.")
        return
    text = _wrap_alert_cards(briefing_text)
    text = _render_heatmap(text)
    text = _colorize_tags(text)
    st.markdown(text, unsafe_allow_html=True)
