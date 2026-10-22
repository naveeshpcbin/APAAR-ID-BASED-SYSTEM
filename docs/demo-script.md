# 5-Minute Evaluator Demonstration Script: PRAMAAN-AICTE
**SIH 2026 Problem Statement SIH26263**

---

## Part 1: Executive Overview & Problem Context (Minute 0:00 - 1:00)

1. Open the application at `http://localhost:3000/dashboard`.
2. Highlight the core architectural achievement:
   - **Explainable Admission Reconciliation Engine**: Not a plain spreadsheet uploader, but a multi-stage regulatory engine that validates APAAR syntax, upstream identity assertions, sanctioned capacity, cross-institution conflicts, and risk anomalies.
3. Observe the live KPI cards:
   - **Active Admissions** vs **Unique APAARs** (ensuring 1-student-1-identity compliance).
   - **Sanctioned Intake Utilization**: Live progress bar comparing enrolled students against approved intake.
   - **Programme Capacity vs Active Enrolment** chart: Real-time capacity breakdown.
   - **Affirmative Action Distribution**: Reservation category proportions.

---

## Part 2: Cross-Institution Duplicate Dispute Adjudication (Minute 1:00 - 2:15)

1. Navigate to `/conflicts` via top-right card or sidebar.
2. Select Case **`CONF-2026-0042`**:
   - Point out student *Kunal Singhania* with masked APAAR `XXXXXXXX9012`.
   - Explain the side-by-side comparison:
     - **Claim A**: Admitted at *COEP Technological University* (CAP Round 1, State Govt Quota).
     - **Claim B**: Simultaneously submitted at *Delhi Technological University* (Management Quota).
3. Demonstrate Adjudication:
   - Select Claim A as the valid enrolment.
   - Select verdict: `Confirm Valid (Adjudicate Winning Seat)`.
   - Enter justification: *"Migration certificate validated from state portal; DTU concurrent seat cancelled."*
   - Click **Execute Adjudication & Append to Hash Chain**.
   - Notice the status change and the automatic audit entry created!

---

## Part 3: Explainable Regulatory Anomaly Detection (Minute 2:15 - 3:15)

1. Navigate to `/anomalies`.
2. Inspect Case **`ANOM-2026-0019`** (R.V. College of Engineering - Risk Score 78.5/100):
   - Highlight that this is **not a black-box AI claim**:
     - *What pattern was detected?* Concentrated Intake Spike (89% annual intake uploaded within 24 hours of portal closure).
     - *Supporting metrics*: Exact JSON payload showing `batch_records: 160`, `total_approved_intake: 180`.
     - *Action*: Click **Escalate to Formal Audit** or **Clear as Compliant**.

---

## Part 4: Cryptographic Ed25519 Signed Verification Receipts & QR Code (Minute 3:15 - 4:15)

1. Navigate to `/verification`.
2. Select an admitted student and click **Issue Asymmetric Signed Receipt & QR Code**:
   - Show the generated high-contrast QR code.
   - Point out the **Ed25519 digital signature** and **SHA-256 digest**.
   - Notice that the public token contains **zero raw student PII** (`rcpt_...`).
3. Click **Test Pre-seeded Valid Receipt** (`rcpt_532763c1caad4cf8bd1ea9bdf7a4b50d`) and click **Verify**:
   - Displays the green **AUTHENTIC_AND_VERIFIED** badge.
4. Click **Test Invalid / Forged Token**:
   - Immediately rejected with **NOT_FOUND** / **INVALID_SIGNATURE**.
5. Click **Open Public Portal** to show the standalone employer/public verifier view (`/verification/receipt/[token]`).

---

## Part 5: Tamper-Evident SHA-256 Audit Ledger (Minute 4:15 - 5:00)

1. Navigate to `/audit`.
2. Show the sequential immutable ledger entries (`#1, #2, #3...`).
3. Click **Verify Hash Chain Integrity**:
   - The engine validates every cryptographic link from Genesis Hash (`0000...`) to the Head Hash.
   - Shows the green banner: **Cryptographic Hash Chain Verified (100% Unbroken Integrity)**!
4. Switch personas using the top bar **Role Switcher** (AICTE Central &rarr; DTU Delhi &rarr; COEP Pune) to demonstrate institutional tenant isolation!
