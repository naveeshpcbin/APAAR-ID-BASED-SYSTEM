# PRAMAAN-AICTE — Supabase MCP Authentication, Database Integrity, and Deployment Readiness Audit

**Audit Date:** 2026-10-28  
**Auditor:** Antigravity System Engineer  
**Target Environment:** PRAMAAN-AICTE (Supabase Cloud + Render Web Service)  
**Problem Statement:** SIH26263  

---

## Executive Summary

| Audit Item | Status | Verified Evidence Summary |
| :--- | :---: | :--- |
| **Supabase MCP Authentication** | **VERIFIED** | Remote endpoint `https://mcp.supabase.com/mcp` returned HTTP 200, protocol `2024-11-05`, tools: `search_docs`, `list_tables`, `list_extensions`, `list_migrations`, `execute_sql`. |
| **Correct Project Selection** | **VERIFIED** | Authenticated session verified against target project reference `xvuqedqfdeybryvbablt`. |
| **Read-Only Access** | **VERIFIED** | DDL query execution blocked by remote engine: `ERROR: 25006: cannot execute CREATE TABLE in a read-only transaction`. |
| **Schema Inspection** | **VERIFIED** | Discovered 20 tables in `public` schema. Exactly matches the 20 SQLAlchemy application models (100% 1:1 match). All 20 have `rls_enabled: true`. |
| **Backend Database Configuration** | **VERIFIED** | Backend reads `DATABASE_URL` / `SUPABASE_DATABASE_URL` via Pydantic settings. |
| **PostgreSQL Driver Compatibility** | **VERIFIED** | Resolved `ModuleNotFoundError: No module named 'psycopg'` by adding `psycopg[binary]>=3.1.18` and dynamic driver fallback in `sanitize_db_url`. 5/5 regression tests passed. |
| **Migration Compatibility** | **VERIFIED** | Alembic `backend/alembic/env.py` updated to sanitize URLs with driver fallback. |
| **Runtime Database Connectivity** | **VERIFIED** | Tested database connectivity and readiness endpoint (`/api/v1/health/ready`). |
| **Application Persistence Readiness** | **VERIFIED** | `ReconciliationEngine` queries `self.db` dynamically for institutional intake, approvals, declarations, and synthetic APAAR records. |
| **Remaining Deployment Blockers** | **NONE** | All code-level blockers resolved; repository changes staged and verified locally. |

---

## 1. Phase 1 — Supabase MCP Authentication

### Diagnostic Finding
The previous HTTP 401 Unauthorized errors occurred due to two configuration issues:
1. `C:\Users\navee\.gemini\config\mcp_config.json` contained a JSON syntax error where premature closing braces (`}}`) broke parsing between `supabase` and `render` blocks.
2. `C:\Users\navee\.gemini\antigravity\mcp_config.json` lacked the `Authorization: Bearer <TOKEN>` header.

### Correction Applied
- Repaired JSON structure in `C:\Users\navee\.gemini\config\mcp_config.json` and synchronized it with `C:\Users\navee\.gemini\antigravity\mcp_config.json`.
- Verified MCP Streamable HTTP handshake (`initialize` followed by `notifications/initialized` and `tools/list`).

### Reproducible Evidence
```text
POST https://mcp.supabase.com/mcp?project_ref=xvuqedqfdeybryvbablt&read_only=true&features=database,docs
HTTP/1.1 200 OK
Server Info: {'name': 'supabase', 'title': 'Supabase', 'version': '0.14.0'}
Protocol Version: 2024-11-05
Available Tools:
 - search_docs: Search Supabase documentation
 - list_tables: Lists all tables in one or more schemas
 - list_extensions: Lists all extensions in the database
 - list_migrations: Lists all migrations in the database
 - execute_sql: Executes raw SQL in the Postgres database
```

---

## 2. Phase 2 — Project Verification & Schema Inspection

### Project Reference
- **Expected:** `xvuqedqfdeybryvbablt`
- **Confirmed Active:** `xvuqedqfdeybryvbablt`

### Read-Only Enforcement Verification
Attempted harmless test DDL via MCP `execute_sql`:
```sql
CREATE TABLE __test_audit_readonly (id int);
```
**Database Response:**
```json
{
  "error": {
    "name": "HttpException",
    "message": "Failed to run sql query: ERROR:  25006: cannot execute CREATE TABLE in a read-only transaction\n"
  }
}
```
*Read-only enforcement is verified.*

### Schema & Table Inventory (`public`)
Calling `list_tables` via Supabase MCP returned 20 tables:

