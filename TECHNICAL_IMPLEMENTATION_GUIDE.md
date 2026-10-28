# PRAMAAN-AICTE: Technical Implementation & Architecture Reference Guide

> **Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network**  
> **Smart India Hackathon 2026 | Problem Statement SIH26263**  
> *"Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions"*

---

## 1. Executive Summary & Problem Statement Compliance Matrix

The All India Council for Technical Education (AICTE) currently faces student record fragmentation across thousands of approved polytechnics, engineering colleges, and management institutes. While PGDM institutions submit annual records, undergraduate and postgraduate technical colleges historically provided aggregate statistical numbers during annual approval renewals. This creates critical governance vulnerabilities:

1. Ghost admissions and artificial capacity hoarding.
2. Inability to prevent concurrent dual admissions across state and central universities.
3. Lack of tamper-proof verification for corporate employers and foreign universities.
4. Vulnerability to quota manipulation in supernumerary categories (NRI, OCI, FN, TFW).

**PRAMAAN-AICTE** resolves these vulnerabilities by anchoring every academic record to the **Automated Permanent Academic Account Registry (APAAR)** 12-digit national identifier, enforced through a **Deterministic 3-Way Reconciliation Engine** and secured by **Ed25519 cryptographic signatures** and an append-only **SHA-256 hash-chain audit ledger**.

### Problem Description Requirements Compliance Matrix

| # | Official AICTE Requirement | System Implementation & Architecture Module | Status | Verification Reference |
|---|-----------------------------|---------------------------------------------|:------:|------------------------|
| **1** | **Secure platform/API for student-level upload using APAAR ID** | Dual-portal Next.js 14 + FastAPI architecture; institution-scoped authenticated upload pipeline; batch staging sandbox. | **COMPLETE** | `backend/app/api/v1/uploads.py` & `frontend/src/app/uploads/page.tsx` |
| **2** | **Full field coverage: Approved Intake, Enrolment, Supernumerary Seats, NRI, OCI, FN** | Explicit schema models for 15+ student dimensions: Approved vs. Declared intake, supernumerary category, NRI/OCI/FN flags, quota codes. | **COMPLETE** | `backend/app/models/admission.py` & `backend/app/models/institution.py` |
| **3** | **Automated validation: Duplicates, invalid/missing APAAR, intake breaches, cross-college conflicts** | Ingestion Header Normalizer, Verhoeff checksum validation, capacity ceiling enforcement, and central cross-institution conflict detector. | **COMPLETE** | `backend/app/services/reconciliation.py` & `backend/tests/test_all_gates.py` |
| **4** | **Real-time monitoring dashboards for AICTE and institutions** | AICTE National Executive Command Center (`/dashboard`) and Institutional Admissions Console (`/admissions`, `/approvals`). | **COMPLETE** | `frontend/src/app/dashboard/page.tsx` & `frontend/src/app/admissions/page.tsx` |
| **5** | **Secure verification mechanism for AICTE, colleges, employers, and regulators** | Role-Based Access Control (RBAC) with 4 distinct personas; public zero-PII employer verification portal with token lookups. | **COMPLETE** | `backend/app/api/v1/verification.py` & `frontend/src/app/verification/page.tsx` |
| **6** | **Verifiable student records linked to academic identity** | Ed25519 asymmetric cryptographic signing; signed tamper-proof JSON-LD verification receipts; high-density 2D QR codes. | **COMPLETE** | `backend/app/core/crypto.py` & `frontend/src/app/verification/receipt/[token]/page.tsx` |
| **7** | **Integration / API capability with existing AICTE and institutional ERPs** | RESTful API with automated OpenAPI 3.1 / Swagger docs at `/docs`; dual-mode JWT bearer authentication and batch webhooks. | **COMPLETE** | `http://127.0.0.1:8000/docs` & `backend/app/main.py` |
| **8** | **Data security, privacy, RBAC, audit trails, and consent mechanisms** | Privacy-preserving HMAC-SHA256 APAAR indexing; cryptographic SHA-256 hash-chain audit ledger; strict tenant isolation. | **COMPLETE** | `backend/app/core/audit.py` & `frontend/src/app/audit/page.tsx` |
| **9** | **Generation of reports for policy-making, accreditation, and monitoring** | Dual-mode authenticated export engine for National Admissions, Cross-College Conflicts, and Sanctioned Intake Compliance CSVs. | **COMPLETE** | `backend/app/api/v1/reports.py` & `frontend/src/app/reports/page.tsx` |
| **10** | **Printing/display of APAAR ID with student ID on degree certificates** | Institutional Certificate Printing Engine formatting APAAR ID, College Roll No, Enrollment Date, and Ed25519 verification QR. | **COMPLETE** | `frontend/src/app/admissions/certificate/[id]/page.tsx` |

