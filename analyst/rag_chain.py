import json
import os
from pathlib import Path

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config import ANTHROPIC_API_KEY, MODEL_NAME
from schemas import AnalysisSchema, EventSchema

_SYSTEM_PROMPT = (
    "You are a senior risk analyst. Given this financial news event and relevant context "
    "from our risk knowledge base, provide: severity_score (1-10), affected_sectors (list), "
    "risk_summary (2-3 sentences), recommended_actions (list of 2-3 actions), "
    "historical_context (reference to similar past events). "
    "Respond in JSON matching the AnalysisSchema."
)

KB_DIR = Path(__file__).parent / "knowledge_base"


class RAGAnalyzer:
    def __init__(self):
        self.llm = ChatAnthropic(model=MODEL_NAME, anthropic_api_key=ANTHROPIC_API_KEY, max_tokens=1024)
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.kb_collection = self.chroma.get_or_create_collection("risk_knowledge")
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if self.kb_collection.count() > 0:
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunk_id = 0
        for txt_file in KB_DIR.glob("*.txt"):
            content = txt_file.read_text(encoding="utf-8")
            chunks = splitter.split_text(content)
            for chunk in chunks:
                self.kb_collection.add(
                    ids=[f"kb_{txt_file.stem}_{chunk_id}"],
                    documents=[chunk],
                    metadatas=[{"source": txt_file.name}],
                )
                chunk_id += 1
        print(f"[RAGAnalyzer] Loaded {chunk_id} chunks from knowledge base.")

    def analyze_event(self, event: EventSchema) -> AnalysisSchema:
        query = f"{event.headline} {event.raw_text}"
        results = self.kb_collection.query(query_texts=[query], n_results=3)
        context_chunks = results.get("documents", [[]])[0]
        context = "\n\n".join(context_chunks)

        prompt = (
            f"EVENT:\nHeadline: {event.headline}\nCategory: {event.category}\n"
            f"Source: {event.source}\nText: {event.raw_text}\n\n"
            f"RELEVANT KNOWLEDGE BASE CONTEXT:\n{context}"
        )

        for attempt in range(3):
            try:
                response = self.llm.invoke(
                    [SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)]
                )
                raw = response.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
                return AnalysisSchema(
                    event_id=event.event_id,
                    severity_score=int(data.get("severity_score", 5)),
                    affected_sectors=data.get("affected_sectors", []),
                    risk_summary=data.get("risk_summary", ""),
                    recommended_actions=data.get("recommended_actions", []),
                    historical_context=data.get("historical_context", ""),
                )
            except Exception as e:
                import time
                wait = 2 ** (attempt + 1)
                print(f"[RAGAnalyzer] attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)

        return AnalysisSchema(
            event_id=event.event_id,
            severity_score=5,
            affected_sectors=[],
            risk_summary="Analysis unavailable.",
            recommended_actions=[],
            historical_context="",
        )
