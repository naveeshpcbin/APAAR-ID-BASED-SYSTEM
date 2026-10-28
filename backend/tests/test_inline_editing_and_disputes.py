import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models import (
    Institution, InstitutionUser, UploadBatch, StagedBatchRow, BatchDisputeQuery,
    Programme, ApprovalSnapshot, InstitutionalDeclaration, SyntheticApaarRecord
)
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clean up test batches & disputes for PSG Tech without deleting other batches
    psg_inst = db.query(Institution).filter(Institution.aicte_id == "1-PSG-TECH-001").first()
    if psg_inst:
        psg_batch_ids = [b[0] for b in db.query(UploadBatch.id).filter(UploadBatch.institution_id == psg_inst.id).all()]
        if psg_batch_ids:
            db.query(BatchDisputeQuery).filter(BatchDisputeQuery.batch_id.in_(psg_batch_ids)).delete(synchronize_session=False)
            db.query(StagedBatchRow).filter(StagedBatchRow.batch_id.in_(psg_batch_ids)).delete(synchronize_session=False)
            db.query(UploadBatch).filter(UploadBatch.id.in_(psg_batch_ids)).delete(synchronize_session=False)
    db.commit()

    # Look up or create test institution
    inst = db.query(Institution).filter(Institution.aicte_id == "1-PSG-TECH-001").first()
    if not inst:
        inst = Institution(
            name="PSG College of Technology",
            aicte_id="1-PSG-TECH-001",
            state="Tamil Nadu",
            district="Coimbatore",
            contact_email="principal@psgtech.edu",
            institution_type="STATE_GOVT_AIDED",
            status="APPROVED"
        )
        db.add(inst)
        db.flush()

    # Look up or create test users
    college_user = db.query(InstitutionUser).filter(InstitutionUser.email == "college@psgtech.edu").first()
    if not college_user:
        college_user = InstitutionUser(
            email="college@psgtech.edu",
            hashed_password=get_password_hash("CollegePSG@2026"),
            full_name="Dr. R. PSG Principal",
            role="INSTITUTION_NODAL_OFFICER",
            institution_id=inst.id,
            is_active=True
        )
        db.add(college_user)

    central_admin = db.query(InstitutionUser).filter(InstitutionUser.email == "admin@aicte-india.org").first()
    if not central_admin:
        central_admin = InstitutionUser(
            email="admin@aicte-india.org",
            hashed_password=get_password_hash("CentralAICTE@2026"),
            full_name="AICTE Central Review Officer",
            role="AICTE_ADMIN",
            institution_id=None,
            is_active=True
        )
        db.add(central_admin)
    db.flush()

    # Look up or create programme
    prog = db.query(Programme).filter(Programme.institution_id == inst.id, Programme.programme_code == "1-01-CSE").first()
    if not prog:
        prog = Programme(
            institution_id=inst.id,
            programme_code="1-01-CSE",
            programme_name="Computer Science and Engineering",
            degree_level="UG"
        )
        db.add(prog)
        db.flush()

    # Create Approval & Declaration
    approval = ApprovalSnapshot(
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        approved_intake=60,
        approval_letter_ref="EOA-2026-PSG-001",
        policy_version="AICTE-APH-2026-27-V1"
    )
    decl = InstitutionalDeclaration(
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year="2026-27",
        declared_intake=60,
        reporting_scope="TOTAL_ENROLMENT"
    )
    db.add(approval)
    db.add(decl)
    db.commit()

    # Auth tokens
    college_token = create_access_token(subject=college_user.id, role=college_user.role, institution_id=college_user.institution_id)
    central_token = create_access_token(subject=central_admin.id, role=central_admin.role, institution_id=central_admin.institution_id)

    yield {
        "db": db,
        "inst": inst,
        "college_user": college_user,
        "central_admin": central_admin,
        "college_token": college_token,
        "central_token": central_token,
        "prog": prog
    }

    db.close()


