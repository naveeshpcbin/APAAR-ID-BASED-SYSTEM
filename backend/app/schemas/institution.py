from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ProgrammeResponse(BaseModel):
    id: int
    programme_code: str
    programme_name: str
    degree_level: str
    duration_years: int

    class Config:
        from_attributes = True

class ApprovalSnapshotResponse(BaseModel):
    id: int
    programme_id: int
    programme_code: Optional[str] = None
    academic_year: str
    approved_intake: int
    supernumerary_quota: Dict[str, Any] = {}
    approval_letter_ref: str
    policy_version: str
    is_active: bool

    class Config:
        from_attributes = True

class InstitutionResponse(BaseModel):
    id: int
    aicte_id: str
    name: str
    state: str
    district: str
    institution_type: str
    status: str
    contact_email: Optional[str] = None
    programmes: List[ProgrammeResponse] = []

    class Config:
        from_attributes = True
