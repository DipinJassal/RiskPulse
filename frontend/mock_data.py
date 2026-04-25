"""Hardcoded mock data so the frontend can be built and demoed independently
of the Sentinel/Analyst/Briefer agents.

Member 4 Step 1 plan: "Start with hardcoded mock data so the UI can be built
independently." Replaced at integration time by `pipeline.run_pipeline()`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from schemas import AnalysisSchema, EventSchema


def _ts(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat(timespec="seconds")


MOCK_EVENTS: list[EventSchema] = [
    EventSchema(
        event_id="evt-001",
        headline="SEC opens fraud probe into mid-size regional bank over loan-loss disclosures",
        source="Reuters",
        category="fraud",
        timestamp=_ts(1.2),
        raw_text=(
            "The SEC has opened a formal investigation into a US regional bank's loan-loss "
            "reserve methodology after a whistleblower alleged systematic understatement of "
            "credit exposure across the commercial real estate book over six quarters."
        ),
        relevance_score=0.94,
    ),
    EventSchema(
        event_id="evt-002",
        headline="Fed minutes signal additional 50bps tightening as core inflation reaccelerates",
        source="Bloomberg",
        category="macro",
        timestamp=_ts(3.5),
        raw_text=(
            "FOMC minutes show broad consensus for further rate increases through Q2, citing "
            "stickier-than-expected services inflation and a labor market that 'remains "
            "imbalanced'. Markets repriced terminal rate expectations 30bps higher."
        ),
        relevance_score=0.88,
    ),
    EventSchema(
        event_id="evt-003",
        headline="Mega-cap chipmaker cuts FY guidance 18% on weakening enterprise demand",
        source="WSJ",
        category="earnings",
        timestamp=_ts(5.0),
        raw_text=(
            "A leading semiconductor company slashed full-year revenue guidance by 18%, citing "
            "deferred capex from hyperscaler customers and softening orders from automotive OEMs. "
            "Shares fell 12% after-hours; suppliers traded down in sympathy."
        ),
        relevance_score=0.81,
    ),
    EventSchema(
        event_id="evt-004",
        headline="EU passes sweeping AI Act provisions affecting US-based foundation model providers",
        source="Financial Times",
        category="regulatory",
        timestamp=_ts(7.8),
        raw_text=(
            "The EU finalized binding obligations for general-purpose AI providers, including "
            "model evaluation, copyright transparency, and red-teaming requirements. Non-compliance "
            "carries fines up to 7% of global revenue. US tech firms have 18 months to comply."
        ),
        relevance_score=0.72,
    ),
    EventSchema(
        event_id="evt-005",
        headline="Strait of Hormuz tensions escalate; Brent jumps 6% on supply disruption fears",
        source="Reuters",
        category="geopolitical",
        timestamp=_ts(9.4),
        raw_text=(
            "Naval incidents in the Strait of Hormuz prompted insurers to widen war-risk premiums "
            "for tanker traffic. Brent crude rose 6% intraday. Roughly 20% of global oil flows "
            "through the chokepoint; analysts warn of sustained price pressure if tensions persist."
        ),
        relevance_score=0.79,
    ),
    EventSchema(
        event_id="evt-006",
        headline="Major retailer announces 4,500 corporate layoffs amid restructuring",
        source="CNBC",
        category="credit",
        timestamp=_ts(11.0),
        raw_text=(
            "A top-10 US retailer disclosed plans to cut 4,500 corporate roles (~7% of HQ "
            "headcount) and shutter 90 underperforming stores. The company cited margin pressure "
            "from shrink, wage inflation, and a weaker consumer."
        ),
        relevance_score=0.55,
    ),
    EventSchema(
        event_id="evt-007",
        headline="Boutique investment bank receives credit-rating downgrade to BBB-",
        source="MarketWatch",
        category="credit",
        timestamp=_ts(14.2),
        raw_text=(
            "S&P downgraded a mid-tier investment bank one notch to BBB- (one above junk), "
            "citing concentration in leveraged-buyout underwriting and reliance on short-term "
            "wholesale funding. Outlook remains negative."
        ),
        relevance_score=0.48,
    ),
]


MOCK_ANALYSES: list[AnalysisSchema] = [
    AnalysisSchema(
        event_id="evt-001",
        severity_score=9,
        affected_sectors=["Financials", "Regional Banks", "Commercial Real Estate"],
        risk_summary=(
            "An SEC fraud probe into loan-loss disclosures echoes the early-2023 SVB and "
            "Signature Bank dynamics. If allegations are substantiated, contagion risk to "
            "peer regional banks and CRE-exposed lenders is high."
        ),
        recommended_actions=[
            "Reduce or hedge exposure to regional bank ETFs (KRE, KBWR) over the next 5 trading days",
            "Stress-test commercial real estate counterparty exposure against a 30% CRE markdown",
            "Monitor deposit-flow data and FHLB advance utilization at peer banks daily",
        ],
        historical_context=(
            "Comparable to SVB (Mar 2023) and Signature Bank disclosure failures — both saw "
            "rapid loss of confidence once regulator involvement became public."
        ),
    ),
    AnalysisSchema(
        event_id="evt-002",
        severity_score=7,
        affected_sectors=["Fixed Income", "Real Estate", "Growth Equities", "Banks"],
        risk_summary=(
            "Hawkish FOMC repricing pressures duration-sensitive assets. Long-duration tech "
            "and CRE most exposed; banks see margin tailwinds offset by deposit-cost pressure."
        ),
        recommended_actions=[
            "Shorten portfolio duration; rotate into 1-3 year Treasuries",
            "Reduce growth-equity beta until 2-year yields stabilize",
        ],
        historical_context=(
            "Reminiscent of the 2022 hiking cycle that triggered the regional bank stress "
            "of March 2023 via held-to-maturity bond losses."
        ),
    ),
    AnalysisSchema(
        event_id="evt-003",
        severity_score=6,
        affected_sectors=["Technology", "Semiconductors", "Industrials"],
        risk_summary=(
            "Guidance cut suggests enterprise IT capex is rolling over. Read-through to "
            "memory, EDA, and capital equipment vendors. Consumer-tech less exposed near-term."
        ),
        recommended_actions=[
            "Trim semi-cap and memory exposure ahead of next earnings cycle",
            "Watch hyperscaler guidance for confirmation of broader capex pause",
        ],
        historical_context=(
            "Pattern resembles the 2019 semis downcycle: single-vendor guidance cuts preceded "
            "a 9-month sector drawdown of ~25%."
        ),
    ),
    AnalysisSchema(
        event_id="evt-004",
        severity_score=5,
        affected_sectors=["Technology", "AI/Software", "Media"],
        risk_summary=(
            "Compliance overhead is material but not existential. Larger players absorb costs "
            "more easily; smaller foundation-model startups face structurally higher bar to EU markets."
        ),
        recommended_actions=[
            "Map portfolio companies' EU revenue exposure and compliance readiness within 30 days",
            "Increase conviction in incumbents with existing trust/safety infrastructure",
        ],
        historical_context=(
            "Parallels GDPR rollout (2018) — short-term volatility, long-term advantage to "
            "well-capitalized incumbents who could absorb compliance costs."
        ),
    ),
    AnalysisSchema(
        event_id="evt-005",
        severity_score=7,
        affected_sectors=["Energy", "Transportation", "Insurance", "Airlines"],
        risk_summary=(
            "Tail risk of a sustained Hormuz disruption is low-probability / high-impact. "
            "Energy beneficiaries near-term; transports and airlines see margin compression."
        ),
        recommended_actions=[
            "Add tactical long energy / short transports overlay sized at 2-3% NAV",
            "Increase hedge on jet-fuel-sensitive airline holdings",
        ],
        historical_context=(
            "2019 Abqaiq attack drove a 15% Brent spike in 24 hours; today's market is more "
            "supply-constrained, so an actual disruption would have a larger price impact."
        ),
    ),
    AnalysisSchema(
        event_id="evt-006",
        severity_score=4,
        affected_sectors=["Consumer Discretionary", "Retail", "Real Estate (Retail)"],
        risk_summary=(
            "Idiosyncratic restructuring rather than a sector-wide signal, but consistent "
            "with weakening discretionary spending. Watch other Q4 retailer guides."
        ),
        recommended_actions=[
            "Track same-store-sales reads and credit-card delinquency data for sector confirmation",
        ],
        historical_context=(
            "Similar in scope to JCPenney and Macy's restructurings (2020-2022) — sector "
            "rerated downward but contagion to consumer staples was limited."
        ),
    ),
    AnalysisSchema(
        event_id="evt-007",
        severity_score=4,
        affected_sectors=["Financials", "Investment Banks", "Leveraged Finance"],
        risk_summary=(
            "Single-name credit event, but signals broader stress in LBO underwriting and "
            "wholesale-funded mid-tier banks. Watch CDS spreads on peers."
        ),
        recommended_actions=[
            "Monitor BBB- to BB credit spread widening as a leading indicator",
        ],
        historical_context=(
            "Echoes 2007-08 sequence where Bear Stearns funding stress preceded broader "
            "systemic events by 9-12 months."
        ),
    ),
]


MOCK_BRIEFING: str = """## Executive Summary

