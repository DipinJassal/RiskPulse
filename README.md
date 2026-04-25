![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit) ![LangChain](https://img.shields.io/badge/LangChain-0.3+-green?logo=chainlink) ![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o-412991?logo=openai) ![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-orange)

# RiskPulse

**Real-time financial news risk intelligence — automated from raw headlines to a structured morning briefing in under 60 seconds.**

RiskPulse is a multi-agent AI system that monitors financial news, reasons about risk exposure using a RAG knowledge base, and generates actionable briefings with an interactive follow-up chat interface.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     pipeline.py (Orchestrator)              │
│                  Sequential multi-agent runner              │
└────────────┬───────────────────┬───────────────────┬────────┘
             │                   │                   │
             ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Sentinel Agent  │ │  Analyst Agent  │ │  Briefer Agent  │
    │  Data Gatherer  │ │ Reasoning Engine│ │Report Generator │
    │                 │ │                 │ │                 │
    │ • NewsAPI fetch │ │ • RAG retrieval │ │ • Structured    │
    │ • LLM classify  │ │ • Severity score│ │   briefing      │
    │ • ChromaDB store│ │ • Sector mapping│ │ • Chat Q&A      │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────────────┐
    │                      ChromaDB                           │
    │         risk_events collection  |  risk_knowledge       │
    └─────────────────────────────────────────────────────────┘
             │                                       │
             ▼                                       ▼
    ┌─────────────────────────────────────────────────────────┐
    │                  Streamlit Frontend                     │
    │    Live Event Feed  |  Risk Briefing  |  Chat Tab      │
    └─────────────────────────────────────────────────────────┘
```

---

## Agentic Capabilities

| Capability | How RiskPulse Delivers |
|---|---|
| **Autonomy** | Pipeline runs end-to-end from news fetch to briefing without human input |
| **Tool Use** | NewsAPI, ChromaDB, OpenAI gpt-4o, yfinance, json-repair |
| **Planning & Reasoning** | Analyst chains RAG retrieval → risk assessment → severity scoring (1-10) grounded in PD/LGD/EAD frameworks |
| **Memory** | ChromaDB persists all events; RiskChat maintains a 10-turn conversation window across follow-up questions |
| **Multi-Agent Coordination** | Three specialized agents orchestrated sequentially via pipeline.py; each activates, completes, and hands off to the next |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI gpt-4o via `langchain-openai` |
| Agent Framework | Plain-Python sequential pipeline (CrewAI-compatible) |
| Vector DB | ChromaDB (persistent) — dual collections for events + knowledge base |
| Embeddings | ChromaDB default (all-MiniLM-L6-v2) |
| RAG | LangChain `RecursiveCharacterTextSplitter` + ChromaDB retrieval |
| Frontend | Streamlit (wide layout, dark theme, chat interface) |
| News API | NewsAPI.org |
| Data Models | Pydantic v2 (`EventSchema`, `AnalysisSchema`) |

---

## Project Structure

```
riskpulse/
├── sentinel/
│   ├── agent.py          # Orchestrates fetch → classify → store
│   ├── news_fetcher.py   # NewsAPI client with mock fallback
│   ├── classifier.py     # LLM relevance classifier (0.0–1.0 score + category)
│   └── store.py          # ChromaDB event storage + similarity search
├── analyst/
│   ├── agent.py          # Runs RAGAnalyzer over all events, sorts by severity
│   ├── rag_chain.py      # RAG retrieval + gpt-4o risk assessment
│   └── knowledge_base/
│       ├── crises.txt         # GFC, SVB, COVID crash, Credit Suisse, Asian crisis
│       ├── risk_frameworks.txt # PD, LGD, EAD, VaR, stress testing
│       └── sector_mappings.txt # 12 sectors → risk factors + contagion paths
├── briefer/
│   ├── agent.py          # Calls report_gen, initialises RiskChat
│   ├── report_gen.py     # Structured 5-section morning briefing
│   └── chat.py           # Conversational Q&A with sliding message window
├── frontend/
│   ├── app.py            # Streamlit dashboard (sidebar, briefing tab, chat tab)
│   └── components.py     # Risk level indicator, event sidebar rendering
├── pipeline.py           # Sequential orchestrator + CrewAI Option A
├── schemas.py            # EventSchema + AnalysisSchema (Pydantic)
├── config.py             # Loads API keys from .env
└── requirements.txt
```

---

## Setup

**1. Clone and create environment**
```bash
git clone https://github.com/DipinJassal/RiskPulse.git
cd RiskPulse
python3 -m venv venv
source venv/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
pip install langchain-text-splitters json-repair   # required extras
```

**3. Configure API keys**
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-...          # Required — used for all LLM calls
NEWS_API_KEY=...               # Optional — falls back to mock articles if missing
ANTHROPIC_API_KEY=             # Optional — reserved for future Claude integration
```

---

## Usage

**Run the full pipeline (terminal)**
```bash
python pipeline.py
```

**Run individual agents**
```bash
python -m sentinel.agent    # Fetch + classify + store events
python -m analyst.agent     # RAG risk assessment on mock events
python -m briefer.agent     # Generate briefing + test chat
```

**Launch the Streamlit dashboard**
```bash
streamlit run frontend/app.py
```
Then click **Refresh** in the top-right — the pipeline runs live and populates the briefing and chat tabs.

---

## Example Output

```
12:23:07  AGENT 1/3 — Sentinel Agent | Data Gatherer
          7 events collected (macro, fraud, earnings, geopolitical, bankruptcy...)

12:23:18  AGENT 2/3 — Analyst Agent | Reasoning Engine
          7 assessments generated | Top severity: 8/10 (Financials, Banking)

12:23:42  AGENT 3/3 — Briefer Agent | Report Generator
          Morning briefing ready

Pipeline COMPLETE — 47s total
```

**Briefing sections generated:**
- Executive Summary
- Critical Alerts (severity ≥ 7)
- Watch List (severity 4–6)
- Sector Exposure Heat Map (HIGH / MEDIUM / LOW)
- Recommended Actions

---

## Team FourSight

Built at the **SJSU Applied Data Science Hackathon 2026**

| Member | Role |
|---|---|
| Member 1 | Sentinel Agent — data pipeline, news fetching, LLM classification |
| Member 2 | Analyst Agent — RAG chain, knowledge base, severity scoring |
| Member 3 | Briefer Agent — report generation, conversational chat |
| Nikhil Khaneja | Pipeline Orchestration, CI/CD, integration & deployment |
