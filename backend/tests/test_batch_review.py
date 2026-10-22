import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from datetime import date
from app.main import app
from app.core.database import Base, get_db
from app.models import Institution, InstitutionUser, Programme, UploadBatch, AdmissionRecord, StudentIdentity, AuditEvent
from app.core.security import get_password_hash, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed Institution
    inst = Institution(id=1, aicte_id="1-000000001", name="Delhi Technological University", state="Delhi", district="North Delhi", institution_type="GOVERNMENT")
    db.add(inst)
    
    # Seed Users
    admin_user = InstitutionUser(
        id=1, email="admin@aicte.gov.in", hashed_password=get_password_hash("AdminPass123!"),
        full_name="Central Officer", role="AICTE_ADMIN", institution_id=1, is_active=True
    )
    inst_user = InstitutionUser(
        id=2, email="nodal@dtu.ac.in", hashed_password=get_password_hash("NodalPass123!"),
        full_name="Nodal Officer", role="INSTITUTION_NODAL", institution_id=1, is_active=True
    )
    db.add_all([admin_user, inst_user])

    # Seed Batch & Admission
    batch = UploadBatch(
        id=10, institution_id=1, filename="dtu_admissions_2026.csv",
        file_hash="mockhash123", academic_year="2026-27", status="COMMITTED",
        total_rows=1, valid_rows=1, warning_rows=0, error_rows=0
    )
    db.add(batch)
    db.flush()

    student = StudentIdentity(
        id=1, apaar_hash="dummyhash", apaar_masked="********1234", full_name="Aarav Sharma",
        dob=date(2004, 5, 12), gender="MALE", verification_status="VERIFIED"
    )
    db.add(student)
    db.flush()

    prog = Programme(id=1, institution_id=1, programme_name="CSE", programme_code="CSE-BTECH")
    db.add(prog)
    db.flush()

    adm = AdmissionRecord(
        id=1, student_id=student.id, institution_id=1, programme_id=prog.id,
        batch_id=batch.id, academic_year="2026-27", enrollment_no="DTU-2026-001",
        category="OPEN", admission_quota="STATE_GOVT", nationality_type="DOMESTIC",
        is_supernumerary=False, status="UNDER_REVIEW"
    )
    db.add(adm)
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

def test_batch_review_permissions_and_lifecycle(client, test_db):
    inst_token = create_access_token(subject="2", role="INSTITUTION_NODAL", institution_id=1)
    admin_token = create_access_token(subject="1", role="AICTE_ADMIN", institution_id=1)

    # 1. Institution user attempts to review -> 403 Forbidden
    res_forbidden = client.post(
        "/api/v1/uploads/10/review",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"decision": "APPROVED", "notes": "Self approval attempt"}
    )
    assert res_forbidden.status_code == 403
    assert "Forbidden" in res_forbidden.json()["detail"]

    # 2. Central Admin reviews and approves
    res_approved = client.post(
        "/api/v1/uploads/10/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"decision": "APPROVED", "notes": "Approved after regulatory seat capacity audit."}
    )
    assert res_approved.status_code == 200
    data = res_approved.json()
    assert data["status"] == "APPROVED"
    assert data["decision"] == "APPROVED"

    # 3. Check batch status and admission status updated in DB
    batch = test_db.query(UploadBatch).filter(UploadBatch.id == 10).first()
    assert batch.status == "APPROVED"

    adm = test_db.query(AdmissionRecord).filter(AdmissionRecord.id == 1).first()
    assert adm.status == "ACTIVE"

    # 4. Check audit event recorded
    audit = test_db.query(AuditEvent).filter(
        AuditEvent.action == "BATCH_APPROVED",
        AuditEvent.entity_id == "10"
    ).first()
    assert audit is not None
    assert audit.actor_email == "admin@aicte.gov.in"
    assert audit.metadata_json["decision"] == "APPROVED"