Today's risk landscape is **elevated**. An SEC fraud probe into a regional bank (severity 9)
layers on top of a hawkish Fed repricing and renewed Strait-of-Hormuz tensions. Cross-asset
signals point to fragility in **financials** and **energy**, with secondary read-through to
**technology** via duration and capex.

## Critical Alerts

### [CRITICAL 9] SEC fraud probe — regional bank loan-loss disclosures
Formal SEC investigation into a US regional bank's reserve methodology. Comparable historical
setups (SVB, Signature) saw confidence erode in days once regulator involvement was public.
- **Sectors** — Financials · Regional Banks · Commercial Real Estate
- **Action** — hedge regional bank ETF exposure; stress-test CRE counterparties at −30% markdown

### [CRITICAL 7] Fed minutes — additional 50 bps signaled
Hawkish repricing pressures duration-sensitive assets. CRE and long-duration tech most exposed.
- **Sectors** — Fixed Income · Real Estate · Growth Equities · Banks
- **Action** — shorten duration; rotate to 1–3y Treasuries; reduce growth-equity beta

### [CRITICAL 7] Strait of Hormuz — Brent +6% on supply fears
Tail-risk event with asymmetric impact. ~20% of global oil flow through the chokepoint.
- **Sectors** — Energy · Transportation · Insurance · Airlines
- **Action** — tactical energy-long / transports-short overlay (2–3% NAV); hedge airline jet-fuel

