# Security, Privacy & Integrity Specification: PRAMAAN-AICTE

## 1. Threat Model & Data Protection Posture

PRAMAAN-AICTE is designed around zero-trust institutional multi-tenancy and data minimization:

1. **Identifier Masking & Obfuscation**:
   - The platform strictly enforces that raw 12-digit APAAR numbers are **never** rendered unmasked in frontend views, logged in application logs, transmitted in public QR URLs, or included in plain error messages.
   - Database lookup uses a keyed HMAC-SHA256 digest (`apaar_hash`), preventing rainbow table reversal.
   - For authorized administrative interfaces, only masked strings (`XXXXXXXX4519`) are displayed.

2. **Tenant Boundary Enforcement (Institution-Level Isolation)**:
   - Institutional Nodal Officers have access strictly scoped to their own `institution_id`.
   - All REST queries and mutations filter through dependency-injected session context (`get_current_active_user`).
   - Cross-institution conflict adjudication is reserved for central or regional `AICTE_ADMIN` / `REGIONAL_OFFICER` roles.

3. **Tamper-Evident Hash Chain Audit Ledger**:
   - Every mutation (batch commit, conflict resolution, receipt generation, policy adjustment) emits an `AuditEvent`.
   - Each event contains:
     $$\text{current\_hash} = \text{SHA256}(\text{sequence\_no} \parallel \text{actor\_id} \parallel \text{action} \parallel \text{timestamp} \parallel \text{metadata\_json} \parallel \text{previous\_hash})$$
   - Any retrospective tampering, deletion, or modification of historical database rows breaks the cryptographic link and is immediately detected by the ledger verification engine.
   - *Limitation Disclosure*: Storing a hash chain in a mutable database provides tamper-evidence against casual modification or unauthorized row updates. True distributed immutability would require an external append-only log or hardware security module (HSM).

4. **Cryptographic Ed25519 Signed Verification Receipts**:
   - Third-party verifiers (e.g. employers, universities, state scholarship bodies) verify student claims without exposing the underlying student database.
   - Uses Ed25519 asymmetric elliptic-curve digital signatures.
   - Receipts are issued with an opaque random UUID token (`receipt_token`), an expiry timestamp, and a canonical signed payload.
   - The public verification endpoint checks the Ed25519 signature, expiration, and revocation status without displaying student PII or raw identifiers.

5. **Upload & File Security**:
   - Ingestion enforces MIME-type validation, file size bounds (max 10MB), and file hashing (`SHA-256`) to prevent replay attacks and duplicate submissions.
   - Column parsing strictly validates formats using Pydantic v2 schemas before database insertion.
