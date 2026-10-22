from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from pydantic import BaseModel

class IdentityVerificationResult(BaseModel):
    is_valid_format: bool
    is_verified: bool
    status_code: str  # "VERIFIED", "FORMAT_INVALID", "IDENTITY_MISMATCH", "NOT_FOUND", "PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"
    provider_name: str
    provider_reference: Optional[str] = None
    message: str
    response_time_ms: float

class IdentityProviderInterface(ABC):
    @abstractmethod
    def verify_identity(
        self,
        apaar_id: str,
        student_name: str,
        dob: Optional[date] = None,
        gender: Optional[str] = None
    ) -> IdentityVerificationResult:
        """
        Validates the APAAR academic identifier against upstream authority.
        """
        pass
