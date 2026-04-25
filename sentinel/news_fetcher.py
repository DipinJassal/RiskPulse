import time
import requests
from datetime import datetime, timezone, timedelta
from newsapi import NewsApiClient
from config import NEWS_API_KEY

_EDGAR_URL = "https://efts.sec.gov/LATEST/search-index"


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

    def fetch_by_keywords(self, keywords=None, page_size=30) -> list[dict]:
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

    def fetch_sec_edgar(self, forms: str = "8-K,10-K", max_results: int = 20) -> list[dict]:
        """
        Fetches recent SEC EDGAR filings (8-K, 10-K) via the public full-text
        search API. No API key required.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        params = {
            "q": "risk material adverse",
            "dateRange": "custom",
            "startdt": since,
            "forms": forms,
            "_source": "file_date,period_of_report,entity_name,file_num,form_type",
            "hits.hits.total.value": max_results,
        }
        try:
            resp = requests.get(_EDGAR_URL, params=params, timeout=10)
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            articles = []
            for hit in hits[:max_results]:
                src = hit.get("_source", {})
                entity = src.get("entity_name", "Unknown")
                form = src.get("form_type", "Filing")
                date = src.get("file_date", datetime.now(timezone.utc).isoformat())
                articles.append({
                    "title": f"SEC {form} Filing: {entity}",
                    "description": f"{entity} filed a {form} with the SEC on {date}.",
                    "source": "SEC EDGAR",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&filenum={src.get('file_num', '')}",
                    "publishedAt": date,
                })
            print(f"[NewsCollector] SEC EDGAR: {len(articles)} filings fetched.")
            return articles
        except Exception as e:
            print(f"[NewsCollector] SEC EDGAR error: {e}")
            return []

    def _normalize(self, raw: list) -> list[dict]:
        return [self._normalize_one(a) for a in raw]

    def _normalize_one(self, a: dict) -> dict:
        return {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "source": (a.get("source") or {}).get("name", "") if isinstance(a.get("source"), dict) else a.get("source", ""),
            "url": a.get("url", ""),
            "publishedAt": a.get("publishedAt", ""),
        }
