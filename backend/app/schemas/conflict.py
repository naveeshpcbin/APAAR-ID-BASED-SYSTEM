from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel
from app.schemas.admission import AdmissionRecordResponse, StudentIdentityResponse

class ConflictCaseResponse(BaseModel):
    id: int
    case_number: str
    student_id: int
    student: Optional[StudentIdentityResponse] = None
    record_a_id: int
    record_a: Optional[AdmissionRecordResponse] = None
    record_b_id: int
    record_b: Optional[AdmissionRecordResponse] = None
    conflict_type: str
    status: str
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConflictResolveRequest(BaseModel):
    resolution_status: str  # RESOLVED_VALID, RESOLVED_CANCELLED, ESCALATED
    winning_record_id: Optional[int] = None
    resolution_notes: str
