from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Tuple

from analyst.rag_chain import RAGAnalyzer
from schemas import EventSchema


def _pretty(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)


def _build_test_events() -> List[Tuple[str, EventSchema]]:
    now = datetime.now(timezone.utc).isoformat()

    minor_earnings = EventSchema(
        event_id=str(uuid.uuid4()),
        headline="Mid-cap software firm misses earnings by a penny; reiterates full-year guidance",
        raw_text=(
            "Company reported EPS slightly below consensus due to timing of expenses. "
            "Management reiterated full-year revenue outlook and noted stable renewal rates. "
            "No changes to liquidity position or debt covenants were disclosed."
        ),
        source="demo",
        category="earnings",
        timestamp=now,
        relevance_score=0.55,
    )

    bank_fraud_run = EventSchema(
        event_id=str(uuid.uuid4()),
        headline="Regional bank discloses internal fraud; large uninsured depositors begin withdrawing",
        raw_text=(
            "The bank said it discovered irregularities in loan documentation and placed several "
            "employees on leave. Social media chatter accelerated after reports of unrealized losses "
            "on securities. Several large uninsured depositors initiated transfers to money market funds. "
            "Management stated it is exploring liquidity options and may seek capital."
        ),
        source="demo",
        category="fraud",
        timestamp=now,
        relevance_score=0.95,
    )

    return [
        ("minor_earnings_miss", minor_earnings),
        ("bank_fraud_and_deposit_run", bank_fraud_run),
    ]


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Add it to your .env before running.")

    analyzer = RAGAnalyzer()
    results = []

    for name, event in _build_test_events():
        analysis = analyzer.analyze_event(event)
        results.append((name, event, analysis))

    for name, event, analysis in results:
        print("\n" + "=" * 88)
        print(name)
        print("- headline:", event.headline)
        print(_pretty(analysis.model_dump()))

    score_minor = results[0][2].severity_score
    score_bank = results[1][2].severity_score
    print("\n" + "=" * 88)
    print("Sanity checks")
    print(f"- minor earnings severity_score : {score_minor}")
    print(f"- bank fraud/run severity_score : {score_bank}")
    if score_bank <= score_minor:
        raise SystemExit("Sanity check FAILED: bank fraud score was not higher than minor earnings.")
    print("- OK: severity score ordering makes sense.")


if __name__ == "__main__":
    main()
