from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ReceiptIssueRequest(BaseModel):
    admission_id: int
    expiry_days: int = 30
    claim_scope: str = "ACTIVE_ENROLMENT_STATUS"

class ReceiptIssueResponse(BaseModel):
    receipt_token: str
    verification_url: str
    qr_code_base64: str
    ed25519_public_key: str
    payload_digest: str
    signature: str
    canonical_payload: Dict[str, Any]
    expires_at: str

class ReceiptVerificationResponse(BaseModel):
    is_valid: bool
    status: str
    message: str
    canonical_payload: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None
    payload_digest: Optional[str] = None
    public_key: Optional[str] = None
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None

class ReceiptRevokeRequest(BaseModel):
    receipt_token: str
    reason: str

class ConsentGrantRequest(BaseModel):
    student_id: int
    consent_type: str = "APAAR_IDENTITY_VERIFICATION"
    granted_by: str = "STUDENT"  # STUDENT, PARENT_GUARDIAN
    is_granted: bool = True

class ConsentGrantResponse(BaseModel):
    id: int
    student_id: int
    consent_type: str
    granted_by: str
    is_granted: bool
    grant_timestamp: datetime
    message: str

class ConsentRevokeRequest(BaseModel):
    student_id: int
    reason: Optional[str] = "Student revoked digital consent"
