# PRAMAAN-AICTE — SIH 2026 Presentation Reconstruction, Content Audit and Quality Assurance Report

**Project Name:** PRAMAAN-AICTE (Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network)  
**Problem Statement ID:** SIH26263  
**Problem Statement Title:** Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions  
**Theme:** Smart Automation | **PS Category:** Software  
**Team ID:** TCE_Yquanto  
**Institution:** Thiagarajar College of Engineering, Madurai  
**Audit & QA Date:** 2026-10-28  
**Report Version:** 1.0 (Final SIH 2026 Submission Grade)

---

## Executive Summary

This Quality Assurance (QA) report documents the complete reconstruction and factual audit of the PRAMAAN-AICTE presentation for Smart India Hackathon (SIH) 2026. The presentation was rebuilt from the ground up using native PowerPoint vector shapes and text, adhering strictly to the official SIH 2026 master template and visual design language derived from winning SIH submissions (specifically `sih-winning-ppt-1.pdf`).

All claims, metrics, architecture layers, and test results have been verified directly against the working codebase in the repository (`https://github.com/naveeshpcbin/APAAR-ID-BASED-SYSTEM`). Unverified claims, exaggerated benchmark timings, placeholder domains, and exposed passwords have been completely eliminated.

### Key Deliverables Summary

| Deliverable | File Path | Format & Specifications | Verification Status |
| :--- | :--- | :--- | :---: |
| **Editable Presentation** | `deck/final/PRAMAAN-AICTE_SIH2026_Final.pptx` | Microsoft PowerPoint (.pptx), 16:9 Widescreen (13.333" × 7.500"), Exactly 6 Slides | **VERIFIED** |
| **Vector PDF Export** | `deck/final/PRAMAAN-AICTE_SIH2026_Final.pdf` | High-Resolution Vector PDF Exported via PowerPoint COM | **VERIFIED** |
| **High-Res Slide Images** | `deck/final/slides/slide_1.png` to `slide_6.png` | 1920 × 1080 (1080p), RGB PNG Exports | **VERIFIED** |
| **Visual Contact Sheet** | `deck/final/contact_sheet.png` | 2 × 3 Grid Slide Overview for Visual Balance Verification | **VERIFIED** |
| **Quality Assurance Report** | `deck/final/PRAMAAN-AICTE_Presentation_QA.md` | Comprehensive Factual Audit & Visual Verification Documentation | **VERIFIED** |

---

## 1. Six-Slide Presentation Outline & Visual Structure

The reconstructed presentation strictly adheres to SIH Rule #1 (maximum 6 slides), allocating exactly one slide per required domain:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PRAMAAN-AICTE SLIDE ARCHITECTURE                                 │
├─────────┬─────────────────────────────────────────────────┬─────────────────────────────────────┤
│ Slide   │ SIH Topic & Title                               │ Key Content & Visual Composition    │
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 1 │ TITLE PAGE                                      │ Official SIH 2026 Branding, Team    │
│         │ SMART INDIA HACKATHON 2026                      │ TCE_Yquanto identity, PS metadata,  │
│         │                                                 │ verified GitHub link, architecture  │
│         │                                                 │ baseline, 64-test verification bar. │
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 2 │ PROPOSED SOLUTION:                              │ 3 Structured Problem/Solution Cards │
│         │ THE PRAMAAN-AICTE RECONCILIATION SYSTEM         │ on left; live AICTE Apex Command    │
│         │                                                 │ Center dashboard screenshot on rt;  │
│         │                                                 │ bottom 4-pillar metric bar.         │
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 3 │ TECHNICAL APPROACH AND SYSTEM ARCHITECTURE      │ 5-Stage Modular Pipeline Cards on   │
│         │                                                 │ left; 4-Layer Architecture Stack &  │
│         │                                                 │ genuine Quarantine Sandbox UI on rt.│
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 4 │ FEASIBILITY, VIABILITY AND RISK MITIGATION      │ 2-Column Balanced Grid: Left column │
│         │                                                 │ details implementation feasibility  │
│         │                                                 │ & maturity; Right column pairs      │
│         │                                                 │ 5 Governance Risks with Controls.   │
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 5 │ MULTI-STAKEHOLDER IMPACT & DEGREE VERIFICATION  │ Left column details impact across 6 │
│         │                                                 │ stakeholder groups; Right column    │
│         │                                                 │ showcases SIH-R10 Degree Certificate│
│         │                                                 │ with Ed25519 QR Code & callouts.    │
├─────────┼─────────────────────────────────────────────────┼─────────────────────────────────────┤
│ Slide 6 │ RESEARCH, REFERENCES AND PROJECT RESOURCES      │ Left column cites 5 statutory/tech  │
│         │                                                 │ standards; Right column features    │
│         │                                                 │ Prior Art Differentiation Table and │
│         │                                                 │ verified project resources.         │
└─────────┴─────────────────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 2. Reference Decks Used for Visual Matching

