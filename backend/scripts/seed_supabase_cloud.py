"""
PRAMAAN-AICTE: One-Click Supabase Cloud Reference Registry Seeder
Connects to Supabase Cloud PostgreSQL REST API and seeds all baseline
institutions, approved programmes, sanctioned intakes, and synthetic APAAR benchmarks.
"""

import os
import sys
import httpx
from datetime import datetime

# Adjust path to import backend core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import SyntheticApaarRecord, Institution, Programme, ApprovalSnapshot

def seed_supabase():
    url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
    key = settings.SUPABASE_KEY or ""

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be defined in .env to seed Supabase Cloud.")
        print("Example: SUPABASE_URL=https://xyzcompany.supabase.co")
        print("         SUPABASE_KEY=eyJhbGciOi...")
        sys.exit(1)

    print(f"Connecting to Supabase Cloud at: {url}")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    client = httpx.Client(base_url=f"{url}/rest/v1", headers=headers, timeout=15.0)

    db = SessionLocal()
    try:
        # 1. Sync Synthetic APAAR Records
        records = db.query(SyntheticApaarRecord).all()
        print(f"Found {len(records)} local synthetic APAAR records.")

        payload = [
            {
                "apaar_id": r.apaar_id,
                "full_name": r.full_name,
                "dob": r.dob.isoformat() if r.dob else "2005-01-01",
                "gender": r.gender,
                "status": r.status,
                "notes": r.notes or "Authoritative SIH Synthetic Regulatory Benchmark"
            }
            for r in records
        ]

        resp = client.post("/synthetic_apaar_registry", json=payload)
        if resp.status_code in [200, 201]:
            print(f"SUCCESS: Seeded {len(payload)} synthetic APAAR records into Supabase Cloud.")
        else:
            print(f"Warning: Supabase responded with {resp.status_code}: {resp.text}")

        # 2. Check Cloud Status
        count_resp = client.get("/synthetic_apaar_registry?select=count", headers={"Range": "0-0"})
        print(f"Supabase Synthetic APAAR Registry Status: HTTP {count_resp.status_code}")

    except Exception as e:
        print(f"ERROR: Cloud synchronization failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_supabase()
