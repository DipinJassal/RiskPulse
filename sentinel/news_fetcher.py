import time
from datetime import datetime, timezone
from config import NEWS_API_KEY

_MOCK_ARTICLES = [
    {
        "title": "Federal Reserve signals two more rate hikes amid sticky inflation",
        "description": "Fed Chair Powell indicated the central bank is prepared to raise rates further if inflation does not cool, rattling bond markets.",
        "source": "Reuters",
        "url": "https://reuters.com/mock-1",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "SEC opens fraud investigation into regional bank's balance sheet",
        "description": "Regulators are probing alleged misrepresentation of loan quality at a mid-size lender, raising fears of broader contagion.",
        "source": "Wall Street Journal",
        "url": "https://wsj.com/mock-2",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "Major tech firm reports 28% earnings miss, warns of further declines",
        "description": "Declining ad revenue and rising operating costs drove the miss; management cut full-year guidance by 15%.",
        "source": "Bloomberg",
        "url": "https://bloomberg.com/mock-3",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "China imposes new tariffs on US semiconductor exports",
        "description": "Beijing's retaliatory tariffs target chip manufacturers, escalating trade tensions and threatening global supply chains.",
        "source": "Financial Times",
        "url": "https://ft.com/mock-4",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "Retail giant files for Chapter 11 bankruptcy protection",
        "description": "Rising debt costs and falling consumer spending pushed the company into insolvency, affecting 40,000 employees.",
        "source": "CNBC",
        "url": "https://cnbc.com/mock-5",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "Energy sector layoffs surge as oil prices drop below $70",
        "description": "Several major producers announced workforce reductions totalling 12,000 jobs as crude prices hit an 18-month low.",
        "source": "Reuters",
        "url": "https://reuters.com/mock-6",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "title": "EU regulators propose sweeping new fintech compliance rules",
        "description": "Draft regulations would require real-time capital reporting for digital lenders, significantly raising compliance costs.",
        "source": "Bloomberg",
        "url": "https://bloomberg.com/mock-7",
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    },
]


class NewsCollector:
    def __init__(self):
        if NEWS_API_KEY:
            try:
                from newsapi import NewsApiClient
                self.client = NewsApiClient(api_key=NEWS_API_KEY)
                self._use_mock = False
            except Exception:
                self._use_mock = True
        else:
            print("[NewsCollector] No NEWS_API_KEY — using mock articles for demo.")
            self._use_mock = True

    def fetch_top_headlines(self, category="business", country="us", page_size=20) -> list[dict]:
        if self._use_mock:
            return _MOCK_ARTICLES[:4]
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
        if self._use_mock:
            return _MOCK_ARTICLES[4:]
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
