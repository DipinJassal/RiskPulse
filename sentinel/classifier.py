import json
import time
from json_repair import repair_json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import OPENAI_API_KEY, MODEL_NAME

_SYSTEM_PROMPT = (
    "You are a financial risk analyst. Given a news article, assess: "
    "1) relevance_score (0.0-1.0) for financial risk impact, "
    "2) category (one of: regulatory, earnings, macro, credit, geopolitical, market, bankruptcy, fraud), "
    "3) affected_entities (list of company/sector names mentioned). "
    "Respond in JSON only."
)

_llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=512)


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
            parsed = json.loads(repair_json(raw))
            # LLM occasionally wraps the object in an array
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else {}
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            wait = 2 ** (attempt + 1)
            print(f"[Classifier] attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    return {"relevance_score": 0.0, "category": "unknown", "affected_entities": []}
