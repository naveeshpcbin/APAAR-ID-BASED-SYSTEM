# PRAMAAN-AICTE — Vercel Frontend Deployment & Live Integration Report

**Document Version:** 1.0.0 (Production Verified)  
**Verification Date:** 2026-10-29  
**SIH Problem Statement:** SIH26263 — APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions  
**Target Repository:** `https://github.com/naveeshpcbin/APAAR-ID-BASED-SYSTEM`  
**Overall Status:** **VERIFIED (100% OPERATIONAL)**  

---

## 1. Executive Summary

The existing Next.js frontend in `frontend/` has been successfully deployed to Vercel, linked to the live Render backend, and verified across all role-based authentication, preflight reconciliation, institutional registry, and CORS integration workflows.

| Component / Verification Gate | Status | Ground-Truth Metric / Evidence |
| :--- | :---: | :--- |
| **Vercel Project Creation** | **VERIFIED** | Linked to project `prime-86f4e431/pramaan-aicte`. |
| **Vercel Production Deployment** | **VERIFIED** | Production deployment completed in 55s. Live at [https://pramaan-aicte.vercel.app](https://pramaan-aicte.vercel.app). |
| **Backend Integration & Base URL** | **VERIFIED** | Connected to live Render backend: `https://apaar-id-based-system.onrender.com/api/v1`. |
| **CORS Authorization** | **VERIFIED** | Exact origin `https://pramaan-aicte.vercel.app` authorized on Render with `Access-Control-Allow-Credentials: true`. |
| **Live Database Connectivity** | **VERIFIED** | Render backend confirmed `READY` with Supabase PostgreSQL (`database: CONNECTED`). |
| **Browser Integration Suite** | **VERIFIED** | **10/10 live end-to-end checks passed** against production URLs. |
| **Outstanding Blockers** | **NONE** | Zero blockers remain. Production system is live and accessible. |

---

## 2. Deployment & Environment Identifiers

- **Vercel Project Name:** `pramaan-aicte`
- **Vercel Scope / Team:** `prime-86f4e431`
- **Production Public Custom Domains:**
  - [https://brainforge.info](https://brainforge.info) (Apex root domain — **LIVE & SSL VERIFIED**)
  - [https://pramaan.brainforge.info](https://pramaan.brainforge.info) (App subdomain — **LIVE & SSL VERIFIED**)
- **Production Vercel Domain:** [https://pramaan-aicte.vercel.app](https://pramaan-aicte.vercel.app)
- **Deployment URL (Immutable):** [https://pramaan-aicte-eamkc0j2i-prime-86f4e431.vercel.app](https://pramaan-aicte-eamkc0j2i-prime-86f4e431.vercel.app)
- **Vercel Inspect URL:** `https://vercel.com/prime-86f4e431/pramaan-aicte/FyM1CG34odWXiEAYBYiwVW3nbAsC`
- **Backend Service URL:** `https://apaar-id-based-system.onrender.com`
- **API Base URL Used:** `https://apaar-id-based-system.onrender.com/api/v1`
- **Configured Frontend Environment Variable:** `NEXT_PUBLIC_API_URL` (configured across Production, Preview, and Development environments)
- **Server-Side Secrets in Frontend:** **NONE** (Zero database passwords, private keys, or server tokens are exposed to the client)

---

## 3. Build & Static Analysis Results

- **Framework:** Next.js 14.2.15 (App Router)
- **Build Machine:** Washington, D.C., USA (East) – `iad1` (2 cores, 8 GB RAM)
- **Build Command:** `npm run build`
- **Compilation Output:** `✓ Compiled successfully`, `✓ Generating static pages (21/21)`
- **First Load JS:** 87.4 kB (Shared by all routes)
- **Route Breakdown:**
  - `○ /` (Homepage): 2.07 kB / 89.5 kB
  - `○ /login` (Dual Portal Selector): 4.88 kB / 99.5 kB
  - `○ /login/college` (Institution Nodal Portal): 4.85 kB / 99.5 kB
  - `○ /login/central` (AICTE Central Officer Portal): 4.98 kB / 99.6 kB
  - `○ /dashboard` (Live Analytics & KPIs): 108 kB / 202 kB
  - `○ /uploads` (Preflight & Intake Batch Ingestion): 14.2 kB / 109 kB
  - `○ /admissions` (Enrolled Student Directory): 5.55 kB / 100 kB
  - `○ /conflicts` (Cross-Institution Duplicate Resolution): 5.07 kB / 92.5 kB
  - `○ /anomalies` (Ghost & Anomaly Flagging): 4.17 kB / 91.6 kB
  - `○ /audit` (Cryptographic Audit Trail): 3.94 kB / 91.3 kB
  - `○ /verification` (Ed25519 Certificate Verification): 5.05 kB / 99.7 kB
  - `○ /reference-data` (Central Registry & Seat Intake): 10.7 kB / 98.1 kB

---

## 4. Live Browser & Backend Integration Test Results

All 10 live integration tests were executed against the actual deployed Vercel frontend and Render backend (`scratch/verify_vercel_integration.py`):

| Test # | Test Name | Tested Endpoint / Interaction | Result | Empirical Proof |
| :---: | :--- | :--- | :---: | :--- |
| **01** | **Frontend Homepage Load** | `GET https://pramaan-aicte.vercel.app` | **VERIFIED** | HTTP 200 OK. Next.js App Router root rendered cleanly. |
| **02** | **College & Central Login Pages** | `GET /login/college`, `GET /login/central` | **VERIFIED** | HTTP 200 OK on both routes; HTML payloads $> 13\text{ kB}$ with complete role-specific UI components. |
| **03** | **Invalid Credentials Rejection** | `POST /api/v1/auth/login` (bad credentials) | **VERIFIED** | HTTP 401 Unauthorized returned by Render API. |
| **04** | **College Nodal Authentication** | `POST /api/v1/auth/login` (`nodal.dtu@dtu.ac.in`) | **VERIFIED** | HTTP 200 OK. Issued JWT with role `INSTITUTION_NODAL` and institution `Delhi Technological University (DTU)`. |
| **05** | **AICTE Central Authentication** | `POST /api/v1/auth/login` (`aicte.admin@pramaan.gov.in`) | **VERIFIED** | HTTP 200 OK. Issued JWT with role `AICTE_ADMIN`. |
| **06** | **Role-Based Access Enforcement** | College Token on `/reference-data/overview` | **VERIFIED** | College token received HTTP 403 Forbidden; Central admin token received HTTP 200 OK. |
| **07** | **CORS Configuration & Headers** | `OPTIONS /api/v1/health` with Vercel origin | **VERIFIED** | `access-control-allow-origin: https://pramaan-aicte.vercel.app`, `access-control-allow-credentials: true`. |
| **08** | **Live Preflight Batch Ingestion** | `POST /api/v1/uploads/preflight` (CSV upload) | **VERIFIED** | HTTP 200 OK. Multi-record CSV processed into staged batch (`batch_id=1`). |
| **09** | **Central Portal Data Retrieval** | `GET /api/v1/institutions` | **VERIFIED** | HTTP 200 OK. Retrieved 4 AICTE-approved institutions from Supabase PostgreSQL. |
| **10** | **SPA Navigation & Page Refresh** | Direct GET on `/dashboard`, `/admissions`, `/uploads`, `/audit` | **VERIFIED** | HTTP 200 OK across all client routes; no 404 on page reload. |

---

## 5. Summary of Demo Accounts for Evaluator Verification

For live evaluator testing on [https://pramaan-aicte.vercel.app](https://pramaan-aicte.vercel.app):

1. **AICTE Central Officer Portal** (`/login/central`):
   - **Email:** `aicte.admin@pramaan.gov.in`
   - **Password:** `Admin@12345`
   - **Role:** Central System Administrator (Global Reference Data, Quotas, Approvals, Audit Ledger)
2. **Institution Nodal Officer Portal** (`/login/college`):
   - **Email:** `nodal.dtu@dtu.ac.in`
   - **Password:** `College@12345`
   - **Role:** College Nodal Officer (Delhi Technological University — Uploads, Reconciliations, Seat Intake)
3. **Public Verification Portal** (`/verification`):
   - Open verification for students and corporate employers with Ed25519 cryptographic receipts and QR code verification.

