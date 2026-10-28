import urllib.request
import urllib.error
import json

vercel_url = 'https://pramaan-aicte.vercel.app'
backend_url = 'https://apaar-id-based-system.onrender.com/api/v1'

results = {}

# 1. Frontend Homepage
try:
    req = urllib.request.Request(vercel_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        results['1_frontend_root'] = (resp.status == 200, f'HTTP {resp.status}')
except Exception as e:
    results['1_frontend_root'] = (False, str(e))

# 2. College & Central Login Pages
for page in ['/login/college', '/login/central']:
    try:
        req = urllib.request.Request(f'{vercel_url}{page}', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            has_content = len(body) > 500
            name = page.replace('/', '_')
            results[f'2_page{name}'] = (resp.status == 200 and has_content, f'HTTP {resp.status}, bytes={len(body)}')
    except Exception as e:
        results[f'2_page_{page}'] = (False, str(e))

# 3. Invalid credentials rejected by live API
try:
    payload = json.dumps({'email': 'nodal.dtu@dtu.ac.in', 'password': 'WrongPassword!999'}).encode()
    req = urllib.request.Request(f'{backend_url}/auth/login', data=payload, headers={'Content-Type': 'application/json', 'Origin': vercel_url})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results['3_invalid_login_rejected'] = (False, 'Unexpected 200 OK')
    except urllib.error.HTTPError as he:
        results['3_invalid_login_rejected'] = (he.code == 401, f'HTTP {he.code} Rejected as Expected')
except Exception as e:
    results['3_invalid_login_rejected'] = (False, str(e))

# 4. Valid College Login
college_token = None
try:
    payload = json.dumps({'email': 'nodal.dtu@dtu.ac.in', 'password': 'College@12345'}).encode()
    req = urllib.request.Request(f'{backend_url}/auth/login', data=payload, headers={'Content-Type': 'application/json', 'Origin': vercel_url})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        college_token = data.get('access_token')
        role = data.get('role')
        inst_name = data.get('institution_name', '')
        results['4_college_login'] = (resp.status == 200 and role == 'INSTITUTION_NODAL', f'HTTP 200, Role={role}, Institution={inst_name}')
except Exception as e:
    results['4_college_login'] = (False, str(e))

# 5. Valid Central Login
central_token = None
try:
    payload = json.dumps({'email': 'aicte.admin@pramaan.gov.in', 'password': 'Admin@12345'}).encode()
    req = urllib.request.Request(f'{backend_url}/auth/login', data=payload, headers={'Content-Type': 'application/json', 'Origin': vercel_url})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        central_token = data.get('access_token')
        role = data.get('role')
        results['5_central_login'] = (resp.status == 200 and role == 'AICTE_ADMIN', f'HTTP 200, Role={role}')
except Exception as e:
    results['5_central_login'] = (False, str(e))

# 6. Role-Based Access Enforcement
try:
    # College token hitting Central reference data overview -> MUST BE 403 Forbidden
    req = urllib.request.Request(f'{backend_url}/reference-data/overview', headers={'Authorization': f'Bearer {college_token}', 'Origin': vercel_url})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results['6_rbac_enforcement'] = (False, 'College user was unexpectedly allowed central access!')
    except urllib.error.HTTPError as he:
        college_blocked = (he.code == 403)
        # Central token hitting Central reference data overview -> MUST BE 200 OK
        req2 = urllib.request.Request(f'{backend_url}/reference-data/overview', headers={'Authorization': f'Bearer {central_token}', 'Origin': vercel_url})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            central_allowed = (resp2.status == 200)
            results['6_rbac_enforcement'] = (college_blocked and central_allowed, f'College 403={college_blocked}, Central 200={central_allowed}')
except Exception as e:
    results['6_rbac_enforcement'] = (False, str(e))

# 7. Live CORS Configuration Check
try:
    req = urllib.request.Request(f'{backend_url}/health', method='OPTIONS', headers={
        'Origin': vercel_url,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,Authorization'
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        cors_origin = resp.headers.get('Access-Control-Allow-Origin')
        cors_cred = resp.headers.get('Access-Control-Allow-Credentials')
        is_exact = (cors_origin == vercel_url)
        results['7_cors_verification'] = (is_exact and cors_cred == 'true', f'Origin={cors_origin}, Credentials={cors_cred}')
except Exception as e:
    results['7_cors_verification'] = (False, str(e))

# 8. Live Database Preflight Reconciliation Ingestion
try:
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    csv_content = 'student_name,dob,gender,apaar_id,programme,academic_year,enrollment_number\nRahul Sharma,2003-05-15,MALE,123456789012,B.Tech Computer Science,2024-2025,DTU-2024-CS-001\n'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="students.csv"\r\n'
        f'Content-Type: text/csv\r\n\r\n'
        f'{csv_content}\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')
    req = urllib.request.Request(f'{backend_url}/uploads/preflight', data=body, headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Authorization': f'Bearer {college_token}',
        'Origin': vercel_url
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        upload_data = json.loads(resp.read().decode())
        has_batch = 'batch_id' in upload_data or 'total_rows' in upload_data
        batch_id = upload_data.get('batch_id')
        total_rows = upload_data.get('total_rows')
        valid_rows = upload_data.get('valid_rows')
        results['8_live_preflight_upload'] = (resp.status == 200 and has_batch, f'HTTP 200, batch_id={batch_id}, rows={total_rows}, valid={valid_rows}')
except Exception as e:
    results['8_live_preflight_upload'] = (False, str(e))

# 9. Central Portal Retrieves Validation Results & Institutional Registry
try:
    req = urllib.request.Request(f'{backend_url}/institutions', headers={'Authorization': f'Bearer {central_token}', 'Origin': vercel_url})
    with urllib.request.urlopen(req, timeout=10) as resp:
        inst_list = json.loads(resp.read().decode())
        inst_count = len(inst_list)
        results['9_central_portal_retrieval'] = (resp.status == 200 and inst_count == 4, f'HTTP 200, institutions_loaded={inst_count}')
except Exception as e:
    results['9_central_portal_retrieval'] = (False, str(e))

# 10. Application Survives Refresh & Client Route Handling
for route in ['/dashboard', '/admissions', '/uploads', '/audit']:
    try:
        req = urllib.request.Request(f'{vercel_url}{route}', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            r_key = '10_route' + route.replace('/', '_')
            results[r_key] = (resp.status == 200 and len(body) > 500, f'HTTP {resp.status}, size={len(body)}')
    except Exception as e:
        results[f'10_route_{route}'] = (False, str(e))

print('\n============================ VERIFICATION RESULTS ============================')
all_passed = True
for k, (status, detail) in sorted(results.items()):
    status_str = 'PASS' if status else 'FAIL'
    if not status:
        all_passed = False
    print(f'[{status_str}] {k}: {detail}')
print(f'==============================================================================')
print(f'OVERALL STATUS: {"ALL 10 TESTS PASSED" if all_passed else "SOME TESTS FAILED"}')
