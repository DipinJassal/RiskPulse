import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import OPENAI_API_KEY, MODEL_NAME
from schemas import AnalysisSchema

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

    for a in analyses:
        for sector in a.affected_sectors:
            sectors[sector] = max(sectors.get(sector, 0), a.severity_score)
        actions.extend(a.recommended_actions[:1])

    def _label(score: int) -> str:
        return "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"

    lines = [
        "## EXECUTIVE SUMMARY",
        f"- [INFO] Processed {len(analyses)} events. {len(critical)} critical, {len(watch)} on watch list.",
        "",
        "## CRITICAL ALERTS",
    ]
    lines += [f"- [CRITICAL] ({a.severity_score}/10) {a.risk_summary}" for a in critical] or ["- [INFO] No critical alerts today."]
    lines += ["", "## WATCH LIST"]
    lines += [f"- [WARNING] ({a.severity_score}/10) {a.risk_summary}" for a in watch] or ["- [INFO] No events in watch-list range."]
    lines += ["", "## SECTOR EXPOSURE HEAT MAP"]
    lines += [f"- {s}: {_label(v)}" for s, v in sorted(sectors.items(), key=lambda x: x[1], reverse=True)] or ["- No sector data available."]
    lines += ["", "## RECOMMENDED ACTIONS"]
    lines += [f"- {a}" for a in actions[:5]] or ["- Review portfolio exposure and monitor developing events."]
    return "\n".join(lines)


def generate_briefing(analyses: list[AnalysisSchema]) -> str:
    if not analyses:
        return _fallback_briefing([])

    try:
        llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=2048)
        payload = json.dumps([a.model_dump() for a in analyses], indent=2)
        response = llm.invoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"ANALYZED RISK EVENTS:\n{payload}"),
            ]
        )
        return response.content.strip()
    except Exception as e:
        print(f"[Briefer] LLM briefing failed: {e}. Using fallback.")
        return _fallback_briefing(analyses)
