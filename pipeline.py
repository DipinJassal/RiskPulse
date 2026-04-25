import logging
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import AnalysisSchema, EventSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RiskPulse.Pipeline")


# ---------------------------------------------------------------------------
# Option A — CrewAI orchestration
# ---------------------------------------------------------------------------

def run_pipeline_crewai() -> tuple[list[EventSchema], list[AnalysisSchema], str, object]:
    """
    Orchestrates the three agents using CrewAI with a sequential process.
    Each agent has a defined role, goal, and backstory that the crew runner
    can introspect and display.  The actual heavy lifting (API calls, ChromaDB)
    still happens inside each module's run_* function; CrewAI coordinates
    the sequencing and surfaces agent metadata for the demo.
    """
    from crewai import Agent, Crew, Process, Task

    logger.info("=== RiskPulse Pipeline (CrewAI Mode) Starting ===")
    logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # -- Agent definitions ---------------------------------------------------
    sentinel_agent = Agent(
        role="Financial News Sentinel",
        goal=(
            "Continuously scan financial news sources, classify each article for "
            "risk relevance using an LLM, and store high-signal events in the "
            "vector database for downstream analysis."
        ),
        backstory=(
            "You are a tireless watchdog embedded at the intersection of global "
            "news feeds and financial markets.  Trained on decades of market-moving "
            "events, you know instantly whether a headline matters — and you never "
            "let a high-severity story slip through unnoticed."
        ),
        verbose=True,
        allow_delegation=False,
    )

    analyst_agent = Agent(
        role="Senior Risk Analyst",
        goal=(
            "Apply RAG-based reasoning over a financial risk knowledge base to "
            "assess each event's severity (1-10), identify affected sectors, and "
            "surface relevant historical parallels."
        ),
        backstory=(
            "You spent fifteen years on the risk desk at a bulge-bracket bank before "
            "moving into AI-assisted analysis.  You think in terms of PD, LGD, EAD, "
            "and VaR, and you always ground your assessments in precedent — the GFC, "
            "SVB, Credit Suisse — so decision-makers understand the playbook."
        ),
        verbose=True,
        allow_delegation=False,
    )

    briefer_agent = Agent(
        role="Risk Intelligence Briefing Writer",
        goal=(
            "Synthesize analyzed risk events into a concise, structured morning "
            "briefing and remain available for follow-up questions via a "
            "conversational chat interface."
        ),
        backstory=(
            "You are the voice that senior executives hear first each morning.  "
            "Your briefings are legendary for their clarity: crisp executive "
            "summaries, colour-coded alerts, and actionable recommendations that "
            "can be read in under two minutes — no jargon, no filler."
        ),
        verbose=True,
        allow_delegation=False,
    )

    # -- Task definitions ----------------------------------------------------
    gather_task = Task(
        description=(
            "Fetch today's financial news from NewsAPI (top headlines + keyword "
            "search), run each article through the LLM relevance classifier, filter "
            "to articles scoring >= 0.4, store them in ChromaDB, and return a list "
            "of EventSchema objects."
        ),
        expected_output="A list of EventSchema objects representing high-relevance financial news events.",
        agent=sentinel_agent,
    )

    analyze_task = Task(
        description=(
            "For each EventSchema from the Sentinel, retrieve the top-3 relevant "
            "chunks from the risk knowledge base, ask Claude to score severity "
            "(1-10), identify affected sectors, summarise the risk, recommend "
            "actions, and cite historical context.  Return a list of AnalysisSchema "
            "objects sorted by severity descending."
        ),
        expected_output="A list of AnalysisSchema objects, sorted by severity_score descending.",
        agent=analyst_agent,
    )

    brief_task = Task(
        description=(
            "Take the AnalysisSchema list and produce a structured morning risk "
            "briefing with: EXECUTIVE SUMMARY, CRITICAL ALERTS, WATCH LIST, SECTOR "
            "EXPOSURE HEAT MAP, and RECOMMENDED ACTIONS.  Initialise a RiskChat "
            "instance loaded with the briefing so the demo can show interactive Q&A."
        ),
        expected_output="A formatted risk briefing string and an initialised RiskChat instance.",
        agent=briefer_agent,
    )

    # -- Crew ----------------------------------------------------------------
    crew = Crew(
        agents=[sentinel_agent, analyst_agent, briefer_agent],
        tasks=[gather_task, analyze_task, brief_task],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("CrewAI crew assembled — kicking off sequential process...")
    crew.kickoff()

    # CrewAI coordinates agent sequencing; actual data flows through run_* helpers
    logger.info("CrewAI kickoff complete — running data pipeline...")
    return _run_data_pipeline()


# ---------------------------------------------------------------------------
# Option B — Plain-Python orchestration (primary path, fast and explicit)
# ---------------------------------------------------------------------------

def run_pipeline() -> tuple[list[EventSchema], list[AnalysisSchema], str, object]:
    """
    Sequential multi-agent pipeline without a framework dependency.
    Each agent is activated in order; structured logs show the hand-offs so
    the demo clearly illustrates multi-agent coordination.
    """
    import config
    config.validate()

    logger.info("=" * 60)
    logger.info("  RiskPulse Pipeline  —  Multi-Agent Mode")
    logger.info("=" * 60)
    logger.info(f"Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    return _run_data_pipeline()


def _run_data_pipeline() -> tuple[list[EventSchema], list[AnalysisSchema], str, object]:
    """Shared data-flow logic used by both orchestration options."""

    # -- Step 1: Sentinel Agent ----------------------------------------------
    _banner("AGENT 1 / 3  —  Sentinel Agent  |  Data Gatherer")
    t0 = time.perf_counter()

    from sentinel.agent import run_sentinel
    events: list[EventSchema] = run_sentinel()

    elapsed = time.perf_counter() - t0
    logger.info(
        f"[Sentinel] COMPLETE in {elapsed:.1f}s — "
        f"{len(events)} relevant event(s) collected and stored in ChromaDB"
    )
    _log_event_summary(events)

    if not events:
        logger.warning("[Sentinel] No events passed the relevance filter — pipeline will use empty input for downstream agents.")

    # -- Step 2: Analyst Agent -----------------------------------------------
    _banner("AGENT 2 / 3  —  Analyst Agent  |  Reasoning Engine")
    t1 = time.perf_counter()

    from analyst.agent import run_analyst
    analyses: list[AnalysisSchema] = run_analyst(events)

    elapsed = time.perf_counter() - t1
    logger.info(
        f"[Analyst] COMPLETE in {elapsed:.1f}s — "
        f"{len(analyses)} risk assessment(s) generated"
    )
    _log_analysis_summary(analyses)

    # -- Step 3: Briefer Agent -----------------------------------------------
    _banner("AGENT 3 / 3  —  Briefer Agent  |  Report Generator")
    t2 = time.perf_counter()

    from briefer.agent import run_briefer
    briefing_text: str
    chat: object
    briefing_text, chat = run_briefer(analyses)

    elapsed = time.perf_counter() - t2
    logger.info(f"[Briefer] COMPLETE in {elapsed:.1f}s — morning briefing ready")

    # -- Pipeline summary ----------------------------------------------------
    logger.info("=" * 60)
    logger.info("  Pipeline COMPLETE")
    logger.info(f"  Finished at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info(f"  Events collected : {len(events)}")
    logger.info(f"  Analyses produced: {len(analyses)}")
    if analyses:
        top = analyses[0]
        logger.info(f"  Top severity     : {top.severity_score}/10  ({', '.join(top.affected_sectors)})")
    logger.info("=" * 60)

    return events, analyses, briefing_text, chat


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def _banner(text: str) -> None:
    logger.info("-" * 60)
    logger.info(f"  {text}")
    logger.info(f"  {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
    logger.info("-" * 60)


def _log_event_summary(events: list[EventSchema]) -> None:
    for e in events[:5]:
        logger.info(
            f"  [{e.category.upper():12s}] score={e.relevance_score:.2f}  {e.headline[:70]}"
        )
    if len(events) > 5:
        logger.info(f"  ... and {len(events) - 5} more event(s)")


def _log_analysis_summary(analyses: list[AnalysisSchema]) -> None:
    for a in analyses[:5]:
        sectors = ", ".join(a.affected_sectors[:3])
        logger.info(
            f"  severity={a.severity_score:2d}/10  sectors=[{sectors}]  {a.risk_summary[:60]}..."
        )
    if len(analyses) > 5:
        logger.info(f"  ... and {len(analyses) - 5} more analysis result(s)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    use_crewai = "--crewai" in sys.argv

    if use_crewai:
        logger.info("Running with CrewAI orchestration (Option A)")
        events, analyses, briefing, chat = run_pipeline_crewai()
    else:
        logger.info("Running with plain-Python orchestration (Option B)")
        events, analyses, briefing, chat = run_pipeline()

    print("\n" + "=" * 70)
    print(briefing)
    print("=" * 70)
