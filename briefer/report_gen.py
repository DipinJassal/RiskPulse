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

_llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=2048)


def generate_briefing(analyses: list[AnalysisSchema]) -> str:
    payload = json.dumps([a.model_dump() for a in analyses], indent=2)
    response = _llm.invoke(
        [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"ANALYZED RISK EVENTS:\n{payload}"),
        ]
    )
    return response.content.strip()
