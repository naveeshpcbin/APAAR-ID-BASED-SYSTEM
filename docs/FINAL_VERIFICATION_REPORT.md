# PRAMAAN-AICTE — Implementation & Verification Report

**Project**: PRAMAAN-AICTE  
**Problem Statement**: SIH26263 — Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions  
**Theme**: Smart Automation | **Category**: Software  
**Team**: TCE_Yquanto  

---

## 1. Executive Summary

This report documents the resolution of all identified errors and the delivery of the complete interactive workflow requested for PRAMAAN-AICTE:

1. **`opendemo` Launcher**: Updated to launch **only** the authentication landing page (`http://localhost:3000/login`) in the default browser. Removed previous multi-tab launching.
2. **Manual Authentication Flow**: Removed auto-redirection on `/login`. Evaluators and users can now choose between **College Portal** and **AICTE Central Portal**, enter their email and password manually, and navigate directly to their respective workspaces.
3. **Supabase Cloud Database & Reference Registry ("SuboBase")**: Delivered hybrid synchronization adapter ([`SupabaseAdapter`](file:///d:/AICTE/backend/app/adapters/supabase_adapter.py)) with live status indicators and synchronization actions on the Reference Data workspace ([`/reference-data`](file:///d:/AICTE/frontend/src/app/reference-data/page.tsx)).
4. **In-Browser Interactive Staged Spreadsheet ("Excel Sheet Front of Page")**: Delivered an in-browser spreadsheet grid ([`frontend/src/app/uploads/[batchId]/page.tsx`](file:///d:/AICTE/frontend/src/app/uploads/[batchId]/page.tsx)) allowing college nodal officers to view all staged records, see highlighted error cells, and edit rows inline directly on the website without modifying an external Excel file.
5. **Real-time Deterministic Python Recalculation**: Inline edits trigger real-time Python 3-way reconciliation (`PATCH /api/v1/uploads/{batch_id}/rows/{row_id}`), immediately re-verifying intake limits, APAAR formats, and approval references.
6. **Algorithm Advice Diagnostic Drawer**: Expandable guidance drawer per row displaying the rule ID, failure explanation, and actionable correction guidance.
7. **Return-to-College Regulatory Cycle**: AICTE Central reviewers can return submissions for correction (`RETURNED_FOR_CORRECTION`) with review notes. The college inspects reviewer notes, fixes records inline, and re-submits.
8. **Institutional APAAR Exemption Communication**: Accommodates students who lack an APAAR ID due to UIDAI biometric/iris synchronization delays. College submits an exemption message to AICTE (`POST /api/v1/uploads/{batch_id}/queries`), and AICTE Central grants provisional admission exemption under AICTE Approval Process Handbook (APH 2026-27 Section 4.2).

---

## 2. Architecture & Workflow Matrix

| User Requirement | Architecture Component | Backend Implementation | Frontend UI View |
| :--- | :--- | :--- | :--- |
| **1. Open Demo Launch** | `opendemo.ps1` & `opendemo.bat` | Verified port 8000 health check | Opens single tab: `http://localhost:3000/login` |
| **2. Manual Credentials** | Dual-portal Auth Architecture | `/api/v1/auth/login` | Empty inputs on `/login/college` and `/login/central` |
| **3. SuboBase / Supabase** | Hybrid Cloud Adapter | `SupabaseAdapter` in `supabase_adapter.py` | SuboBase Cloud Card & Sync on `/reference-data` |
| **4. Central Return Batch** | Regulatory Adjudication Engine | `POST /api/v1/uploads/{id}/review` | Return for Correction Banner with reviewer notes |
| **5. Front Spreadsheet** | `StagedBatchRow` DB Table | `GET /api/v1/uploads/{id}/rows` | Interactive table grid in `/uploads/[batchId]` |
| **6. Inline Web Cell Fix** | Staged Storage Sync & Engine | `PATCH /api/v1/uploads/{id}/rows/{row_id}` | Inline inputs + Save & Re-calculate button |
| **7. Algorithm Advice** | `ValidationFinding` Rule Engine | Rule diagnosis mapping per row index | Expandable "Algorithm Advice" card per row |
| **8. Missing APAAR Query** | `BatchDisputeQuery` Audit Trail | `POST /api/v1/uploads/{id}/queries` | "AICTE Exemption" modal + Central approval |

---

## 3. Detailed Technical Implementations

### 3.1. Single-Entry Authentication Page & Manual Login
- **File**: [`frontend/src/app/login/page.tsx`](file:///d:/AICTE/frontend/src/app/login/page.tsx)
- **Problem**: When `opendemo` ran, previous sessions stored in `localStorage` caused `useEffect` to immediately redirect the browser to `/dashboard` or `/uploads`, bypassing the authentication selection.
- **Solution**: Removed the forced automatic `router.replace()`. Added an Active Session Indicator allowing the user to either continue or explicitly switch accounts/sign out. Maintained distinct choices for **College Portal** and **AICTE Central Portal**.
- **Credentials Support**:
  - **DTU Delhi (College Nodal)**: `nodal.dtu@dtu.ac.in` / `College@12345`
  - **COEP Pune (College Nodal)**: `nodal.coep@coep.ac.in` / `College@12345`
  - **AICTE Central Admin**: `aicte.admin@pramaan.gov.in` / `Admin@12345`
  - **AICTE Regional Office (WRO)**: `ro.mumbai@aicte.gov.in` / `Officer@12345`

### 3.2. SuboBase (Supabase Cloud Database & Registry Adapter)
- **File**: [`backend/app/adapters/supabase_adapter.py`](file:///d:/AICTE/backend/app/adapters/supabase_adapter.py)
- **Status API**: `GET /api/v1/reference-data/supabase/status`
- **Sync API**: `POST /api/v1/reference-data/supabase/sync`
- **Capabilities**:
  - Provides cloud-backed REST synchronization with Supabase PostgreSQL.
  - Supports hybrid fallback to the authoritative local database (`pramaan.db`) in WAL mode when offline.
  - Interactive UI card on [`/reference-data`](file:///d:/AICTE/frontend/src/app/reference-data/page.tsx) displays live connection status, synced record count, and cloud sync trigger.

### 3.3. In-Browser Interactive Staged Spreadsheet Grid
- **Database Model**: `StagedBatchRow` in [`backend/app/models/__init__.py`](file:///d:/AICTE/backend/app/models/__init__.py)
- **Endpoints**:
  - `GET /api/v1/uploads/{batch_id}/rows`: Returns all staged records with current status and linked findings.
  - `PATCH /api/v1/uploads/{batch_id}/rows/{row_id}`: Performs inline updates on `student_name`, `apaar_id`, `programme_code`, `category`, `gender`, `admission_quota`, and `dob`. Updates backing CSV storage and executes real-time Python reconciliation.
- **Frontend Component**: [`frontend/src/app/uploads/[batchId]/page.tsx`](file:///d:/AICTE/frontend/src/app/uploads/[batchId]/page.tsx)
  - Color-coded rows: Rose (`BLOCKING_ERROR`), Amber (`REQUIRES_REVIEW`), Teal (`EXEMPTED`), Purple (`EXEMPTION_REQUESTED`).
  - Inline editing inputs appear when clicking "Edit", and saving triggers an instant recalculation without page reload.

### 3.4. Algorithm Advice & Rule Diagnosis
- Evaluates 7 deterministic admission reconciliation rules:
  1. `RULE_MANDATORY_FIELDS`: Mandatory student identity fields.
  2. `RULE_BATCH_DUPLICATE`: Within-batch duplicate identification.
  3. `RULE_APAAR_FORMAT`: 12-digit numeric format and Verhoeff checksum.
  4. `RULE_PROGRAMME_APPROVED`: Comparison against AICTE Sanctioned Programmes.
  5. `RULE_INTAKE_CAPACITY`: Comparison against Sanctioned Approval Intake limits.
  6. `RULE_CATEGORY_SANCTION`: Quota and category allocation compliance.
  7. `RULE_CROSS_INSTITUTION_CONFLICT`: Multi-institutional dual-enrolment detection.
- When an evaluator or college officer clicks "Algorithm Advice", a card expands detailing the rule ID, submitted vs. expected values, and recommended correction.

### 3.5. Institutional AICTE Exemption Communication for Missing APAAR
- **Problem**: Certain genuine students may lack an APAAR ID during admission deadlines due to biometric/iris capture synchronization delays at Aadhaar Seva Kendras.
- **Regulatory Clause**: AICTE Approval Process Handbook (APH 2026-27 Section 4.2) allows provisional admission subject to institutional verification.
- **Workflow**:
  1. College clicks "AICTE Exemption" on the student row in the spreadsheet.
  2. Modal opens to compose an official query/message with category and justification.
  3. `POST /api/v1/uploads/{batch_id}/queries` logs the request in the audit ledger.
  4. AICTE Central Reviewers inspect queries on the batch review page.
  5. AICTE Central grants provisional exemption via `PATCH /api/v1/uploads/{batch_id}/queries/{query_id}/resolve`.
  6. Row status transitions to `EXEMPTED`. The mandatory APAAR check is downgraded to an informational notice, unblocking batch approval.

---

## 4. Test & Verification Results

### 4.1. Automated Backend Tests
All 50 tests across the test suite passed with 0 failures:

```
tests\test_inline_editing_and_disputes.py ...                            [ 6%]
tests\test_login_workflow.py .......                                     [20%]
tests\test_persistence_and_transactions.py ..                            [24%]
tests\test_reconciliation_workflow.py .........                          [42%]
tests\test_security_and_tenant_isolation.py ....                         [50%]
tests\test_verification_receipts_and_certificates.py ....                [58%]
tests\test_anomalies.py .....                                            [68%]
tests\test_audit_hash_chain.py ....                                      [76%]
tests\test_batch_review.py .....                                         [86%]
tests\test_conflicts.py .......                                          [100%]

====================== 50 passed, 20 warnings in 15.24s =======================
```

### 4.2. Frontend Build & Static Analysis
Compiled all 20 static and dynamic routes with **Exit Code 0**:
- `/login`: 200 OK
- `/login/college`: 200 OK
- `/login/central`: 200 OK
- `/uploads`: 200 OK
- `/uploads/[batchId]`: 200 OK
- `/reference-data`: 200 OK

---

## 5. How to Run the Demonstration

1. Open PowerShell and run:
   ```powershell
   .\opendemo
   ```
2. The browser opens **only** `http://localhost:3000/login`.
3. Choose **College Portal** or **AICTE Central Portal**.
4. Enter credentials manually:
   - **College**: `nodal.dtu@dtu.ac.in` / `College@12345`
   - **Central**: `aicte.admin@pramaan.gov.in` / `Admin@12345`
5. On the College Workspace (`/uploads`), open any batch to inspect the interactive spreadsheet:
   - View error row highlights in rose/amber.
   - Click **Algorithm Advice** to view the diagnosis.
   - Click **Edit** on a row, update the value, and click **Save**.
   - Click **AICTE Exemption** on a student without an APAAR ID to send an exemption message to AICTE.
6. Switch to AICTE Central Portal to review exemption queries, grant provisional exemptions, or return batches with reviewer notes.
