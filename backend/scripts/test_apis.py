import httpx
import json

BASE = "http://127.0.0.1:8000/api/v1"

def test_user(email, password, role_name):
    print(f"\n=======================================================")
    print(f"=== Testing Login for {role_name} ({email}) ===")
    print(f"=======================================================")
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        login_resp = client.post(f"{BASE}/auth/login", json={"email": email, "password": password})
        if login_resp.status_code != 200:
            print(f"FAILED LOGIN: {login_resp.status_code} {login_resp.text}")
            return None
        data = login_resp.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Login OK! User: {data.get('full_name')} (Role: {data.get('role')})")
        
        endpoints = [
            ("GET", "/auth/me"),
            ("GET", "/dashboards/metrics?academic_year=2026-27"),
            ("GET", "/institutions"),
            ("GET", "/approvals?academic_year=2026-27"),
            ("GET", "/uploads"),
            ("GET", "/admissions"),
            ("GET", "/conflicts"),
            ("GET", "/anomalies"),
            ("GET", "/audit?limit=20"),
            ("POST", "/audit/verify-chain"),
            ("GET", "/reports/admissions.csv"),
            ("GET", "/reference-data/overview"),
            ("GET", "/reference-data/approvals"),
            ("GET", "/reference-data/declarations"),
            ("GET", "/reference-data/synthetic-apaar"),
            ("GET", "/reference-data/supabase/status"),
            ("GET", "/reference-data/vault/integrity"),
        ]
        failures = 0
        for method, ep in endpoints:
            res = client.request(method, f"{BASE}{ep}", headers=headers)
            status = res.status_code
            if status >= 400:
                print(f"  [ERR] {method:4} {ep:45} -> {status}: {res.text[:120]}")
                failures += 1
            else:
                print(f"  [OK ] {method:4} {ep:45} -> {status}")
        print(f"Completed with {failures} errors for {role_name}")

if __name__ == "__main__":
    test_user("aicte.admin@pramaan.gov.in", "Admin@12345", "AICTE Central Admin")
    test_user("nodal.dtu@dtu.ac.in", "College@12345", "DTU College Nodal Officer")
    test_user("nodal.coep@coep.ac.in", "College@12345", "COEP College Nodal Officer")
    test_user("verifier.corp@tcs.com", "Verify@12345", "Authorized Verifier")
