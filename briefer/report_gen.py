import json
import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL_NAME
from schemas import AnalysisSchema

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a risk intelligence briefing writer. Given analyzed risk events, \
produce a structured morning briefing.

REQUIRED SECTIONS — use exactly these markdown headers in this order:
## Executive Summary
## Critical Alerts
## Watch List
## Sector Exposure Heat Map
## Recommended Actions

FORMATTING RULES:
- Executive Summary: 2-3 sentences on the overall risk landscape today.
- Critical Alerts (severity ≥ 7): one card per event using this heading format exactly:
    ### [CRITICAL <score>] <short title>
  Then 2-3 sentences of analysis, a Sectors line, and an Action line.
- Watch List (severity 4-6): bullet list using inline `[WARNING <score>]` tags.
- Sector Exposure Heat Map: a markdown table with columns Sector | Risk | Driver.
  Risk values must be exactly HIGH, MEDIUM, or LOW (no bold, no other values).
- Recommended Actions: numbered list with time horizon prefix (Today / This week / Next 30 days).
- Be concise and data-driven. No filler sentences."""


def _fallback_briefing(analyses: list[AnalysisSchema]) -> str:
    critical = [a for a in analyses if a.severity_score >= 7]
    watch = [a for a in analyses if 4 <= a.severity_score <= 6]
    sectors: dict[str, int] = {}
    actions: list[str] = []

    for a in analyses:
        for sector in a.affected_sectors:
            sectors[sector] = max(sectors.get(sector, 0), a.severity_score)
        actions.extend(a.recommended_actions[:1])

    def _label(score: int) -> str:
        return "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"

    lines = [
        "## Executive Summary",
        f"Processed {len(analyses)} events. {len(critical)} critical, {len(watch)} on watch list.",
        "",
        "## Critical Alerts",
    ]
    for a in critical:
        lines.append(f"### [CRITICAL {a.severity_score}] Event {a.event_id}")
        lines.append(a.risk_summary)
        lines.append(f"- **Sectors** — {', '.join(a.affected_sectors)}")
        lines.append("")
    if not critical:
        lines.append("No critical alerts today.")
    lines += ["", "## Watch List"]
    lines += [f"- **[WARNING {a.severity_score}]** {a.risk_summary}" for a in watch] or ["- No events in watch-list range."]
    lines += ["", "## Sector Exposure Heat Map", "", "| Sector | Risk | Driver |", "|---|---|---|"]
    lines += [f"| {s} | {_label(v)} | — |" for s, v in sorted(sectors.items(), key=lambda x: x[1], reverse=True)] or ["| — | LOW | No data |"]
    lines += ["", "## Recommended Actions"]
    lines += [f"{i+1}. {a}" for i, a in enumerate(actions[:5])] or ["1. Review portfolio exposure and monitor developing events."]
    return "\n".join(lines)


def generate_briefing(analyses: list[AnalysisSchema]) -> str:
    if not analyses:
        return _fallback_briefing([])

    try:
        llm = ChatAnthropic(model=ANTHROPIC_MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=2048)
        payload = json.dumps([a.model_dump() for a in analyses], indent=2)
        response = llm.invoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"ANALYZED RISK EVENTS:\n{payload}"),
            ]
        )
        return response.content.strip()
    except Exception as e:
        logger.error("LLM briefing failed: %s — using fallback.", e)
        return _fallback_briefing(analyses)
