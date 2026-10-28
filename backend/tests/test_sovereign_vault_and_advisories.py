"""
PRAMAAN-AICTE: Test Suite for Sovereign Cryptographic Vault,
AICTE Central Advisory Guidance System, and Reference Data Governance.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models import UploadBatch, StagedBatchRow, AicteCentralAdvisory, Programme, ApprovalSnapshot, InstitutionUser
from app.core.security import create_access_token
from app.core.sovereign_vault import SovereignDataVault

client = TestClient(app)

@pytest.fixture
def central_admin_headers():
    db = SessionLocal()
    admin = db.query(InstitutionUser).filter(InstitutionUser.role == "AICTE_ADMIN").first()
    token = create_access_token(subject=admin.id, role=admin.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def college_nodal_headers():
    db = SessionLocal()
    batch = db.query(UploadBatch).filter(UploadBatch.id == 2).first()
    nodal = db.query(InstitutionUser).filter(InstitutionUser.institution_id == batch.institution_id).first()
    token = create_access_token(subject=nodal.id, role=nodal.role, institution_id=nodal.institution_id)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def test_sovereign_vault_integrity_and_sealing(central_admin_headers):
    """Test 1: Sovereign Cryptographic Data Vault computes Merkle root and verifies consensus."""
    db = SessionLocal()
    try:
        vault = SovereignDataVault(db=db)
        digest_info = vault.compute_dataset_digest()
        assert "sovereign_seal" in digest_info
        assert len(digest_info["sovereign_seal"]) == 64  # SHA-256
        assert digest_info["record_counts"]["synthetic_apaar_records"] > 0
        assert digest_info["record_counts"]["approval_snapshots"] > 0

        # Verify via API endpoint
        resp = client.get("/api/v1/reference-data/vault/integrity", headers=central_admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "current_seal" in data

        # Seal vault via API
        seal_resp = client.post("/api/v1/reference-data/vault/seal", headers=central_admin_headers)
        assert seal_resp.status_code == 200
        seal_data = seal_resp.json()
        assert seal_data["success"] is True
        assert "sovereign_seal" in seal_data

        # Post-sealing verification should be VERIFIED
        verify_resp = client.get("/api/v1/reference-data/vault/integrity", headers=central_admin_headers)
        assert verify_resp.status_code == 200
        assert verify_resp.json()["status"] == "VERIFIED"
    finally:
        db.close()


def test_central_advisory_lifecycle(central_admin_headers, college_nodal_headers):
    """Test 2: Central Admin issues an advisory/idea, college views and applies it, auto-reconciling batch."""
    db = SessionLocal()
    try:
        # Check Batch #2 exists
        batch = db.query(UploadBatch).filter(UploadBatch.id == 2).first()
        assert batch is not None, "Batch #2 should exist"

        # Ensure staged rows are synchronized and Tanvi Joshi has BTECH-AI
        from app.services.reconciliation_engine import ReconciliationEngine
        engine = ReconciliationEngine(db)
        engine.get_or_sync_staged_rows(2)
        tanvi_init = db.query(StagedBatchRow).filter(
            StagedBatchRow.batch_id == 2,
            StagedBatchRow.student_name.ilike("%Tanvi%")
        ).first()
        if tanvi_init and tanvi_init.programme_code != "BTECH-AI":
            tanvi_init.programme_code = "BTECH-AI"
            db.commit()

        # 1. Central Admin issues advisory
        payload = {
            "title": "AICTE Guidance: Remap Emerging Branch to Approved CSE Cluster",
            "idea_description": "Under AICTE APH Circular 2026/A-09, college is advised to map artificial intelligence electives into approved BTECH-CSE.",
            "advisory_type": "PROGRAMME_REMAP_RECOMMENDATION",
            "recommended_action": {
                "action": "REMAP_PROGRAMME",
                "from_code": "BTECH-AI",
                "to_code": "BTECH-CSE"
            }
        }
        create_resp = client.post("/api/v1/uploads/2/advisories", json=payload, headers=central_admin_headers)
        assert create_resp.status_code == 201
        adv_data = create_resp.json()
        advisory_id = adv_data["id"]
        assert adv_data["status"] == "ACTIVE"

        # 2. College retrieves advisories
        list_resp = client.get("/api/v1/uploads/2/advisories", headers=college_nodal_headers)
        assert list_resp.status_code == 200
        advisories = list_resp.json()
        assert any(a["id"] == advisory_id for a in advisories)

        # 3. College applies the advisory recommendation
        apply_resp = client.post(f"/api/v1/uploads/2/advisories/{advisory_id}/apply", headers=college_nodal_headers)
        assert apply_resp.status_code == 200
        result = apply_resp.json()
        assert result["success"] is True
        assert result["advisory_status"] == "APPLIED_BY_COLLEGE"

        # Refresh session to see updates committed by the API
        db.expire_all()

        # Check that staged row with BTECH-AI was remapped to BTECH-CSE
        remapped_row = db.query(StagedBatchRow).filter(
            StagedBatchRow.batch_id == 2,
            StagedBatchRow.programme_code == "BTECH-AI"
        ).first()
        assert remapped_row is None, "BTECH-AI should have been remapped to BTECH-CSE"

        # Verify that Tanvi Joshi is now BTECH-CSE
        tanvi = db.query(StagedBatchRow).filter(
            StagedBatchRow.batch_id == 2,
            StagedBatchRow.student_name.ilike("%Tanvi%")
        ).first()
        assert tanvi is not None
        assert tanvi.programme_code == "BTECH-CSE"

    finally:
        db.close()


def test_central_manual_programme_and_approval_creation(central_admin_headers):
    """Test 3: Central Admin manually sanctions a new academic programme and intake capacity."""
    payload = {
        "institution_id": 2,
        "programme_code": "BTECH-ROBOTICS",
        "programme_name": "B.Tech in Robotics & Automation",
        "academic_year": "2026-27",
        "approved_intake": 60,
        "tfw_quota": 3
    }
    resp = client.post("/api/v1/reference-data/programmes-with-approval", json=payload, headers=central_admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["programme_code"] == "BTECH-ROBOTICS"
    assert data["approved_intake"] == 60

    # Verify programme exists in database
    db = SessionLocal()
    try:
        prog = db.query(Programme).filter(
            Programme.institution_id == 2,
            Programme.programme_code == "BTECH-ROBOTICS"
        ).first()
        assert prog is not None
        assert prog.programme_name == "B.Tech in Robotics & Automation"

        appr = db.query(ApprovalSnapshot).filter(
            ApprovalSnapshot.institution_id == 2,
            ApprovalSnapshot.programme_id == prog.id
        ).first()
        assert appr is not None
        assert appr.approved_intake == 60
    finally:
        db.close()
