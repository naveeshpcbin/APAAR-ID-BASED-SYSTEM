from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Float, ForeignKey, Text, JSON, BigInteger, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    aicte_id = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    state = Column(String(64), nullable=False, index=True)
    district = Column(String(64), nullable=False)
    institution_type = Column(String(64), default="STATE_GOVT_AIDED")  # CENTRAL_UNIVERSITY, STATE_GOVT_AIDED, PRIVATE_UNAIDED
    status = Column(String(32), default="APPROVED")  # APPROVED, SUSPENDED, PROBATION
    contact_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("InstitutionUser", back_populates="institution")
    programmes = relationship("Programme", back_populates="institution")
    approvals = relationship("ApprovalSnapshot", back_populates="institution")
    batches = relationship("UploadBatch", back_populates="institution")
    admissions = relationship("AdmissionRecord", back_populates="institution")
    anomalies = relationship("AnomalyCase", back_populates="institution")
    declarations = relationship("InstitutionalDeclaration", back_populates="institution")


class InstitutionUser(Base):
    __tablename__ = "institution_users"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), default="INSTITUTION_NODAL")  # AICTE_ADMIN, REGIONAL_OFFICER, INSTITUTION_NODAL, VERIFIER
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="users")
    batches = relationship("UploadBatch", back_populates="submitted_by", foreign_keys="UploadBatch.submitted_by_user_id")


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_code = Column(String(32), nullable=False)  # e.g. BTECH-CSE, BTECH-ECE, MBA, MCA
    programme_name = Column(String(128), nullable=False)
    degree_level = Column(String(32), default="UG")  # UG, PG, DIPLOMA
    duration_years = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="programmes")
    approvals = relationship("ApprovalSnapshot", back_populates="programme")
    admissions = relationship("AdmissionRecord", back_populates="programme")
    declarations = relationship("InstitutionalDeclaration", back_populates="programme")


