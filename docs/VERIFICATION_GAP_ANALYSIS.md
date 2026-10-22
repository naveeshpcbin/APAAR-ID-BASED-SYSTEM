# PRAMAAN-AICTE: Verification Gap Analysis & Audit Matrix

**Audit Date**: October 22, 2026 | 23:30 IST  
**Target Reference**: Problem Statement SIH26263  
**Audit Objective**: Identify discrepancies between previously claimed verification results (`FINAL_VERIFICATION_REPORT.md` / `.json`) and genuine code, test, and environment realities.

---

## 1. Executive Gap Analysis Table

| Claim ID | Previous Claim | Source Files | Verification Method | Actual Result | Defect | Corrective Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-01** | Database schema created and verified via Alembic migrations (`alembic upgrade head`) | `backend/alembic/versions/98d85ae389ed_initial_pramaan_schema.py`<br>`backend/app/main.py`<br>`backend/scripts/seed_data.py` | Inspected startup hooks and executed migration check | Application startup and seed script used `Base.metadata.create_all(bind=engine)`. `alembic stamp head` was used on a pre-existing SQLite database instead of running migrations on an empty database. | Alembic migration execution against an empty database was unverified. | Create an isolated empty test database (`test_migration.db`), run `alembic upgrade head`, verify all 13 tables, indices, and foreign keys, and record output in `artifacts/verification/alembic_upgrade_isolated.log`. |
| **GAP-02** | PostgreSQL compatibility verified | `backend/app/core/database.py`<br>`backend/app/core/config.py` | Executed `docker --version` and `psql --version` in terminal | Neither Docker nor PostgreSQL binaries are installed on the local Windows environment. | PostgreSQL runtime compatibility cannot be verified by live execution in this environment. | Explicitly report PostgreSQL compatibility as **UNVERIFIED** due to missing local Docker/PostgreSQL runtime, despite dialect-neutral SQLAlchemy models. |
| **GAP-03** | Automated backend acceptance tests (7 gates) proved all 20 criteria passed | `backend/tests/test_all_gates.py` | Inspected test coverage and executed pytest | The single test file (`test_all_gates.py`) contained 7 basic assertions. Critical edge cases (tenant isolation, transaction rollback, Excel ingestion errors, duplicate batch rows, revoked receipts) lacked test coverage. | Acceptance claim was disproportionate to test suite depth. | Author comprehensive focused test modules for Ingestion, Identity, Capacity, Conflicts, Security/Tenant Isolation, Anomalies, and Receipts in `backend/tests/`. |
| **GAP-04** | Cross-institution tenant isolation verified | `backend/app/api/v1/admissions.py`<br>`backend/app/api/v1/uploads.py` | Source code review and API token testing | Institution ID filtering was implemented in select endpoints, but no test explicitly asserted that Institution User A receives `403 Forbidden` or empty results when attempting to read or mutate Institution B's student records. | Missing negative security test for cross-tenant data access. | Write dedicated tenant-isolation tests creating two independent institution operators and asserting rejection of cross-institution data retrieval and mutations. |
| **GAP-05** | Transaction safety & rollback on upload failure verified | `backend/app/services/reconciliation_engine.py`<br>`backend/app/api/v1/uploads.py` | Inspected upload commit logic | Upload preview created `UploadBatch` and `ValidationFinding` records, but transaction rollback during a simulated mid-commit database exception was not covered by tests. | Lack of explicit automated verification for atomic rollback on database failure. | Implement automated test injecting a failure during batch commit and asserting zero orphaned student identities or admission records remain. |
| **GAP-06** | Claimed "Zero-Knowledge Proof" & "NAD Conformance" | `docs/FINAL_VERIFICATION_REPORT.md`<br>`frontend/src/app/verification/page.tsx` | Inspected cryptographic algorithms used | System uses Ed25519 digital signatures (RFC 8032) and SHA-256 payload digests. It does not use ZK-SNARKs/STARKs, nor has it been certified against official National Academic Depository production APIs. | Inflated and inaccurate terminology used in documentation. | Replace all occurrences of "zero-knowledge proof" with "Ed25519 asymmetric digital signature verification" and label NAD integration as "NAD-inspired synthetic verification receipt format". |
| **GAP-07** | Official government account representation (`@aicte.gov.in`) | `backend/scripts/seed_data.py`<br>`frontend/src/lib/auth-context.tsx`<br>`frontend/src/app/login/page.tsx` | Inspected seed data and persona switcher | Demo accounts used `@aicte.gov.in` domain emails (e.g., `aicte.central@aicte.gov.in`), potentially implying genuine government credentials. | Unclear synthetic data demarcation. | Clarify in login UI, seed scripts, and documentation that all accounts are synthetic demonstration personas (`demo.regulator@pramaan.internal`, etc.) and require development environment configuration. |
| **GAP-08** | Audit ledger described as "immutable" | `docs/FINAL_VERIFICATION_REPORT.md`<br>`backend/app/core/hash_chain.py` | Inspected hash chain implementation | The ledger is implemented via sequential SHA-256 hash chaining stored in a relational database table (`audit_events`). Without an external WORM or cloud HSM anchor, it is tamper-evident, not strictly immutable. | Immutability claim is imprecise. | Rephrase documentation and UI to accurately describe the ledger as "cryptographically tamper-evident SHA-256 append-only ledger". |
| **GAP-09** | End-to-end frontend Playwright automated test suite | `frontend/` package dependencies and test scripts | Inspected `frontend/package.json` | Playwright was not configured in `frontend/package.json`. Browser verification relied solely on interactive subagent execution without a repeatable scripted Playwright test file. | Missing scriptable end-to-end regression test suite. | Install and configure Playwright or provide automated browser test scripts with repeatable execution commands and output logs. |
| **GAP-10** | Detailed ingestion of malformed Excel/CSV files | `backend/app/services/reconciliation_engine.py` | Tested file upload handling | Engine handled basic CSVs, but lacked unit tests verifying corrupted binary headers, unsupported extensions, missing required headers, and ambiguous column mappings. | Ingestion resilience untested on malformed payloads. | Write unit tests testing corrupt file bytes, non-CSV/Excel extensions, and missing mandatory columns. |

