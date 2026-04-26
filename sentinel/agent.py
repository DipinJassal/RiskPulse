import logging
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher

from schemas import EventSchema
from sentinel.news_fetcher import NewsCollector
from sentinel.classifier import classify_relevance
from sentinel.stock_enricher import get_stock_info
from sentinel.store import EventStore
from config import DEMO_MODE, DEMO_MAX_ARTICLES

logger = logging.getLogger(__name__)

RELEVANCE_THRESHOLD = 0.4
_HEADLINE_SIM_THRESHOLD = 0.78


def _headlines_similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > _HEADLINE_SIM_THRESHOLD


def run_sentinel() -> list[EventSchema]:
    logger.info("Starting at %s", datetime.now(timezone.utc).isoformat())
    collector = NewsCollector()
    store = EventStore()

    raw_articles = collector.fetch_top_headlines()
    raw_articles += collector.fetch_by_keywords()
    raw_articles += collector.fetch_sec_edgar()
    logger.info("Fetched %d raw articles across all sources", len(raw_articles))

    if DEMO_MODE:
        raw_articles = raw_articles[:DEMO_MAX_ARTICLES]
        logger.info("DEMO MODE: capped to %d articles", len(raw_articles))

    seen_urls: set[str] = set()
    seen_headlines: list[str] = []
    events: list[EventSchema] = []
    skipped_dup = 0

    for article in raw_articles:
        url = article.get("url", "")
        if url in seen_urls:
            skipped_dup += 1
            continue
        seen_urls.add(url)

        headline = article.get("title", "") or ""
        if any(_headlines_similar(headline, h) for h in seen_headlines):
            logger.debug("Skipping near-duplicate headline: %s", headline[:60])
            skipped_dup += 1
            continue
        seen_headlines.append(headline)

        text = f"{headline} {article.get('description', '') or ''}"
        classification = classify_relevance(text)

        score = float(classification.get("relevance_score", 0.0))
        if score < RELEVANCE_THRESHOLD:
            continue

        category = classification.get("category", "unknown")
        if isinstance(category, list):
            category = category[0] if category else "unknown"

        entities = classification.get("affected_entities", [])
        stock_info = get_stock_info(entities) if entities else {}

        event = EventSchema(
            event_id=str(uuid.uuid4()),
            headline=headline,
            source=article.get("source", "") or "",
            category=category,
            timestamp=article.get("publishedAt", datetime.now(timezone.utc).isoformat()) or datetime.now(timezone.utc).isoformat(),
            raw_text=article.get("description", "") or "",
            relevance_score=score,
            stock_info=stock_info if stock_info else None,
        )
        store.add_event(event)
        events.append(event)

    logger.info(
        "Done. %d relevant events stored (%d duplicates skipped).",
        len(events), skipped_dup,
    )
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    events = run_sentinel()
    for e in events:
        stock = ""
        if e.stock_info:
            parts = [f"{t}: {v['change_pct']:+.1f}%" for t, v in e.stock_info.items()]
            stock = " | " + ", ".join(parts)
        print(f"  [{e.category.upper()}] {e.headline} (score={e.relevance_score:.2f}){stock}")