Visual hierarchy, font sizing, spacing, card radiuses, and margins were directly matched against the reference SIH winning presentations:

1. **Primary Structural Reference — `sih-winning-ppt-1.pdf` (Niet - SafeSecure, SIH 2025 Winner):**
   - **Slide Dimensions & Ratio:** 16:9 widescreen format (13.333" × 7.500" in PowerPoint points).
   - **Title Page Composition:** Left metadata list paired with official SIH visual artwork on the right and a continuous navy/blue footer band.
   - **Slide 2 Layout:** Three stacked container cards on the left (Problem Addressed, Proposed Solution, Unique Value) paired with a high-impact system interface mockup on the right.
   - **Slide 3 Layout:** Step-by-step implementation pipeline paired with architecture blocks and live UI evidence.
   - **Slide 4 Layout:** Two-column split with Feasibility/Maturity on the left and Risk vs Mitigation pairs on the right.
   - **Slide 5 Layout:** Multi-stakeholder impact breakdown paired with verified certificate output.
   - **Slide 6 Layout:** Authoritative regulatory citations on the left paired with a solutions comparison table and project resources on the right.
   - **Footer & Badge Placement:** Oval team badge at top left (`left=0.30in, top=0.20in`), official SIH logo at top right (`left=10.70in, top=0.00in`), and dark blue footer bar (`top=6.95in, height=0.55in`) with `@ TCE_Yquanto | Smart India Hackathon 2026` centered and slide number right-aligned.

2. **Secondary Cross-Check References:**
   - **`sih-winning-ppt-2.pdf` (MAITRI AI, SIH 2025 Winner):** Cross-checked for typography contrast, bold lead-in phrases, and problem/solution clarity.
   - **`sih-winning-ppt-3.pdf` (GeoGuards / Techbyte, SIH 2025 Winner):** Cross-checked for decoupled technical flow diagrams and clean container borders.
   - **`SIH2026-IDEA-Presentation-Format.pptx` (Official SIH 2026 Base):** Reused the official slide master, layout relationships, vector shapes, and official SIH 2026 logo assets.

---

## 3. Actual Repository Architecture Audited & Represented

The slides accurately represent the verified application architecture implemented in the repository:

### Layer Breakdown

1. **Presentation Layer:**
   - Framework: Next.js 14 (App Router) with TypeScript (Strict mode).
   - Styling & UI: Tailwind CSS, Lucide icons, Recharts for analytics.
   - Portals: Decoupled role-based interfaces for Institutional College Users (upload, staging, sandbox) and AICTE Central Administrators (intake monitoring, batch review, conflict adjudication, audit ledger).

2. **Application & Processing Layer:**
   - Framework: FastAPI (Modular Monolith architecture) with Python 3.10+.
   - Validation & Data Schemas: Pydantic v2 schemas across 13 modular API routers.
   - Endpoints: **73 total registered endpoints across 67 unique API paths** under `/api/v1` and root.
   - Reconciliation Core: Pure Python deterministic engine (`ReconciliationEngine`) cross-checking institutional seat declarations, staged student records, and approved capacity snapshots without black-box or non-deterministic AI models.

