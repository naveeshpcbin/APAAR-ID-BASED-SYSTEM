import io
import pytest
import pandas as pd
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Institution, Programme, UploadBatch, AdmissionRecord, StudentIdentity, ValidationFinding
from app.services.reconciliation_engine import ReconciliationEngine

# In-memory test engine with StaticPool
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
    # Seed college and programmes
    inst = Institution(aicte_id="INGEST-INST-01", name="Ingestion Test College", state="Delhi", district="New Delhi")
    session.add(inst)
    session.flush()

    p1 = Programme(institution_id=inst.id, programme_code="BTECH-CSE", programme_name="Computer Science")
    p2 = Programme(institution_id=inst.id, programme_code="BTECH-ECE", programme_name="Electronics")
    session.add_all([p1, p2])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_valid_csv_ingestion_and_preflight(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    csv_data = (
        "apaar_id,student_name,programme_code,dob,gender,enrollment_no,category,quota\n"
        "400192831001,Amit Sharma,BTECH-CSE,2005-06-12,MALE,ENR-001,OPEN,STATE_GOVT\n"
        "400192831002,Pooja Verma,BTECH-ECE,2005-09-20,FEMALE,ENR-002,OBC_NCL,STATE_GOVT\n"
    ).encode("utf-8")

    result = engine.parse_and_validate_preflight(
        file_bytes=csv_data,
        filename="valid_students.csv",
        institution_id=inst.id,
        academic_year="2026-27"
    )

    assert result["total_rows"] == 2
    assert result["valid_rows"] == 2
    assert result["error_rows"] == 0
    assert result["status"] == "PREFLIGHT"

def test_idempotent_duplicate_upload(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    csv_data = "apaar_id,student_name,programme_code\n400192831003,Same File,BTECH-CSE\n".encode("utf-8")

    res1 = engine.parse_and_validate_preflight(
        file_bytes=csv_data,
        filename="idempotent.csv",
        institution_id=inst.id,
        academic_year="2026-27"
    )
    batch_id = res1["batch_id"]

    # Commit first batch
    engine.commit_batch(batch_id=batch_id, user_id=1, user_email="op@test.edu", user_role="INSTITUTION_OPERATOR")

    # Second upload with identical file hash
    res2 = engine.parse_and_validate_preflight(
        file_bytes=csv_data,
        filename="idempotent.csv",
        institution_id=inst.id,
        academic_year="2026-27"
    )
    assert res2.get("idempotent") is True
    assert res2.get("batch_id") == batch_id
    assert res2.get("status") == "COMMITTED"

def test_duplicate_apaar_within_batch(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    # Two rows with identical APAAR ID
    csv_data = (
        "apaar_id,student_name,programme_code\n"
        "400192831010,Student One,BTECH-CSE\n"
        "400192831010,Student Duplicate,BTECH-CSE\n"
    ).encode("utf-8")

    result = engine.parse_and_validate_preflight(
        file_bytes=csv_data,
        filename="dup_batch.csv",
        institution_id=inst.id,
        academic_year="2026-27"
    )

    assert result["error_rows"] >= 1
    rule_ids = [f["rule_id"] for f in result["findings_preview"]]
    assert "RULE_WITHIN_BATCH_DUPLICATE" in rule_ids

def test_malformed_and_missing_mandatory_fields(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    # Missing mandatory header
    bad_csv = "random_header_one,random_header_two\nval1,val2\n".encode("utf-8")
    with pytest.raises(ValueError, match="Missing mandatory mapped fields"):
        engine.parse_and_validate_preflight(
            file_bytes=bad_csv,
            filename="missing_headers.csv",
            institution_id=inst.id,
            academic_year="2026-27"
        )

def test_excel_file_ingestion(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    # Generate genuine binary Excel workbook in memory
    df = pd.DataFrame([
        {"apaar_id": "400192831020", "student_name": "Excel Student", "programme_code": "BTECH-CSE", "dob": "2005-01-01"},
        {"apaar_id": "400192831021", "student_name": "Excel Student 2", "programme_code": "BTECH-ECE", "dob": "2005-02-02"}
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_bytes = output.getvalue()

    result = engine.parse_and_validate_preflight(
        file_bytes=excel_bytes,
        filename="test_upload.xlsx",
        institution_id=inst.id,
        academic_year="2026-27"
    )

    assert result["total_rows"] == 2
    assert result["error_rows"] == 0
    assert result["valid_rows"] == 2

def test_commit_batch_persistence_and_rollback(db):
    engine = ReconciliationEngine(db=db)
    inst = db.query(Institution).filter(Institution.aicte_id == "INGEST-INST-01").first()

    csv_data = (
        "apaar_id,student_name,programme_code,enrollment_no\n"
        "400192831050,Commit Student,BTECH-CSE,ENR-COMMIT-01\n"
    ).encode("utf-8")

    preflight = engine.parse_and_validate_preflight(
        file_bytes=csv_data,
        filename="commit_test.csv",
        institution_id=inst.id,
        academic_year="2026-27"
    )
    b_id = preflight["batch_id"]

    commit_res = engine.commit_batch(
        batch_id=b_id,
        user_id=1,
        user_email="operator@test.edu",
        user_role="INSTITUTION_OPERATOR"
    )
    assert commit_res["status"] == "COMMITTED"
    assert commit_res["committed_valid_records"] >= 1

    # Verify actual persistence in AdmissionRecord
    adm = db.query(AdmissionRecord).filter(AdmissionRecord.batch_id == b_id).first()
    assert adm is not None
    assert adm.enrollment_no == "ENR-COMMIT-01"
    assert adm.student is not None
    assert adm.student.full_name == "Commit Student"
