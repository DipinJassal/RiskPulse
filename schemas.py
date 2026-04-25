from pydantic import BaseModel
from typing import List


class EventSchema(BaseModel):
    event_id: str
    headline: str
    source: str
    category: str
    timestamp: str
    raw_text: str
    relevance_score: float


class AnalysisSchema(BaseModel):
    event_id: str
    severity_score: int  # 1-10
    affected_sectors: List[str]
    risk_summary: str
    recommended_actions: List[str]
    historical_context: str
