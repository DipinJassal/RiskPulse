import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from briefer.chat import RiskChat
from schemas import AnalysisSchema, EventSchema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("Pipeline")


def run_pipeline() -> tuple[list[EventSchema], list[AnalysisSchema], str, RiskChat]:
    logger.info("=== RiskPulse Pipeline Starting ===")

    logger.info("Step 1/3 — Sentinel Agent: gathering and filtering news...")
    from sentinel.agent import run_sentinel
    events = run_sentinel()
    logger.info(f"Sentinel complete: {len(events)} events collected.")

    logger.info("Step 2/3 — Analyst Agent: RAG-based risk assessment...")
    from analyst.agent import run_analyst
    analyses = run_analyst(events)
    logger.info(f"Analyst complete: {len(analyses)} analyses generated.")

    logger.info("Step 3/3 — Briefer Agent: synthesizing risk briefing...")
    from briefer.agent import run_briefer
    briefing_text, chat = run_briefer(analyses)
    logger.info("Briefer complete: briefing ready.")

    logger.info("=== Pipeline Complete ===")
    return events, analyses, briefing_text, chat


if __name__ == "__main__":
    events, analyses, briefing, chat = run_pipeline()
    print("\n" + "=" * 70)
    print(briefing)
    print("=" * 70)
