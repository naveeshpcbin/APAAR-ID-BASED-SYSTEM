# PRAMAAN-AICTE: 100% Free Online Cloud Hosting & Architecture Guide

This guide provides end-to-end instructions for deploying the **PRAMAAN-AICTE** sovereign admission reconciliation and verification platform online completely for free using production-grade infrastructure:

1. **Database Base**: [Supabase Cloud PostgreSQL](https://supabase.com) (Free Tier: 500 MB DB, Row-Level Security, automated SSL, global connection pooling)
2. **Backend API**: [Render](https://render.com) or [Railway](https://railway.app) (Free Web Service Tier: FastAPI + Python 3.10)
3. **Frontend Application**: [Vercel](https://vercel.com) (Free Hobby Tier: Next.js 14 App Router, Edge CDN, automatic HTTPS)
4. **Sovereign Cryptographic Vault**: Deterministic SHA-256 Merkle root verification ensuring reference datasets cannot be surreptitiously altered in the cloud.

---

## Architecture Topology

```
+-----------------------------------------------------------------------------------+
|                                  USER BROWSER                                     |
|           College Officers (Nodal)   |   AICTE Central Officers (Advisory)         |
+-----------------------------------------------------------------------------------+
                                          |
                     HTTPS / WSS          |
                                          v
+-----------------------------------------------------------------------------------+
|                        VERCEL EDGE CDN (Frontend)                                 |
|   Next.js 14 App Router | In-Browser Spreadsheet | Regulatory Advisory System    |
+-----------------------------------------------------------------------------------+
                                          |
                     REST API / JSON      |   NEXT_PUBLIC_API_URL
                                          v
+-----------------------------------------------------------------------------------+
|                   RENDER / RAILWAY / FLY.IO (FastAPI Backend)                     |
|  - Deterministic Reconciliation Engine (Zero Non-Deterministic AI)               |
|  - Sovereign Cryptographic Vault (Merkle Root Digest & Ledger Consensus)          |
|  - Ed25519 Cryptographic Verification Receipt Issuer                             |
|  - AICTE Central Advisory Guidance & Auto-Remapping Service                       |
+-----------------------------------------------------------------------------------+
                                          |
                     PostgreSQL Pooler    |   DATABASE_URL (SSL Mode)
                                          v
+-----------------------------------------------------------------------------------+
|                       SUPABASE CLOUD POSTGRESQL (Free Tier)                       |
|  - Row-Level Security (RLS) Multi-Tenant Policies                                 |
|  - Sovereign Synthetic Reference Datasets (Zero Real PII)                         |
|  - Tamper-Evident SHA-256 Hash Chain Audit Ledger                                 |
+-----------------------------------------------------------------------------------+
```

---

## Phase 1: Database Setup on Supabase Cloud (Free)

### Step 1.1: Create a Free Supabase Project
1. Navigate to [https://supabase.com](https://supabase.com) and sign in with your GitHub account.
2. Click **New Project**.
3. Choose a project name: `pramaan-aicte-db`.
4. Enter a strong Database Password (store this securely).
5. Select a region close to your primary audience (e.g., `ap-south-1` Mumbai).
6. Click **Create new project**.

### Step 1.2: Execute the Production PostgreSQL Schema
1. In the Supabase project dashboard, click on the **SQL Editor** icon in the left navigation sidebar.
2. Open the file [`backend/supabase_schema.sql`](file:///d:/AICTE/backend/supabase_schema.sql) from this repository.
3. Copy its entire contents and paste it into the Supabase SQL Editor.
4. Click **Run** (or `Ctrl+Enter`).
5. Verify that all 14 tables, indexes, triggers, and Row-Level Security (RLS) policies are created successfully:
   - `institutions`, `institution_users`
   - `programmes`, `approval_snapshots`, `institutional_declarations`
   - `synthetic_apaar_registry`
   - `upload_batches`, `staged_batch_rows`, `batch_dispute_queries`
   - `aicte_central_advisories`
   - `validation_runs`, `validation_findings`
   - `admission_conflicts`, `anomaly_cases`
   - `verification_receipts`, `audit_events`

### Step 1.3: Seed Synthetic Reference Data to Supabase Cloud
1. In Supabase, go to **Project Settings** -> **Database** -> **Connection string** -> **URI**.
2. Select **Session Pooler** (Port `5432`) or **Transaction Pooler** (Port `6543`).
3. Copy the URI string, which looks like:
   ```bash
   postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
4. Run the automated seeder script from your local terminal:
   ```bash
   cd d:\AICTE\backend
   .\venv\Scripts\python.exe scripts/seed_supabase_cloud.py "postgresql://postgres.[PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
   ```
5. The script automatically populates all institutions, default users, programmes, institutional declarations, and synthetic APAAR reference profiles in one execution.

---

## Phase 2: Deploy Backend to Render (Free Tier)

### Step 2.1: Prepare GitHub Repository
Ensure your repository is pushed to GitHub:
```bash
git add .
git commit -m "feat: sovereign data vault, supabase cloud base, and central advisories"
git push origin main
```

### Step 2.2: Create a Web Service on Render
1. Visit [https://render.com](https://render.com) and connect your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your `PRAMAAN-AICTE` repository.
4. Configure the service settings:
   - **Name**: `pramaan-backend`
   - **Region**: Singapore or Frankfurt (closest free tier)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

### Step 2.3: Configure Environment Variables on Render
Add the following key-value pairs in the **Environment** tab:
| Key | Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PASS]@[HOST]:6543/postgres` | Your Supabase connection string |
| `SECRET_KEY` | *(generate a random 32-char hex string)* | JWT HMAC-SHA256 signature key |
| `CORS_ORIGINS` | `["*"]` (or your Vercel URL once deployed) | Allowed frontend origins |
| `ENVIRONMENT` | `production` | Deployment mode |

Click **Deploy Web Service**. Once deployed, Render provides your public backend URL, e.g.:
`https://pramaan-backend.onrender.com`

Verify backend health by opening `https://pramaan-backend.onrender.com/docs` in your browser.

---

## Phase 3: Deploy Frontend to Vercel (Free Tier)

### Step 3.1: Import Project to Vercel
1. Visit [https://vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New...** -> **Project**.
3. Select your repository.
4. In the configuration screen:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and select `frontend`.

### Step 3.2: Set Environment Variables on Vercel
In the **Environment Variables** section, add:
| Key | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://pramaan-backend.onrender.com/api/v1` | Public URL of your Render backend |

Click **Deploy**. Vercel will compile and optimize all 20 routes, producing a live URL like:
`https://pramaan-aicte.vercel.app`

---

## Phase 4: Production Verification & Zero-Cost SLA

Once deployed, test the complete workflow:
1. **Login Portal**:
   - Navigate to `https://pramaan-aicte.vercel.app/login`.
   - Test **AICTE Central Login**: `aicte.admin@pramaan.gov.in` / `Admin@12345`.
   - Test **College Nodal Login**: `nodal.dtu@dtu.ac.in` / `College@12345`.
2. **Sovereign Cryptographic Vault**:
   - As AICTE Central Admin, navigate to `/reference-data`.
   - View the live **Sovereign Cryptographic Vault** card showing the SHA-256 Merkle root digest over the Supabase dataset.
   - Click **Re-Verify Cryptographic Consensus** to test real-time tamper-evident validation.
3. **Institutional Upload & Reconciliation**:
   - As College Nodal Officer, navigate to `/uploads`.
   - Upload any CSV or Excel file or view Batch #2 (`supernumerary_tfw_coep.csv`).
   - Observe deterministic Python discrepancy flags (e.g. `RULE_UNKNOWN_PROGRAMME`).
4. **Central Advisory ("Give an Idea") & 1-Click Fix**:
   - Central Admin clicks **+ Give an Idea** on Batch #2 and issues an advisory to remap `BTECH-AI` to `BTECH-CSE`.
   - College Nodal Officer clicks **Apply AICTE Advisory Recommendation**.
   - The batch is automatically re-reconciled, the backing file is synchronized, and errors are resolved into compliance.
5. **Ed25519 Verification Receipt**:
   - Navigate to `/verification` and verify a student's public certificate or Ed25519 cryptographic token.

---

## Maintenance & Free-Tier Optimization Tips
- **Supabase Free Tier**: Free tier projects pause after 1 week of zero queries. Any access from the live application automatically resumes the database within seconds.
- **Render Free Tier**: Spins down after 15 minutes of inactivity; the first request may take 20-30 seconds to wake up (cold start).
- **Data Privacy**: All data is pre-configured with synthetic markers complying with the DPDP Act 2023. No actual citizen PII is exposed.
