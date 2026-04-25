import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
try:
    from config import ANTHROPIC_API_KEY, MODEL_NAME
except Exception:
    ANTHROPIC_API_KEY = ""
    MODEL_NAME = "claude-sonnet-4-6"
from briefer.models import AnalysisSchema

_SYSTEM_PROMPT = (
    "You are a risk intelligence briefing writer. Given a list of analyzed risk events, "
    "produce a structured morning risk briefing with these sections: "
    "1) EXECUTIVE SUMMARY (2-3 sentences on overall risk landscape), "
    "2) CRITICAL ALERTS (severity >= 7, detailed analysis), "
    "3) WATCH LIST (severity 4-6, brief descriptions), "
    "4) SECTOR EXPOSURE HEAT MAP (list sectors with HIGH/MEDIUM/LOW risk), "
    "5) RECOMMENDED ACTIONS (prioritized list). "
    "Use clear headers, bullet points, and severity color coding [CRITICAL] [WARNING] [INFO]."
)

def _fallback_briefing(analyses: list[AnalysisSchema]) -> str:
    critical = [a for a in analyses if a.severity_score >= 7]
    watch = [a for a in analyses if 4 <= a.severity_score <= 6]
    sectors: dict[str, int] = {}
    actions: list[str] = []

    for analysis in analyses:
        for sector in analysis.affected_sectors:
            sectors[sector] = max(sectors.get(sector, 0), analysis.severity_score)
        actions.extend(analysis.recommended_actions[:1])

    def _risk_label(score: int) -> str:
        if score >= 7:
            return "HIGH"
        if score >= 4:
            return "MEDIUM"
        return "LOW"

    lines = [
        "## EXECUTIVE SUMMARY",
        f"- [INFO] Processed {len(analyses)} events. {len(critical)} are critical and {len(watch)} are on watch list.",
        "",
        "## CRITICAL ALERTS",
    ]
    if critical:
        for item in critical:
            lines.append(f"- [CRITICAL] ({item.severity_score}/10) {item.risk_summary}")
    else:
        lines.append("- [INFO] No critical alerts today.")

    lines.append("")
    lines.append("## WATCH LIST")
    if watch:
        for item in watch:
            lines.append(f"- [WARNING] ({item.severity_score}/10) {item.risk_summary}")
    else:
        lines.append("- [INFO] No events in watch-list range.")

    lines.append("")
    lines.append("## SECTOR EXPOSURE HEAT MAP")
    if sectors:
        for sector, score in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- {sector}: {_risk_label(score)}")
    else:
        lines.append("- No sector exposure data available.")

    lines.append("")
    lines.append("## RECOMMENDED ACTIONS")
    if actions:
        for action in actions[:5]:
            lines.append(f"- {action}")
    else:
        lines.append("- Review portfolio exposure and monitor developing events.")

    lines.append("")
    lines.append("_Fallback briefing generated without Anthropic API key._")
    return "\n".join(lines)


def generate_briefing(analyses: list[AnalysisSchema]) -> str:
    if not ANTHROPIC_API_KEY:
        return _fallback_briefing(analyses)

    llm = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=2048)
    payload = json.dumps([a.model_dump() for a in analyses], indent=2)
    response = llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"ANALYZED RISK EVENTS:\n{payload}"),
        ]
    )
    return response.content.strip()