---

## 2. SIH Requirement Traceability & Remediation Roadmap

| SIH Requirement | Prior Reported Status | Genuine Status | Key Gap to Remediate |
| :--- | :---: | :---: | :--- |
| **SIH-R01**: Secure student upload & APAAR identification | `PASS` | **PARTIAL** | Need automated tests for corrupt uploads, column alias ambiguities, and batch-level duplicate APAAR detection. |
| **SIH-R02**: Approved intake, supernumerary, NRI/OCI/FN | `PASS` | **PASS** | Logic implemented; verify via expanded tests for missing approval snapshots and multi-year snapshots. |
| **SIH-R03**: Ingestion errors, duplicate APAARs, cross-institution conflicts | `PASS` | **PARTIAL** | Conflict detection works, but human adjudication workflow and audit trail creation need end-to-end integration tests. |
| **SIH-R04**: Role-specific monitoring dashboards | `PASS` | **PASS** | Dashboard charts and metrics work; verify tenant scoping on metrics endpoint. |
| **SIH-R05**: Authorized stakeholder verification | `PASS` | **PARTIAL** | Need tests for expired and revoked verification tokens, and non-disclosure of raw APAARs on public endpoints. |
| **SIH-R06**: Verifiable student records linked to academic identity | `PASS` | **PASS** | Ed25519 digital signature verified; ensure accurate terminology. |
| **SIH-R07**: API and interoperability capability | `PASS` | **PASS** | REST API v1 and OpenAPI 3.1 schema operational. |
| **SIH-R08**: Security, privacy, auth, audit trails, consent | `PASS` | **PARTIAL** | Tenant isolation and transaction rollback require automated negative tests. |
| **SIH-R09**: Regulatory reports and CSV export | `PASS` | **PASS** | CSV export functional; verify role restrictions on export endpoints. |
| **SIH-R10**: Student ID alongside APAAR ID on certificate | `PASS` | **PASS** | Certificate view rendered at `/admissions/certificate/[id]`; ensure prominent synthetic disclaimer. |

---

## 3. Plan of Execution for Remediation
1. **Stage 2**: Run Alembic migration against an isolated, clean SQLite database (`test_migration.db`), verify all tables and schema integrity, document PostgreSQL limitation.
2. **Stage 3**: Build and execute comprehensive automated test suites covering all areas (A through H).
3. **Stage 4**: Verify frontend build, lint, TypeScript compilation, and run automated browser tests.
4. **Stage 5**: Standardize terminology across codebase, UI, and documentation.
5. **Stage 6**: Collect and validate all test artifacts in `artifacts/verification/`.
6. **Stage 7**: Regenerate `FINAL_VERIFICATION_REPORT.md` and `FINAL_VERIFICATION_REPORT.json` with authentic, evidenced results.
