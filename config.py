import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MODEL_NAME = "claude-haiku-4-5-20251001"           # Sentinel + Analyst (fast)
ANTHROPIC_MODEL_NAME = "claude-haiku-4-5-20251001" # Briefer + Chat

DEMO_MODE = True       # limits news fetch for fast demo runs
DEMO_MAX_ARTICLES = 20


def validate() -> None:
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not NEWS_API_KEY:
        missing.append("NEWS_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in the values."
        )
