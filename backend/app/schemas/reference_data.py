from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date


class InstitutionCreate(BaseModel):
    aicte_id: str
    name: str
    state: str
    district: str
    institution_type: str = "STATE_GOVT_AIDED"
    status: str = "APPROVED"
    contact_email: Optional[str] = None


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    institution_type: Optional[str] = None
    status: Optional[str] = None
    contact_email: Optional[str] = None


class ProgrammeCreate(BaseModel):
    institution_id: int
    programme_code: str
    programme_name: str
    degree_level: str = "UG"
    duration_years: int = 4


class ProgrammeUpdate(BaseModel):
    programme_code: Optional[str] = None
    programme_name: Optional[str] = None
    degree_level: Optional[str] = None
    duration_years: Optional[int] = None


class ApprovalUpdate(BaseModel):
    approved_intake: int = Field(..., ge=0, description="Approved intake must be non-negative integer")
    supernumerary_quota: Optional[Dict[str, Any]] = None
    approval_letter_ref: Optional[str] = None
    policy_version: Optional[str] = None

    @validator("approved_intake")
    def validate_intake(cls, v):
        if v < 0:
            raise ValueError("Approved intake cannot be negative.")
        return v


class DeclarationUpdate(BaseModel):
    declared_intake: int = Field(..., ge=0, description="Declared intake must be non-negative integer")
    reporting_scope: Optional[str] = None
    declaration_ref: Optional[str] = None

    @validator("declared_intake")
    def validate_declared(cls, v):
        if v < 0:
            raise ValueError("Declared intake cannot be negative.")
        return v


class SyntheticApaarCreate(BaseModel):
    apaar_id: str = Field(..., description="12-digit numeric identifier")
    full_name: str
    dob: Union[date, str] = Field(default_factory=lambda: date(2005, 1, 1))
    gender: str = "MALE"
    status: str = "DEMO_REFERENCE_MATCH"
    notes: Optional[str] = None

    @validator("dob", pre=True)
    def validate_dob(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                return date(2005, 1, 1)
            try:
                # Handle YYYY-MM-DD
                parts = clean.split("-")
                if len(parts) == 3:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                return datetime.strptime(clean, "%Y-%m-%d").date()
            except Exception:
                return date(2005, 1, 1)
        return date(2005, 1, 1)

    @validator("apaar_id")
    def validate_apaar(cls, v):
        clean = str(v).replace(" ", "").replace("-", "").strip()
        if not clean.isdigit() or len(clean) != 12:
            raise ValueError("APAAR ID must be exactly 12 numeric digits.")
        return clean

    @validator("status")
    def validate_status(cls, v):
        allowed = {
            "DEMO_REFERENCE_MATCH",
            "NO_DEMO_REFERENCE_MATCH",
            "PENDING_EXTERNAL_VERIFICATION",
            "PROVIDER_CONFIRMED",
            "PROVIDER_FAILED",
            "MANUAL_REVIEW_REQUIRED"
        }
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class SyntheticApaarUpdate(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            allowed = {
                "DEMO_REFERENCE_MATCH",
                "NO_DEMO_REFERENCE_MATCH",
                "PENDING_EXTERNAL_VERIFICATION",
                "PROVIDER_CONFIRMED",
                "PROVIDER_FAILED",
                "MANUAL_REVIEW_REQUIRED"
            }
            if v not in allowed:
                raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class ReferenceOverviewResponse(BaseModel):
    total_institutions: int
    total_programmes: int
    total_approvals: int
    total_declarations: int
    total_synthetic_apaar: int
    synthetic_apaar_by_status: Dict[str, int]
    policy_versions: List[str]
    last_audit_event: Optional[Dict[str, Any]]
