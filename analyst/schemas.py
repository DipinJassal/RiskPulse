from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    headline: str = Field(..., description="Short headline/title for the news event.")
    raw_text: str = Field(..., description="Raw article text / wire copy / extracted content.")
    source: Optional[str] = Field(default=None, description="Optional source identifier (publisher, feed, etc.).")
    timestamp: Optional[str] = Field(default=None, description="Optional event timestamp as ISO string.")


class AnalysisSchema(BaseModel):
    severity_score: int = Field(..., ge=1, le=10, description="Severity from 1 (low) to 10 (systemic).")
    affected_sectors: List[str] = Field(default_factory=list)
    risk_summary: str
    recommended_actions: List[str] = Field(default_factory=list)
    historical_context: str