def test_inline_editing_and_reconciliation_recalc(setup_db):
    """
    Verifies that uploading a batch creates StagedBatchRow records,
    that invalid rows can be corrected inline via PATCH, and that
    the Python reconciliation algorithms recalculate immediately.
    """
    college_token = setup_db["college_token"]
    inst = setup_db["inst"]
    headers = {"Authorization": f"Bearer {college_token}"}

    # Upload CSV with an error in Row 2 (invalid APAAR: "INVALID_APAAR")
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        "123456789012,Aarav Sharma,1-01-CSE,2005-01-15,MALE,OPEN,STATE_GOVT\n"
        "INVALID_APAAR,Priya Sundaram,1-01-CSE,2005-03-20,FEMALE,OBC_NCL,STATE_GOVT\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))

    resp = client.post(
        "/api/v1/uploads/preflight",
        files={"file": ("test_batch.csv", file_obj, "text/csv")},
        data={"institution_id": inst.id, "academic_year": "2026-27"},
        headers=headers
    )
    assert resp.status_code == 200, resp.text
    batch_id = resp.json()["batch_id"]

    # 1. Inspect staged spreadsheet rows
    resp_rows = client.get(f"/api/v1/uploads/{batch_id}/rows", headers=headers)
    assert resp_rows.status_code == 200
    rows = resp_rows.json()["rows"]
    assert len(rows) == 2

    # Row 1 is valid, Row 2 has BLOCKING_ERROR
    row_1 = next(r for r in rows if r["row_index"] == 1)
    row_2 = next(r for r in rows if r["row_index"] == 2)
    assert row_2["status"] == "BLOCKING_ERROR"
    assert any(f["rule_id"] == "RULE_APAAR_FORMAT" for f in row_2["findings"])

    # 2. Perform inline spreadsheet cell fix on Row 2
    patch_resp = client.patch(
        f"/api/v1/uploads/{batch_id}/rows/{row_2['id']}",
        json={"apaar_id": "987654321098"},
        headers=headers
    )
    assert patch_resp.status_code == 200, patch_resp.text
    updated_row = patch_resp.json()["staged_row"]
    assert updated_row["apaar_id"] == "987654321098"
    assert updated_row["status"] != "BLOCKING_ERROR"
    # No more blocking errors for this row
    assert not any(f["rule_id"] == "RULE_APAAR_FORMAT" for f in updated_row["findings"])