3. **Persistence & Data Schema Layer:**
   - ORM: SQLAlchemy 2.0 with Alembic database migrations.
   - Database Tables: **20 tables in `public` schema**, exactly matching the 20 application models (1:1 parity):
     `institutions`, `institution_users`, `programmes`, `approval_snapshots`, `policy_rule_sets`, `institutional_declarations`, `synthetic_apaar_registry`, `student_identities`, `upload_batches`, `validation_runs`, `validation_findings`, `staged_batch_rows`, `admission_records`, `consent_grants`, `admission_conflicts`, `anomaly_cases`, `verification_receipts`, `audit_events`, `batch_dispute_queries`, `aicte_central_advisories`.
   - Security: **Row Level Security (RLS) enabled across all 20 tables**.
   - Dual-Dialect Support: Verified SQLite WAL mode for local zero-dependency evaluation, with connection sanitization and driver fallback for PostgreSQL.

4. **Cryptography & Security Layer:**
   - Digital Receipts: Ed25519 (RFC 8032) asymmetric cryptographic signing via PyNaCl/cryptography for tamper-evident verification receipts and degree QR codes.
   - Identifier Protection: Keyed HMAC-SHA256 pseudonymized indexing and dynamic display masking (`XXXX-XXXX-9012`) to uphold DPDP Act 2023 data minimization principles.
   - Audit Integrity: Append-only sequential SHA-256 hash chaining (`Hash_n = SHA256(Record_n || Hash_n-1)`) for regulatory audit events.

---

## 4. Technical Fact-Check and Claim Control Audit

Every assertion in previous presentations was audited against source code and execution evidence:

| Previous / Draft Claim | Audit Finding | Correction Applied in Final Deck | Status |
| :--- | :--- | :--- | :---: |
| "Dihedral D5 Verhoeff checksum suppresses 100% of single-digit and transposition transcription errors." | Verhoeff algorithm checks syntax and detects specific transcription mistakes, but cannot prevent all human errors (e.g., submitting an authentic but wrong student ID). It is an application-level preflight check, not a statutory UIDAI requirement. | Replaced with: "Deterministic checksum validation and regex syntax checks isolate structural format errors in preflight staging." | **CORRECTED** |
| "Fixed intake percentages applied: TFW 5%, EWS 10%, KM, NRI/FN 15%." | AICTE Approval Process Handbook (APH 2026-27) applies supernumerary quotas dynamically based on institutional approval snapshots and declared categories, not a single rigid formula across all institutions. | Replaced with: "Three-way cross-reconciliation evaluating declared enrolment against approved programme intake and applicable supernumerary categories (TFW, EWS, Kashmiri Migrants)." | **CORRECTED** |
| "Sub-50ms regex mapping; 5,000+ student records processed in under 1.8 seconds." | No reproducible benchmark script exists in the repository measuring microsecond ingestion or 5,000-record batch commits. | Removed speculative millisecond claims. Described as: "Fast deterministic header normalization and chunked batch persistence." | **CORRECTED** |
| "Conflicting test counts cited: 40, 47, or 59 passing tests." | Executed current full test suite (`pytest backend/tests/`). Exact verified result is **64 passed, 0 failed in 13.79s** across 14 test suites. | Stated exact measured figure: "64/64 automated pytest test suite passing across 14 verification gates." | **VERIFIED** |
| "33/33 live verified FastAPI endpoints." | Inspection of FastAPI OpenAPI schema revealed 73 registered endpoints across 67 paths. | Updated to accurate count: "73 endpoints registered across 67 paths under `/api/v1`." | **CORRECTED** |
| "Zero plaintext APAAR storage in database." | Staging tables and synthetic references store test identifiers for demonstration; cryptographic protection uses HMAC indexing and display masking. | Accurately stated: "Keyed HMAC-SHA256 pseudonymized indexing and dynamic masking (XXXX-XXXX-9012) ensure zero plaintext PII exposure across public workflows." | **CORRECTED** |
| "Ed25519 provides quantum tamper-resistance." | Mathematically false. Ed25519 is an elliptic curve signature scheme (Curve25519); Shor's algorithm on a quantum computer breaks discrete logarithms on elliptic curves. | Corrected to: "High-speed asymmetric Ed25519 (RFC 8032) digital signatures providing mathematical non-repudiation." | **CORRECTED** |
| "Eliminates fraud nationwide, saves crores in fraudulent grants, reduces audits from 3 months to 5 minutes." | Unsubstantiated economic claims without nationwide empirical data. | Replaced with accurate functional descriptions: "Direct real-time visibility into institutional enrolment versus sanctioned intake quotas; early detection of seat limit breaches." | **CORRECTED** |
| Placeholder Domain: `https://pramaan-aicte.yourdomain.com` / `[PASTE YOUR CUSTOM DOMAIN HERE]` | Unverified custom domain placeholder present on Slide 1 and Slide 6. | Completely removed all placeholder domains. Cited verified GitHub repository and local Swagger API documentation route (`/docs`). | **REMOVED** |
| Exposed Credentials: Plain-text passwords on Slide 6 (`Admin@12345`, `College@12345`, `Verify@12345`). | Security anti-pattern; exposing credentials on public hackathon presentation slides is improper. | Completely removed all plain-text passwords and credentials from the presentation. | **REMOVED** |
| Live Government Integration Claims (UIDAI, ABC, DigiLocker). | No live government API connections exist; external APAAR data is generated from a synthetic database model. | Explicitly marked: "External APAAR / DigiLocker / ABC API: SIMULATED (Synthetic reference dataset)." | **CORRECTED** |
| Hosted Production Cloud Status. | Render web service deploy failed on startup due to a host resolution error (`failed to resolve host 'aws-0-[ap-southeast-2].pooler.supabase.com'`). | Transparently stated: "Application architecture and database schemas 100% verified locally; cloud Render web deployment is currently pending resolution of cloud environment DNS configuration." | **HONESTLY REPORTED** |