class ApprovalSnapshot(Base):
    __tablename__ = "approval_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(16), nullable=False, index=True)  # e.g. "2026-27"
    approved_intake = Column(Integer, nullable=False)
    supernumerary_quota = Column(JSON, default=dict)  # {"TFW": 5, "EWS": 10, "JK_MIGRANT": 2}
    approval_letter_ref = Column(String(128), nullable=False)
    policy_version = Column(String(32), default="AICTE-APH-2026-V1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="approvals")
    programme = relationship("Programme", back_populates="approvals")


class PolicyRuleSet(Base):
    __tablename__ = "policy_rule_sets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    rules_config = Column(JSON, default=dict)  # quotas, tolerance thresholds, weights
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudentIdentity(Base):
    __tablename__ = "student_identities"

    id = Column(Integer, primary_key=True, index=True)
    apaar_hash = Column(String(64), unique=True, index=True, nullable=False)  # Keyed HMAC-SHA256
    apaar_masked = Column(String(16), nullable=False)  # XXXXXXXX1234
    full_name = Column(String(128), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String(16), default="MALE")
    verification_status = Column(String(32), default="VERIFIED")  # VERIFIED, UNVERIFIED, MISMATCH, NOT_FOUND
    provider_name = Column(String(64), default="MOCK_APAAR_SANDBOX")
    provider_reference = Column(String(128), nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    admissions = relationship("AdmissionRecord", back_populates="student")
    receipts = relationship("VerificationReceipt", back_populates="student")
    consent_grants = relationship("ConsentGrant", back_populates="student")


class InstitutionalDeclaration(Base):
    __tablename__ = "institutional_declarations"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(16), nullable=False, index=True)  # e.g. "2026-27"
    declared_intake = Column(Integer, nullable=False, default=0)  # Total students declared by college
    reporting_scope = Column(String(64), default="ALL")  # ALL, REGULAR_FIRST_YEAR, LATERAL_ENTRY
    declaration_ref = Column(String(128), nullable=True)  # Official declaration reference code
    declared_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution", back_populates="declarations")
    programme = relationship("Programme", back_populates="declarations")


class SyntheticApaarRecord(Base):
    """
    Dedicated editable database-backed registry for synthetic APAAR reference records.
    Explicitly labelled as DEMO DATA per SIH requirements.
    """
    __tablename__ = "synthetic_apaar_registry"

    id = Column(Integer, primary_key=True, index=True)
    apaar_id = Column(String(12), unique=True, index=True, nullable=False)  # 12-digit numeric identifier
    full_name = Column(String(128), nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String(16), default="MALE")  # MALE, FEMALE, OTHER
    status = Column(String(32), default="DEMO_REFERENCE_MATCH", nullable=False)
    # Allowed statuses:
    # DEMO_REFERENCE_MATCH, NO_DEMO_REFERENCE_MATCH, PENDING_EXTERNAL_VERIFICATION,
    # PROVIDER_CONFIRMED, PROVIDER_FAILED, MANUAL_REVIEW_REQUIRED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 for idempotency
    academic_year = Column(String(16), nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    warning_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    # Lifecycle: DRAFT, UPLOADED, VALIDATING, NEEDS_CORRECTION, READY_FOR_REVIEW, SUBMITTED, UNDER_REVIEW, APPROVED, RETURNED_FOR_CORRECTION, REJECTED
    status = Column(String(32), default="UPLOADED")
    mapping_config = Column(JSON, default=dict)
    review_notes = Column(Text, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution", back_populates="batches")
    submitted_by = relationship("InstitutionUser", foreign_keys=[submitted_by_user_id], back_populates="batches")
    reviewed_by = relationship("InstitutionUser", foreign_keys=[reviewed_by_user_id])
    findings = relationship("ValidationFinding", back_populates="batch", cascade="all, delete-orphan")
    validation_runs = relationship("ValidationRun", back_populates="batch", cascade="all, delete-orphan")
    admissions = relationship("AdmissionRecord", back_populates="batch")
    staged_rows = relationship("StagedBatchRow", back_populates="batch", cascade="all, delete-orphan")
    dispute_queries = relationship("BatchDisputeQuery", back_populates="batch", cascade="all, delete-orphan")
    advisories = relationship("AicteCentralAdvisory", back_populates="batch", cascade="all, delete-orphan")


class ValidationRun(Base):
    """
    Stores each validation run as a separately identifiable result linked to its
    source batch and configuration versions for historical traceability.
    """
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number = Column(Integer, default=1, nullable=False)
    triggered_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="COMPLETED")  # COMPLETED, FAILED
    total_rows = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    unique_records = Column(Integer, default=0)
    blocking_errors = Column(Integer, default=0)
    requiring_review = Column(Integer, default=0)
    eligible_to_proceed = Column(Integer, default=0)
    declared_intake = Column(Integer, default=0)
    declared_discrepancy = Column(Integer, default=0)
    reference_versions_json = Column(JSON, default=dict)
    summary_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("UploadBatch", back_populates="validation_runs")
    triggered_by = relationship("InstitutionUser")
    findings = relationship("ValidationFinding", back_populates="validation_run", cascade="all, delete-orphan")


class ValidationFinding(Base):
    __tablename__ = "validation_findings"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    validation_run_id = Column(Integer, ForeignKey("validation_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    row_index = Column(Integer, nullable=False)
    field_name = Column(String(64), nullable=False)
    rule_id = Column(String(64), nullable=False)
    severity = Column(String(16), nullable=False)  # ERROR, WARNING, INFO
    finding_type = Column(String(64), default="VALIDATION_CHECK")
    submitted_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    reference_source_id = Column(String(128), nullable=True)
    rule_version = Column(String(64), default="AICTE-APH-2026-V1")
    message = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("UploadBatch", back_populates="findings")
    validation_run = relationship("ValidationRun", back_populates="findings")


class AdmissionRecord(Base):
    __tablename__ = "admission_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year = Column(String(16), nullable=False, index=True)
    enrollment_no = Column(String(64), nullable=False)
    category = Column(String(32), default="OPEN")  # OPEN, OBC_NCL, SC, ST, EWS
    admission_quota = Column(String(32), default="STATE_GOVT")  # STATE_GOVT, AICTE_TFW, MANAGEMENT, NRI, PIO
    nationality_type = Column(String(32), default="DOMESTIC")  # DOMESTIC, NRI, OCI, FOREIGN_NATIONAL
    is_supernumerary = Column(Boolean, default=False)
    admission_date = Column(Date, default=date.today)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, UNDER_REVIEW, WITHDRAWN, TRANSFERRED, CANCELLED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentIdentity", back_populates="admissions")
    institution = relationship("Institution", back_populates="admissions")
    programme = relationship("Programme", back_populates="admissions")
    batch = relationship("UploadBatch", back_populates="admissions")
    receipts = relationship("VerificationReceipt", back_populates="admission")


class ConsentGrant(Base):
    __tablename__ = "consent_grants"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(64), default="APAAR_IDENTITY_VERIFICATION")
    granted_by = Column(String(32), default="STUDENT")  # STUDENT, PARENT_GUARDIAN
    is_granted = Column(Boolean, default=True)
    grant_timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentIdentity", back_populates="consent_grants")


class AdmissionConflict(Base):
    __tablename__ = "admission_conflicts"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(32), unique=True, index=True, nullable=False)  # CONF-2026-0001
    student_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    record_a_id = Column(Integer, ForeignKey("admission_records.id", ondelete="CASCADE"), nullable=False)
    record_b_id = Column(Integer, ForeignKey("admission_records.id", ondelete="CASCADE"), nullable=False)
    conflict_type = Column(String(64), nullable=False)  # CROSS_INSTITUTION_DUPLICATE, WITHIN_BATCH_DUPLICATE
    status = Column(String(32), default="OPEN")  # OPEN, UNDER_INVESTIGATION, RESOLVED_VALID, RESOLVED_CANCELLED, ESCALATED
    resolution_notes = Column(Text, nullable=True)
    resolved_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    student = relationship("StudentIdentity")
    record_a = relationship("AdmissionRecord", foreign_keys=[record_a_id])
    record_b = relationship("AdmissionRecord", foreign_keys=[record_b_id])
    resolved_by = relationship("InstitutionUser")


class AnomalyCase(Base):
    __tablename__ = "anomaly_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(32), unique=True, index=True, nullable=False)  # ANOM-2026-0001
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True)
    academic_year = Column(String(16), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0.0 - 100.0
    anomaly_type = Column(String(64), nullable=False)  # INTAKE_SPIKE, CATEGORY_DISTRIBUTION, COLLISION_BURST, DEADLINE_CLUSTER
    signals_json = Column(JSON, default=dict)
    explanation = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, INSPECTED_CLEARED, ESCALATED_AUDIT
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="anomalies")
    programme = relationship("Programme")


class VerificationReceipt(Base):
    __tablename__ = "verification_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_token = Column(String(64), unique=True, index=True, nullable=False)  # Opaque random token
    student_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False)
    admission_record_id = Column(Integer, ForeignKey("admission_records.id", ondelete="CASCADE"), nullable=False)
    claim_scope = Column(String(64), default="ACTIVE_ENROLMENT_STATUS")
    ed25519_signature = Column(Text, nullable=False)
    payload_digest = Column(String(64), nullable=False)  # SHA-256
    canonical_payload = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revocation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentIdentity", back_populates="receipts")
    admission = relationship("AdmissionRecord", back_populates="receipts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    sequence_no = Column(BigInteger, unique=True, index=True, nullable=False)
    actor_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)
    actor_role = Column(String(32), nullable=False)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    metadata_json = Column(JSON, default=dict)
    correlation_id = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagedBatchRow(Base):
    """
    Persisted staged student record from uploaded batch.
    Enables in-browser spreadsheet inspection, algorithm error highlighting, and inline corrections.
    """
    __tablename__ = "staged_batch_rows"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)  # 0-indexed row number
    apaar_id = Column(String(32), nullable=True, index=True)
    student_name = Column(String(128), nullable=True)
    programme_code = Column(String(32), nullable=True)
    category = Column(String(32), default="OPEN")
    gender = Column(String(16), default="MALE")
    dob = Column(Date, nullable=True)
    admission_quota = Column(String(32), default="STATE_GOVT")
    admission_date = Column(Date, nullable=True)
    merit_rank = Column(Integer, nullable=True)
    is_supernumerary = Column(Boolean, default=False)
    status = Column(String(32), default="ELIGIBLE")  # ELIGIBLE, REQUIRES_REVIEW, BLOCKING_ERROR, EXEMPTION_REQUESTED, EXEMPTED
    raw_data = Column(JSON, default=dict)
    normalized_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batch = relationship("UploadBatch", back_populates="staged_rows")
    queries = relationship("BatchDisputeQuery", back_populates="staged_row", cascade="all, delete-orphan")


