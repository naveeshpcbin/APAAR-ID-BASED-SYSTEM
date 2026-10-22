# Architecture & Design Specification: PRAMAAN-AICTE

## 1. System Vision & Problem Statement

**PRAMAAN-AICTE** (*Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network*) addresses Smart India Hackathon 2026 problem statement **SIH26263**:
> "Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions."

The platform establishes an end-to-end, privacy-respecting regulatory workflow that connects technical education institutions, student identity verification, compliance rules, anomaly detection, and tamper-evident auditing.

---

## 2. Architectural Pillars

```text
+-----------------------------------------------------------------------------------+
|                              PRESENTATION LAYER                                   |
|   Next.js 14 App Router | React Server Components | Tailwind CSS | Recharts       |
|                                                                                   |
|  [AICTE Central Oversight]   [Institution Portal]   [Public/Verifier QR Portal]  |
+----------------------------------------+------------------------------------------+
                                         | REST / JSON (Strict Pydantic v2 schemas)
+----------------------------------------v------------------------------------------+
|                                APPLICATION CORE                                   |
|                    FastAPI (Modular Monolith) with Python 3.10                    |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                EXPLAINABLE ADMISSION RECONCILIATION ENGINE                  |  |
|  |  1. Ingestion & Column Mapping Normalizer                                   |  |
|  |  2. APAAR Identifier Syntax & Deterministic Identity Provider Adapter        |  |
|  |  3. Deduplication & Cross-Institution Active Enrolment Conflict Detector    |  |
|  |  4. Versioned Approval Snapshot & Category Capacity Evaluator               |  |
|  |  5. Statistical & Rule-Based Anomaly Scoring Service                         |  |
|  |  6. Transactional Staging & Controlled Commit Pipeline                       |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                         TRUST & SECURITY SERVICES                           |  |
|  |  - Cryptographic SHA-256 Tamper-Evident Hash Chain Audit Log                |  |
|  |  - Ed25519 Asymmetric Digital Signature Verification Receipts               |  |
|  |  - RBAC & Institution Data Isolation (Tenant Boundary Security)             |  |
|  |  - Zero-PII Leakage Policy (Hashed Search Indexes, Opaque Tokens)            |  |
|  +-----------------------------------------------------------------------------+  |
+----------------------------------------+------------------------------------------+
                                         | SQLAlchemy 2 (Dual SQLite / PostgreSQL)
+----------------------------------------v------------------------------------------+
|                                PERSISTENCE LAYER                                  |
|   Relational Schema with Foreign Keys, Composite Indexes, and Transaction Safety  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Data Flow: The Ingestion to Reconciliation Pipeline

1. **Pre-flight Ingestion**:
   - Institutional officer uploads CSV / XLSX file.
   - Smart header normalizer matches column names against known schemas (e.g., `apaar_id`, `student_name`, `dob`, `programme_code`, `category`, `admission_quota`).
   - Operator confirms or adjusts mappings before processing.

2. **Stage 1: Syntactic & Schema Validation**:
   - Validation against strict regexes (e.g. 12-digit numeric APAAR format, date formats, valid quota tags).
   - Generates row-level findings with distinct severity: `ERROR`, `WARNING`, `INFO`.

3. **Stage 2: Identity Verification Adapter**:
   - Calls the `IdentityProviderInterface`.
   - In production: Plugs into MeriPehchaan / ABC / DigiLocker gateway.
   - In demo/prototype: Deterministic Mock APAAR Adapter returns verified status, identity mismatch, not-found, or simulated provider downtime with zero third-party data leakage.

4. **Stage 3: Cross-Institution Duplicate & Conflict Analysis**:
   - Checks within-batch duplicates.
   - Scans central repository for overlapping active enrolments in the same academic year across different institutions.
   - Classifies findings as `ACTIVE_DUPLICATE_CONFLICT` or legitimate lifecycle events (e.g. `WITHDRAWN`, `TRANSFERRED`).

5. **Stage 4: Versioned Approval Intake & Quota Verification**:
   - Queries versioned `ApprovalSnapshot` for the institution, programme, and academic year.
   - Evaluates current confirmed admissions + proposed admissions against Approved Intake and Category limits (EWS, TFW, Supernumerary).
   - Records calculation details and policy version used.

6. **Stage 5: Anomaly Scoring & Priority Ranking**:
   - Computes risk indicators: intake spikes, category anomalies, submission time clustering, high duplicate ratios.
   - Returns structured explanation for regulatory officers.

7. **Stage 6: Controlled Commit & Audit Hash-Chaining**:
   - Clean records committed in an atomic database transaction.
   - High-severity conflicting records quarantined in case-management queue.
   - Every state transition logged to the SHA-256 tamper-evident audit ledger.