## Watch List

- **[WARNING 6]** Mega-cap chipmaker cuts FY guidance 18% — enterprise IT capex rolling over; semi-cap and memory exposed.
- **[WARNING 5]** EU AI Act final provisions — compliance overhead favors incumbents; map EU revenue exposure within 30 days.
- **[WARNING 4]** Major retailer 4,500 corporate layoffs — idiosyncratic restructuring, consistent with weakening discretionary spend.
- **[WARNING 4]** Boutique investment bank downgraded to BBB− — single-name credit event; watch BBB→BB spread widening.

## Sector Exposure Heat Map

| Sector | Risk | Driver |
|---|---|---|
| Financials / Regional Banks | **HIGH** | SEC fraud probe · Fed repricing · CRE exposure |
| Energy | **HIGH** | Hormuz supply-disruption tail risk |
| Commercial Real Estate | **HIGH** | Loan-loss reserves under regulator scrutiny |
| Technology / Semis | MEDIUM | Capex pause · duration sensitivity |
| Consumer Discretionary | MEDIUM | Restructuring signals · softer demand |
| Insurance / Transports | MEDIUM | War-risk premiums · fuel-cost pressure |
| Healthcare | LOW | No material catalysts today |
| Utilities | LOW | Defensive · benefits from energy overlay |