---

## 2. End-to-End System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Frontend Client Layer (Next.js 14 App Router)"]
        UI_Central["AICTE National Command Center (/dashboard)"]
        UI_College["Institutional Ingestion Portal (/uploads, /admissions)"]
        UI_Verifier["Authorized Verifier Portal (/verification)"]
        UI_Cert["Certificate Printing Engine (/admissions/certificate/[id])"]
    end

    subgraph APILayer["API & Security Layer (FastAPI + Pydantic v2)"]
        AuthModule["OAuth2 / JWT Engine (Bcrypt + RBAC Guards)"]
        Normalizer["Resilient Ingestion Normalizer (Fuzzy Column Mapping)"]
        CryptoEngine["Ed25519 Curve25519 Digital Signing Engine"]
        HashChainLedger["SHA-256 Tamper-Evident Hash Chain Ledger"]
    end

    subgraph BusinessEngine["Reconciliation & Governance Core"]
        Verhoeff["APAAR Checksum Validator (Verhoeff Dihedral D5)"]
        ApprovalRules["Versioned AICTE Intake Ceiling Enforcer"]
        ConflictEngine["Cross-Institution Duplicate Detection Engine"]
        AnomalyEngine["Statistical Intake Spike & Quota Skew Scorer"]
    end

    subgraph DataLayer["Relational Storage Layer"]
        DB[("Supabase PostgreSQL / Local WAL SQLite")]
        T_Users["users & roles"]
        T_Institutions["institutions & programmes"]
        T_Approvals["approval_snapshots"]
        T_Batches["upload_batches & staged_rows"]
        T_Students["students & admissions"]
        T_Conflicts["conflict_cases & hearing_logs"]
        T_Audit["audit_events (Hash Chain)"]
        T_Receipts["verification_receipts"]
    end

    ClientLayer --> APILayer
    APILayer --> BusinessEngine
    BusinessEngine --> DataLayer
