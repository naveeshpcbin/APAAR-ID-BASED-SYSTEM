# Validation Rules & Reconciliation Engine Specification: PRAMAAN-AICTE

## 1. Finding Severity Semantics

The reconciliation engine categorizes every validation finding into one of three distinct severities:

| Severity | Definition | Admission Lifecycle Impact | Operator Action Required |
| :--- | :--- | :--- | :--- |
| **`ERROR`** | Hard syntactic or regulatory barrier (e.g. invalid APAAR format, non-existent programme code, missing mandatory fields). | Record **cannot** be committed to active status. Staged as `REJECTED` or quarantined. | Operator must correct the data source or mapping and re-upload. |
| **`WARNING`** | Regulatory collision, quota saturation, or identity mismatch requiring human adjudication (e.g. active enrolment in another college, capacity limit reached). | Record placed into `UNDER_REVIEW` / `CONFLICT` case. Cannot graduate to verified status automatically. | AICTE Officer or Institutional Nodal Officer must review supporting documents. |
| **`INFO`** | Non-blocking observation (e.g. legitimate historical withdrawal detected, supernumerary quota utilized, minor column name normalization). | Record proceeds to standard commit pipeline. | Logged in the audit event ledger for administrative transparency. |

---

## 2. Rule Catalogue

### Rule Group 1: Syntactic & Schema Checks
- **`RULE_APAAR_FORMAT`** (`ERROR`):
  - *Condition*: APAAR identifier must be exactly 12 numeric digits (`^\d{12}$`).
  - *Rationale*: Official AICTE/MoE guidelines define APAAR as a 12-digit persistent identifier.
  - *Remediation*: Verify student's APAAR card or ABC ID card.
- **`RULE_MANDATORY_FIELDS`** (`ERROR`):
  - *Condition*: Student full name, date of birth, programme code, and academic year must be present.
  - *Remediation*: Supply missing columns in upload file.
- **`RULE_DATE_PLAUSIBILITY`** (`ERROR`):
  - *Condition*: Student age at admission must be plausibly between 14 and 80 years old.

### Rule Group 2: Identity Provider Adapter Checks
- **`RULE_IDENTITY_VERIFIED`** (`INFO`):
  - *Condition*: Identity adapter confirms APAAR number exists and name/DOB match within tolerance.
- **`RULE_IDENTITY_MISMATCH`** (`WARNING`):
  - *Condition*: APAAR number exists in registry, but name or DOB contradicts official record.
  - *Remediation*: Institutional officer must trigger manual verification or request updated proof.
- **`RULE_IDENTITY_NOT_FOUND`** (`WARNING`):
  - *Condition*: APAAR number not located in central identity registry.
  - *Remediation*: Check if student recently generated APAAR or if APAAR consent is pending.
- **`RULE_PROVIDER_UNAVAILABLE`** (`WARNING`):
  - *Condition*: Upstream identity gateway timed out or returned HTTP 503.
  - *Remediation*: Record staged for automated background retry; does not fail hard.

### Rule Group 3: Deduplication & Cross-Institution Conflicts
- **`RULE_WITHIN_BATCH_DUPLICATE`** (`ERROR`):
  - *Condition*: The exact same APAAR appears multiple times within the same upload batch.
  - *Remediation*: Deduplicate file rows before final commit.
- **`RULE_CROSS_INSTITUTION_ACTIVE_CONFLICT`** (`WARNING`):
  - *Condition*: Student with APAAR $X$ is currently marked as `ACTIVE` at Institution $A$ for academic year $Y$, while Institution $B$ submits an active admission for the same year $Y$.
  - *Remediation*: Opens an `AdmissionConflict` case. Regulators investigate whether a transfer occurred or if dual simultaneous full-time technical enrolment took place.
- **`RULE_LEGITIMATE_LIFECYCLE_TRANSITION`** (`INFO`):
  - *Condition*: Student with APAAR $X$ was previously enrolled at Institution $A$ but marked as `WITHDRAWN` or `TRANSFERRED` prior to admission at Institution $B$.
  - *Remediation*: Validated automatically without generating a dispute case.

### Rule Group 4: Intake & Capacity Compliance
- **`RULE_APPROVED_INTAKE_EXCEEDED`** (`ERROR` / `WARNING`):
  - *Condition*: Total active general admissions exceed `approved_intake` in the versioned `ApprovalSnapshot` for that programme and year.
  - *Remediation*: Admissions beyond approved intake are blocked or flagged for regulatory audit.
- **`RULE_QUOTA_OVERUTILIZATION`** (`WARNING`):
  - *Condition*: Supernumerary admissions (e.g. AICTE TFW - Tuition Fee Waiver, EWS) exceed configured limits (e.g. 5% for TFW, 10% for EWS).
  - *Remediation*: Flagged for state admission committee quota verification.

### Rule Group 5: Anomaly & Risk Indicators
- **`RULE_INTAKE_SURGE`** (`WARNING`):
  - *Condition*: Batch uploads 95%+ of annual intake in the final 24 hours of admission portal closure.
- **`RULE_CATEGORY_DISTRIBUTION_ANOMALY`** (`WARNING`):
  - *Condition*: Statistically extreme deviations in category distribution compared to state regulatory baseline.
