from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    aicte_id: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    institution_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class InstitutionRegisterRequest(BaseModel):
    # Institutional Identity & AICTE Approval
    aicte_id: str
    name: str
    state: str
    district: str
    institution_type: str = "PRIVATE_UNAIDED"
    contact_email: Optional[str] = None

    # Nodal Officer Credentials
    nodal_name: str
    nodal_email: str
    password: str

    # Primary Approved Academic Programme & Sanctioned Capacity
    programme_code: str = "BTECH-CSE"
    programme_name: str = "B.Tech in Computer Science & Engineering"
    degree_level: str = "UG"
    approved_intake: int = 120
    tfw_quota: int = 6
    academic_year: str = "2026-27"
    approval_letter_ref: Optional[str] = None

