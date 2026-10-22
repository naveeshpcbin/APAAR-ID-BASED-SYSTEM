import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Institution, Programme, ApprovalSnapshot, AdmissionRecord, StudentIdentity
from app.adapters.mock_apaar_adapter import MockApaarAdapter
from app.services.capacity_service import ApprovalCapacityService

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
    inst = Institution(aicte_id="CAP-INST-01", name="Capacity Test Institute", state="Maharashtra", district="Pune")
    session.add(inst)
    session.flush()

    prog = Programme(institution_id=inst.id, programme_code="BTECH-MECH", programme_name="Mechanical Engineering")
    session.add(prog)
    session.flush()

    snap = ApprovalSnapshot(
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        approved_intake=60,
        supernumerary_quota={"TFW": 3, "EWS": 6, "JK_MIGRANT": 1},
        approval_letter_ref="AICTE/WR/2026-27/042",
        policy_version="APH_2026_V1"
    )
    session.add(snap)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

# Identity Adapter Unit Tests
def test_identity_adapter_deterministic_outcomes():
    adapter = MockApaarAdapter()

    # 1. Format Invalid (< 12 digits)
    res_short = adapter.verify_identity("123456789", "Aarav Gupta")
    assert res_short.is_valid_format is False
    assert res_short.status_code == "FORMAT_INVALID"

    # 2. Format Invalid (alphanumeric)
    res_alpha = adapter.verify_identity("12345678901A", "Aarav Gupta")
    assert res_alpha.is_valid_format is False
    assert res_alpha.status_code == "FORMAT_INVALID"

    # 3. Verified Match (0000-8999 suffix)
    res_match = adapter.verify_identity("400192831200", "Aarav Gupta")
    assert res_match.is_valid_format is True
    assert res_match.is_verified is True
    assert res_match.status_code == "VERIFIED"
    assert res_match.provider_name == "MOCK_APAAR_DEMO_ADAPTER_V1"

    # 4. Identity Mismatch (9000-9299 suffix)
    res_mismatch = adapter.verify_identity("400192839100", "Wrong Name")
    assert res_mismatch.is_valid_format is True
    assert res_mismatch.is_verified is False
    assert res_mismatch.status_code == "IDENTITY_MISMATCH"

    # 5. Not Found (9300-9599 suffix)
    res_notfound = adapter.verify_identity("400192839400", "Ghost Candidate")
    assert res_notfound.is_valid_format is True
    assert res_notfound.is_verified is False
    assert res_notfound.status_code == "NOT_FOUND"

    # 6. Provider Timeout (9600-9799 suffix)
    res_timeout = adapter.verify_identity("400192839700", "Delayed Response")
    assert res_timeout.is_valid_format is True
    assert res_timeout.is_verified is False
    assert res_timeout.status_code == "PROVIDER_UNAVAILABLE"

    # 7. Manual Review Required (9800-9999 suffix)
    res_manual = adapter.verify_identity("400198009950", "Audit Review")
    assert res_manual.is_valid_format is True
    assert res_manual.is_verified is False
    assert res_manual.status_code == "MANUAL_REVIEW_REQUIRED"

# Approval Capacity & Quotas Unit Tests
def test_approval_capacity_under_and_over_intake(db):
    inst = db.query(Institution).filter(Institution.aicte_id == "CAP-INST-01").first()
    prog = db.query(Programme).filter(Programme.institution_id == inst.id).first()

    # Case A: Within Capacity (approved = 60, incoming = 45)
    eval_under = ApprovalCapacityService.evaluate_programme_capacity(
        db=db,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        incoming_count=45
    )
    assert eval_under["has_approval"] is True
    assert eval_under["is_compliant"] is True
    assert eval_under["approved_intake"] == 60
    assert eval_under["overage"] == 0
    assert eval_under["utilization_pct"] == 75.0

    # Case B: Exceeds Capacity (incoming = 72)
    eval_over = ApprovalCapacityService.evaluate_programme_capacity(
        db=db,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        incoming_count=72
    )
    assert eval_over["has_approval"] is True
    assert eval_over["is_compliant"] is False
    assert eval_over["overage"] == 12
    assert "WARNING" in eval_over["explanation"]

def test_supernumerary_quota_and_international_segregation(db):
    inst = db.query(Institution).filter(Institution.aicte_id == "CAP-INST-01").first()
    prog = db.query(Programme).filter(Programme.institution_id == inst.id).first()

    # Seed 3 regular students, 2 supernumerary TFW students, 1 NRI student
    students = []
    for i in range(6):
        s = StudentIdentity(
            apaar_hash=f"hash_sup_test_{i}",
            apaar_masked=f"XXXXXXXX{i:04d}",
            full_name=f"Student {i}",
            dob=date(2005, 1, 1),
            verification_status="VERIFIED"
        )
        db.add(s)
        students.append(s)
    db.flush()

    admissions = [
        # Regular
        AdmissionRecord(student_id=students[0].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-01", category="OPEN", admission_quota="STATE_GOVT", is_supernumerary=False),
        AdmissionRecord(student_id=students[1].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-02", category="OBC_NCL", admission_quota="STATE_GOVT", is_supernumerary=False),
        AdmissionRecord(student_id=students[2].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-03", category="SC", admission_quota="STATE_GOVT", is_supernumerary=False),
        # Supernumerary TFW (Over and above approved intake)
        AdmissionRecord(student_id=students[3].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-04", category="OPEN", admission_quota="AICTE_TFW", is_supernumerary=True),
        AdmissionRecord(student_id=students[4].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-05", category="OPEN", admission_quota="AICTE_TFW", is_supernumerary=True),
        # International (NRI)
        AdmissionRecord(student_id=students[5].id, institution_id=inst.id, programme_id=prog.id, academic_year="2026-27", enrollment_no="ME-06", category="OPEN", admission_quota="NRI_QUOTA", nationality_type="NRI", is_supernumerary=False)
    ]
    db.add_all(admissions)
    db.commit()

    eval_breakdown = ApprovalCapacityService.evaluate_programme_capacity(
        db=db,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        incoming_count=0
    )

    assert eval_breakdown["current_active"] == 6
    assert eval_breakdown["general_enrolment"] == 4  # 3 regular + 1 NRI
    assert eval_breakdown["supernumerary_enrolment"] == 2  # 2 TFW
    assert eval_breakdown["nri_count"] == 1
    assert "AICTE_TFW" in eval_breakdown["supernumerary_breakdown"]
    assert eval_breakdown["reservation_breakdown"]["SC"] == 1

def test_missing_approval_snapshot_handling(db):
    inst = db.query(Institution).filter(Institution.aicte_id == "CAP-INST-01").first()

    # Non-existent programme ID
    eval_missing = ApprovalCapacityService.evaluate_programme_capacity(
        db=db,
        institution_id=inst.id,
        programme_id=999999,
        academic_year="2026-27",
        incoming_count=10
    )

    assert eval_missing["has_approval"] is False
    assert eval_missing["is_compliant"] is False
    assert eval_missing["approved_intake"] == 0
    assert "No active approval snapshot" in eval_missing["explanation"]
