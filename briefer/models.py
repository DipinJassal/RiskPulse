from pydantic import BaseModel

try:
    from schemas import AnalysisSchema as AnalysisSchema  # type: ignore
except Exception:
    class AnalysisSchema(BaseModel):
        event_id: str
        severity_score: int
        affected_sectors: list[str]
        risk_summary: str
        recommended_actions: list[str]
        historical_context: str