## Recommended Actions

1. **Today** — hedge regional bank ETF exposure; tighten CRE counterparty risk limits.
2. **This week** — shorten portfolio duration; reduce long-duration tech beta.
3. **This week** — initiate tactical energy-long / transports-short overlay (2–3% NAV).
4. **Next 30 days** — map EU revenue exposure for AI/software holdings; assess compliance readiness.
5. **Ongoing** — monitor regional-bank deposit flows, FHLB advance utilization, BBB→BB credit spreads.
"""


class MockChat:
    """Stand-in for briefer.chat.RiskChat used while agents are mock-only."""

    def __init__(self, briefing: str = MOCK_BRIEFING):
        self.briefing = briefing
        self.history: list[tuple[str, str]] = []

    def chat(self, user_question: str) -> str:
        q = user_question.lower()
        if any(k in q for k in ["sector", "worried", "exposure", "highest"]):
            answer = (
                "**Financials — specifically regional banks and CRE-exposed lenders.** "
                "The SEC fraud probe (severity 9) on loan-loss disclosures is the dominant "
                "driver. Add the hawkish Fed repricing on top, and you have a setup that "
                "structurally resembles the lead-up to the March 2023 regional bank stress."
            )
        elif any(k in q for k in ["2008", "gfc", "compare", "historical", "history", "svb"]):
            answer = (
                "Today's pattern is closer to **early 2023 (SVB / Signature)** than to 2008. "
                "The 2008 GFC was a solvency crisis driven by mortgage credit losses that had "
                "been building for years. What we're seeing now is a confidence/disclosure "
                "shock at a single regional bank against a backdrop of duration stress — the "
                "same mechanism that took down SVB. Severity is high but the systemic "
                "transmission channel is narrower."
            )
        elif any(k in q for k in ["energy", "oil", "brent", "hormuz"]):
            answer = (
                "Energy is one of the two highest-conviction risk vectors today. Brent +6% "
                "intraday reflects insurance-premium widening rather than an actual outage. "
                "If Hormuz traffic is materially disrupted, expect a $15-25 spike in Brent "
                "given today's tighter supply backdrop versus 2019."
            )
        elif any(k in q for k in ["action", "do", "recommend", "trade"]):
            answer = (
                "Three actions for today: (1) hedge regional bank ETF exposure (KRE/KBWR), "
                "(2) shorten portfolio duration toward 1-3y Treasuries, (3) initiate a small "
                "(2-3% NAV) tactical energy-long / transports-short overlay. The first is "
                "defensive against the highest-severity event; the other two play the "
                "secondary themes."
            )
        elif any(k in q for k in ["tech", "ai", "semi", "chip"]):
            answer = (
                "Two distinct pressures on tech today: (a) the chipmaker guidance cut "
                "(severity 6) signals enterprise-IT capex is rolling over, with read-through "
                "to memory, EDA, and capital equipment, and (b) the EU AI Act (severity 5) "
                "creates a compliance moat that favors incumbents with existing trust/safety "
                "infrastructure. Net: trim semi-cap exposure, hold mega-cap AI incumbents."
            )
        else:
            answer = (
                "Based on today's briefing, the dominant risk vector is the SEC probe into "
                "regional bank loan-loss disclosures (severity 9). Combined with the hawkish "
                "Fed repricing and Hormuz tensions, this is an above-average risk day with "
                "concentration in financials and energy."
            )
        self.history.append((user_question, answer))
        return answer

    def reset(self) -> None:
        self.history.clear()


def get_mock_payload():
    """Return a payload shaped like `pipeline.run_pipeline()` returns."""
    return MOCK_EVENTS, MOCK_ANALYSES, MOCK_BRIEFING, MockChat()