---

## 5. Authoritative Standards and Regulatory Sources Checked

All regulatory and technical citations in Slide 6 were verified:

1. **AICTE Approval Process Handbook (APH 2026-27):**
   - Statutory source for approved intake capacity, supernumerary seat reservations (Tuition Fee Waiver 5%, EWS 10%, Kashmiri Migrants), and programme approval guidelines.
2. **National Education Policy (NEP 2020) & APAAR / Academic Bank of Credits (ABC):**
   - Government policy establishing the 12-digit Automated Permanent Academic Account Registry as the lifelong national academic identifier for students.
3. **Digital Personal Data Protection Act (DPDP Act 2023):**
   - Statutory source for data fiduciary obligations, purpose limitation, identifier pseudonymization, dynamic masking, and student consent management.
4. **IETF RFC 8032 (Edwards-Curve Digital Signature Algorithm - Ed25519):**
   - Cryptographic standard governing high-speed, collision-resistant digital signatures for verification receipts and offline QR code authentication.
5. **NIST SP 800-107 (Recommendation for Applications Using Cryptographic Hashes):**
   - Technical standard for sequential SHA-256 cryptographic hash chaining used to construct the immutable regulatory audit trail.

---

## 6. Test Suite and Deployment Status Verification

### Automated Test Execution Evidence

Full test execution was executed on Python 3.10.11 with pytest 9.1.1:

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\AICTE
plugins: anyio-4.15.1, cov-7.1.0
collected 64 items

backend\tests\test_all_gates.py .......                                  [ 10%]
backend\tests\test_batch_review.py .                                     [ 12%]
backend\tests\test_conflicts_and_anomalies.py ...                        [ 17%]
backend\tests\test_database_configuration_and_drivers.py .....           [ 25%]
backend\tests\test_identity_and_approval_rules.py ....                   [ 31%]
backend\tests\test_ingestion_and_reconciliation.py ......                [ 40%]
backend\tests\test_inline_editing_and_disputes.py .....                  [ 48%]
backend\tests\test_institution_registration.py ....                      [ 54%]
backend\tests\test_login_workflow.py .......                             [ 65%]
backend\tests\test_persistence_and_transactions.py ..                    [ 68%]
backend\tests\test_reconciliation_workflow.py .........                  [ 82%]
backend\tests\test_security_and_tenant_isolation.py ....                 [ 89%]
backend\tests\test_sovereign_vault_and_advisories.py ...                 [ 93%]
backend\tests\test_verification_receipts_and_certificates.py ....        [100%]

