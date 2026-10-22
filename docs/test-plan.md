# Test Plan & Automated Verification Gates: PRAMAAN-AICTE

## 1. Overview & Verification Strategy

PRAMAAN-AICTE is tested across 7 strict acceptance gates spanning backend unit/integration tests, security boundary validation, cryptographic assertions, and browser-driven end-to-end workflows.

---

## 2. Gate-by-Gate Specification

| Gate | Category | Test Target | Verification Command / Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Gate 1** | Environment & Foundation | Health (`/api/v1/health`), Readiness (`/api/v1/health/ready`), DB connection pool. | `pytest backend/tests/test_all_gates.py::test_gate1_health_readiness` | **PASSED** |
| **Gate 2** | Identity & Security | Password hashing, JWT creation/verification, keyed HMAC APAAR hashing, identifier masking (`XXXXXXXX1234`). | `pytest backend/tests/test_all_gates.py::test_gate2_security_primitives` | **PASSED** |
| **Gate 3** | Data Ingestion | 12-digit APAAR validation, missing fields detection, within-batch duplicate flagging, mock adapter simulations. | `pytest backend/tests/test_all_gates.py::test_gate3_apaar_adapter_and_rules` | **PASSED** |
| **Gate 4** | Rules & Capacity | Versioned `ApprovalSnapshot` retrieval, approved intake calculation, overage detection, quota isolation. | `pytest backend/tests/test_all_gates.py::test_gate4_approval_capacity_calculation` | **PASSED** |
| **Gate 5** | Duplicate Conflicts | Multi-institution active enrolment collision detection, case assignment (`CONF-2026-0042`), case resolution. | `pytest backend/tests/test_all_gates.py::test_gate5_conflict_detection` | **PASSED** |
| **Gate 6** | Trust & Cryptography | Ed25519 signature generation, public verification, forged token rejection, SHA-256 hash-chain verification. | `pytest backend/tests/test_all_gates.py::test_gate6_signed_receipts_and_hash_chain` | **PASSED** |
| **Gate 7** | Full Browser Workflow | Dashboard rendering, conflict adjudication, anomaly escalation, QR receipt generation, live ledger verification. | Antigravity Browser Subagent (`pramaan_full_workflow_1792686961959.webp`) | **VERIFIED** |

---

## 3. Test Execution Instructions

### Running Backend Pytest Suite
```powershell
# From workspace root
.\backend\venv\Scripts\pytest .\backend\tests\test_all_gates.py -o pythonpath=backend -v
```

### Running Seed Data Script
```powershell
.\backend\venv\Scripts\python .\backend\scripts\seed_data.py
```
