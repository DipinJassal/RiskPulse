from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
try:
    from config import ANTHROPIC_API_KEY, MODEL_NAME
except Exception:
    ANTHROPIC_API_KEY = ""
    MODEL_NAME = "claude-sonnet-4-6"

_SYSTEM_CONTEXT = (
    "You are a risk analyst assistant. You have access to today's risk briefing and "
    "conversation history. Answer questions about the briefing, compare to historical events, "
    "explain risk scores, and provide additional analysis. Be concise and data-driven."
)


class RiskChat:
    def __init__(self, briefing_text: str = ""):
        self.briefing_text = briefing_text
        self.history: list[tuple[str, str]] = []
        self.llm = None
        self._build_chain()

    def _build_chain(self):
        if ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=1024)
        else:
            self.llm = None

    def chat(self, user_question: str) -> str:
        if not self.llm:
            response = (
                "No ANTHROPIC_API_KEY found. Running in fallback mode.\n"
                f"Question: {user_question}\n"
                "Use a valid key in .env for model-powered follow-ups."
            )
            self.history.append((user_question, response))
            self.history = self.history[-10:]
            return response

        history_text = "\n".join(
            [f"Human: {q}\nAssistant: {a}" for q, a in self.history[-10:]]
        )
        prompt = (
            f"{_SYSTEM_CONTEXT}\n\n"
            f"TODAY'S RISK BRIEFING:\n{self.briefing_text}\n\n"
            f"Current conversation:\n{history_text}\n"
            f"Human: {user_question}\nAssistant:"
        )
        response = self.llm.invoke(
            [
                SystemMessage(content=_SYSTEM_CONTEXT),
                HumanMessage(content=prompt),
            ]
        )
        answer = response.content.strip() if isinstance(response.content, str) else str(response.content)
        self.history.append((user_question, answer))
        self.history = self.history[-10:]
        return answer

    def reset(self, new_briefing: str = ""):
        self.briefing_text = new_briefing
        self.history = []
        self._build_chain()
