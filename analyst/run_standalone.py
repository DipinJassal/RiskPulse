from __future__ import annotations

import json
import os
from typing import List, Tuple

from analyst.rag_chain import RAGAnalyzer
from analyst.schemas import EventSchema


def _pretty(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)


def _build_test_events() -> List[Tuple[str, EventSchema]]:
    # Two contrasting events to sanity-check score ordering and action specificity.
    minor_earnings = EventSchema(
        headline="Mid-cap software firm misses earnings by a penny; reiterates full-year guidance",
        raw_text=(
            "Company reported EPS slightly below consensus due to timing of expenses. "
            "Management reiterated full-year revenue outlook and noted stable renewal rates. "
            "No changes to liquidity position or debt covenants were disclosed."
        ),
        source="demo",
    )

    bank_fraud_run = EventSchema(
        headline="Regional bank discloses internal fraud investigation; large uninsured depositors begin withdrawing funds",
        raw_text=(
            "The bank said it discovered irregularities in loan documentation and has placed several employees on leave. "
            "Social media chatter among local business groups accelerated after reports of unrealized losses on securities. "
            "Several large, uninsured depositors reportedly initiated transfers to money market funds. "
            "Management stated it is exploring liquidity options and may seek capital."
        ),
        source="demo",
    )

    return [
        ("minor_earnings_miss", minor_earnings),
        ("bank_fraud_and_deposit_run", bank_fraud_run),
    ]


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Add it to your environment (or .env) before running."
        )

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

    # Simple ordering check: bank fraud/run should score higher than minor earnings miss.
    score_minor = results[0][2].severity_score
    score_bank = results[1][2].severity_score
    print("\n" + "=" * 88)
    print("Sanity checks")
    print(f"- minor earnings severity_score: {score_minor}")
    print(f"- bank fraud/run severity_score: {score_bank}")
    if score_bank <= score_minor:
        raise SystemExit(
            "Sanity check failed: bank fraud/run severity_score was not higher than minor earnings miss."
        )
    print("- OK: severity score ordering makes sense.")


if __name__ == "__main__":
    main()

