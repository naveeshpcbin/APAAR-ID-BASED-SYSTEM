import io
import pytest
import pandas as pd
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import (
    Institution, InstitutionUser, Programme, ApprovalSnapshot,
    InstitutionalDeclaration, SyntheticApaarRecord, UploadBatch,
    ValidationRun, ValidationFinding, AdmissionRecord, StudentIdentity,
    AdmissionConflict, AuditEvent
)
from app.core.security import get_password_hash, create_access_token, hash_apaar_id, mask_apaar_id
from app.services.reconciliation_engine import ReconciliationEngine

# In-memory test engine
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # 1. Seed Institutions
    inst1 = Institution(id=1, aicte_id="1-DTU-001", name="Delhi Technological University", state="Delhi", district="North West Delhi", institution_type="STATE_GOVT_AIDED", status="APPROVED")
    inst2 = Institution(id=2, aicte_id="1-COEP-002", name="COEP Technological University", state="Maharashtra", district="Pune", institution_type="STATE_GOVT_AIDED", status="APPROVED")
    db.add_all([inst1, inst2])
    db.flush()

    # 2. Seed Users
    admin_user = InstitutionUser(
        id=1, email="admin@aicte.gov.in", hashed_password=get_password_hash("AdminPass123!"),
        full_name="AICTE Central Reviewer", role="AICTE_ADMIN", institution_id=None, is_active=True
    )
    dtu_user = InstitutionUser(
        id=2, email="nodal@dtu.ac.in", hashed_password=get_password_hash("CollegePass123!"),
        full_name="DTU Nodal Officer", role="INSTITUTION_NODAL", institution_id=1, is_active=True
    )
    coep_user = InstitutionUser(
        id=3, email="nodal@coep.ac.in", hashed_password=get_password_hash("CollegePass123!"),
        full_name="COEP Nodal Officer", role="INSTITUTION_NODAL", institution_id=2, is_active=True
    )
    db.add_all([admin_user, dtu_user, coep_user])
    db.flush()

    # 3. Seed Programmes
    prog1 = Programme(id=1, institution_id=1, programme_code="BTECH-CSE", programme_name="Computer Science & Engineering", degree_level="UG", duration_years=4)
    prog2 = Programme(id=2, institution_id=2, programme_code="BTECH-CSE", programme_name="Computer Engineering", degree_level="UG", duration_years=4)
    db.add_all([prog1, prog2])
    db.flush()

    # 4. Seed Approval Snapshots (Baseline intake = 100)
    appr1 = ApprovalSnapshot(
        id=1, institution_id=1, programme_id=1, academic_year="2026-27",
        approved_intake=100, supernumerary_quota={"TFW": 5, "EWS": 10},
        approval_letter_ref="AICTE/EOA/2026/DTU-CSE", policy_version="AICTE-APH-2026-V1"
    )
    db.add(appr1)
    db.flush()

    # 5. Seed Institutional Declarations (Baseline declared = 100)
    decl1 = InstitutionalDeclaration(
        id=1, institution_id=1, programme_id=1, academic_year="2026-27",
        declared_intake=100, reporting_scope="ALL", declaration_ref="DECL-DTU-2026-CSE"
    )
    db.add(decl1)
    db.flush()

    # 6. Seed Synthetic APAAR Reference Registry
    synth1 = SyntheticApaarRecord(
        id=1, apaar_id="400192831001", full_name="Aarav Mehta", dob=date(2005, 4, 12),
        gender="MALE", status="DEMO_REFERENCE_MATCH", notes="[DEMO DATA] Baseline verified record"
    )
    synth2 = SyntheticApaarRecord(
        id=2, apaar_id="400192831002", full_name="Ananya Sharma", dob=date(2005, 8, 23),
        gender="FEMALE", status="DEMO_REFERENCE_MATCH", notes="[DEMO DATA] Baseline verified record"
    )
    synth_conflict = SyntheticApaarRecord(
        id=3, apaar_id="512398459012", full_name="Kunal Singhania", dob=date(2005, 5, 20),
        gender="MALE", status="DEMO_REFERENCE_MATCH", notes="[DEMO DATA] Cross-institution conflict candidate"
    )
    db.add_all([synth1, synth2, synth_conflict])
    db.flush()

    # 7. Seed active admission at COEP for conflict test candidate
    conflict_student = StudentIdentity(
        id=1, apaar_hash=hash_apaar_id("512398459012"), apaar_masked=mask_apaar_id("512398459012"),
        full_name="Kunal Singhania", dob=date(2005, 5, 20), gender="MALE", verification_status="VERIFIED"
    )
    db.add(conflict_student)
    db.flush()

    conflict_adm = AdmissionRecord(
        id=1, student_id=conflict_student.id, institution_id=2, programme_id=2,
        academic_year="2026-27", enrollment_no="COEP/2026/CSE/01", category="OPEN",
        admission_quota="STATE_GOVT", status="ACTIVE"
    )
    db.add(conflict_adm)

    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# =========================================================================
