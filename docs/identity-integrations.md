# Identity Integration Contract: APAAR / ABC / MeriPehchaan

## 1. Context & Regulatory Mandate

APAAR (*Automated Permanent Academic Account Registry*), introduced under the National Education Policy (NEP 2020) and the Academic Bank of Credits (ABC), assigns a persistent 12-digit academic ID to every student in India.

In an operational deployment, verification against the APAAR gateway involves:
1. Student / Parent explicit consent.
2. Federated authentication via MeriPehchaan / DigiLocker.
3. Verification of demographic parameters (Name, Gender, Year of Birth) against the APAAR registry.

---

## 2. Prototype Architecture: Identity Provider Interface

To ensure safety, zero test PII leakage, and reproducible demonstration testing, PRAMAAN-AICTE abstracts identity verification behind an explicit provider interface:

```python
class IdentityVerificationResult(BaseModel):
    is_valid_format: bool
    is_verified: bool
    status_code: str  # "VERIFIED", "FORMAT_INVALID", "IDENTITY_MISMATCH", "NOT_FOUND", "PROVIDER_UNAVAILABLE", "MANUAL_REVIEW_REQUIRED"
    provider_name: str
    provider_reference: Optional[str]
    message: str
    response_time_ms: float

class IdentityProviderInterface(ABC):
    @abstractmethod
    async def verify_identity(
        self,
        apaar_id: str,
        student_name: str,
        dob: date,
        gender: Optional[str] = None
    ) -> IdentityVerificationResult:
        pass
```

---

## 3. Deterministic Mock APAAR Adapter

The included `MockApaarAdapter` simulates realistic outcomes based on deterministic test patterns:

1. **Standard Successful Verification**: Any valid 12-digit number ending in `0000` through `8999` returns `status_code="VERIFIED"`.
2. **Identity Mismatch**: Any 12-digit number ending in `9000` through `9299` simulates a name or date-of-birth mismatch in the national registry (`status_code="IDENTITY_MISMATCH"`).
3. **Record Not Found**: Numbers ending in `9300` through `9599` simulate an APAAR ID that has not yet been seeded or registered (`status_code="NOT_FOUND"`).
4. **Provider Outage**: Numbers ending in `9600` through `9799` simulate temporary upstream gateway timeout / 503 error (`status_code="PROVIDER_UNAVAILABLE"`).
5. **Manual Review Required**: Numbers ending in `9800` through `9999` simulate flagged edge cases (`status_code="MANUAL_REVIEW_REQUIRED"`).
6. **Syntactic Failure**: Any string that is not exactly 12 digits returns `status_code="FORMAT_INVALID"` before reaching the upstream adapter.

---

## 4. Production Integration Contract (Future Phase)

When authorized government credentials and Sandboxes are provided:
- Gateway: HTTPS REST endpoint with mutual TLS (mTLS).
- Authentication: Signed OAuth2 Client Credentials / JWT bearer tokens.
- Request correlation: Unique `X-Request-Correlation-ID` header attached to every verification call.
- Data retention: Upstream returns signed demographic assertion; raw biometrics or Aadhaar tokens are strictly forbidden from traversing or persisting in PRAMAAN-AICTE.
