import json
import time
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from config import ANTHROPIC_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (
    "You are a financial risk analyst. Given a news article, assess: "
    "1) relevance_score (0.0-1.0) for financial risk impact, "
    "2) category (one of: regulatory, earnings, macro, credit, geopolitical, market, bankruptcy, fraud), "
    "3) affected_entities (list of company/sector names mentioned). "
    "Respond in JSON only."
)

_llm = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=512)


def classify_relevance(article_text: str) -> dict:
    for attempt in range(3):
        try:
            response = _llm.invoke(
                [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=article_text),
                ]
            )
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw)
        except Exception as e:
            wait = 2 ** (attempt + 1)
            print(f"[Classifier] attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return {"relevance_score": 0.0, "category": "unknown", "affected_entities": []}