# TEST A: APAAR REFERENCE MUTATION & REVALIDATION
# =========================================================================
def test_a_apaar_reference_mutation_and_revalidation(client, test_db):
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    # 1. Create batch containing synthetic identifier '400192831001'
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,enrollment_no,category,quota\n"
        "400192831001,Aarav Mehta,BTECH-CSE,2005-04-12,MALE,DTU-001,OPEN,STATE_GOVT\n"
    ).encode("utf-8")

    engine = ReconciliationEngine(db=test_db)
    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_content, filename="test_a.csv", institution_id=1, academic_year="2026-27", user_id=2
    )
    batch_id = preflight["batch_id"]

    # Commit the batch
    commit_res = engine.commit_and_submit_batch(batch_id=batch_id, user_id=2, user_email="nodal@dtu.ac.in", user_role="INSTITUTION_NODAL")
    assert commit_res["status"] == "UNDER_REVIEW"

    # Confirm run 1 reports DEMO_REFERENCE_MATCH
    findings_r1 = test_db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id).all()
    finding_types_r1 = [f.finding_type for f in findings_r1]
    assert "DEMO_REFERENCE_MATCH" in finding_types_r1
    assert "NO_DEMO_REFERENCE_MATCH" not in finding_types_r1

    # 2. Authorized admin deletes synthetic reference record from DB
    rec = test_db.query(SyntheticApaarRecord).filter(SyntheticApaarRecord.apaar_id == "400192831001").first()
    del_res = client.delete(f"/api/v1/reference-data/synthetic-apaar/{rec.id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 3. Dynamic Revalidation against updated DB reference state
    reval_res = client.post(f"/api/v1/reference-data/revalidate/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert reval_res.status_code == 200
    data = reval_res.json()
    assert data["run_number"] >= 2

    # 4. Confirm new validation run reports NO_DEMO_REFERENCE_MATCH!
    finding_types_r2 = [f["finding_type"] for f in data["findings"]]
    assert "NO_DEMO_REFERENCE_MATCH" in finding_types_r2
    assert "DEMO_REFERENCE_MATCH" not in finding_types_r2


# =========================================================================
# TEST B: APPROVED INTAKE CAPACITY MUTATION & REVALIDATION
# =========================================================================
def test_b_approved_intake_change_revalidation(client, test_db):
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    # 1. Batch contains 2 student records, baseline capacity is 100 (compliant)
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,enrollment_no,category,quota\n"
        "400192831001,Aarav Mehta,BTECH-CSE,2005-04-12,MALE,DTU-001,OPEN,STATE_GOVT\n"
        "400192831002,Ananya Sharma,BTECH-CSE,2005-08-23,FEMALE,DTU-002,OPEN,STATE_GOVT\n"
    ).encode("utf-8")

    engine = ReconciliationEngine(db=test_db)
    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_content, filename="test_b.csv", institution_id=1, academic_year="2026-27", user_id=2
    )
    batch_id = preflight["batch_id"]
    engine.commit_and_submit_batch(batch_id=batch_id, user_id=2, user_email="nodal@dtu.ac.in", user_role="INSTITUTION_NODAL")

    # Initial run: No intake capacity error
    findings_r1 = test_db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id).all()
    assert "INTAKE_CAPACITY_EXCEEDED" not in [f.finding_type for f in findings_r1]

    # 2. Admin lowers capacity to 1 in DB through Reference Management API
    approval = test_db.query(ApprovalSnapshot).filter(ApprovalSnapshot.institution_id == 1, ApprovalSnapshot.programme_id == 1).first()
    update_res = client.put(
        f"/api/v1/reference-data/approvals/{approval.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approved_intake": 1}
    )
    assert update_res.status_code == 200
    assert update_res.json()["approved_intake"] == 1

    # 3. Dynamic Revalidation against updated DB reference state
    reval_res = client.post(f"/api/v1/reference-data/revalidate/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert reval_res.status_code == 200
    findings_r2 = reval_res.json()["findings"]

    # 4. Confirm new run dynamically detected INTAKE_CAPACITY_EXCEEDED!
    intake_findings = [f for f in findings_r2 if f["finding_type"] == "INTAKE_CAPACITY_EXCEEDED"]
    assert len(intake_findings) == 1
    assert "Intake capacity exceeded" in intake_findings[0]["message"]
    assert intake_findings[0]["expected_value"] == "1"


# =========================================================================
# TEST C: INSTITUTIONAL DECLARATION MUTATION & REVALIDATION
# =========================================================================
def test_c_institutional_declaration_mutation_and_revalidation(client, test_db):
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    # 1. 2 student records uploaded, declaration initially set to 2
    decl = test_db.query(InstitutionalDeclaration).filter(InstitutionalDeclaration.institution_id == 1, InstitutionalDeclaration.programme_id == 1).first()
    decl.declared_intake = 2
    test_db.commit()

    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,enrollment_no,category,quota\n"
        "400192831001,Aarav Mehta,BTECH-CSE,2005-04-12,MALE,DTU-001,OPEN,STATE_GOVT\n"
        "400192831002,Ananya Sharma,BTECH-CSE,2005-08-23,FEMALE,DTU-002,OPEN,STATE_GOVT\n"
    ).encode("utf-8")

    engine = ReconciliationEngine(db=test_db)
    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_content, filename="test_c.csv", institution_id=1, academic_year="2026-27", user_id=2
    )
    batch_id = preflight["batch_id"]
    engine.commit_and_submit_batch(batch_id=batch_id, user_id=2, user_email="nodal@dtu.ac.in", user_role="INSTITUTION_NODAL")

    # Initial check: discrepancy is 0 (2 submitted - 2 declared)
    runs = test_db.query(ValidationRun).filter(ValidationRun.batch_id == batch_id).all()
    assert runs[-1].declared_discrepancy == 0

    # 2. Modify declaration to 5 in DB
    update_res = client.put(
        f"/api/v1/reference-data/declarations/{decl.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"declared_intake": 5}
    )
    assert update_res.status_code == 200

    # 3. Dynamic Revalidation against updated DB reference state
    reval_res = client.post(f"/api/v1/reference-data/revalidate/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert reval_res.status_code == 200
    disposition = reval_res.json()["disposition"]

    # 4. Discrepancy is now -3 (2 submitted - 5 declared)
    assert disposition["declared_intake"] == 5
    assert disposition["declared_discrepancy"] == -3
    decl_findings = [f for f in reval_res.json()["findings"] if f["finding_type"] == "DECLARATION_DISCREPANCY"]
    assert len(decl_findings) == 1
    assert "Discrepancy: -3" in decl_findings[0]["message"]


# =========================================================================
# TEST D: INVALID REFERENCE EDIT REJECTION & PRESERVATION
# =========================================================================
def test_d_invalid_reference_edit_rejected(client, test_db):
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    # 1. Negative approved intake rejection
    appr = test_db.query(ApprovalSnapshot).filter(ApprovalSnapshot.id == 1).first()
    orig_intake = appr.approved_intake

    res_neg_intake = client.put(
        f"/api/v1/reference-data/approvals/{appr.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approved_intake": -50}
    )
    assert res_neg_intake.status_code == 422
    # Verify previous value was preserved
    test_db.refresh(appr)
    assert appr.approved_intake == orig_intake

    # 2. Invalid APAAR format rejection (not 12 digits)
    res_bad_apaar = client.post(
        "/api/v1/reference-data/synthetic-apaar",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"apaar_id": "12345", "full_name": "Bad Candidate", "dob": "2005-01-01", "status": "DEMO_REFERENCE_MATCH"}
    )
    assert res_bad_apaar.status_code == 422