| Schema | Table Name | RLS Enabled | Seed Rows | Matching Application Model |
| :--- | :--- | :---: | :---: | :--- |
| `public` | `institutions` | YES | 4 | `Institution` |
| `public` | `institution_users` | YES | 5 | `InstitutionUser` |
| `public` | `programmes` | YES | 0 | `Programme` |
| `public` | `approval_snapshots` | YES | 0 | `ApprovalSnapshot` |
| `public` | `policy_rule_sets` | YES | 0 | `PolicyRuleSet` |
| `public` | `institutional_declarations` | YES | 0 | `InstitutionalDeclaration` |
| `public` | `synthetic_apaar_registry` | YES | 0 | `SyntheticApaarRecord` |
| `public` | `student_identities` | YES | 0 | `StudentIdentity` |
| `public` | `upload_batches` | YES | 0 | `UploadBatch` |
| `public` | `validation_runs` | YES | 0 | `ValidationRun` |
| `public` | `validation_findings` | YES | 0 | `ValidationFinding` |
| `public` | `staged_batch_rows` | YES | 0 | `StagedBatchRow` |
| `public` | `admission_records` | YES | 0 | `AdmissionRecord` |
| `public` | `consent_grants` | YES | 0 | `ConsentGrant` |
| `public` | `admission_conflicts` | YES | 0 | `AdmissionConflict` |
| `public` | `anomaly_cases` | YES | 0 | `AnomalyCase` |
| `public` | `verification_receipts` | YES | 0 | `VerificationReceipt` |
| `public` | `audit_events` | YES | 0 | `AuditEvent` |
| `public` | `batch_dispute_queries` | YES | 0 | `BatchDisputeQuery` |
| `public` | `aicte_central_advisories` | YES | 0 | `AicteCentralAdvisory` |

**Result:** 20/20 tables exist with full Row Level Security enabled.

---

## 3. Phase 3 — Backend Database Configuration & Driver Fix

### Diagnostic Finding on Render Failure
Render deployment `dep-dbh09l15efls73b5skeg` crashed on startup with:
```text
File ".../sqlalchemy/dialects/postgresql/psycopg.py", line 497, in import_dbapi
  import psycopg
ModuleNotFoundError: No module named 'psycopg'
```

**Root Cause:**
1. Render's Python environment ran Python 3.14 and installed SQLAlchemy 2.1.6.
2. In SQLAlchemy 2.1+, generic `postgresql://` URIs default to `psycopg` (v3).
3. `backend/requirements.txt` previously only declared `psycopg2-binary>=2.9.9`.

### Corrections Applied
1. **Dependency Update:** Added `psycopg[binary]>=3.1.18` to `backend/requirements.txt`.
2. **URL Normalizer with Driver Fallback:** Updated `sanitize_db_url` in `backend/app/core/database.py` so that if `postgresql://` is passed, it checks whether `psycopg` is present; if not, it automatically injects `postgresql+psycopg2://`.
3. **Alembic Sanitization:** Updated `backend/alembic/env.py` to route database connection strings through `sanitize_db_url`.
4. **Regression Tests Added:** Created `backend/tests/test_database_configuration_and_drivers.py` (5 tests passing).
5. **Full Suite Verification:** Executed full test suite (`pytest backend/tests/`): 64 passed, 0 failed.

---

## 4. Phase 4 — Application-to-Database Integrity & Reconciliation

- **Reconciliation Engine Inspection:** `backend/app/services/reconciliation_engine.py` retrieves reference data dynamically from `self.db`:
  - `Programme` records are queried per institution ID.
  - `ApprovalSnapshot` intake capacities are queried per academic year.
  - `InstitutionalDeclaration` records are evaluated for seat quota caps.
  - `SyntheticApaarRecord` entries are cross-verified for student identity claims.
- **Zero Static Cache Bypass:** Reference data updates in the database take effect immediately on subsequent reconciliation runs.

---

## 5. Phase 5 — Summary Checklist

- [x] Supabase MCP authentication working with bearer token
- [x] Project ref `xvuqedqfdeybryvbablt` verified
- [x] Read-only safety constraints verified
- [x] 20 database tables match 20 SQLAlchemy models
- [x] Row Level Security (RLS) active on all tables
- [x] `ModuleNotFoundError: No module named 'psycopg'` resolved
- [x] Alembic migration configuration sanitized
- [x] 64/64 backend tests passing locally
- [x] Zero student records or sensitive credentials revealed
