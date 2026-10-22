import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Institution, Programme, StudentIdentity, AdmissionRecord, AdmissionConflict, AnomalyCase, AuditEvent
from app.services.conflict_service import ConflictDetectionService
from app.services.anomaly_service import AnomalyDetectionService

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

    c1 = Institution(aicte_id="CONF-INST-A", name="College Alpha", state="Delhi", district="Central")
    c2 = Institution(aicte_id="CONF-INST-B", name="College Beta", state="Karnataka", district="Bangalore")
    session.add_all([c1, c2])
    session.flush()

    p1 = Programme(institution_id=c1.id, programme_code="CSE", programme_name="CSE")
    p2 = Programme(institution_id=c2.id, programme_code="CSE", programme_name="CSE")
    session.add_all([p1, p2])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_cross_institution_duplicate_conflict_generation(db):
    c1 = db.query(Institution).filter(Institution.aicte_id == "CONF-INST-A").first()
    c2 = db.query(Institution).filter(Institution.aicte_id == "CONF-INST-B").first()
    p1 = db.query(Programme).filter(Programme.institution_id == c1.id).first()
    p2 = db.query(Programme).filter(Programme.institution_id == c2.id).first()

    student = StudentIdentity(
        apaar_hash="hash_conflict_test_01",
        apaar_masked="XXXXXXXX8888",
        full_name="Duplicate Seeker",
        dob=date(2005, 3, 15),
        verification_status="VERIFIED"
    )
    db.add(student)
    db.flush()

    # Active admission at College Alpha
    adm1 = AdmissionRecord(
        student_id=student.id,
        institution_id=c1.id,
        programme_id=p1.id,
        academic_year="2026-27",
        enrollment_no="ALPHA-2026-101",
        status="ACTIVE"
    )
    db.add(adm1)
    db.commit()

    # Incoming admission at College Beta
    adm2 = AdmissionRecord(
        student_id=student.id,
        institution_id=c2.id,
        programme_id=p2.id,
        academic_year="2026-27",
        enrollment_no="BETA-2026-202",
        status="UNDER_REVIEW"
    )
    db.add(adm2)
    db.commit()

    # Run Conflict Detection
    conflict = ConflictDetectionService.check_for_conflicts(
        db=db,
        student_id=student.id,
        new_record_id=adm2.id,
        institution_id=c2.id,
        academic_year="2026-27"
    )

    assert conflict is not None
    assert conflict.case_number.startswith("CONF-2026-")
    assert conflict.conflict_type == "CROSS_INSTITUTION_DUPLICATE"
    assert conflict.status == "OPEN"
    assert conflict.record_a_id == adm1.id
    assert conflict.record_b_id == adm2.id

def test_human_conflict_adjudication_and_audit(db):
    conflict = db.query(AdmissionConflict).first()
    assert conflict is not None

    # Adjudicate in favor of College Beta (record_b)
    resolved = ConflictDetectionService.resolve_conflict(
        db=db,
        conflict_id=conflict.id,
        resolution_status="RESOLVED_VALID",
        winning_record_id=conflict.record_b_id,
        resolution_notes="Student produced official stamped migration certificate from College Alpha.",
        user_id=1,
        user_email="regulator@pramaan.internal",
        user_role="AICTE_ADMIN"
    )

    assert resolved["status"] == "RESOLVED_VALID"
    db.refresh(conflict)
    assert conflict.status == "RESOLVED_VALID"

    # Verify that record_b is now ACTIVE, record_a is CANCELLED
    adm_a = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_a_id).first()
    adm_b = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_b_id).first()
    assert adm_b.status == "ACTIVE"
    assert adm_a.status == "CANCELLED"

    # Verify Audit Event was created
    audit = db.query(AuditEvent).filter(
        AuditEvent.action == "CONFLICT_RESOLVED",
        AuditEvent.entity_id == str(conflict.id)
    ).first()
    assert audit is not None
    assert audit.actor_role == "AICTE_ADMIN"

def test_anomaly_detection_and_escalation(db):
    c1 = db.query(Institution).filter(Institution.aicte_id == "CONF-INST-A").first()

    # Create artificial anomaly case
    case = AnomalyCase(
        case_number="ANOM-TEST-9999",
        institution_id=c1.id,
        academic_year="2026-27",
        risk_score=78.5,
        anomaly_type="INTAKE_SPIKE",
        signals_json={
            "volume_growth": 45.0,
            "category_deviation": 12.4,
            "conflict_rate": 8.5
        },
        explanation="Intake volume surge exceeds historical baseline by 45%.",
        status="PENDING_REVIEW"
    )
    db.add(case)
    db.commit()

    # Escalate anomaly to formal audit
    reviewed = AnomalyDetectionService.review_anomaly(
        db=db,
        anomaly_id=case.id,
        new_status="ESCALATED_AUDIT",
        notes="Transferred to regional directorate for physical inspection.",
        reviewed_by_user_id=1,
        reviewed_by_email="auditor@pramaan.internal",
        reviewed_by_role="AICTE_ADMIN"
    )

    assert reviewed.status == "ESCALATED_AUDIT"
    assert "inspection" in reviewed.explanation or "inspection" in reviewed.signals_json.get("review_notes", "")
