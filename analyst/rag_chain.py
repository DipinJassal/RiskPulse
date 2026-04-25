from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

try:
    # Newer LangChain split packages.
    from langchain_core.documents import Document
except Exception:  # pragma: no cover
    from langchain.schema import Document  # type: ignore

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore

from analyst.schemas import AnalysisSchema, EventSchema


def _extract_first_json_object(text: str) -> str:
    """
    Claude sometimes wraps JSON with commentary. This extracts the first {...} block.
    """
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
    """
    Loads analyst/knowledge_base/*.txt, splits into overlapping chunks, embeds into a
    Chroma collection named 'risk_knowledge', and uses Claude to generate an
    AnalysisSchema for a given event.
    """

    def __init__(
        self,
        knowledge_base_dir: str | Path = Path(__file__).parent / "knowledge_base",
        persist_directory: str | Path = Path(__file__).parent / ".chroma",
        collection_name: str = "risk_knowledge",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: Optional[object] = None,
        claude_model: str = "claude-3-5-sonnet-latest",
    ) -> None:
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.claude_model = claude_model

        txt_files = sorted(self.knowledge_base_dir.glob("*.txt"))
        if not txt_files:
            raise FileNotFoundError(
                f"No .txt files found under {self.knowledge_base_dir}. "
                "Add knowledge-base documents to proceed."
            )

        raw_docs: List[Document] = []
        for p in txt_files:
            raw_docs.append(
                Document(
                    page_content=p.read_text(encoding="utf-8"),
                    metadata={"source": p.name},
                )
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(raw_docs)

        self._vectorstore = self._build_vectorstore(
            chunks=chunks, embedding_model=embedding_model
        )

    def _default_embeddings(self):
        """
        Prefer local HuggingFace embeddings (no API key required). If that import
        isn't available, fall back to OpenAI embeddings if OPENAI_API_KEY is set.
        """
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            pass

        if os.getenv("OPENAI_API_KEY"):
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings()

        raise ImportError(
            "No embedding backend available. Install `langchain-community` (for "
            "HuggingFaceEmbeddings) or set OPENAI_API_KEY and install `langchain-openai`."
        )

    def _build_vectorstore(self, chunks: Sequence[Document], embedding_model: Optional[object] = None):
        # Import here to avoid hard dependency errors at import time.
        from langchain_chroma import Chroma

        embeddings = embedding_model or self._default_embeddings()

        # Rebuild collection each time to keep behavior deterministic for small KBs.
        # Chroma will create/overwrite within the same persist_directory/collection.
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        vs = Chroma(
            collection_name=self.collection_name,
            persist_directory=str(self.persist_directory),
            embedding_function=embeddings,
        )

        # Clear then add (best-effort across Chroma versions).
        try:
            # Newer langchain-chroma exposes delete_collection().
            if hasattr(vs, "delete_collection"):
                vs.delete_collection()
                vs = Chroma(
                    collection_name=self.collection_name,
                    persist_directory=str(self.persist_directory),
                    embedding_function=embeddings,
                )
            elif hasattr(vs, "_collection"):
                vs._collection.delete(where={})  # type: ignore[attr-defined]
        except Exception:
            pass

        vs.add_documents(list(chunks))
        return vs

    def _retrieve(self, query: str, k: int = 3) -> List[RetrievedChunk]:
        docs = self._vectorstore.similarity_search(query, k=k)
        out: List[RetrievedChunk] = []
        for d in docs:
            out.append(
                RetrievedChunk(
                    content=d.page_content,
                    source=str(d.metadata.get("source", "unknown")),
                )
            )
        return out

    def _call_claude(self, prompt: str) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY is not set.")

        try:
            import anthropic
        except Exception as e:
            raise ImportError(
                "Missing `anthropic` package. Install it to call Claude."
            ) from e

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=self.claude_model,
            max_tokens=600,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        # anthropic SDK returns a list of content blocks; join text blocks.
        parts: List[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()

    def analyze_event(self, event: EventSchema) -> AnalysisSchema:
        query = f"{event.headline}\n\n{event.raw_text}".strip()
        retrieved = self._retrieve(query=query, k=3)

        context_lines: List[str] = []
        for i, c in enumerate(retrieved, start=1):
            context_lines.append(f"[{i}] source={c.source}\n{c.content}")
        context = "\n\n---\n\n".join(context_lines)

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
            "- Respond with ONLY valid JSON matching AnalysisSchema.\n"
            "- `affected_sectors`: use common sector names (e.g., Financials, Technology, Real Estate, Energy).\n"
            "- `recommended_actions`: 2-3 specific, actionable steps (e.g., tighten limits on X, hedge Y, monitor indicator Z).\n"
            "- `historical_context`: reference at least one comparable real event from the retrieved context and cite it as [1], [2], or [3].\n\n"
            "EVENT:\n"
            f"headline: {event.headline}\n"
            f"raw_text: {event.raw_text}\n\n"
            "RETRIEVED CONTEXT:\n"
            f"{context}\n"
        )

        raw = self._call_claude(prompt=prompt)
        json_text = _extract_first_json_object(raw)
        data = json.loads(json_text)
        return AnalysisSchema.model_validate(data)

