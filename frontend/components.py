"""UI helpers for the RiskPulse Streamlit dashboard."""
from __future__ import annotations

import re
from datetime import datetime, timezone

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
    glow = ' class="rp-badge rp-badge-crit"' if color == "#ef4444" else ' class="rp-badge"'
    return (
        f'<span{glow} style="background:{color}1f;color:{color};'
        f'border:1px solid {color}55">{label} {score}</span>'
    )


def _format_ts(ts: str) -> str:
    return ts[:16].replace("T", " ") if ts else ""

def render_sidebar_minimal(
    events: list[EventSchema],
    analyses: list[AnalysisSchema],
) -> str | None:
    """Minimal sidebar: a couple of filters + a single event picker."""
    if not events or not analyses:
        st.sidebar.info("No events yet. Click **Refresh**.")
        return None

    score_map = {a.event_id: int(a.severity_score) for a in analyses}

    st.sidebar.markdown(
        '<div class="rp-side-h"><span>Events</span></div>', unsafe_allow_html=True
    )

    min_sev = st.sidebar.slider("Min severity", 1, 10, 4)
    categories = sorted({(e.category or "").lower() for e in events if e.category})
    cat = st.sidebar.selectbox("Category", ["all"] + categories, index=0)

    filtered = []
    for e in events:
        sev = score_map.get(e.event_id, 0)
        if sev < min_sev:
            continue
        if cat != "all" and (e.category or "").lower() != cat:
            continue
        filtered.append(e)

    if not filtered:
        st.sidebar.warning("No events match the filters.")
        return None

    filtered = sorted(filtered, key=lambda e: score_map.get(e.event_id, 0), reverse=True)

    def _label(e: EventSchema) -> str:
        sev = score_map.get(e.event_id, 0)
        title = e.headline if len(e.headline) <= 60 else e.headline[:57] + "..."
        return f"{sev}/10 · {title}"

    # keep selection if still present
    current = st.session_state.get("selected_event_id")
    ids = [e.event_id for e in filtered]
    idx = ids.index(current) if current in ids else 0
    id_to_event = {e.event_id: e for e in filtered}
    picked = st.sidebar.radio(
        "Pick an event",
        ids,
        index=idx,
        format_func=lambda i: _label(id_to_event[i]),
    )
    st.session_state["selected_event_id"] = picked
    return picked


def render_selected_event(
    events: list[EventSchema],
    analyses: list[AnalysisSchema],
    *,
    selected_event_id: str | None,
) -> None:
    if not selected_event_id:
        st.info("Pick an event from the sidebar.")
        return

    event = next((e for e in events if e.event_id == selected_event_id), None)
    analysis = next((a for a in analyses if a.event_id == selected_event_id), None)
    if not event or not analysis:
        st.info("Selected event not found.")
        return

    color, label = _severity(int(analysis.severity_score))
    st.markdown(
        f'<div class="rp-alert" style="--accent:{color}">'
        f"<h3>{severity_badge(int(analysis.severity_score))} {event.headline}</h3>"
        f'<div class="rp-evt-time">{_format_ts(event.timestamp)} · {event.source} · {event.category}</div>'
        f"<p>{analysis.risk_summary}</p>"
        f"<p><b>Historical context:</b> {analysis.historical_context}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if analysis.affected_sectors:
        chips = "".join(f'<span class="rp-chip">{s}</span>' for s in analysis.affected_sectors)
        st.markdown(f'<div class="rp-chips">{chips}</div>', unsafe_allow_html=True)

    if analysis.recommended_actions:
        st.markdown("#### Recommended actions")
        for a in analysis.recommended_actions[:5]:
            st.markdown(f"- {a}")


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


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # ISO timestamps in mock/pipeline are tz-aware (e.g. 2026-...+00:00)
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def render_overview(events: list[EventSchema], analyses: list[AnalysisSchema]) -> None:
    """Minimal, high-signal overview with a few charts."""
    if not events or not analyses:
        st.info("No data yet. Click **Refresh** to generate events and analyses.")
        return

    import pandas as pd

    sev_by_id = {a.event_id: int(a.severity_score) for a in analyses}
    sectors_by_id = {a.event_id: list(a.affected_sectors or []) for a in analyses}

    rows = []
    for e in events:
        sev = sev_by_id.get(e.event_id)
        if sev is None:
            continue
        rows.append(
            {
                "event_id": e.event_id,
                "timestamp": _parse_ts(e.timestamp),
                "headline": e.headline,
                "category": (e.category or "").upper(),
                "source": e.source,
                "relevance": float(e.relevance_score),
                "severity": int(sev),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("No analyzed events available yet.")
        return

    df = df.sort_values("severity", ascending=False)

    # --- Layout: keep it minimal (2 charts) ---
    col_a, col_b = st.columns([1.0, 1.6], gap="large")

    with col_a:
        st.markdown("#### Severity mix")
        buckets = (
            df.assign(
                bucket=pd.cut(
                    df["severity"],
                    bins=[0, 3, 6, 10],
                    labels=["1–3 (Low)", "4–6 (Medium)", "7–10 (High)"],
                    include_lowest=True,
                )
            )["bucket"]
            .value_counts()
            .reindex(["7–10 (High)", "4–6 (Medium)", "1–3 (Low)"])
            .fillna(0)
            .astype(int)
        )
        st.bar_chart(buckets, height=220)
        st.caption("Fast read on today’s risk concentration.")

    with col_b:
        st.markdown("#### Sector exposure (weighted)")
        weights = {}
        for a in analyses:
            sev = int(a.severity_score)
            for s in a.affected_sectors or []:
                weights[s] = weights.get(s, 0) + sev
        sector_df = (
            pd.DataFrame([{"sector": k, "risk_weight": v} for k, v in weights.items()])
            .sort_values("risk_weight", ascending=False)
            .head(10)
        )
        if sector_df.empty:
            st.info("No sectors found.")
        else:
            st.bar_chart(sector_df.set_index("sector")["risk_weight"], height=220)
        st.caption("Sum of severities across events mentioning the sector.")

    st.caption("Keep this page minimal: use the sidebar picker for details.")