def test_missing_apaar_exemption_workflow(setup_db):
    """
    Verifies that for a student without an APAAR ID,
    the institution can submit an exemption query to AICTE,
    the central reviewer can grant provisional exemption,
    and the blocking error is automatically resolved.
    """
    college_token = setup_db["college_token"]
    central_token = setup_db["central_token"]
    inst = setup_db["inst"]
    college_headers = {"Authorization": f"Bearer {college_token}"}
    central_headers = {"Authorization": f"Bearer {central_token}"}

    # Upload CSV where student in Row 1 has missing APAAR
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        ",Karthik Selvan,1-01-CSE,2005-04-12,MALE,OPEN,STATE_GOVT\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))

    resp = client.post(
        "/api/v1/uploads/preflight",
        files={"file": ("missing_apaar.csv", file_obj, "text/csv")},
        data={"institution_id": inst.id, "academic_year": "2026-27"},
        headers=college_headers
    )
    assert resp.status_code == 200
    batch_id = resp.json()["batch_id"]

    # Check rows: Row 1 has missing mandatory APAAR
    resp_rows = client.get(f"/api/v1/uploads/{batch_id}/rows", headers=college_headers)
    rows = resp_rows.json()["rows"]
    row_1 = rows[0]
    assert row_1["status"] == "BLOCKING_ERROR"

    # College submits exemption query to AICTE
    query_resp = client.post(
        f"/api/v1/uploads/{batch_id}/queries",
        json={
            "row_id": row_1["id"],
            "subject": "Student APAAR creation failed due to UIDAI biometric delay",
            "category": "MISSING_APAAR_UIDAI_FAIL",
            "student_identifier": "Karthik Selvan",
            "message": "Student underwent iris recapture at Aadhaar Seva Kendra on 2026-10-15; APAAR generation in progress."
        },
        headers=college_headers
    )
    assert query_resp.status_code == 200, query_resp.text
    query_id = query_resp.json()["id"]

    # AICTE Central Reviewer inspects queries
    list_queries_resp = client.get(f"/api/v1/uploads/{batch_id}/queries", headers=central_headers)
    assert list_queries_resp.status_code == 200
    assert len(list_queries_resp.json()) == 1

    # AICTE Central Reviewer grants provisional exemption
    resolve_resp = client.patch(
        f"/api/v1/uploads/{batch_id}/queries/{query_id}/resolve",
        json={
            "action": "APPROVE_EXEMPTION",
            "reply_message": "Provisional exemption sanctioned under AICTE APH 2026-27 Section 4.2. Verify before end semester."
        },
        headers=central_headers
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["status"] == "PROVISIONALLY_EXEMPTED"

    # Check that Row 1 status is now EXEMPTED and blocking errors dropped to 0
    resp_rows_after = client.get(f"/api/v1/uploads/{batch_id}/rows", headers=college_headers)
    row_after = resp_rows_after.json()["rows"][0]
    assert row_after["status"] == "EXEMPTED"


def test_college_submit_central_return_inline_fix_resubmit(setup_db):
    """
    Verifies the complete circular regulatory cycle:
    1. College commits and submits batch with an intentional error.
    2. Central Government reviews and returns batch to college (RETURNED_FOR_CORRECTION).
    3. College inspects returned batch, sees reviewer notes, fixes the cell inline in the web spreadsheet.
    4. Deterministic algorithms re-evaluate the batch with 0 errors.
    5. College commits & re-submits the corrected batch.
    6. Central Government reviewer approves the batch.
    """
    college_token = setup_db["college_token"]
    central_token = setup_db["central_token"]
    inst = setup_db["inst"]
    college_headers = {"Authorization": f"Bearer {college_token}"}
    central_headers = {"Authorization": f"Bearer {central_token}"}

    # 1. Upload CSV with an invalid programme code
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        "123456789012,Ananya Krishnan,NON_EXISTENT_PROG,2005-06-18,FEMALE,OPEN,STATE_GOVT\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))

    resp = client.post(
        "/api/v1/uploads/preflight",
        files={"file": ("circular_test.csv", file_obj, "text/csv")},
        data={"institution_id": inst.id, "academic_year": "2026-27"},
        headers=college_headers
    )
    assert resp.status_code == 200
    batch_id = resp.json()["batch_id"]

    # College commits & submits batch (with skip_errors=True)
    commit_resp = client.post(
        f"/api/v1/uploads/{batch_id}/commit",
        json={"skip_errors": True},
        headers=college_headers
    )
    assert commit_resp.status_code == 200

    # 2. Central Regulator reviews and returns batch to college
    return_resp = client.post(
        f"/api/v1/uploads/{batch_id}/review",
        json={
            "decision": "RETURNED_FOR_CORRECTION",
            "notes": "Invalid programme code NON_EXISTENT_PROG. Please map to approved programme 1-01-CSE."
        },
        headers=central_headers
    )
    assert return_resp.status_code == 200
    assert return_resp.json()["status"] == "RETURNED_FOR_CORRECTION"
    assert "NON_EXISTENT_PROG" in return_resp.json()["notes"]

    # 3. College inspects batch status
    batch_detail = client.get(f"/api/v1/uploads/{batch_id}", headers=college_headers).json()
    assert batch_detail["batch"]["status"] == "RETURNED_FOR_CORRECTION"
    assert "NON_EXISTENT_PROG" in batch_detail["batch"]["review_notes"]

    # 4. College fixes the cell inline in front of the page without leaving the website
    resp_rows = client.get(f"/api/v1/uploads/{batch_id}/rows", headers=college_headers).json()
    row_1 = resp_rows["rows"][0]
    assert row_1["status"] == "BLOCKING_ERROR"

    patch_resp = client.patch(
        f"/api/v1/uploads/{batch_id}/rows/{row_1['id']}",
        json={"programme_code": "1-01-CSE"},
        headers=college_headers
    )
    assert patch_resp.status_code == 200
    updated_row = patch_resp.json()["staged_row"]
    assert updated_row["programme_code"] == "1-01-CSE"
    assert updated_row["status"] != "BLOCKING_ERROR"

    # 5. College commits and re-submits the corrected batch
    recommit_resp = client.post(
        f"/api/v1/uploads/{batch_id}/commit",
        json={"skip_errors": False},
        headers=college_headers
    )
    assert recommit_resp.status_code == 200
    assert recommit_resp.json()["status"] == "UNDER_REVIEW"

    # 6. Central Reviewer approves the batch
    approve_resp = client.post(
        f"/api/v1/uploads/{batch_id}/review",
        json={
            "decision": "APPROVED",
            "notes": "Corrected programme code verified against AICTE Approval Snapshot. Batch approved."
        },
        headers=central_headers
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"


def test_quick_fix_and_download_csv(setup_db):
    """
    Verifies the one-click quick-fix feature that maps unknown programme codes
    to approved institutional offerings, and downloads the corrected CSV.
    """
    college_token = setup_db["college_token"]
    inst = setup_db["inst"]
    headers = {"Authorization": f"Bearer {college_token}"}

    # Upload CSV with 2 unknown programme errors (BTECH-AI, BTECH-ELEC)
    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        "123456789012,Aryan Deshmukh,1-01-CSE,2005-07-11,MALE,OPEN,STATE_GOVT\n"
        "912345678901,Tanvi Joshi,BTECH-AI,2005-10-03,FEMALE,OBC_NCL,STATE_GOVT\n"
        "923456789012,Sameer Khan,1-01-CSE,2004-05-18,MALE,OPEN,STATE_GOVT\n"
        "934567890123,Meera Rao,BTECH-ELEC,2005-12-22,FEMALE,OPEN,STATE_GOVT\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))

    resp = client.post(
        "/api/v1/uploads/preflight",
        files={"file": ("supernumerary_test.csv", file_obj, "text/csv")},
        data={"institution_id": inst.id, "academic_year": "2026-27"},
        headers=headers
    )
    assert resp.status_code == 200
    batch_id = resp.json()["batch_id"]
    assert resp.json()["error_rows"] == 2

    # Execute quick-fix to map all unknown programmes to '1-01-CSE'
    qf_resp = client.post(
        f"/api/v1/uploads/{batch_id}/quick-fix",
        json={"target_rule": "RULE_UNKNOWN_PROGRAMME", "replacement_value": "1-01-CSE"},
        headers=headers
    )
    assert qf_resp.status_code == 200
    assert qf_resp.json()["fixed_count"] == 2
    assert qf_resp.json()["error_rows"] == 0

    # Verify download of corrected CSV
    dl_resp = client.get(f"/api/v1/uploads/{batch_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"].startswith("text/csv")
    csv_text = dl_resp.text
    assert "BTECH-AI" not in csv_text
    assert "BTECH-ELEC" not in csv_text
    assert "1-01-CSE" in csv_text
    assert "Tanvi Joshi" in csv_text
    assert "Meera Rao" in csv_text


def test_raw_csv_web_editor_update(setup_db):
    """
    Verifies direct in-browser Raw CSV web editor update: modifies raw CSV text,
    re-validates, and updates database records and backing disk file.
    """
    college_token = setup_db["college_token"]
    inst = setup_db["inst"]
    headers = {"Authorization": f"Bearer {college_token}"}

    csv_content = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        "123456789012,Initial Student,INVALID_CODE,2005-01-01,MALE,OPEN,STATE_GOVT\n"
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))

    resp = client.post(
        "/api/v1/uploads/preflight",
        files={"file": ("raw_edit_test.csv", file_obj, "text/csv")},
        data={"institution_id": inst.id, "academic_year": "2026-27"},
        headers=headers
    )
    assert resp.status_code == 200
    batch_id = resp.json()["batch_id"]
    assert resp.json()["error_rows"] == 1

    # Directly update raw CSV text from the website editor
    corrected_raw_csv = (
        "apaar_id,student_name,programme_code,dob,gender,category,admission_quota\n"
        "123456789012,Initial Student,1-01-CSE,2005-01-01,MALE,OPEN,STATE_GOVT\n"
        "987654321098,Second Student,1-01-CSE,2005-02-02,FEMALE,OPEN,STATE_GOVT\n"
    )

    put_resp = client.put(
        f"/api/v1/uploads/{batch_id}/raw",
        json={"csv_content": corrected_raw_csv},
        headers=headers
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["total_rows"] == 2
    assert put_resp.json()["error_rows"] == 0

    # Verify staged rows match new count and content
    rows_resp = client.get(f"/api/v1/uploads/{batch_id}/rows", headers=headers)
    assert rows_resp.status_code == 200
    rows = rows_resp.json()["rows"]
    assert len(rows) == 2
    assert rows[1]["student_name"] == "Second Student"
    assert rows[1]["programme_code"] == "1-01-CSE"


