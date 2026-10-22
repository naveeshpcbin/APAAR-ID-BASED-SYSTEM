import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.security import verify_password, get_password_hash, hash_apaar_id, mask_apaar_id, ReceiptSigner
from app.adapters.mock_apaar_adapter import MockApaarAdapter
from app.services.capacity_service import ApprovalCapacityService
from app.services.conflict_service import ConflictDetectionService
from app.services.receipt_service import ReceiptService
from app.core.hash_chain import append_audit_event, verify_hash_chain_integrity
import app.models
from app.models import (
    Institution, InstitutionUser, Programme, ApprovalSnapshot,
    StudentIdentity, AdmissionRecord, UploadBatch, AdmissionConflict
)

from sqlalchemy.pool import StaticPool

# In-memory test database with StaticPool to share state across connections
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = override_get_db
    c = TestClient(fastapi_app)
    yield c
    fastapi_app.dependency_overrides.clear()

# GATE 1: Environment & Health Endpoints
def test_gate1_health_readiness(client):
    r1 = client.get("/api/v1/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "UP"

    r2 = client.get("/api/v1/health/ready")
    assert r2.status_code == 200
    assert r2.json()["status"] == "READY"

# GATE 2: Password Hashing, JWT & Identifier Masking
def test_gate2_security_primitives():
    plain = "Secur3P@ssw0rd!"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPass", hashed) is False

    apaar = "123456789012"
    masked = mask_apaar_id(apaar)
    assert masked == "XXXXXXXX9012"

    h1 = hash_apaar_id(apaar)
    h2 = hash_apaar_id("1234-5678-9012")  # Normalized match
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 length

# GATE 3: Ingestion & Mock APAAR Adapter
def test_gate3_apaar_adapter_and_rules():
    adapter = MockApaarAdapter()
    
    # Valid APAAR
    res_valid = adapter.verify_identity("400192831000", "Aarav Mehta")
    assert res_valid.is_valid_format is True
    assert res_valid.is_verified is True
    assert res_valid.status_code == "VERIFIED"

    # Invalid Format (not 12 digits)
    res_inv = adapter.verify_identity("12345", "Test User")
    assert res_inv.is_valid_format is False
    assert res_inv.status_code == "FORMAT_INVALID"

    # Mismatch Simulation (suffix 9000-9299)
    res_mismatch = adapter.verify_identity("400192839100", "Wrong Name")
    assert res_mismatch.is_valid_format is True
    assert res_mismatch.is_verified is False
    assert res_mismatch.status_code == "IDENTITY_MISMATCH"

# GATE 4: Capacity & Policy Rules Engine
def test_gate4_approval_capacity_calculation(db_session):
    inst = Institution(aicte_id="TEST-001", name="Test Tech Inst", state="Delhi", district="New Delhi")
    db_session.add(inst)
    db_session.flush()

    prog = Programme(institution_id=inst.id, programme_code="BTECH-AI", programme_name="AI & DS")
    db_session.add(prog)
    db_session.flush()

    app_snap = ApprovalSnapshot(
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        approved_intake=60,
        supernumerary_quota={"TFW": 3},
        approval_letter_ref="AICTE/TEST/2026-27/001"
    )
    db_session.add(app_snap)
    db_session.commit()

    # Test within capacity
    eval1 = ApprovalCapacityService.evaluate_programme_capacity(
        db=db_session,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        incoming_count=50
    )
    assert eval1["is_compliant"] is True
    assert eval1["overage"] == 0
    assert eval1["approved_intake"] == 60

    # Test capacity exceeded
    eval2 = ApprovalCapacityService.evaluate_programme_capacity(
        db=db_session,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        incoming_count=65
    )
    assert eval2["is_compliant"] is False
    assert eval2["overage"] == 5

# GATE 5: Cross-Institution Conflict Detection
def test_gate5_conflict_detection(db_session):
    inst1 = Institution(aicte_id="INST-A", name="College A", state="Delhi", district="Central")
    inst2 = Institution(aicte_id="INST-B", name="College B", state="UP", district="Noida")
    db_session.add_all([inst1, inst2])
    db_session.flush()

    prog1 = Programme(institution_id=inst1.id, programme_code="CSE", programme_name="CSE")
    prog2 = Programme(institution_id=inst2.id, programme_code="CSE", programme_name="CSE")
    db_session.add_all([prog1, prog2])
    db_session.flush()

    student = StudentIdentity(
        apaar_hash=hash_apaar_id("999988887777"),
        apaar_masked="XXXXXXXX7777",
        full_name="Duplicate Student",
        dob=date(2005, 1, 1),
        verification_status="VERIFIED"
    )
    db_session.add(student)
    db_session.flush()

    adm1 = AdmissionRecord(
        student_id=student.id,
        institution_id=inst1.id,
        programme_id=prog1.id,
        academic_year="2026-27",
        enrollment_no="ENR-1",
        status="ACTIVE"
    )
    db_session.add(adm1)
    db_session.commit()

    adm2 = AdmissionRecord(
        student_id=student.id,
        institution_id=inst2.id,
        programme_id=prog2.id,
        academic_year="2026-27",
        enrollment_no="ENR-2",
        status="UNDER_REVIEW"
    )
    db_session.add(adm2)
    db_session.commit()

    conflict = ConflictDetectionService.check_for_conflicts(
        db=db_session,
        student_id=student.id,
        new_record_id=adm2.id,
        institution_id=inst2.id,
        academic_year="2026-27"
    )
    assert conflict is not None
    assert conflict.conflict_type == "CROSS_INSTITUTION_DUPLICATE"
    assert conflict.status == "OPEN"

# GATE 6: Ed25519 Signed Verification Receipt & Tamper-Evident Hash Chain
def test_gate6_signed_receipts_and_hash_chain(db_session, client):
    # Test Hash Chain
    append_audit_event(db=db_session, action="TEST_ACTION_1", entity_type="System", entity_id="1")
    append_audit_event(db=db_session, action="TEST_ACTION_2", entity_type="System", entity_id="2")
    
    chain_status = verify_hash_chain_integrity(db=db_session)
    assert chain_status["is_valid"] is True
    assert chain_status["total_events"] >= 2

    # Issue receipt
    adm = db_session.query(AdmissionRecord).first()
    receipt = ReceiptService.issue_receipt(
        db=db_session,
        admission_id=adm.id,
        expiry_days=10
    )
    assert receipt["receipt_token"].startswith("rcpt_")
    assert receipt["signature"] is not None
    assert receipt["qr_code_base64"].startswith("data:image/png;base64,")

    # Verify public receipt
    v_res = ReceiptService.verify_receipt(db=db_session, receipt_token=receipt["receipt_token"])
    assert v_res["is_valid"] is True
    assert v_res["status"] == "AUTHENTIC_AND_VERIFIED"

    # Test invalid / forged token
    v_fake = ReceiptService.verify_receipt(db=db_session, receipt_token="rcpt_forged_token_123")
    assert v_fake["is_valid"] is False
    assert v_fake["status"] == "NOT_FOUND"

    # Test tampered receipt signature
    receipt_obj = db_session.query(app.models.VerificationReceipt).filter(
        app.models.VerificationReceipt.receipt_token == receipt["receipt_token"]
    ).first()
    original_sig = receipt_obj.ed25519_signature
    receipt_obj.ed25519_signature = "a" * 128  # Invalid 64-byte hex signature
    db_session.commit()

    v_tampered = ReceiptService.verify_receipt(db=db_session, receipt_token=receipt["receipt_token"])
    assert v_tampered["is_valid"] is False
    assert v_tampered["status"] in ["INVALID_SIGNATURE", "SIGNATURE_INVALID", "VERIFICATION_FAILED"]
    # Restore signature
    receipt_obj.ed25519_signature = original_sig
    db_session.commit()

# GATE 7: Edge Cases - Missing Approval & Hash Chain Tamper Detection
def test_gate7_edge_cases_and_tamper_detection(db_session):
    # Missing approval returns has_approval=False
    eval_missing = ApprovalCapacityService.evaluate_programme_capacity(
        db=db_session,
        institution_id=99999,
        programme_id=99999,
        academic_year="2026-27",
        incoming_count=10
    )
    assert eval_missing["has_approval"] is False
    assert eval_missing["is_compliant"] is False
    assert "No active approval snapshot" in eval_missing["explanation"]

    # Tamper detection in Hash Chain
    ev = append_audit_event(db=db_session, action="LEGIT_EVENT", entity_type="Policy", entity_id="10")
    # Tamper with event payload in database
    ev.action = "TAMPERED_ACTION"
    db_session.commit()

    tamper_result = verify_hash_chain_integrity(db=db_session)
    assert tamper_result["is_valid"] is False
    assert "Cryptographic integrity failed" in tamper_result["reason"] or "mismatch" in tamper_result["reason"]

