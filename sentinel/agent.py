import uuid
from datetime import datetime, timezone

from schemas import EventSchema
from sentinel.news_fetcher import NewsCollector
from sentinel.classifier import classify_relevance
from sentinel.store import EventStore

RELEVANCE_THRESHOLD = 0.4


def run_sentinel() -> list[EventSchema]:
    print(f"[Sentinel] Starting at {datetime.now(timezone.utc).isoformat()}")
    collector = NewsCollector()
    store = EventStore()

    raw_articles = collector.fetch_top_headlines()
    raw_articles += collector.fetch_by_keywords()

    seen_urls: set[str] = set()
    events: list[EventSchema] = []

    for article in raw_articles:
        url = article.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        text = f"{article.get('title', '')} {article.get('description', '')}"
        classification = classify_relevance(text)

        score = float(classification.get("relevance_score", 0.0))
        if score < RELEVANCE_THRESHOLD:
            continue

        event = EventSchema(
            event_id=str(uuid.uuid4()),
            headline=article.get("title", "") or "",
            source=article.get("source", "") or "",
            category=classification.get("category", "unknown"),
            timestamp=article.get("publishedAt", datetime.now(timezone.utc).isoformat()) or datetime.now(timezone.utc).isoformat(),
            raw_text=article.get("description", "") or "",
            relevance_score=score,
        )
        store.add_event(event)
        events.append(event)

    print(f"[Sentinel] Done. {len(events)} relevant events stored.")
    return events


if __name__ == "__main__":
    events = run_sentinel()
    for e in events:
        print(f"  [{e.category.upper()}] {e.headline} (score={e.relevance_score:.2f})")
