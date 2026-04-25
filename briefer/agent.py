from schemas import AnalysisSchema
from briefer.report_gen import generate_briefing
from briefer.chat import RiskChat


def run_briefer(analyses: list[AnalysisSchema]) -> tuple[str, RiskChat]:
    print("[Briefer] Generating risk briefing...")
    briefing_text = generate_briefing(analyses)
    chat = RiskChat(briefing_text=briefing_text)
    print("[Briefer] Done.")
    return briefing_text, chat


def ask_followup(chat: RiskChat, question: str) -> str:
    return chat.chat(question)


if __name__ == "__main__":
    from datetime import datetime
    from schemas import AnalysisSchema

    mock_analyses = [
        AnalysisSchema(
            event_id="mock-001",
            severity_score=9,
            affected_sectors=["financials", "credit"],
            risk_summary="A regional bank is under SEC investigation for accounting fraud, raising systemic risk concerns.",
            recommended_actions=["Reduce exposure to regional bank equities", "Monitor credit spreads", "Alert compliance team"],
            historical_context="Similar to the 2023 SVB collapse, where deposit runs followed regulatory scrutiny.",
        ),
        AnalysisSchema(
            event_id="mock-002",
            severity_score=7,
            affected_sectors=["macro", "fixed income"],
            risk_summary="Fed rate hike of 50bps signals continued tightening cycle, pressuring bond markets.",
            recommended_actions=["Shorten duration", "Review floating rate exposure", "Stress test bond portfolios"],
            historical_context="Mirrors the 2022 rate hike cycle that triggered a bond market selloff.",
        ),
        AnalysisSchema(
            event_id="mock-003",
            severity_score=4,
            affected_sectors=["technology", "advertising"],
            risk_summary="Tech earnings miss driven by ad revenue decline signals sector softness.",
            recommended_actions=["Review tech overweights", "Watch for sector rotation"],
            historical_context="Minor relative to broader earnings miss cycles seen in 2022.",
        ),
    ]

    briefing, chat = run_briefer(mock_analyses)
    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)

    q1 = "Which sector has the highest risk today?"
    print(f"\nQ: {q1}\nA: {ask_followup(chat, q1)}")

    q2 = "How does today compare to the 2008 crisis?"
    print(f"\nQ: {q2}\nA: {ask_followup(chat, q2)}")
