from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_CONTEXT = (
    "You are a risk analyst assistant. You have access to today's risk briefing and "
    "conversation history. Answer questions about the briefing, compare to historical events, "
    "explain risk scores, and provide additional analysis. Be concise and data-driven."
)


class RiskChat:
    def __init__(self, briefing_text: str = ""):
        self.briefing_text = briefing_text
        self.history: list[tuple[str, str]] = []
        self.llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=1024)

    def chat(self, user_question: str) -> str:
        history_text = "\n".join(
            f"Human: {q}\nAssistant: {a}" for q, a in self.history[-10:]
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
