![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-red?logo=streamlit) ![LangChain](https://img.shields.io/badge/LangChain-0.3+-green?logo=chainlink) ![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o-412991?logo=openai) ![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-orange)

# RiskPulse

**Real-time financial news risk intelligence — automated from raw headlines to a structured morning briefing in under 60 seconds.**

RiskPulse is a multi-agent AI system that autonomously monitors financial news, SEC filings, and market data to generate actionable risk intelligence briefings — in under 90 seconds.

Built for the **SJSU Applied Data Science Hackathon 2026** by **Team FourSight**.

---

## Architecture

```
NewsAPI + SEC EDGAR + yfinance
          │
          ▼
┌─────────────────────┐
│   Sentinel Agent    │  Fetches, classifies, and stores news events
│  sentinel/agent.py  │  GPT-4o relevance classifier → ChromaDB
└────────┬────────────┘
         │  list[EventSchema]
         ▼
┌─────────────────────┐
│   Analyst Agent     │  RAG-based risk assessment (parallel, cached)
│  analyst/agent.py   │  Knowledge base → severity scoring (1-10)
└────────┬────────────┘
         │  list[AnalysisSchema]
         ▼
┌─────────────────────┐
│   Briefer Agent     │  Generates structured morning briefing
│  briefer/agent.py   │  + conversational follow-up chat
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Streamlit Dashboard│  Live event feed, risk briefing, chat tab
│  frontend/app.py    │
└─────────────────────┘
```

---

## Agentic Capabilities

| Capability | How RiskPulse Delivers |
|---|---|
| **Autonomy** | Pipeline runs end-to-end without human input |
| **Tool Use** | NewsAPI, SEC EDGAR, yfinance, ChromaDB, GPT-4o |
| **Planning & Reasoning** | Analyst chains RAG retrieval → risk frameworks → severity scoring |
| **Memory** | ChromaDB persists events; 1h result cache; chat history (10-turn window) |
| **Multi-Agent** | 3 specialized agents orchestrated sequentially via pipeline |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o (via `langchain-openai`) |
| Orchestration | Plain-Python pipeline + CrewAI (dual-mode) |
| Vector DB | ChromaDB (persistent, local) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local, no API key) |
| News | NewsAPI (headlines + keyword search) |
| Filings | SEC EDGAR full-text search (public API, no key) |
| Market Data | yfinance (real-time stock prices) |
| Frontend | Streamlit |
| Schemas | Pydantic v2 |

---

## Project Structure

```
riskpulse/
├── sentinel/
│   ├── agent.py          # Orchestrates fetch → classify → store → enrich
│   ├── news_fetcher.py   # NewsAPI + SEC EDGAR client
│   ├── classifier.py     # GPT-4o relevance + category classifier
│   ├── stock_enricher.py # yfinance ticker lookup + price change %
│   └── store.py          # ChromaDB persistent event store
│
├── analyst/
│   ├── agent.py          # Parallel analysis (5 workers) with cache
│   ├── rag_chain.py      # RAGAnalyzer: retrieval + GPT-4o scoring
│   ├── cache.py          # md5-keyed 1h result cache
│   ├── run_standalone.py # Sanity-check runner (bank fraud > earnings miss)
│   └── knowledge_base/
│       ├── crises.txt         # GFC, COVID, SVB, Credit Suisse, Asian crisis
│       ├── risk_frameworks.txt # PD, LGD, EAD, VaR, stress testing
│       └── sector_mappings.txt # 12 sectors: risk factors + contagion paths
│
├── briefer/
│   ├── agent.py          # run_briefer() + ask_followup()
│   ├── report_gen.py     # GPT-4o briefing writer + fallback generator
│   └── chat.py           # Conversational Q&A with 10-turn history
│
├── frontend/
│   ├── app.py            # Streamlit dashboard (briefing + chat tabs)
│   └── components.py     # Severity badges + sidebar event renderer
│
├── pipeline.py           # Dual-mode orchestrator (CrewAI / plain-Python)
├── schemas.py            # EventSchema + AnalysisSchema (Pydantic)
├── config.py             # Loads API keys from .env
├── requirements.txt
└── .env.example
```

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/DipinJassal/RiskPulse.git
cd RiskPulse
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

**2. Configure API keys**
```bash
cp .env.example .env
```
Edit `.env`:
```
OPENAI_API_KEY=your_openai_key
NEWS_API_KEY=your_newsapi_key      # newsapi.org — free tier: 100 req/day
ANTHROPIC_API_KEY=                 # optional, not required
```

**3. Run**
```bash
# Full dashboard
streamlit run frontend/app.py

# Test agents individually
python -m sentinel.agent    # fetches live news + stock prices
python -m analyst.agent     # RAG risk scoring (uses cache on repeat)
python -m briefer.agent     # generates briefing + demo chat
python pipeline.py          # full pipeline with logs
```

---

## How It Works

### Sentinel Agent
Pulls news from three sources simultaneously:
- **NewsAPI** — top business headlines + 7 financial keyword searches
- **SEC EDGAR** — recent 8-K and 10-K filings (material events)
- **yfinance** — resolves mentioned company names to tickers, fetches live price change %

Each article is sent to GPT-4o for classification: relevance score (0–1), category (regulatory/earnings/macro/credit/geopolitical/market/bankruptcy/fraud), and affected entities. Articles scoring below 0.4 are dropped. Events are stored in ChromaDB.

### Analyst Agent
Runs 5 parallel GPT-4o calls (ThreadPoolExecutor) with a 1-hour md5 result cache so repeated runs are near-instant. For each event:
1. Retrieves top-3 relevant chunks from the knowledge base (HuggingFace embeddings)
2. Sends event + context to GPT-4o with severity calibration anchored to real crises
3. Returns `AnalysisSchema` with severity score, affected sectors, recommended actions, and historical context

### Briefer Agent
Synthesizes all analyses into a structured morning briefing with 5 sections: Executive Summary, Critical Alerts (≥7), Watch List (4–6), Sector Heat Map, and Recommended Actions. Falls back to a template-generated briefing if the LLM call fails — the demo never crashes. A conversational `RiskChat` interface handles follow-up questions with 10-turn memory.

### Pipeline
Two orchestration modes in `pipeline.py`:
- **Option A (CrewAI)** — `run_pipeline_crewai()`: full CrewAI Agent/Task/Crew setup with role definitions and backstories visible during the demo
- **Option B (plain-Python)** — `run_pipeline()`: sequential with agent banners, timing logs, and event summaries — used by the Streamlit dashboard

---

## Team

**Team FourSight** — SJSU Applied Data Science Hackathon 2026

| Member | Role |
|---|---|
| Member 1 | Sentinel Agent — data pipeline, yfinance, SEC EDGAR |
| Member 2 | Analyst Agent — RAG chain, knowledge base |
| Member 3 | Briefer Agent — report generation, chat |
| Member 4 | Frontend + Pipeline integration |
