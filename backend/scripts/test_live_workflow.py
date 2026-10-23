import urllib.request
import json

# 1. Login as DTU Nodal
login_data = json.dumps({'email': 'nodal.dtu@dtu.ac.in', 'password': 'College@12345'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read())
token = res['access_token']
print('1. DTU Login OK: Token acquired')

# 2. Upload sample_data/valid_admissions_dtu.csv to /uploads/preflight
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
with open('d:/AICTE/sample_data/valid_admissions_dtu.csv', 'rb') as f:
    file_content = f.read()

part1 = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="institution_id"\r\n\r\n1\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="academic_year"\r\n\r\n2026-27\r\n'
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="valid_admissions_dtu.csv"\r\n'
    f'Content-Type: text/csv\r\n\r\n'
).encode('utf-8')
part2 = file_content
part3 = f'\r\n--{boundary}--\r\n'.encode('utf-8')
body = part1 + part2 + part3

req2 = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/uploads/preflight',
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Authorization': f'Bearer {token}'
    }
)
res2 = json.loads(urllib.request.urlopen(req2).read())
print('2. Preflight Upload Result:', res2)

# 3. Commit batch
batch_id = res2['batch_id']
commit_req = urllib.request.Request(
    f'http://127.0.0.1:8000/api/v1/uploads/{batch_id}/commit',
    data=json.dumps({'skip_errors': True}).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
)
res3 = json.loads(urllib.request.urlopen(commit_req).read())
print('3. Commit Batch Result:', res3)

# 4. Central Admin Login and Review
admin_login = json.dumps({'email': 'aicte.admin@pramaan.gov.in', 'password': 'Admin@12345'}).encode('utf-8')
req_adm = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=admin_login, headers={'Content-Type': 'application/json'})
admin_token = json.loads(urllib.request.urlopen(req_adm).read())['access_token']

review_req = urllib.request.Request(
    f'http://127.0.0.1:8000/api/v1/uploads/{batch_id}/review',
    data=json.dumps({'decision': 'APPROVED', 'notes': 'Verified seat matrix and admission guidelines.'}).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {admin_token}'
    }
)
res4 = json.loads(urllib.request.urlopen(review_req).read())
print('4. AICTE Review Approval Result:', res4)
