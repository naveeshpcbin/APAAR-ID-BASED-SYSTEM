import re
import time
from datetime import date
from typing import Optional
from app.adapters.identity_interface import IdentityProviderInterface, IdentityVerificationResult

class MockApaarAdapter(IdentityProviderInterface):
    """
    Deterministic Synthetic APAAR Provider for testing & SIH evaluation.
    Clearly simulates official ABC / MeriPehchaan / APAAR gateway behaviors
    without transmitting sensitive data over third-party networks.
    """
    PROVIDER_NAME = "MOCK_APAAR_DEMO_ADAPTER_V1"

    def verify_identity(
        self,
        apaar_id: str,
        student_name: str,
        dob: Optional[date] = None,
        gender: Optional[str] = None
    ) -> IdentityVerificationResult:
        start_time = time.perf_counter()
        
        # 1. Syntactic validation: Exactly 12 numeric digits
        cleaned = apaar_id.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^\d{12}$", cleaned):
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return IdentityVerificationResult(
                is_valid_format=False,
                is_verified=False,
                status_code="FORMAT_INVALID",
                provider_name=self.PROVIDER_NAME,
                message="APAAR ID must contain exactly 12 numeric digits.",
                response_time_ms=round(elapsed_ms, 2)
            )

        suffix = int(cleaned[-4:])
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Deterministic simulation branches
        if 9000 <= suffix <= 9299:
            return IdentityVerificationResult(
                is_valid_format=True,
                is_verified=False,
                status_code="IDENTITY_MISMATCH",
                provider_name=self.PROVIDER_NAME,
                provider_reference=f"MOCK-ERR-MISMATCH-{suffix}",
                message="Student name or Date of Birth does not match central APAAR registry record.",
                response_time_ms=round(elapsed_ms + 12.5, 2)
            )
        elif 9300 <= suffix <= 9599:
            return IdentityVerificationResult(
                is_valid_format=True,
                is_verified=False,
                status_code="NOT_FOUND",
                provider_name=self.PROVIDER_NAME,
                provider_reference=f"MOCK-ERR-NF-{suffix}",
                message="APAAR identifier not found in Academic Bank of Credits (ABC) registry.",
                response_time_ms=round(elapsed_ms + 8.2, 2)
            )
        elif 9600 <= suffix <= 9799:
            return IdentityVerificationResult(
                is_valid_format=True,
                is_verified=False,
                status_code="PROVIDER_UNAVAILABLE",
                provider_name=self.PROVIDER_NAME,
                provider_reference=f"MOCK-ERR-TIMEOUT-{suffix}",
                message="Upstream identity gateway timed out (HTTP 503). Record queued for retry.",
                response_time_ms=round(elapsed_ms + 45.0, 2)
            )
        elif 9800 <= suffix <= 9999:
            return IdentityVerificationResult(
                is_valid_format=True,
                is_verified=False,
                status_code="MANUAL_REVIEW_REQUIRED",
                provider_name=self.PROVIDER_NAME,
                provider_reference=f"MOCK-FLAG-REVIEW-{suffix}",
                message="Demographic variation detected; requires institutional nodal officer manual document audit.",
                response_time_ms=round(elapsed_ms + 15.0, 2)
            )
        else:
            # 0000 - 8999: Passed
            return IdentityVerificationResult(
                is_valid_format=True,
                is_verified=True,
                status_code="VERIFIED",
                provider_name=self.PROVIDER_NAME,
                provider_reference=f"MOCK-APAAR-VERIFIED-{suffix}",
                message="Identity successfully verified against simulated APAAR registry.",
                response_time_ms=round(elapsed_ms + 18.0, 2)
            )