====================== 64 passed, 21 warnings in 13.79s =======================
```

**Verification Result:** Exactly **64 passed, 0 failed** across 14 test suites.

### Deployment Status Audit

1. **Local Environment:**
   - Status: **IMPLEMENTED AND VERIFIED**.
   - Backend runs on `http://127.0.0.1:8000`, Frontend on `http://localhost:3000`.
   - SQLite WAL database and Supabase PostgreSQL schema verified (20 tables, RLS active).

2. **Render Cloud Web Service (`srv-dbguvkgm7kps73ersuig`):**
   - Status: **BLOCKED / PENDING HOST CONFIGURATION**.
   - Latest deploy: `dep-dbh32g7b9u1s73e8blmg` (`update_failed`).
   - Root Cause: Host resolution error during startup:
     `sqlalchemy.exc.OperationalError: (psycopg.OperationalError) failed to resolve host 'aws-0-[ap-southeast-2].pooler.supabase.com': [Errno -2] Name or service not known`
   - Diagnostic: The Render environment variable `DATABASE_URL` contains literal bracket characters `[ap-southeast-2]` which cannot be resolved by DNS.
   - Quality Rule Compliance: Rather than falsely claiming production readiness, Slides 4 and 6 transparently record: *"Cloud Render web deployment is currently pending resolution of cloud environment DNS configuration."*

---

## 7. Confirmation of Rendering & Visual Inspection

A complete visual QA inspection was conducted across all slides:

1. **PDF Rendering & Text Geometry:**
   - Exported PPTX to PDF via Microsoft PowerPoint COM object (`ppSaveAsPDF = 32`).
   - Extracted all vector text blocks and coordinates using PyMuPDF (`fitz`).
   - Verified that text blocks sit cleanly within container cards without clipping or overflow.

2. **Slide-by-Slide Visual Review:**
   - **Slide 1:** Title, metadata rows, and team branding are well-balanced against the right-hand SIH artwork. The bottom blue footer band grounds the slide.
   - **Slide 2:** The 3 left cards (Problem, Solution, Value) provide clear thematic grouping. The right-hand AICTE Apex Command Center preview (`02_dashboard_overview.png`) is crisp and flanked by 3 feature callouts and 4 bottom metric pills.
   - **Slide 3:** The 5 modular stage cards on the left create an architectural pipeline. The right-hand column pairs the 4-layer tech stack with a genuine screenshot of the Quarantine Sandbox (`07_interactive_spreadsheet_sandbox.png`).
   - **Slide 4:** The 2-column layout evenly balances 6 feasibility maturity points on the left against 5 paired Governance Risks and Technical Controls on the right.
   - **Slide 5:** Left column articulates impact across 6 distinct stakeholder groups. Right column presents the SIH-R10 Degree Certificate preview (`08_student_certificate_verified.png`) with callouts for dual-display identifiers and Ed25519 QR codes.
   - **Slide 6:** Left column lists 5 authoritative regulatory standards. Right column presents a clear Prior Art comparison table alongside verified project links (GitHub repo, Swagger `/docs` with 73 endpoints).

3. **Contact Sheet Overview:**
   - Generated `deck/final/contact_sheet.png` (2 rows × 3 columns, 1920 × 1080 thumbs).
   - Confirmed consistent typography hierarchy (Arial bold headings, navy headers, teal/slate accents, charcoal body).
   - Confirmed consistent margins, uniform blue footers, and legible text throughout.

---

## 8. Remaining Limitations and Next Steps

1. **Cloud Environment Hostname Correction:**
   - To make the remote Render web service healthy, the user needs to update the `DATABASE_URL` / `SUPABASE_DATABASE_URL` environment variable in the Render dashboard to remove bracket formatting from the pooler hostname (e.g. replacing `aws-0-[ap-southeast-2].pooler.supabase.com` with `aws-0-ap-southeast-2.pooler.supabase.com`).
2. **External Government Identity Integrations:**
   - Live integration with DigiLocker, UIDAI, and the Academic Bank of Credits is currently simulated via a database-backed synthetic APAAR registry model. Connecting to live production gateways requires institutional MoUs and government sandbox API credentials.

---

**Report Prepared By:** Antigravity AI Pair Programmer & System Engineer  
**Inspection Status:** 100% COMPLETE AND VERIFIED  
**Final Output Location:** `D:\AICTE\deck\final\`

