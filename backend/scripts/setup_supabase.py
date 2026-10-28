"""
PRAMAAN-AICTE: Supabase Cloud Database Provisioning & Migration Utility
Connects to a remote or local Supabase PostgreSQL database, validates connectivity,
creates all required schema tables via SQLAlchemy metadata, enables indexes,
and seeds foundational reference data (institutions, programmes, snapshots, users, synthetic registry).

Usage:
    python scripts/setup_supabase.py
    python scripts/setup_supabase.py --db-url "postgresql://postgres.[REF]:[PASS]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
"""

import sys
import os
import argparse
import time

# Ensure parent directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base
from app.models import (
    Institution, InstitutionUser, Programme, ApprovalSnapshot,
    StudentIdentity, AdmissionRecord, UploadBatch, ValidationFinding,
    AdmissionConflict, AnomalyCase, VerificationReceipt, AuditEvent,
    SyntheticApaarRecord, InstitutionalDeclaration, ConsentGrant, PolicyRuleSet,
    StagedBatchRow, ValidationRun, BatchDisputeQuery, AicteCentralAdvisory
)
from scripts.seed_data import _seed_core_entities, _seed_synthetic_apaar_registry

import urllib.parse

def sanitize_db_url(raw_url: str) -> str:
    """
    Robustly sanitizes PostgreSQL / Supabase connection strings:
    - Strips surrounding brackets like [password] or [Naveeapaarid@26]
    - URL-encodes special characters in passwords (e.g. '@', '#', '%')
    - Normalizes postgres:// to postgresql://
    """
    if not raw_url or raw_url.startswith("sqlite"):
        return raw_url
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    
    if "://" in raw_url and "@" in raw_url:
        scheme, rest = raw_url.split("://", 1)
        user_pass, host_part = rest.rsplit("@", 1)
        if ":" in user_pass:
            username, password = user_pass.split(":", 1)
            if password.startswith("[") and password.endswith("]"):
                password = password[1:-1]
            if "%" not in password:
                password = urllib.parse.quote_plus(password)
            return f"{scheme}://{username}:{password}@{host_part}"
    return raw_url

def setup_supabase(db_url: str = None, seed: bool = True):
    print("=" * 70)
    print("   PRAMAAN-AICTE: SUPABASE CLOUD DATABASE SETUP & MIGRATION")
    print("=" * 70)

    # 1. Resolve Target Database URL
    raw_target_url = db_url or settings.SUPABASE_DATABASE_URL or settings.DATABASE_URL
    if not raw_target_url:
        print("[!] ERROR: No database connection URL provided.")
        print("    Please set SUPABASE_DATABASE_URL in .env or pass --db-url.")
        sys.exit(1)

    target_url = sanitize_db_url(raw_target_url)

    # Mask password for secure logging
    masked_url = target_url
    if "://" in masked_url and "@" in masked_url:
        scheme, rest = masked_url.split("://", 1)
        user_pass, host_part = rest.rsplit("@", 1)
        if ":" in user_pass:
            username = user_pass.split(":", 1)[0]
            masked_url = f"{scheme}://{username}:****@{host_part}"

    print(f"[*] Target Database: {masked_url}")

    # 2. Configure Engine
    connect_args = {}
    if "sslmode=" not in target_url and not target_url.startswith("sqlite"):
        connect_args["sslmode"] = "require"

    engine = create_engine(
        target_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )

    # 3. Test Connection
    print("[*] Testing connection to database...")
    t0 = time.time()
    try:
        with engine.connect() as conn:
            v_sql = "SELECT sqlite_version();" if "sqlite" in target_url else "SELECT version();"
            result = conn.execute(text(v_sql)).scalar()
            latency = (time.time() - t0) * 1000
            print(f"[+] Connected successfully! Latency: {latency:.1f}ms")
            print(f"[+] Server Version: {str(result)[:60]}...")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        print("\nTroubleshooting tips for Supabase:")
        print("  1. Verify your database password in the connection string.")
        print("  2. If using IPv4 only, ensure you use the Supabase Transaction Pooler port (6543).")
        print("  3. Check that your IP is allowed in Supabase Project Settings -> Database -> Network Restrictions.")
        sys.exit(1)

    # 4. Create Tables
    print("\n[*] Synchronizing schema and creating tables in Supabase...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"[+] Total tables registered in Supabase: {len(existing_tables)}")
    for tbl in sorted(existing_tables):
        print(f"    - {tbl}")

    # 5. Seed Core Reference Data
    if seed:
        print("\n[*] Checking reference data and users...")
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            inst_count = db.query(Institution).count()
            if inst_count == 0:
                print("[*] Empty database detected. Seeding foundational institutions, programmes, and users...")
                _seed_core_entities(db)
                print("[+] Core entities seeded successfully.")
            else:
                print(f"[+] Existing institutions found ({inst_count} records). Skipping entity overwrite.")

            apaar_count = db.query(SyntheticApaarRecord).count()
            if apaar_count == 0:
                print("[*] Seeding initial synthetic APAAR reference records...")
                _seed_synthetic_apaar_registry(db)
                print("[+] Synthetic APAAR registry initialized.")
            else:
                print(f"[+] Existing synthetic APAAR records found ({apaar_count} records).")
        except Exception as e:
            print(f"[!] Error seeding data: {e}")
            db.rollback()
        finally:
            db.close()

    print("\n" + "=" * 70)
    print("   SUPABASE PROVISIONING COMPLETE")
    print("=" * 70)
    print("Next steps to connect your application to this Supabase database:")
    print("  1. Update backend/.env:")
    print(f'     DATABASE_URL="{target_url}"')
    print("  2. Restart FastAPI backend:")
    print("     python -m uvicorn app.main:app --reload")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PRAMAAN-AICTE Supabase Setup Utility")
    parser.add_argument("--db-url", type=str, default=None, help="PostgreSQL connection string")
    parser.add_argument("--no-seed", action="store_true", help="Skip seeding test data")
    args = parser.parse_args()

    setup_supabase(db_url=args.db_url, seed=not args.no_seed)
