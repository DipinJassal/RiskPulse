from datetime import datetime, timedelta
import chromadb
from schemas import EventSchema


class EventStore:
    def __init__(self, persist_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection("risk_events")

    def add_event(self, event: EventSchema) -> None:
        text = f"{event.headline} {event.raw_text}"
        self.collection.add(
            ids=[event.event_id],
            documents=[text],
            metadatas=[
                {
                    "event_id": event.event_id,
                    "headline": event.headline,
                    "source": event.source,
                    "category": event.category,
                    "timestamp": event.timestamp,
                    "relevance_score": event.relevance_score,
                }
            ],
        )

    def search_similar(self, query: str, n: int = 5) -> list[dict]:
        results = self.collection.query(query_texts=[query], n_results=n)
        return results.get("metadatas", [[]])[0]

    def get_recent(self, hours: int = 24) -> list[dict]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        results = self.collection.get(where={"timestamp": {"$gte": cutoff}})
        return results.get("metadatas", [])
