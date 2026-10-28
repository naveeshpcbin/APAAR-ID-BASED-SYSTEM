import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_college_nodal_login_success():
    """Verify college user authenticates and receives institutional membership."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nodal.dtu@dtu.ac.in",
        "password": "College@12345"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "INSTITUTION_NODAL"
    assert data["institution_id"] is not None
    assert "Delhi Technological University" in data["institution_name"]
    assert data["email"] == "nodal.dtu@dtu.ac.in"

def test_central_admin_login_success():
    """Verify AICTE central admin authenticates and receives central role."""
    res = client.post("/api/v1/auth/login", json={
        "email": "aicte.admin@pramaan.gov.in",
        "password": "Admin@12345"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "AICTE_ADMIN"
    assert data["institution_id"] is None
    assert data["email"] == "aicte.admin@pramaan.gov.in"

def test_login_invalid_password_rejected():
    """Verify wrong password returns 401 Unauthorized."""
    res = client.post("/api/v1/auth/login", json={
        "email": "nodal.dtu@dtu.ac.in",
        "password": "WrongPassword!123"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_login_nonexistent_user_rejected():
    """Verify non-existent user returns 401 Unauthorized."""
    res = client.post("/api/v1/auth/login", json={
        "email": "fake.user@unknown.ac.in",
        "password": "AnyPassword"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_get_current_user_me_endpoint():
    """Verify /auth/me returns authenticated user details from valid token."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "nodal.dtu@dtu.ac.in",
        "password": "College@12345"
    })
    token = login_res.json()["access_token"]
    
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "nodal.dtu@dtu.ac.in"
    assert user_data["role"] == "INSTITUTION_NODAL"
    assert user_data["institution_id"] is not None

def test_unauthenticated_request_rejected():
    """Verify protected /auth/me fails when no token is supplied."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

def test_college_user_blocked_from_central_reference_registry():
    """Verify college user is blocked by backend RBAC from mutating synthetic reference data."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "nodal.dtu@dtu.ac.in",
        "password": "College@12345"
    })
    token = login_res.json()["access_token"]
    
    res = client.post(
        "/api/v1/reference-data/synthetic-apaar",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "apaar_id": "999999999999",
            "full_name": "Unauthorized Test Record",
            "gender": "MALE",
            "status": "DEMO_REFERENCE_MATCH"
        }
    )
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"] or "Forbidden" in res.json()["detail"]
