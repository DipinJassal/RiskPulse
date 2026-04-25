from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from schemas import AnalysisSchema, EventSchema
from analyst.rag_chain import RAGAnalyzer
import analyst.cache as cache

_MAX_WORKERS = 5  # parallel LLM calls


def _analyze_one(analyzer: RAGAnalyzer, event: EventSchema) -> AnalysisSchema:
    cached = cache.get(event.headline)
    if cached:
        print(f"[Analyst] Cache hit: {event.headline[:60]}")
        return cached
    result = analyzer.analyze_event(event)
    cache.set(event.headline, result)
    return result


def run_analyst(events: list[EventSchema]) -> list[AnalysisSchema]:
    if not events:
        print("[Analyst] No events to analyze.")
        return []

    print(f"[Analyst] Analyzing {len(events)} events with {_MAX_WORKERS} parallel workers...")
    t0 = time.perf_counter()

    analyzer = RAGAnalyzer()
    analyses: list[AnalysisSchema] = [None] * len(events)  # type: ignore

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        future_to_idx = {
            pool.submit(_analyze_one, analyzer, event): i
            for i, event in enumerate(events)
        }
        done = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                analyses[idx] = future.result()
            except Exception as e:
                print(f"[Analyst] Event {idx} failed: {e}")
                analyses[idx] = AnalysisSchema(
                    event_id=events[idx].event_id,
                    severity_score=1,
                    affected_sectors=[],
                    risk_summary="Analysis failed.",
                    recommended_actions=[],
                    historical_context="",
                )
            done += 1
            print(f"[Analyst] {done}/{len(events)} complete", end="\r")

    analyses = [a for a in analyses if a is not None]
    analyses.sort(key=lambda a: a.severity_score, reverse=True)
    elapsed = time.perf_counter() - t0
    print(f"\n[Analyst] Done in {elapsed:.1f}s. Top severity: {analyses[0].severity_score if analyses else 'N/A'}")
    return analyses


if __name__ == "__main__":
    from datetime import datetime, timezone

    mock_events = [
        EventSchema(
            event_id="mock-001",
            headline="Federal Reserve raises interest rates by 50 basis points",
            source="Reuters", category="macro",
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_text="The Federal Reserve increased its benchmark rate in response to persistent inflation.",
            relevance_score=0.85,
        ),
        EventSchema(
            event_id="mock-002",
            headline="Major tech company reports 30% earnings miss",
            source="Bloomberg", category="earnings",
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_text="The company cited declining ad revenue and increased competition as causes.",
            relevance_score=0.72,
        ),
        EventSchema(
            event_id="mock-003",
            headline="Regional bank under SEC investigation for accounting fraud",
            source="WSJ", category="fraud",
            timestamp=datetime.now(timezone.utc).isoformat(),
            raw_text="Regulators have opened a probe into the bank's balance sheet misrepresentations.",
            relevance_score=0.95,
        ),
    ]

    results = run_analyst(mock_events)
    for r in results:
        print(f"\n[{r.severity_score}/10] {r.event_id}")
        print(f"  Sectors: {r.affected_sectors}")
        print(f"  Summary: {r.risk_summary}")
