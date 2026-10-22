import pytest
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Institution, Programme, StudentIdentity, AdmissionRecord, VerificationReceipt, AuditEvent
from app.core.security import hash_apaar_id, mask_apaar_id
from app.core.hash_chain import append_audit_event, verify_hash_chain_integrity
from app.services.receipt_service import ReceiptService

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSession()

    inst = Institution(aicte_id="RCPT-INST-01", name="Receipt College", state="Delhi", district="New Delhi")
    session.add(inst)
    session.flush()

    prog = Programme(institution_id=inst.id, programme_code="BTECH-IT", programme_name="Information Technology")
    session.add(prog)
    session.flush()

    student = StudentIdentity(
        apaar_hash=hash_apaar_id("400192833333"),
        apaar_masked=mask_apaar_id("400192833333"),
        full_name="Kavita Rao",
        dob=date(2005, 7, 20),
        verification_status="VERIFIED"
    )
    session.add(student)
    session.flush()

    adm = AdmissionRecord(
        student_id=student.id,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        enrollment_no="IT-2026-999",
        category="OPEN",
        admission_quota="STATE_GOVT",
        status="ACTIVE"
    )
    session.add(adm)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_ed25519_signed_receipt_creation_and_verification(db):
    adm = db.query(AdmissionRecord).first()
    receipt_dict = ReceiptService.issue_receipt(
        db=db,
        admission_id=adm.id,
        expiry_days=30
    )

    assert receipt_dict["receipt_token"].startswith("rcpt_")
    assert receipt_dict["signature"] is not None
    assert len(receipt_dict["signature"]) >= 64  # Ed25519 signature hex
    assert receipt_dict["qr_code_base64"].startswith("data:image/png;base64,")

    # Verify authentic token
    verified = ReceiptService.verify_receipt(db=db, receipt_token=receipt_dict["receipt_token"])
    assert verified["is_valid"] is True
    assert verified["status"] == "AUTHENTIC_AND_VERIFIED"
    assert verified["canonical_payload"]["student_name"] == "Kavita Rao"
    assert verified["canonical_payload"]["apaar_masked"] == "XXXXXXXX3333"

def test_tampered_payload_and_signature_detection(db):
    adm = db.query(AdmissionRecord).first()
    receipt_dict = ReceiptService.issue_receipt(db=db, admission_id=adm.id, expiry_days=5)
    token = receipt_dict["receipt_token"]

    receipt_obj = db.query(VerificationReceipt).filter(VerificationReceipt.receipt_token == token).first()

    # Case 1: Tampered signature
    orig_sig = receipt_obj.ed25519_signature
    receipt_obj.ed25519_signature = "f" * 128
    db.commit()

    v_tampered_sig = ReceiptService.verify_receipt(db=db, receipt_token=token)
    assert v_tampered_sig["is_valid"] is False
    assert v_tampered_sig["status"] in ["INVALID_SIGNATURE", "VERIFICATION_FAILED"]

    # Restore signature and tamper with payload
    receipt_obj.ed25519_signature = orig_sig
    receipt_obj.canonical_payload = {"forged": "malicious payload"}
    db.commit()

    v_tampered_payload = ReceiptService.verify_receipt(db=db, receipt_token=token)
    assert v_tampered_payload["is_valid"] is False
    assert v_tampered_payload["status"] in ["INVALID_SIGNATURE", "PAYLOAD_MISMATCH", "VERIFICATION_FAILED"]

def test_expired_and_revoked_receipt(db):
    adm = db.query(AdmissionRecord).first()
    # Expired token (expires in negative days)
    receipt_dict = ReceiptService.issue_receipt(db=db, admission_id=adm.id, expiry_days=-1)
    token_exp = receipt_dict["receipt_token"]

    v_exp = ReceiptService.verify_receipt(db=db, receipt_token=token_exp)
    assert v_exp["is_valid"] is False
    assert v_exp["status"] == "EXPIRED"

    # Revoked token
    receipt_dict2 = ReceiptService.issue_receipt(db=db, admission_id=adm.id, expiry_days=10)
    token_rev = receipt_dict2["receipt_token"]

    rcpt_obj = db.query(VerificationReceipt).filter(VerificationReceipt.receipt_token == token_rev).first()
    rcpt_obj.is_revoked = True
    rcpt_obj.revocation_reason = "Enrolment cancelled by university registrar."
    db.commit()

    v_rev = ReceiptService.verify_receipt(db=db, receipt_token=token_rev)
    assert v_rev["is_valid"] is False
    assert v_rev["status"] == "REVOKED"
    assert "cancelled" in v_rev["revocation_reason"]

def test_tamper_evident_hash_chain_verification(db):
    # Append events
    append_audit_event(db=db, action="RECEIPT_ISSUED", entity_type="VerificationReceipt", entity_id="1")
    append_audit_event(db=db, action="STATUS_CHANGED", entity_type="AdmissionRecord", entity_id="1")

    # Clean chain verify
    chain_res = verify_hash_chain_integrity(db=db)
    assert chain_res["is_valid"] is True
    assert chain_res["total_events"] >= 2

    # Inject deliberate tamper in database row
    ev = db.query(AuditEvent).first()
    orig_action = ev.action
    ev.action = "TAMPERED_ACTION_MALICIOUS"
    db.commit()

    # Verify tamper is caught
    broken_res = verify_hash_chain_integrity(db=db)
    assert broken_res["is_valid"] is False
    assert broken_res["broken_at_sequence"] == ev.sequence_no

    # Restore clean state
    ev.action = orig_action
    db.commit()
