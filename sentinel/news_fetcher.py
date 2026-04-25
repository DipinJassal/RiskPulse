import time
from newsapi import NewsApiClient
from config import NEWS_API_KEY


class NewsCollector:
    def __init__(self):
        self.client = NewsApiClient(api_key=NEWS_API_KEY)

    def fetch_top_headlines(self, category="business", country="us", page_size=20) -> list[dict]:
        try:
            response = self.client.get_top_headlines(
                category=category, country=country, page_size=page_size
            )
            return self._normalize(response.get("articles", []))
        except Exception as e:
            print(f"[NewsCollector] fetch_top_headlines error: {e}")
            return []

    def fetch_by_keywords(
        self,
        keywords=None,
        page_size=30,
    ) -> list[dict]:
        if keywords is None:
            keywords = [
                "federal reserve", "SEC", "earnings", "bankruptcy",
                "layoffs", "tariff", "regulation",
            ]
        seen_urls: set[str] = set()
        articles: list[dict] = []
        for kw in keywords:
            try:
                response = self.client.get_everything(q=kw, page_size=page_size, language="en")
                for article in response.get("articles", []):
                    url = article.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        articles.append(self._normalize_one(article))
                time.sleep(1)
            except Exception as e:
                print(f"[NewsCollector] fetch_by_keywords '{kw}' error: {e}")
        return articles

    def _normalize(self, raw: list) -> list[dict]:
        return [self._normalize_one(a) for a in raw]

    def _normalize_one(self, a: dict) -> dict:
        return {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "source": (a.get("source") or {}).get("name", ""),
            "url": a.get("url", ""),
            "publishedAt": a.get("publishedAt", ""),
        }
