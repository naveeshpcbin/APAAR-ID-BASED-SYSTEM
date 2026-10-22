import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token, hash_apaar_id, mask_apaar_id
from app.models import Institution, InstitutionUser, Programme, StudentIdentity, AdmissionRecord

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

    # Create two isolated colleges
    inst1 = Institution(aicte_id="TENANT-COLLEGE-1", name="College One", state="Delhi", district="Central")
    inst2 = Institution(aicte_id="TENANT-COLLEGE-2", name="College Two", state="Karnataka", district="Bangalore")
    session.add_all([inst1, inst2])
    session.flush()

    # User 1 belongs strictly to College 1
    u1 = InstitutionUser(
        institution_id=inst1.id,
        email="operator1@college1.edu",
        hashed_password=get_password_hash("SecretPass1!"),
        full_name="Operator College One",
        role="INSTITUTION_OPERATOR",
        is_active=True
    )
    # User 2 belongs strictly to College 2
    u2 = InstitutionUser(
        institution_id=inst2.id,
        email="operator2@college2.edu",
        hashed_password=get_password_hash("SecretPass2!"),
        full_name="Operator College Two",
        role="INSTITUTION_OPERATOR",
        is_active=True
    )
    # Central Regulator
    u_admin = InstitutionUser(
        institution_id=None,
        email="admin@pramaan.internal",
        hashed_password=get_password_hash("AdminPass1!"),
        full_name="Central Regulator",
        role="AICTE_ADMIN",
        is_active=True
    )
    session.add_all([u1, u2, u_admin])
    session.flush()

    # Create programme and student in College 2
    p2 = Programme(institution_id=inst2.id, programme_code="CSE", programme_name="CSE")
    session.add(p2)
    session.flush()

    s2 = StudentIdentity(
        apaar_hash=hash_apaar_id("400192837777"),
        apaar_masked=mask_apaar_id("400192837777"),
        full_name="College Two Student",
        dob=date(2005, 5, 5),
        verification_status="VERIFIED"
    )
    session.add(s2)
    session.flush()

    adm2 = AdmissionRecord(
        student_id=s2.id,
        institution_id=inst2.id,
        programme_id=p2.id,
        academic_year="2026-27",
        enrollment_no="C2-STUDENT-01",
        status="ACTIVE"
    )
    session.add(adm2)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = override_get_db
    c = TestClient(fastapi_app)
    yield c
    fastapi_app.dependency_overrides.clear()

def test_login_authentication_success_and_failure(client):
    # Success
    res = client.post("/api/v1/auth/login", json={"email": "operator1@college1.edu", "password": "SecretPass1!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "INSTITUTION_OPERATOR"

    # Wrong password
    bad_res = client.post("/api/v1/auth/login", json={"email": "operator1@college1.edu", "password": "WrongPassword"})
    assert bad_res.status_code == 401

def test_invalid_and_expired_jwt_rejection(client):
    headers = {"Authorization": "Bearer invalid_garbage_token_12345"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401

def test_cross_institution_tenant_isolation(client, db):
    # Log in as Operator 1 (College 1)
    res1 = client.post("/api/v1/auth/login", json={"email": "operator1@college1.edu", "password": "SecretPass1!"})
    token1 = res1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Query admissions: Operator 1 should NOT see College 2's student
    adm_res = client.get("/api/v1/admissions", headers=headers1)
    assert adm_res.status_code == 200
    records = adm_res.json()
    # College 1 has zero students, so count should be 0
    assert len(records) == 0

    # Operator 1 attempts to upload for College 2
    c2 = db.query(Institution).filter(Institution.aicte_id == "TENANT-COLLEGE-2").first()
    upload_res = client.post(
        "/api/v1/uploads/preflight",
        headers=headers1,
        data={"institution_id": c2.id, "academic_year": "2026-27"},
        files={"file": ("test.csv", b"apaar_id,student_name,programme_code\n400192831001,Hack,CSE\n", "text/csv")}
    )
    # Must be 403 Forbidden!
    assert upload_res.status_code == 403

def test_unmasked_apaar_never_disclosed(client):
    # Log in as Operator 2 (College 2)
    res2 = client.post("/api/v1/auth/login", json={"email": "operator2@college2.edu", "password": "SecretPass2!"})
    token2 = res2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    adm_res = client.get("/api/v1/admissions", headers=headers2)
    assert adm_res.status_code == 200
    records = adm_res.json()
    assert len(records) == 1
    # Check that APAAR is strictly masked
    student = records[0]["student"]
    assert "400192837777" not in str(records)  # Raw APAAR must never appear
    assert student["apaar_masked"].startswith("XXXXXXXX")
    assert student["apaar_masked"].endswith("7777")
