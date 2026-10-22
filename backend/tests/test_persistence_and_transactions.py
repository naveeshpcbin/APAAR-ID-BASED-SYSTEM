import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Institution, Programme, ApprovalSnapshot, StudentIdentity, AdmissionRecord, UploadBatch
from app.core.security import hash_apaar_id, mask_apaar_id

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

    inst = Institution(aicte_id="PERSIST-01", name="Persistence Test College", state="Delhi", district="Central")
    session.add(inst)
    session.flush()

    p = Programme(institution_id=inst.id, programme_code="BTECH-EE", programme_name="Electrical")
    session.add(p)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_admission_status_lifecycle_transitions(db):
    inst = db.query(Institution).filter(Institution.aicte_id == "PERSIST-01").first()
    prog = db.query(Programme).filter(Programme.institution_id == inst.id).first()

    student = StudentIdentity(
        apaar_hash=hash_apaar_id("400192835555"),
        apaar_masked=mask_apaar_id("400192835555"),
        full_name="Lifecycle Student",
        dob=date(2005, 1, 1),
        verification_status="VERIFIED"
    )
    db.add(student)
    db.flush()

    adm = AdmissionRecord(
        student_id=student.id,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        enrollment_no="EE-2026-001",
        status="ACTIVE"
    )
    db.add(adm)
    db.commit()

    # Transition 1: ACTIVE -> UNDER_REVIEW
    adm.status = "UNDER_REVIEW"
    adm.notes = "Audit inquiry requested"
    db.commit()
    db.refresh(adm)
    assert adm.status == "UNDER_REVIEW"

    # Transition 2: UNDER_REVIEW -> WITHDRAWN
    adm.status = "WITHDRAWN"
    adm.notes = "Transferred to IIT Delhi"
    db.commit()
    db.refresh(adm)
    assert adm.status == "WITHDRAWN"

def test_transaction_rollback_guarantee(db):
    inst = db.query(Institution).filter(Institution.aicte_id == "PERSIST-01").first()
    prog = db.query(Programme).filter(Programme.institution_id == inst.id).first()

    initial_count = db.query(AdmissionRecord).count()

    # Simulate transactional failure
    try:
        s = StudentIdentity(
            apaar_hash=hash_apaar_id("400192836666"),
            apaar_masked=mask_apaar_id("400192836666"),
            full_name="Rollback Candidate",
            dob=date(2005, 1, 1)
        )
        db.add(s)
        db.flush()

        adm = AdmissionRecord(
            student_id=s.id,
            institution_id=inst.id,
            programme_id=prog.id,
            academic_year="2026-27",
            enrollment_no="ROLLBACK-01",
            status="ACTIVE"
        )
        db.add(adm)
        db.flush()

        # Deliberate failure: insert duplicate student with identical apaar_hash
        duplicate_s = StudentIdentity(
            apaar_hash=hash_apaar_id("400192836666"),  # unique constraint violation
            apaar_masked=mask_apaar_id("400192836666"),
            full_name="Duplicate Violator",
            dob=date(2005, 1, 1)
        )
        db.add(duplicate_s)
        db.commit()
    except Exception:
        db.rollback()

    final_count = db.query(AdmissionRecord).count()
    assert final_count == initial_count  # No orphaned records persisted!
