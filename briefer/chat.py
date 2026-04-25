from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_CONTEXT = (
    "You are a risk analyst assistant. You have access to today's risk briefing and "
    "conversation history. Answer questions about the briefing, compare to historical events, "
    "explain risk scores, and provide additional analysis. Be concise and data-driven."
)


class RiskChat:
    def __init__(self, briefing_text: str = ""):
        self.briefing_text = briefing_text
        self.llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=1024)
        self.history: list = []

    def chat(self, user_question: str) -> str:
        system_prompt = (
            f"{_SYSTEM_CONTEXT}\n\n"
            f"TODAY'S RISK BRIEFING:\n{self.briefing_text}"
        )
        messages = [SystemMessage(content=system_prompt)]
        # Keep last 10 exchanges (20 messages)
        messages += self.history[-20:]
        messages.append(HumanMessage(content=user_question))

        response = self.llm.invoke(messages)
        answer = response.content

        self.history.append(HumanMessage(content=user_question))
        self.history.append(AIMessage(content=answer))
        return answer

    def reset(self, new_briefing: str = ""):
        self.briefing_text = new_briefing
        self.history = []