class BatchDisputeQuery(Base):
    """
    Institutional query or exemption message sent by the college to AICTE Central
    (e.g., student lacks an APAAR ID due to creation failure, UIDAI sync delay, or technical exception).
    """
    __tablename__ = "batch_dispute_queries"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_id = Column(Integer, ForeignKey("staged_batch_rows.id", ondelete="SET NULL"), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(255), nullable=False)
    category = Column(String(64), default="MISSING_APAAR_UIDAI_FAIL")  # MISSING_APAAR_UIDAI_FAIL, QUOTA_DISPUTE, TECHNICAL_EXCEPTION, OTHER
    student_identifier = Column(String(128), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, PROVISIONALLY_EXEMPTED, RESOLVED_REJECTED
    aicte_reply = Column(Text, nullable=True)
    resolved_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    batch = relationship("UploadBatch", back_populates="dispute_queries")
    staged_row = relationship("StagedBatchRow", back_populates="queries")
    institution = relationship("Institution")
    raised_by = relationship("InstitutionUser", foreign_keys=[raised_by_user_id])
    resolved_by = relationship("InstitutionUser", foreign_keys=[resolved_by_user_id])


class AicteCentralAdvisory(Base):
    """
    Official AICTE Central Government Advisory / Remediation Idea / Policy Recommendation.
    Allows Central Officers to give specific remediation ideas or policy exemptions to an institution's batch.
    """
    __tablename__ = "aicte_central_advisories"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    advisory_type = Column(String(64), default="PROGRAMME_REMAP_RECOMMENDATION")  # PROGRAMME_REMAP_RECOMMENDATION, QUOTA_REALLOCATION_IDEA, PROVISIONAL_UNDERTAKING, GENERAL_ADVISORY
    title = Column(String(255), nullable=False)
    idea_description = Column(Text, nullable=False)
    recommended_action = Column(JSON, default=dict)  # e.g. {"action": "REMAP_PROGRAMME", "from_code": "BTECH-AI", "to_code": "BTECH-CSE"}
    status = Column(String(32), default="ACTIVE")  # ACTIVE, APPLIED_BY_COLLEGE, DISMISSED
    created_by_user_id = Column(Integer, ForeignKey("institution_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime, nullable=True)

    batch = relationship("UploadBatch", back_populates="advisories")
    institution = relationship("Institution")
    created_by = relationship("InstitutionUser")
