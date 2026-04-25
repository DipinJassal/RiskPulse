from schemas import AnalysisSchema, EventSchema
from analyst.rag_chain import RAGAnalyzer


def run_analyst(events: list[EventSchema]) -> list[AnalysisSchema]:
    print(f"[Analyst] Analyzing {len(events)} events...")
    analyzer = RAGAnalyzer()
    analyses = [analyzer.analyze_event(event) for event in events]
    analyses.sort(key=lambda a: a.severity_score, reverse=True)
    print(f"[Analyst] Done. Top severity: {analyses[0].severity_score if analyses else 'N/A'}")
    return analyses


if __name__ == "__main__":
    from datetime import datetime

    mock_events = [
        EventSchema(
            event_id="mock-001",
            headline="Federal Reserve raises interest rates by 50 basis points",
            source="Reuters",
            category="macro",
            timestamp=datetime.utcnow().isoformat(),
            raw_text="The Federal Reserve increased its benchmark rate in response to persistent inflation.",
            relevance_score=0.85,
        ),
        EventSchema(
            event_id="mock-002",
            headline="Major tech company reports 30% earnings miss",
            source="Bloomberg",
            category="earnings",
            timestamp=datetime.utcnow().isoformat(),
            raw_text="The company cited declining ad revenue and increased competition as causes.",
            relevance_score=0.72,
        ),
        EventSchema(
            event_id="mock-003",
            headline="Regional bank under SEC investigation for accounting fraud",
            source="WSJ",
            category="fraud",
            timestamp=datetime.utcnow().isoformat(),
            raw_text="Regulators have opened a probe into the bank's balance sheet misrepresentations.",
            relevance_score=0.95,
        ),
    ]

    results = run_analyst(mock_events)
    for r in results:
        print(f"\n[{r.severity_score}/10] {r.event_id}")
        print(f"  Sectors: {r.affected_sectors}")
        print(f"  Summary: {r.risk_summary}")
        print(f"  Context: {r.historical_context}")
