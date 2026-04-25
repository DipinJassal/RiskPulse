from langchain_anthropic import ChatAnthropic
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain_core.prompts import PromptTemplate
from config import ANTHROPIC_API_KEY, MODEL_NAME

_SYSTEM_CONTEXT = (
    "You are a risk analyst assistant. You have access to today's risk briefing and "
    "conversation history. Answer questions about the briefing, compare to historical events, "
    "explain risk scores, and provide additional analysis. Be concise and data-driven."
)


class RiskChat:
    def __init__(self, briefing_text: str = ""):
        self.briefing_text = briefing_text
        self._build_chain()

    def _build_chain(self):
        self.memory = ConversationBufferWindowMemory(k=10, return_messages=False)
        llm = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=1024)
        template = (
            f"{_SYSTEM_CONTEXT}\n\n"
            f"TODAY'S RISK BRIEFING:\n{self.briefing_text}\n\n"
            "Current conversation:\n{history}\nHuman: {input}\nAssistant:"
        )
        prompt = PromptTemplate(input_variables=["history", "input"], template=template)
        self.chain = ConversationChain(llm=llm, memory=self.memory, prompt=prompt, verbose=False)

    def chat(self, user_question: str) -> str:
        return self.chain.predict(input=user_question)

    def reset(self, new_briefing: str = ""):
        self.briefing_text = new_briefing
        self._build_chain()
