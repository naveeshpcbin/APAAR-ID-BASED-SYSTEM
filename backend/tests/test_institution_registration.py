"""
Test suite for New College Registration and Institutional Onboarding.
Verifies that ANY AICTE-approved institution can register, configure approved programmes,
and obtain instant isolated access.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models import Institution, InstitutionUser, Programme, ApprovalSnapshot

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def clean_test_institution():
    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.aicte_id == "1-99887766").first()
        if inst:
            # Delete related batches, programmes, approvals, users
            from app.models import UploadBatch, ValidationFinding, ValidationRun, StagedBatchRow
            batches = db.query(UploadBatch).filter(UploadBatch.institution_id == inst.id).all()
            for b in batches:
                db.query(StagedBatchRow).filter(StagedBatchRow.batch_id == b.id).delete()
                db.query(ValidationFinding).filter(ValidationFinding.batch_id == b.id).delete()
                db.query(ValidationRun).filter(ValidationRun.batch_id == b.id).delete()
                db.delete(b)
            db.query(ApprovalSnapshot).filter(ApprovalSnapshot.institution_id == inst.id).delete()
            db.query(Programme).filter(Programme.institution_id == inst.id).delete()
            db.query(InstitutionUser).filter(InstitutionUser.institution_id == inst.id).delete()
            db.delete(inst)
            db.commit()
    finally:
        db.close()
    yield

def test_register_new_institution_success():
    """Test 1: Any AICTE-approved institution registers and obtains isolated credentials."""
    payload = {
        "aicte_id": "1-99887766",
        "name": "Vellore Institute of Technology (VIT)",
        "state": "Tamil Nadu",
        "district": "Vellore",
        "institution_type": "DEEMED_UNIVERSITY",
        "contact_email": "admissions@vit.ac.in",
        "nodal_name": "Dr. K. Ramanathan",
        "nodal_email": "nodal.vit@vit.ac.in",
        "password": "College@Secure123",
        "programme_code": "BTECH-CSE",
        "programme_name": "B.Tech in Computer Science & Engineering",
        "degree_level": "UG",
        "approved_intake": 180,
        "tfw_quota": 9,
        "academic_year": "2026-27"
    }

    resp = client.post("/api/v1/auth/register-institution", json=payload)
    assert resp.status_code == 201, f"Expected 201 Created, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert "access_token" in data
    assert data["role"] == "INSTITUTION_NODAL"
    assert data["email"] == "nodal.vit@vit.ac.in"
    assert data["institution_name"] == "Vellore Institute of Technology (VIT)"
    assert data["aicte_id"] == "1-99887766"

    # Verify database records created
    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.aicte_id == "1-99887766").first()
        assert inst is not None
        assert inst.name == "Vellore Institute of Technology (VIT)"
        assert inst.status == "APPROVED"

        prog = db.query(Programme).filter(Programme.institution_id == inst.id).first()
        assert prog is not None
        assert prog.programme_code == "BTECH-CSE"

        appr = db.query(ApprovalSnapshot).filter(ApprovalSnapshot.institution_id == inst.id).first()
        assert appr is not None
        assert appr.approved_intake == 180

        user = db.query(InstitutionUser).filter(InstitutionUser.email == "nodal.vit@vit.ac.in").first()
        assert user is not None
        assert user.role == "INSTITUTION_NODAL"
    finally:
        db.close()


def test_register_duplicate_aicte_id_rejected():
    """Test 2: Rejecting duplicate registration under an already registered AICTE ID."""
    payload = {
        "aicte_id": "1-99887766",  # Duplicate of test 1
        "name": "Different College Name",
        "state": "Kerala",
        "district": "Kochi",
        "nodal_name": "Dr. Test User",
        "nodal_email": "other.user@college.edu",
        "password": "Password@123"
    }
    resp = client.post("/api/v1/auth/register-institution", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_with_newly_registered_college():
    """Test 3: The newly registered college logs in through standard /auth/login."""
    login_payload = {
        "email": "nodal.vit@vit.ac.in",
        "password": "College@Secure123"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "nodal.vit@vit.ac.in"
    assert data["role"] == "INSTITUTION_NODAL"
    assert data["aicte_id"] == "1-99887766"


def test_generate_web_dataset_and_preflight():
    """Test 4: Generate a dataset on the web platform and run preflight validation."""
    # 1. Login as the newly registered college
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "nodal.vit@vit.ac.in",
        "password": "College@Secure123"
    })
    token = login_resp.json()["access_token"]
    inst_id = login_resp.json()["institution_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Call generate-dataset endpoint
    gen_resp = client.post("/api/v1/uploads/generate-dataset", json={
        "institution_id": inst_id,
        "count": 5,
        "mode": "CLEAN",
        "academic_year": "2026-27"
    }, headers=headers)
    assert gen_resp.status_code == 200
    gen_data = gen_resp.json()
    assert gen_data["success"] is True
    assert gen_data["total_rows"] == 5
    assert len(gen_data["rows"]) == 5
    assert "student_name" in gen_data["csv_content"]

    # 3. Direct preflight upload of the generated CSV content
    import io
    csv_bytes = gen_data["csv_content"].encode("utf-8")
    files = {"file": ("vit_web_generated.csv", io.BytesIO(csv_bytes), "text/csv")}
    data = {"institution_id": inst_id, "academic_year": "2026-27"}

    preflight_resp = client.post("/api/v1/uploads/preflight", data=data, files=files, headers=headers)
    assert preflight_resp.status_code == 200
    preflight_data = preflight_resp.json()
    assert preflight_data["total_rows"] == 5
    assert preflight_data["status"] in ["PREFLIGHT", "VALID", "READY_FOR_COMMIT"]

