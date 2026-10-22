from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

class StudentIdentityResponse(BaseModel):
    id: int
    apaar_masked: str
    full_name: str
    dob: date
    gender: str
    verification_status: str
    provider_name: str

    class Config:
        from_attributes = True

class AdmissionRecordResponse(BaseModel):
    id: int
    student_id: int
    institution_id: int
    institution_name: Optional[str] = None
    programme_id: int
    programme_code: Optional[str] = None
    programme_name: Optional[str] = None
    academic_year: str
    enrollment_no: str
    category: str
    admission_quota: str
    nationality_type: str = "DOMESTIC"
    is_supernumerary: bool = False
    admission_date: date
    status: str
    notes: Optional[str] = None
    student: Optional[StudentIdentityResponse] = None

    class Config:
        from_attributes = True

class ManualAdmissionCreate(BaseModel):
    apaar_id: str
    student_name: str
    dob: date
    gender: str = "MALE"
    programme_code: str
    academic_year: str
    enrollment_no: str
    category: str = "OPEN"
    admission_quota: str = "STATE_GOVT"
    nationality_type: str = "DOMESTIC"
    is_supernumerary: bool = False
    admission_date: date = date.today()