```

---

## 3. Core Feature Deep Dive & Technical Explanation

### Feature 1: Dual-Portal Architecture & Multi-Role RBAC
- **Technical Implementation**: Implemented in [`backend/app/core/security.py`](file:///d:/AICTE/backend/app/core/security.py) and [`frontend/src/context/AuthContext.tsx`](file:///d:/AICTE/frontend/src/context/AuthContext.tsx).
- **Access Roles**:
  1. `CENTRAL_ADMIN`: Full national governance over all states, institutions, conflict hearings, anomaly alerts, and export pipelines.
  2. `REGIONAL_OFFICER`: Regional oversight (e.g. WRO Mumbai, NRO Delhi) for localized institutional monitoring.
  3. `COLLEGE_NODAL`: Strict tenant isolation; can only view and stage student data for their assigned institution code (e.g. `DTU-DEL-01`).
  4. `VERIFIER`: Restricted zero-PII corporate access for academic credentials verification.
- **Security Boundary**: The backend enforces dependency injection via `get_current_active_user` and `require_role(["CENTRAL_ADMIN"])`. Attempts by institutional users to access central endpoints yield HTTP 403 Forbidden with cryptographic audit logging.

### Feature 2: Smart Ingestion & Resilient Column Normalizer
- **Technical Implementation**: Located in [`backend/app/services/reconciliation.py`](file:///d:/AICTE/backend/app/services/reconciliation.py).
- **Explanation**: Institutions maintain vastly different spreadsheet nomenclature across ERP systems. The smart normalizer dynamically matches headers using fuzzy alias dictionaries:
  - `apaar_id` aliases: `apaar`, `apaar_number`, `national_id`, `abc_id`, `student_apaar`
  - `student_name` aliases: `name`, `candidate_name`, `full_name`, `student`
  - `programme_code` aliases: `branch`, `course`, `stream`, `department`, `programme`
  - `category` aliases: `social_category`, `reservation_category`, `caste_category`
  - `supernumerary` aliases: `quota`, `seat_type`, `nri_status`, `fn_flag`
- **Validation Pipeline**: Ingestion occurs in a staged quarantine table (`staged_rows`). Only rows passing syntax, identity, and capacity checks are committed to the central master repository upon institution submission.

### Feature 3: Verhoeff Checksum & APAAR Identity Verification
- **Technical Implementation**: Located in [`backend/app/services/reconciliation.py`](file:///d:/AICTE/backend/app/services/reconciliation.py).
- **Explanation**: APAAR IDs are 12-digit national identifiers utilizing the **Verhoeff checksum algorithm** (based on the dihedral group $D_5$ permutations) to prevent transcription and transposition errors.
- **Verification Adapter**: The system implements a deterministic `MockApaarAdapter` that simulates the National Academic Depository (NAD) / ABC DigiLocker gateway with distinct simulated statuses:
  - `VERIFIED`: Name and DOB match government records.
  - `DEMOGRAPHIC_MISMATCH`: APAAR ID is valid, but the student's name or date of birth differs from national records.
  - `RECORD_NOT_FOUND`: Checksum passes but ID is not registered in the central depository.
  - `GATEWAY_TIMEOUT`: Simulates transient network resilience.

### Feature 4: Versioned AICTE Approval Capacity & Intake Ceiling Engine
- **Technical Implementation**: Governed by [`backend/app/models/institution.py`](file:///d:/AICTE/backend/app/models/institution.py) and verified in `backend/tests/test_identity_and_approval_rules.py`.
- **Explanation**: Every approved institution has an immutable AICTE Approval Order specifying:
  - `approved_intake`: Absolute sanctioned capacity for regular general/reserved students.
  - `supernumerary_quota`: Specific caps for Tuition Fee Waiver (TFW 5%), Kashmiri Migrants (KM), NRI (15%), and Foreign Nationals (FN).
- **Enforcement Logic**: When an institution stages admissions exceeding sanctioned capacity, the Reconciliation Engine flags the batch with an `EXCESS_ENROLMENT` violation (Severity: `ERROR`). Staged rows are quarantined, blocking batch commitment until excess seats are resolved.

### Feature 5: Central Cross-Institution Conflict Detection & Resolution Workflow
- **Technical Implementation**: Located in [`backend/app/api/v1/conflicts.py`](file:///d:/AICTE/backend/app/api/v1/conflicts.py) and [`frontend/src/app/conflicts/page.tsx`](file:///d:/AICTE/frontend/src/app/conflicts/page.tsx).
- **Explanation**: Identifies concurrent full-time admissions where the same APAAR ID is claimed by multiple institutions across different states (e.g. DTU Delhi and COEP Pune).
- **Resolution Workflow**:
  1. Automated detection triggers a `CONFLICT_DETECTED` event and generates a conflict case (e.g. `CONF-2026-0042`).
  2. Both institutions receive a dispute notice and upload admission proof (allotment order, fee receipt, physical reporting timestamp).
  3. AICTE Central Admin reviews claims side-by-side on `/conflicts` and executes a one-click administrative ruling, locking the verified admission and revoking the conflicting claim.

### Feature 6: Explainable Anomaly Detection Engine
- **Technical Implementation**: Located in [`backend/app/services/reconciliation.py`](file:///d:/AICTE/backend/app/services/reconciliation.py) and [`backend/app/api/v1/anomalies.py`](file:///d:/AICTE/backend/app/api/v1/anomalies.py).
- **Explanation**: Operates on transparent, auditable statistical heuristics rather than opaque black-box models:
  - **Intake Surge Clustering**: Flags institutions uploading more than 80% of their intake within 24 hours of the deadline.
  - **Quota Skew Index**: Flags abnormal ratios in supernumerary or management quotas relative to historical baselines.
  - **Demographic Variance**: Flags clusters of out-of-state or unusual age distributions.
- **Anomaly Cases**: Each flagged anomaly produces an investigation case (`ANOM-YYYY-XXXX`) with explainable metric breakdowns and risk severity scoring (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### Feature 7: Ed25519 Cryptographic Verification Receipts & PII-Safe QR Codes
- **Technical Implementation**: Implemented in [`backend/app/core/crypto.py`](file:///d:/AICTE/backend/app/core/crypto.py) using the `PyNaCl` library.
- **Explanation**: Solves academic credential forgery for corporate employers and verification agencies:
  1. The backend maintains an asymmetric **Ed25519** (Edwards-curve Digital Signature Algorithm, Curve25519) keypair.
  2. For any verified admission, an authorized officer can issue a signed verification receipt.
  3. The receipt generates a tamper-evident payload containing student roll number, college code, intake year, and cryptographic signature.
  4. The public verification URL (`/verification/receipt/[token]`) contains **zero student PII** in the query string or URL path.
  5. Employers scan the high-density QR code to verify the Ed25519 digital signature against AICTE's public key in sub-second latency.

### Feature 8: SHA-256 Tamper-Evident Hash Chain Audit Ledger
- **Technical Implementation**: Implemented in [`backend/app/core/audit.py`](file:///d:/AICTE/backend/app/core/audit.py) and visualized in [`frontend/src/app/audit/page.tsx`](file:///d:/AICTE/frontend/src/app/audit/page.tsx).
- **Explanation**: To ensure legal defensibility and prevent insider database tampering, all critical state changes are committed to a cryptographic hash chain:
  $$\text{Hash}_n = \text{SHA256}(\text{Index}_n \parallel \text{Timestamp}_n \parallel \text{Action}_n \parallel \text{Actor}_n \parallel \text{Details}_n \parallel \text{Hash}_{n-1})$$
- **Integrity Verification**: Clicking **"Verify Hash Chain Integrity"** on `/audit` walks the entire sequence from Genesis Block 0 to the current event, mathematically recomputing every hash to certify that zero records have been deleted, modified, or reordered.

### Feature 9: Privacy-Preserving HMAC-SHA256 APAAR Indexing
- **Technical Implementation**: In accordance with the Digital Personal Data Protection (DPDP) Act 2023, plain 12-digit APAAR numbers are never indexed or exposed in raw form in searchable public logs.
- **Masking Strategy**: The UI displays masked representations (`XXXX-XXXX-9012`). In the database, fast lookups use a keyed `apaar_hash` generated via HMAC-SHA256 using a server-side pepper, protecting student privacy even in the event of an unauthorized read-only database dump.

### Feature 10: Institutional Certificate Support & Regulatory Export Engine
- **Technical Implementation**: Built in [`frontend/src/app/admissions/certificate/[id]/page.tsx`](file:///d:/AICTE/frontend/src/app/admissions/certificate/[id]/page.tsx) and [`backend/app/api/v1/reports.py`](file:///d:/AICTE/backend/app/api/v1/reports.py).
- **Certificate Printing**: Provides an AICTE-compliant degree certificate template displaying the student's name, college roll number, degree programme, and prominent APAAR ID, embedded with the Ed25519 verification QR code for instant offline/online authenticity checks.
- **Reporting Engine**: Dual-mode authenticated endpoints supporting both `Authorization: Bearer <JWT>` headers and `?token=<JWT>` direct download tokens:
  - National Admissions Roster (`/reports/admissions.csv`)
  - Cross-Institution Conflicts Report (`/reports/conflicts.csv`)
  - Institutional Sanctioned Intake Compliance Report (`/reports/compliance.csv`)

---

## 4. Full-Stack Codebase Organization

```
d:\AICTE\
├── backend/
│   ├── app/
│   │   ├── api/v1/                     # FastAPI Modular Endpoints
│   │   │   ├── admissions.py           # Student records & pagination
│   │   │   ├── anomalies.py            # AICTE anomaly alerts & triage
│   │   │   ├── audit.py                # Hash-chain audit ledger & integrity check
│   │   │   ├── auth.py                 # OAuth2 login & persona role switcher
│   │   │   ├── conflicts.py            # Cross-institution duplicate resolution
│   │   │   ├── dashboard.py            # AICTE National & College KPI aggregates
│   │   │   ├── institutions.py         # Institutional approvals & programmes
│   │   │   ├── reports.py              # Regulatory CSV/PDF export endpoints
│   │   │   ├── uploads.py              # Staged batch ingestion & pre-flight validator
│   │   │   └── verification.py         # Ed25519 receipt generation & verification
│   │   ├── core/
│   │   │   ├── audit.py                # SHA-256 hash-chain implementation
│   │   │   ├── config.py               # Pydantic v2 Settings & environment bindings
│   │   │   ├── crypto.py               # Ed25519 digital signatures & QR encoding
│   │   │   ├── database.py             # SQLAlchemy session & URL sanitization
│   │   │   └── security.py             # Password hashing, JWT tokens, RBAC dependencies
│   │   ├── models/                     # SQLAlchemy Relational Models (20 tables)
│   │   ├── schemas/                    # Pydantic v2 Request/Response validation models
│   │   ├── services/                   # 3-Way Reconciliation & Verhoeff validation
│   │   └── main.py                     # FastAPI application setup & CORS configuration
│   ├── scripts/
│   │   ├── seed_data.py                # Synthetic institutional test data generator
│   │   └── setup_supabase.py           # Automated Supabase migration & setup script
│   ├── tests/                          # 59 Automated Pytest tests (6 acceptance gates)
│   ├── requirements.txt                # Python backend dependencies
│   └── supabase_schema.sql             # Full DDL schema script for Supabase SQL Editor
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js 14 App Router Pages (21 routes)
│   │   │   ├── admissions/             # Institutional enrolled student roster
│   │   │   ├── anomalies/              # AICTE anomaly inspection cases
│   │   │   ├── approvals/              # Approved intake capacity view
│   │   │   ├── audit/                  # SHA-256 hash-chain ledger page
│   │   │   ├── conflicts/              # Cross-college duplicate resolution page
│   │   │   ├── dashboard/              # National Executive Dashboard
│   │   │   ├── reports/                # Regulatory downloads & KPI exports
│   │   │   ├── uploads/                # Batch upload & staged row editor
│   │   │   └── verification/           # Public Ed25519 QR verification portal
│   │   ├── components/                 # Reusable Gov-Tech UI design tokens & layouts
│   │   ├── context/                    # React Context (AuthContext & role switching)
│   │   └── lib/                        # API client, fetch interceptors, and tokens
│   └── package.json                    # Next.js, Tailwind CSS, Lucide dependencies
└── README.md                           # Quickstart & system documentation
```

---

## 5. Supabase Cloud Database Integration Guide

The system supports two parallel methods to connect to Supabase Cloud (`xvuqedqfdeybryvbablt`):

### Method A: Automated Python Migration Script
The project includes a dedicated migration utility: [`backend/scripts/setup_supabase.py`](file:///d:/AICTE/backend/scripts/setup_supabase.py). It automatically handles password URL-encoding (e.g. converting `@` in passwords to `%40`), tests database connectivity, creates all 20 relational tables, and migrates existing local records.

```powershell
# Run the automated setup script pointing to your Supabase Transaction Pooler URI:
.\backend\venv\Scripts\python .\backend\scripts\setup_supabase.py --db-url "postgresql://postgres.xvuqedqfdeybryvbablt:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres"
```

> [!NOTE]
> Supabase direct connections (`db.xvuqedqfdeybryvbablt.supabase.co:5432`) resolve via IPv6. On standard IPv4 network connections, always use the Supabase **Transaction Pooler** URI (`aws-0-[REGION].pooler.supabase.com:6543`) from your Supabase Dashboard under **Project Settings → Database → Connection Pooling**.

### Method B: Direct Supabase SQL Editor Execution
To set up Supabase Cloud directly without network proxy or IPv6 configuration:
1. Open your browser and navigate to: [https://supabase.com/dashboard/project/xvuqedqfdeybryvbablt/sql](https://supabase.com/dashboard/project/xvuqedqfdeybryvbablt/sql).
2. Open the file [`backend/supabase_schema.sql`](file:///d:/AICTE/backend/supabase_schema.sql) in your editor.
3. Copy the entire contents of `supabase_schema.sql` and paste them into the Supabase SQL Editor.
4. Click **Run**.
5. All 20 tables, primary keys, foreign key constraints, indexes, Row-Level Security (RLS) policies, and reference seed data will be created instantly.

### Supabase MCP Server Integration
Your Antigravity MCP configuration is permanently configured in `~/.gemini/antigravity/mcp_config.json`:
```json
{
  "mcpServers": {
    "supabase": {
      "serverUrl": "https://mcp.supabase.com/mcp?project_ref=xvuqedqfdeybryvbablt&read_only=true&features=docs%2Caccount%2Cdatabase%2Cdebugging%2Cdevelopment%2Cfunctions%2Cbranching"
    }
  }
}
```
Supabase Agent Skills are installed in `.agents/skills/supabase` and `.agents/skills/supabase-postgres-best-practices`.

---

## 6. Verification & Quality Assurance Summary

### Pytest Automated Test Suite (100% Pass)
The test suite in [`backend/tests`](file:///d:/AICTE/backend/tests) verifies all 6 functional acceptance gates specified by the AICTE problem statement:
- **Gate 1**: Header normalizer resilience across arbitrary CSV/Excel column orders.
- **Gate 2**: Deterministic APAAR validation & Verhoeff checksum calculation.
- **Gate 3**: Strict sanctioned intake ceiling & supernumerary quota isolation.
- **Gate 4**: Central cross-institution duplicate admission detection.
- **Gate 5**: Explainable statistical anomaly scoring.
- **Gate 6**: Ed25519 digital signature generation, verification, and hash-chain ledger continuity.

**Verification Command**:
```powershell
.\backend\venv\Scripts\pytest .\backend\tests -o pythonpath=backend -v
```
**Result**: `59 passed in 13.53s` (Zero failures, zero regressions).

### Next.js Frontend Production Build
**Verification Command**:
```powershell
npm run build --prefix frontend
```
**Result**: `✓ Compiled successfully`, `21 of 21 routes pre-rendered with zero TypeScript or hydration errors`.

---

## 7. Evaluator Testing & Live Demonstration Guide

### Quick Demonstration Credentials

The platform features an instant **Role Switcher** in the top navigation bar, allowing evaluators to switch personas with one click:

| Role / Persona | Email | Password | Primary Demonstration Responsibility |
| :--- | :--- | :--- | :--- |
| **AICTE Central Admin** | `aicte.admin@pramaan.gov.in` | `Admin@12345` | Nationwide intake compliance, cross-college conflict adjudication, and audit. |
| **Regional Officer (WRO)** | `ro.mumbai@aicte.gov.in` | `Officer@12345` | Regional monitoring and college hearing management. |
| **DTU Delhi (Nodal Officer)** | `nodal.dtu@dtu.ac.in` | `College@12345` | College student batch uploads, staged row editing, and pre-flight validation. |
| **COEP Pune (Nodal Officer)** | `nodal.coep@coep.ac.in` | `College@12345` | Upload batch history and cross-college duplicate claim verification. |
| **Authorized Verifier** | `verifier.corp@tcs.com` | `Verify@12345` | Employer zero-PII student verification and QR receipt scanning. |

### Step-by-Step Evaluator Walkthrough

1. **National Intake Compliance (`http://localhost:3000/dashboard`)**:
   - Log in as **AICTE Central Admin**.
   - Review live national KPIs: Approved Intake vs. Verified Enrolments, Quota Breakdown (TFW, NRI, FN), and Anomaly Risk Index.
