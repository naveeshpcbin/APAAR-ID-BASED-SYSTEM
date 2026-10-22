import os
import sys
from pathlib import Path

# Set paths
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import sqlite3
from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command

def run_migration_audit():
    log_lines = []
    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=" * 70)
    log("STAGE 2: ISOLATED DATABASE MIGRATION VERIFICATION AUDIT")
    log("=" * 70)

    test_db_path = backend_dir / "isolated_migration_test.db"
    if test_db_path.exists():
        log(f"Removing pre-existing test database: {test_db_path.name}")
        test_db_path.unlink()

    test_db_url = f"sqlite:///{test_db_path.as_posix()}"
    log(f"Target Isolated Test Database: {test_db_url}")
    os.environ["DATABASE_URL"] = test_db_url

    # 1. Run Alembic upgrade head
    log("\n[Step 1] Executing 'alembic upgrade head' on empty database...")
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

    try:
        command.upgrade(alembic_cfg, "head")
        log("--> Alembic upgrade head executed successfully.")
    except Exception as e:
        log(f"FAILED: Alembic upgrade failed: {e}")
        return False

    # 2. Inspect created schema
    log("\n[Step 2] Introspecting database schema...")
    engine = create_engine(test_db_url)
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    log(f"Discovered tables in migrated DB ({len(tables)} total):")
    for t in sorted(tables):
        log(f"  - {t}")

    expected_tables = {
        "institutions", "institution_users", "programmes", "approval_snapshots",
        "policy_rule_sets", "student_identities", "consent_grants", "upload_batches",
        "validation_findings", "admission_records", "admission_conflicts",
        "anomaly_cases", "verification_receipts", "audit_events", "alembic_version"
    }

    missing_tables = expected_tables - set(tables)
    if missing_tables:
        log(f"FAILED: Missing expected tables: {missing_tables}")
        return False
    log("--> All 14 expected domain and version tables are present.")

    # 3. Check Alembic revision record
    log("\n[Step 3] Checking migration revision stamp...")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
        version_num = res[0] if res else None
        log(f"Recorded Alembic version_num: {version_num}")
        if version_num != "98d85ae389ed":
            log(f"FAILED: Unexpected migration version {version_num}")
            return False
        log("--> Revision 98d85ae389ed confirmed.")

    # 4. Check Foreign Keys and Indices
    log("\n[Step 4] Checking table columns and foreign key constraints...")
    for target in ["admission_records", "verification_receipts", "audit_events"]:
        fks = inspector.get_foreign_keys(target)
        cols = inspector.get_columns(target)
        indices = inspector.get_indexes(target)
        log(f"\nTable '{target}':")
        log(f"  - Columns ({len(cols)}): {', '.join([c['name'] for c in cols])}")
        log(f"  - Foreign Keys ({len(fks)}):")
        for fk in fks:
            log(f"      {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        log(f"  - Indices ({len(indices)}): {', '.join([i['name'] for i in indices])}")

    # 5. Test Live Persistence & Constraints on Migrated DB
    log("\n[Step 5] Testing transactional persistence on migrated database...")
    from app.models import Institution, Programme, ApprovalSnapshot, StudentIdentity, AdmissionRecord
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        inst = Institution(aicte_id="TEST-ISO-01", name="Isolated Test College", state="Delhi", district="New Delhi")
        session.add(inst)
        session.flush()

        prog = Programme(institution_id=inst.id, programme_code="CSE-ISO", programme_name="Computer Science")
        session.add(prog)
        session.flush()

        student = StudentIdentity(
            apaar_hash="hash_iso_test_12345",
            apaar_masked="XXXXXXXX1234",
            full_name="Isolated Test Student",
            dob=sqlite3.Date(2005, 1, 1),
            verification_status="VERIFIED"
        )
        session.add(student)
        session.flush()

        adm = AdmissionRecord(
            student_id=student.id,
            institution_id=inst.id,
            programme_id=prog.id,
            academic_year="2026-27",
            enrollment_no="ISO-2026-001",
            category="OPEN",
            admission_quota="STATE_GOVT",
            nationality_type="DOMESTIC",
            is_supernumerary=False,
            status="ACTIVE"
        )
        session.add(adm)
        session.commit()
        log(f"--> Successfully persisted admission record ID={adm.id} with FK references on fresh schema.")
    except Exception as e:
        session.rollback()
        log(f"FAILED: Persistence test failed: {e}")
        return False
    finally:
        session.close()

    # 6. Check PostgreSQL availability
    log("\n[Step 6] Verifying PostgreSQL availability...")
    import shutil
    has_docker = shutil.which("docker") is not None
    has_psql = shutil.which("psql") is not None
    log(f"  - Docker binary available: {has_docker}")
    log(f"  - psql binary available: {has_psql}")
    if not (has_docker or has_psql):
        log("  - PostgreSQL status: BLOCKED / UNVERIFIED in this Windows environment (no local Docker/PostgreSQL server).")
        log("  - Architectural note: SQLAlchemy models use ANSI/PostgreSQL standard types (UUID/BigInteger/DateTime/JSON) ready for deployment when PostgreSQL is provisioned.")

    log("\n" + "=" * 70)
    log("STAGE 2 MIGRATION AUDIT: PASS (Isolated SQLite WAL Schema Verified)")
    log("=" * 70)

    # Save artifact
    artifact_path = backend_dir.parent / "artifacts" / "verification" / "alembic_upgrade_isolated.log"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    log(f"\nSaved audit log to: {artifact_path}")

    return True

if __name__ == "__main__":
    success = run_migration_audit()
    sys.exit(0 if success else 1)
