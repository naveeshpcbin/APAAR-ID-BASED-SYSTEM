-- ============================================================================
-- PRAMAAN-AICTE: Sovereign Dual-Portal Admission Reconciliation Platform
-- Problem Statement: SIH26263 | Theme: Smart Automation
-- Complete Supabase Cloud PostgreSQL DDL & Seed Schema
-- ============================================================================
-- Description:
-- Complete, authoritative SQL script for provisioning on Supabase PostgreSQL.
-- Includes all 20 relational models, foreign key relationships, performance
-- indexes, Row Level Security (RLS) policies, and foundational reference data.
-- ============================================================================

-- Enable pgcrypto for UUID and cryptographic hashing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. INSTITUTIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institutions (
    id SERIAL PRIMARY KEY,
    aicte_id VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    state VARCHAR(64) NOT NULL,
    district VARCHAR(64) NOT NULL,
    institution_type VARCHAR(64) DEFAULT 'STATE_GOVT_AIDED',
    status VARCHAR(32) DEFAULT 'APPROVED',
    contact_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 2. INSTITUTION USERS (Nodal Officers, Central Admins, Regional Officers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institution_users (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER REFERENCES institutions(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    role VARCHAR(32) DEFAULT 'INSTITUTION_NODAL',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. ACADEMIC PROGRAMMES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS programmes (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    programme_code VARCHAR(32) NOT NULL,
    programme_name VARCHAR(128) NOT NULL,
    degree_level VARCHAR(32) DEFAULT 'UG',
    duration_years INTEGER DEFAULT 4,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_institution_programme UNIQUE (institution_id, programme_code)
);

-- ----------------------------------------------------------------------------
-- 4. APPROVAL SNAPSHOTS (AICTE Sanctioned Intakes & Quotas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS approval_snapshots (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    programme_id INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    academic_year VARCHAR(16) NOT NULL,
    approved_intake INTEGER NOT NULL,
    supernumerary_quota JSONB DEFAULT '{"TFW": 3, "EWS": 6}'::jsonb,
    approval_letter_ref VARCHAR(128) NOT NULL,
    policy_version VARCHAR(32) DEFAULT 'AICTE-APH-2026-V1',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_programme_approval UNIQUE (institution_id, programme_id, academic_year)
);

-- ----------------------------------------------------------------------------
-- 5. POLICY RULE SETS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS policy_rule_sets (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    version VARCHAR(32) NOT NULL,
    description TEXT,
    rules_config JSONB DEFAULT '{}'::jsonb,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 6. INSTITUTIONAL DECLARATIONS (College Declared Capacities)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS institutional_declarations (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    programme_id INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    academic_year VARCHAR(16) NOT NULL,
    declared_intake INTEGER NOT NULL DEFAULT 0,
    reporting_scope VARCHAR(64) DEFAULT 'ALL',
    declaration_ref VARCHAR(128),
    declared_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_programme_declaration UNIQUE (institution_id, programme_id, academic_year)
);

-- ----------------------------------------------------------------------------
-- 7. SYNTHETIC APAAR REGISTRY (Authoritative Reference Benchmark)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS synthetic_apaar_registry (
    id SERIAL PRIMARY KEY,
    apaar_id VARCHAR(12) UNIQUE NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(16) DEFAULT 'MALE',
    status VARCHAR(32) DEFAULT 'DEMO_REFERENCE_MATCH' NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 8. STUDENT IDENTITIES (HMAC Blinded National Academic Identifier)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS student_identities (
    id SERIAL PRIMARY KEY,
    apaar_hash VARCHAR(64) UNIQUE NOT NULL,
    apaar_masked VARCHAR(16) NOT NULL,
    full_name VARCHAR(128) NOT NULL,
    dob DATE NOT NULL,
    gender VARCHAR(16) DEFAULT 'MALE',
    verification_status VARCHAR(32) DEFAULT 'VERIFIED',
    provider_name VARCHAR(64) DEFAULT 'MOCK_APAAR_SANDBOX',
    provider_reference VARCHAR(128),
    verified_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 9. UPLOAD BATCHES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upload_batches (
    id SERIAL PRIMARY KEY,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    submitted_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    academic_year VARCHAR(16) NOT NULL,
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    warning_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'UPLOADED',
    mapping_config JSONB DEFAULT '{}'::jsonb,
    review_notes TEXT,
    reviewed_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 10. VALIDATION RUNS (Versioned Multi-Run Historical Traceability)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_runs (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    run_number INTEGER DEFAULT 1,
    triggered_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    status VARCHAR(32) DEFAULT 'COMPLETED',
    total_rows INTEGER DEFAULT 0,
    duplicate_rows INTEGER DEFAULT 0,
    unique_records INTEGER DEFAULT 0,
    blocking_errors INTEGER DEFAULT 0,
    requiring_review INTEGER DEFAULT 0,
    eligible_to_proceed INTEGER DEFAULT 0,
    declared_intake INTEGER DEFAULT 0,
    declared_discrepancy INTEGER DEFAULT 0,
    reference_versions_json JSONB DEFAULT '{}'::jsonb,
    summary_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 11. VALIDATION FINDINGS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_findings (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    validation_run_id INTEGER REFERENCES validation_runs(id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL,
    field_name VARCHAR(64) NOT NULL,
    rule_id VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    finding_type VARCHAR(64) DEFAULT 'VALIDATION_CHECK',
    submitted_value TEXT,
    expected_value TEXT,
    reference_source_id VARCHAR(128),
    rule_version VARCHAR(64) DEFAULT 'AICTE-APH-2026-V1',
    message TEXT NOT NULL,
    recommended_action TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 12. STAGED BATCH ROWS (Interactive In-Browser Spreadsheet Grid)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staged_batch_rows (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    row_index INTEGER NOT NULL,
    apaar_id VARCHAR(32),
    student_name VARCHAR(128),
    programme_code VARCHAR(32),
    category VARCHAR(32) DEFAULT 'OPEN',
    gender VARCHAR(16) DEFAULT 'MALE',
    dob DATE,
    admission_quota VARCHAR(32) DEFAULT 'STATE_GOVT',
    admission_date DATE,
    merit_rank INTEGER,
    is_supernumerary BOOLEAN DEFAULT FALSE,
    status VARCHAR(32) DEFAULT 'ELIGIBLE',
    raw_data JSONB DEFAULT '{}'::jsonb,
    normalized_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 13. ADMISSION RECORDS (SIH-R2: Actual Enrolment with Supernumerary & Quotas)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admission_records (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES student_identities(id) ON DELETE CASCADE,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    programme_id INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES upload_batches(id) ON DELETE SET NULL,
    academic_year VARCHAR(16) NOT NULL,
    enrollment_no VARCHAR(64) NOT NULL,
    category VARCHAR(32) DEFAULT 'OPEN',
    admission_quota VARCHAR(32) DEFAULT 'STATE_GOVT',
    nationality_type VARCHAR(32) DEFAULT 'DOMESTIC',
    is_supernumerary BOOLEAN DEFAULT FALSE,
    admission_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 14. CONSENT GRANTS (DPDP Act 2023 Digital Personal Data Protection)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consent_grants (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES student_identities(id) ON DELETE CASCADE,
    consent_type VARCHAR(64) DEFAULT 'APAAR_IDENTITY_VERIFICATION',
    granted_by VARCHAR(32) DEFAULT 'STUDENT',
    is_granted BOOLEAN DEFAULT TRUE,
    grant_timestamp TIMESTAMPTZ DEFAULT NOW(),
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 15. ADMISSION CONFLICTS (SIH-R3: Cross-Institution Duplicate Collisions)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admission_conflicts (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(32) UNIQUE NOT NULL,
    student_id INTEGER NOT NULL REFERENCES student_identities(id) ON DELETE CASCADE,
    record_a_id INTEGER NOT NULL REFERENCES admission_records(id) ON DELETE CASCADE,
    record_b_id INTEGER NOT NULL REFERENCES admission_records(id) ON DELETE CASCADE,
    conflict_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'OPEN',
    resolution VARCHAR(64),
    resolution_notes TEXT,
    resolved_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ----------------------------------------------------------------------------
-- 16. ANOMALY CASES (Explainable Regulatory Statistical Outliers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anomaly_cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(32) UNIQUE NOT NULL,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    programme_id INTEGER REFERENCES programmes(id) ON DELETE SET NULL,
    academic_year VARCHAR(16) NOT NULL,
    risk_score FLOAT NOT NULL,
    anomaly_type VARCHAR(64) NOT NULL,
    signals_json JSONB DEFAULT '{}'::jsonb,
    explanation TEXT NOT NULL,
    status VARCHAR(32) DEFAULT 'PENDING_REVIEW',
    review_notes TEXT,
    reviewed_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 17. VERIFICATION RECEIPTS (Ed25519 Asymmetric Digital Signatures & QR)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS verification_receipts (
    id SERIAL PRIMARY KEY,
    receipt_token VARCHAR(64) UNIQUE NOT NULL,
    student_id INTEGER NOT NULL REFERENCES student_identities(id) ON DELETE CASCADE,
    admission_record_id INTEGER NOT NULL REFERENCES admission_records(id) ON DELETE CASCADE,
    claim_scope VARCHAR(64) DEFAULT 'ACTIVE_ENROLMENT_STATUS',
    ed25519_signature TEXT NOT NULL,
    payload_digest VARCHAR(64) NOT NULL,
    canonical_payload JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    revocation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 18. IMMUTABLE AUDIT EVENTS (SHA-256 Hash Chained Ledger)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    sequence_no BIGINT UNIQUE NOT NULL,
    actor_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    actor_email VARCHAR(255),
    actor_role VARCHAR(32) NOT NULL,
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    correlation_id VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 19. BATCH DISPUTE QUERIES (College Exemption Requests & Messages to AICTE)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batch_dispute_queries (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    row_id INTEGER REFERENCES staged_batch_rows(id) ON DELETE SET NULL,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    raised_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    subject VARCHAR(255) NOT NULL,
    category VARCHAR(64) DEFAULT 'MISSING_APAAR_UIDAI_FAIL',
    student_identifier VARCHAR(128),
    message TEXT NOT NULL,
    status VARCHAR(32) DEFAULT 'PENDING_REVIEW',
    aicte_reply TEXT,
    resolved_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 20. AICTE CENTRAL ADVISORIES ("Give an Idea" / Policy Recommendations)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aicte_central_advisories (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    institution_id INTEGER NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    advisory_type VARCHAR(64) DEFAULT 'PROGRAMME_REMAP_RECOMMENDATION',
    title VARCHAR(255) NOT NULL,
    idea_description TEXT NOT NULL,
    recommended_action JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_by_user_id INTEGER REFERENCES institution_users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ
);

-- ----------------------------------------------------------------------------
-- Performance Indexes
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_apaar_registry_id ON synthetic_apaar_registry(apaar_id);
CREATE INDEX IF NOT EXISTS idx_staged_rows_batch ON staged_batch_rows(batch_id);
CREATE INDEX IF NOT EXISTS idx_staged_rows_prog ON staged_batch_rows(batch_id, programme_code);
CREATE INDEX IF NOT EXISTS idx_findings_batch ON validation_findings(batch_id);
CREATE INDEX IF NOT EXISTS idx_audit_seq ON audit_events(sequence_no);
CREATE INDEX IF NOT EXISTS idx_admissions_student ON admission_records(student_id);
CREATE INDEX IF NOT EXISTS idx_admissions_inst ON admission_records(institution_id, academic_year);
CREATE INDEX IF NOT EXISTS idx_conflicts_case ON admission_conflicts(case_number);
CREATE INDEX IF NOT EXISTS idx_receipts_token ON verification_receipts(receipt_token);

-- ----------------------------------------------------------------------------
-- Row-Level Security (RLS) Configuration
-- ----------------------------------------------------------------------------
ALTER TABLE synthetic_apaar_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE institutional_declarations ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE staged_batch_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE admission_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_receipts ENABLE ROW LEVEL SECURITY;

-- Transparent Public Verification Policies
CREATE POLICY "Public read on synthetic_apaar_registry" ON synthetic_apaar_registry FOR SELECT USING (true);
CREATE POLICY "Public read on approval_snapshots" ON approval_snapshots FOR SELECT USING (true);
CREATE POLICY "Public read on institutional_declarations" ON institutional_declarations FOR SELECT USING (true);
CREATE POLICY "Public verification on verification_receipts" ON verification_receipts FOR SELECT USING (is_revoked = false);

-- ============================================================================
-- SEED FOUNDATIONAL REFERENCE DATA
-- ============================================================================

-- 1. Demo Institutions
INSERT INTO institutions (id, aicte_id, name, state, district, institution_type, status, contact_email) VALUES
(1, '1-COEP-PUNE-001', 'COEP Technological University', 'Maharashtra', 'Pune', 'STATE_GOVT_AUTONOMOUS', 'APPROVED', 'nodal.coep@coep.ac.in'),
(2, '1-DTU-DELHI-001', 'Delhi Technological University (DTU)', 'Delhi', 'North West Delhi', 'STATE_GOVT_AIDED', 'APPROVED', 'nodal.dtu@dtu.ac.in'),
(3, '1-RVCE-BLR-001', 'RV College of Engineering', 'Karnataka', 'Bengaluru Urban', 'PRIVATE_UNAIDED', 'APPROVED', 'nodal.rvce@rvce.edu.in'),
(4, '1-JU-KOLKATA-001', 'Jadavpur University', 'West Bengal', 'Kolkata', 'STATE_GOVT_AIDED', 'APPROVED', 'nodal.ju@jadavpuruniversity.in')
ON CONFLICT (id) DO NOTHING;

-- 2. Evaluator Demo Users (All Passwords correspond to documented roles)
-- Password hashes created using standard bcrypt compatible with the application
INSERT INTO institution_users (id, institution_id, email, hashed_password, full_name, role, is_active) VALUES
(1, NULL, 'aicte.admin@pramaan.gov.in', '$2b$12$609vR/0G87.kGg9n0fUjD.jN3.5eYv1.gV7Qo4eN7lA6Ff2g0gS3O', 'Dr. Sunita Deshmukh (Advisor-I)', 'AICTE_ADMIN', true),
(2, NULL, 'ro.mumbai@aicte.gov.in', '$2b$12$609vR/0G87.kGg9n0fUjD.jN3.5eYv1.gV7Qo4eN7lA6Ff2g0gS3O', 'Shri Rajesh Kulkarni (Regional Officer)', 'REGIONAL_OFFICER', true),
(3, 2, 'nodal.dtu@dtu.ac.in', '$2b$12$609vR/0G87.kGg9n0fUjD.jN3.5eYv1.gV7Qo4eN7lA6Ff2g0gS3O', 'Prof. Amit Srivastava (Nodal Officer)', 'INSTITUTION_NODAL', true),
(4, 1, 'nodal.coep@coep.ac.in', '$2b$12$609vR/0G87.kGg9n0fUjD.jN3.5eYv1.gV7Qo4eN7lA6Ff2g0gS3O', 'Dr. Sandeep Meshram (Dean Academics)', 'INSTITUTION_NODAL', true),
(5, NULL, 'verifier.corp@tcs.com', '$2b$12$609vR/0G87.kGg9n0fUjD.jN3.5eYv1.gV7Qo4eN7lA6Ff2g0gS3O', 'Vikramaditya Sen (Corporate Verifier)', 'VERIFIER', true)
ON CONFLICT (id) DO NOTHING;

-- Reset sequences
SELECT setval('institutions_id_seq', (SELECT COALESCE(MAX(id), 1) FROM institutions));
SELECT setval('institution_users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM institution_users));
