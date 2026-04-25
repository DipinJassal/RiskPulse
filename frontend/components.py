"""UI helpers for the RiskPulse Streamlit dashboard."""
from __future__ import annotations

import re

import streamlit as st

from schemas import AnalysisSchema, EventSchema

_CATEGORY_STYLE: dict[str, tuple[str, str]] = {
    "fraud":       ("#ef4444", "#2d0f0f"),
    "macro":       ("#f59e0b", "#2d1f06"),
    "earnings":    ("#f97316", "#2d1506"),
    "regulatory":  ("#3b82f6", "#0c1a35"),
    "geopolitical":("#a855f7", "#1c0e30"),
    "credit":      ("#ec4899", "#2d0a1c"),
    "market":      ("#06b6d4", "#041e28"),
    "bankruptcy":  ("#84cc16", "#121e04"),
}


def _severity(score: int) -> tuple[str, str]:
    """(hex_color, label) for a 1-10 severity score."""
    if score >= 7:
        return "#ef4444", "CRITICAL"
    if score >= 4:
        return "#f59e0b", "WARNING"
    return "#10b981", "INFO"


def severity_badge(score: int) -> str:
    color, label = _severity(score)
    glow = ' class="rp-badge rp-badge-crit"' if color == "#ef4444" else ' class="rp-badge"'
    return (
        f'<span{glow} style="background:{color}1f;color:{color};'
        f'border:1px solid {color}55">{label} {score}</span>'
    )


def _format_ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""


def render_event_sidebar(
    events: list[EventSchema],
    analyses: list[AnalysisSchema],
    severity_filter: str = "ALL",
) -> None:
    """Compact left-stripe event list with optional severity filter."""
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

    ordered = sorted(events, key=lambda e: score_map.get(e.event_id, 0), reverse=True)

    # apply filter
    if severity_filter != "ALL":
        ordered = [
            e for e in ordered
            if _severity(score_map.get(e.event_id, 0))[1] == severity_filter
        ]

    if not ordered:
        st.sidebar.info("No events match this filter.")
        return

    for event in ordered:
        score = score_map.get(event.event_id, 0)
        color, _ = _severity(score)
        title = event.headline if len(event.headline) <= 70 else event.headline[:67] + "..."

        cat = event.category.lower()
        cat_color, cat_bg = _CATEGORY_STYLE.get(cat, ("#7c8aa1", "#1a2638"))

        st.sidebar.markdown(
            f'<div class="rp-evt-wrap" style="--sev:{color}">', unsafe_allow_html=True
        )
        with st.sidebar.expander(f"{score}   {title}"):
            st.markdown(
                f'<div class="rp-evt-meta">'
                f'<span class="rp-pill" style="background:{color}1f;color:{color};border-color:{color}55">'
                f"sev {score}</span>"
                f'<span class="rp-pill-cat" style="background:{cat_bg};color:{cat_color};border:1px solid {cat_color}44">'
                f"{event.category}</span>"
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
    """KPI bar: counts by severity bucket with percentage of total."""
    counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for a in analyses:
        _, lab = _severity(a.severity_score)
        counts[lab] += 1
    total = len(analyses)

    def _pct(n: int) -> str:
        return f"{n / total * 100:.0f}% of total" if total else "—"

    spec = [
        ("CRITICAL", counts["CRITICAL"], "#ef4444", "severity ≥ 7"),
        ("WARNING",  counts["WARNING"],  "#f59e0b", "severity 4–6"),
        ("INFO",     counts["INFO"],     "#10b981", "severity 1–3"),
        ("TOTAL",    total,              "#06b6d4", "events tracked"),
    ]
    cards = "".join(
        f'<div class="rp-stat" style="--accent:{color}">'
        f'<div class="rp-stat-num">{n}</div>'
        f'<div class="rp-stat-lab">{lab}</div>'
        f'<div class="rp-stat-sub">{sub}</div>'
        f'<div class="rp-stat-pct">{"—" if lab == "TOTAL" else _pct(n)}</div>'
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
        glow = " rp-badge-crit" if label == "CRITICAL" else ""
        return (
            f'<span class="rp-badge{glow}" style="background:{c}1f;color:{c};'
            f'border:1px solid {c}55">{body}</span>'
        )

    return _TAG_RE.sub(_sub, text)


_ALERT_BLOCK_RE = re.compile(
    r"^###\s+\[(CRITICAL|WARNING|INFO)\s+(\d+)\]\s+(.+?)(?=^###\s|^##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _wrap_alert_cards(markdown: str) -> str:
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
