from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

logger = logging.getLogger(__name__)

try:
    from langchain_core.documents import Document
except Exception:
    from langchain.schema import Document  # type: ignore

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore

from schemas import AnalysisSchema, EventSchema


def _extract_first_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Model response did not contain a JSON object.")
    return match.group(0)


@dataclass(frozen=True)
class RetrievedChunk:
    content: str
    source: str


class RAGAnalyzer:
    def __init__(
        self,
        knowledge_base_dir: str | Path = Path(__file__).parent / "knowledge_base",
        persist_directory: str | Path = Path(__file__).parent / ".chroma",
        collection_name: str = "risk_knowledge",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: Optional[object] = None,
    ) -> None:
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name

        txt_files = sorted(self.knowledge_base_dir.glob("*.txt"))
        if not txt_files:
            raise FileNotFoundError(
                f"No .txt files found under {self.knowledge_base_dir}."
            )

        raw_docs: List[Document] = []
        for p in txt_files:
            raw_docs.append(
                Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name})
            )

        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(raw_docs)
        logger.info("Loaded %d KB chunks from %d knowledge-base files", len(chunks), len(txt_files))
        self._vectorstore = self._build_vectorstore(chunks=chunks, embedding_model=embedding_model)

    def _default_embeddings(self):
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            pass

        if os.getenv("OPENAI_API_KEY"):
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings()

        raise ImportError("No embedding backend available.")

    def _build_vectorstore(self, chunks: Sequence[Document], embedding_model: Optional[object] = None):
        from langchain_chroma import Chroma

        embeddings = embedding_model or self._default_embeddings()
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        vs = Chroma(
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory),
            embedding_function=embeddings,
        )

        try:
            if hasattr(vs, "delete_collection"):
                vs.delete_collection()
                vs = Chroma(
                    collection_name=self.collection_name,
                    persist_directory=str(self.persist_directory),
                    embedding_function=embeddings,
                )
            elif hasattr(vs, "_collection"):
                vs._collection.delete(where={})
        except Exception:
            pass

        vs.add_documents(list(chunks))
        return vs

    def _retrieve(self, query: str, k: int = 4) -> List[RetrievedChunk]:
        """Retrieve top-k chunks; use MMR if available for diversity."""
        try:
            docs = self._vectorstore.max_marginal_relevance_search(query, k=k, fetch_k=k * 3)
        except Exception:
            docs = self._vectorstore.similarity_search(query, k=k)
        return [
            RetrievedChunk(content=d.page_content, source=str(d.metadata.get("source", "unknown")))
            for d in docs
        ]

    def _call_llm(self, prompt: str) -> str:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from config import OPENAI_API_KEY, MODEL_NAME

        llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=OPENAI_API_KEY, max_tokens=600)
        response = llm.invoke([
            SystemMessage(content="You are a senior risk analyst. Respond with valid JSON only."),
            HumanMessage(content=prompt),
        ])
        return response.content.strip()

    def analyze_event(self, event: EventSchema) -> AnalysisSchema:
        query = f"{event.headline}\n\n{event.raw_text}".strip()
        retrieved = self._retrieve(query=query, k=4)

        context = "\n\n---\n\n".join(
            f"[{i}] source={c.source}\n{c.content}"
            for i, c in enumerate(retrieved, start=1)
        )

        prompt = (
            "You are a senior risk analyst.\n\n"
            "Task: Given this financial news event and retrieved context from our risk knowledge base, "
            "produce a concise risk assessment.\n\n"
            "Severity calibration (1-10):\n"
            "- 1-3: minor/contained (routine earnings miss, small guidance tweak, limited balance-sheet impact)\n"
            "- 4-6: material but manageable (sector-wide pressure, funding costs rising, localized credit losses)\n"
            "- 7-8: severe (bank run dynamics, major counterparty failure risk, sharp liquidity tightening)\n"
            "- 9-10: systemic (broad market plumbing failure, multiple major institutions at risk, crisis-level policy response)\n\n"
            "Output requirements:\n"
            "- Respond with ONLY valid JSON matching this schema: "
            "{event_id, severity_score, affected_sectors, risk_summary, recommended_actions, historical_context}\n"
            "- `affected_sectors`: list of sector names (e.g. Financials, Technology, Energy).\n"
            "- `recommended_actions`: 2-3 specific, actionable steps.\n"
            "- `historical_context`: reference at least one comparable real event from the retrieved context.\n\n"
            "EVENT:\n"
            f"event_id: {event.event_id}\n"
            f"headline: {event.headline}\n"
            f"raw_text: {event.raw_text}\n\n"
            "RETRIEVED CONTEXT:\n"
            f"{context}\n"
        )

        for attempt in range(3):
            try:
                raw = self._call_llm(prompt=prompt)
                json_text = _extract_first_json_object(raw)
                data = json.loads(json_text)
                data["event_id"] = event.event_id
                return AnalysisSchema.model_validate(data)
            except Exception as e:
                wait = 2 ** (attempt + 1)
                logger.warning("Attempt %d failed: %s. Retrying in %ds...", attempt + 1, e, wait)
                time.sleep(wait)

        logger.error("All retries exhausted for event %s — returning fallback.", event.event_id)
        return AnalysisSchema(
            event_id=event.event_id,
            severity_score=5,
            affected_sectors=[],
            risk_summary="Analysis unavailable.",
            recommended_actions=[],
            historical_context="",
        )