# =========================================================================
# TEST E: HISTORICAL TRACEABILITY & MULTI-RUN PRESERVATION
# =========================================================================
def test_e_historical_traceability_across_revalidations(client, test_db):
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    csv_content = (
        "apaar_id,student_name,programme_code\n"
        "400192831001,Aarav Mehta,BTECH-CSE\n"
    ).encode("utf-8")

    engine = ReconciliationEngine(db=test_db)
    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_content, filename="test_e.csv", institution_id=1, academic_year="2026-27", user_id=2
    )
    batch_id = preflight["batch_id"]

    # Run 1: Submission
    engine.commit_and_submit_batch(batch_id=batch_id, user_id=2, user_email="nodal@dtu.ac.in", user_role="INSTITUTION_NODAL")

    # Run 2: Revalidation
    client.post(f"/api/v1/reference-data/revalidate/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Run 3: Another Revalidation
    client.post(f"/api/v1/reference-data/revalidate/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})

    # Retrieve all runs through API
    batch_res = client.get(f"/api/v1/uploads/{batch_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert batch_res.status_code == 200
    batch_data = batch_res.json()

    # Verify all 3 runs are preserved in history
    runs = batch_data["validation_runs_history"]
    assert len(runs) >= 3
    run_numbers = [r["run_number"] for r in runs]
    assert 1 in run_numbers
    assert 2 in run_numbers
    assert 3 in run_numbers


# =========================================================================
# ADDITIONAL INTEGRATION TESTS COVERING ACCEPTANCE CRITERIA 1-26
# =========================================================================
def test_cross_institution_active_conflict_detection(client, test_db):
    """AC 15: Cross-institution active admission conflict detected"""
    # Student 512398459012 is actively enrolled in COEP (inst 2)
    csv_content = (
        "apaar_id,student_name,programme_code\n"
        "512398459012,Kunal Singhania,BTECH-CSE\n"
    ).encode("utf-8")

    engine = ReconciliationEngine(db=test_db)
    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_content, filename="conflict.csv", institution_id=1, academic_year="2026-27", user_id=2
    )
    batch_id = preflight["batch_id"]

    batch_details = client.get(f"/api/v1/uploads/{batch_id}", headers={"Authorization": f"Bearer {create_access_token(subject='1', role='AICTE_ADMIN')}"})
    finding_types = [f["finding_type"] for f in batch_details.json()["findings"]]
    assert "CROSS_INSTITUTION_CONFLICT" in finding_types


def test_college_cannot_approve_own_submission(client, test_db):
    """AC 22: College users cannot approve submissions (403 Forbidden)"""
    college_token = create_access_token(subject="2", role="INSTITUTION_NODAL", institution_id=1)

    batch = UploadBatch(id=99, institution_id=1, filename="test.csv", file_hash="hash99", academic_year="2026-27", status="UNDER_REVIEW")
    test_db.add(batch)
    test_db.commit()

    res = client.post(
        f"/api/v1/uploads/{batch.id}/review",
        headers={"Authorization": f"Bearer {college_token}"},
        json={"decision": "APPROVED", "notes": "Self-approval"}
    )
    assert res.status_code == 403


def test_tenant_isolation_college_cannot_view_other_college_batch(client, test_db):
    """AC 23: Tenant isolation: One institution cannot view another's records"""
    coep_token = create_access_token(subject="3", role="INSTITUTION_NODAL", institution_id=2)

    batch_dtu = UploadBatch(id=88, institution_id=1, filename="dtu.csv", file_hash="hash88", academic_year="2026-27", status="UNDER_REVIEW")
    test_db.add(batch_dtu)
    test_db.commit()

    res = client.get(f"/api/v1/uploads/{batch_dtu.id}", headers={"Authorization": f"Bearer {coep_token}"})
    assert res.status_code == 403


def test_audit_event_recorded_on_review_adjudication(client, test_db):
    """AC 26: Audit events recorded into SHA-256 hash chain for critical changes"""
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=None)

    batch = UploadBatch(id=77, institution_id=1, filename="clean.csv", file_hash="hash77", academic_year="2026-27", status="UNDER_REVIEW")
    test_db.add(batch)
    test_db.commit()

    res = client.post(
        f"/api/v1/uploads/{batch.id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVED", "notes": "Formally sanctioned"}
    )
    assert res.status_code == 200

    # Verify audit event
    audit_ev = test_db.query(AuditEvent).filter(AuditEvent.entity_id == str(batch.id), AuditEvent.action == "BATCH_APPROVED").first()
    assert audit_ev is not None
    assert audit_ev.actor_email == "admin@aicte.gov.in"
    assert audit_ev.current_hash is not None
