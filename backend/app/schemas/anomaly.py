from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class AnomalyCaseResponse(BaseModel):
    id: int
    case_number: str
    institution_id: int
    institution_name: Optional[str] = None
    academic_year: str
    risk_score: float
    anomaly_type: str
    signals_json: Dict[str, Any] = {}
    explanation: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AnomalyReviewRequest(BaseModel):
    status: str  # INSPECTED_CLEARED, ESCALATED_AUDIT
    review_notes: str
