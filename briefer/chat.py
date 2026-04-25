from __future__ import annotations

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import OPENAI_API_KEY, MODEL_NAME
from schemas import AnalysisSchema

logger = logging.getLogger(__name__)

_SYSTEM_CONTEXT = (
    "You are a risk analyst assistant. You have access to today's risk briefing, "
    "the full structured analysis data (severity scores, affected sectors, recommended "
    "actions, historical context), and conversation history. "
    "Answer questions precisely — cite exact severity scores and sectors from the data. "
    "Compare to historical events when relevant. Be concise and data-driven."
)


class RiskChat:
    def __init__(self, briefing_text: str = "", analyses: list[AnalysisSchema] | None = None):
        self.briefing_text = briefing_text
        self.analyses = analyses or []
        self.history: list[tuple[str, str]] = []
        self.llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=1024)

    def _analysis_context(self) -> str:
        if not self.analyses:
            return ""
        lines = ["STRUCTURED ANALYSIS DATA (cite exact values in your answers):"]
        for a in self.analyses:
            lines.append(
                f"  • severity={a.severity_score}/10 | sectors={', '.join(a.affected_sectors)} | "
                f"summary={a.risk_summary[:120]} | "
                f"actions={'; '.join(a.recommended_actions[:2])} | "
                f"history={a.historical_context[:100]}"
            )
        return "\n".join(lines)

    def chat(self, user_question: str) -> str:
        history_text = "\n".join(
            f"Human: {q}\nAssistant: {a}" for q, a in self.history[-10:]
        )
        prompt = (
            f"TODAY'S RISK BRIEFING:\n{self.briefing_text}\n\n"
            f"{self._analysis_context()}\n\n"
            f"Conversation so far:\n{history_text}\n"
            f"Human: {user_question}\nAssistant:"
        )
        try:
            response = self.llm.invoke(
                [
                    SystemMessage(content=_SYSTEM_CONTEXT),
                    HumanMessage(content=prompt),
                ]
            )
            answer = response.content.strip() if isinstance(response.content, str) else str(response.content)
        except Exception as e:
            logger.error("Chat LLM call failed: %s", e)
            answer = "I'm unable to answer right now — the LLM call failed. Please try again."
        self.history.append((user_question, answer))
        self.history = self.history[-10:]
        return answer

    def reset(self, new_briefing: str = "", analyses: list[AnalysisSchema] | None = None) -> None:
        self.briefing_text = new_briefing
        self.analyses = analyses or []
        self.history = []