2. **Student Data Ingestion & Pre-Flight Validation (`http://localhost:3000/uploads`)**:
   - Switch persona to **DTU Delhi Nodal Officer**.
   - Click **Upload Admissions Batch** and select a student CSV.
   - Observe automatic column header mapping and instant row-level validation findings (Severity: `ERROR`, `WARNING`, `INFO`).
3. **Cross-Institution Duplicate Adjudication (`http://localhost:3000/conflicts`)**:
   - Switch back to **AICTE Central Admin**.
   - Open case **`CONF-2026-0042`** (student claimed concurrently by COEP Pune and DTU Delhi).
   - Inspect side-by-side claim timestamps and allotment orders, then click **Resolve Dispute**.
4. **Explainable Anomaly Inspection (`http://localhost:3000/anomalies`)**:
   - Navigate to `/anomalies`.
   - Open case **`ANOM-2026-0019`** (89% intake surge near deadline flagged at RVCE).
   - Review transparent statistical deviation scores and explainable rationale.
5. **Ed25519 Cryptographic Receipt & QR Verification (`http://localhost:3000/verification`)**:
   - Issue a digital verification receipt for any verified student.
   - Scan or click through to `/verification/receipt/[token]` to witness sub-second cryptographic signature verification with zero student PII exposed.
6. **Tamper-Evident SHA-256 Audit Ledger (`http://localhost:3000/audit`)**:
   - Navigate to `/audit`.
   - Click **"Verify Hash Chain Integrity"**.
   - Watch the system cryptographically recompute every block hash from Genesis Block 0 to present, displaying the green verification seal.
7. **Certificate Printing (`http://localhost:3000/admissions`)**:
   - Select an enrolled student and click **Print Degree Certificate**.
   - Preview the official degree certificate featuring student roll number, verified APAAR ID, and the Ed25519 verification QR code.
8. **Regulatory Policy Reports (`http://localhost:3000/reports`)**:
   - Navigate to `/reports`.
   - Download the National Admissions Roster, Conflicts Audit, or Intake Compliance CSV with dual-mode JWT bearer authentication.

