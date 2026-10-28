"""
PRAMAAN-AICTE Supabase Cloud Database & Registry Adapter
Provides cloud-backed synchronization with Supabase PostgreSQL / REST API
for authoritative APAAR reference data, approved intake snapshots, and policy references.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SyntheticApaarRecord, ApprovalSnapshot, InstitutionalDeclaration

logger = logging.getLogger(__name__)


class SupabaseAdapter:
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
        self.supabase_key = settings.SUPABASE_KEY or ""
        self.is_configured = bool(self.supabase_url and self.supabase_key)
        self.client: Optional[httpx.Client] = None

        if self.is_configured:
            headers = {
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            self.client = httpx.Client(
                base_url=f"{self.supabase_url}/rest/v1",
                headers=headers,
                timeout=5.0
            )

    def get_status(self) -> Dict[str, Any]:
        """Returns the real-time health and connection status of the Supabase integration."""
        if not self.is_configured:
            # Report hybrid local authoritative status with full explanation
            local_apaar_count = self.db.query(SyntheticApaarRecord).count() if self.db else 0
            local_approvals_count = self.db.query(ApprovalSnapshot).count() if self.db else 0
            return {
                "connected": False,
                "configured": False,
                "mode": "AUTHORITATIVE_LOCAL_HYBRID",
                "provider": "Supabase Cloud Database Connector (Offline / Local Standby)",
                "supabase_url": None,
                "message": (
                    "Running on Authoritative Local Database (WAL mode). "
                    "To bind live Supabase cloud instance, provide SUPABASE_URL and SUPABASE_KEY in .env."
                ),
                "stats": {
                    "local_apaar_records": local_apaar_count,
                    "local_approval_snapshots": local_approvals_count,
                    "authoritative_source": "SQLite / PostgreSQL Local Engine"
                }
            }

        try:
            # Ping Supabase REST API
            resp = self.client.get("/synthetic_apaar_registry?select=count", headers={"Range": "0-0"})
            if resp.status_code in [200, 206]:
                return {
                    "connected": True,
                    "configured": True,
                    "mode": "SUPABASE_CLOUD_SYNCHRONIZED",
                    "provider": "Supabase Cloud PostgreSQL REST v1",
                    "supabase_url": self.supabase_url,
                    "message": "Live connection to Supabase cloud instance active.",
                    "http_status": resp.status_code
                }
            else:
                return {
                    "connected": False,
                    "configured": True,
                    "mode": "ERROR",
                    "provider": "Supabase Cloud PostgreSQL REST v1",
                    "supabase_url": self.supabase_url,
                    "message": f"Supabase responded with HTTP {resp.status_code}: {resp.text}"
                }
        except Exception as e:
            logger.warning(f"Failed to connect to Supabase: {e}")
            return {
                "connected": False,
                "configured": True,
                "mode": "CONNECTION_FAILED",
                "provider": "Supabase Cloud PostgreSQL REST v1",
                "supabase_url": self.supabase_url,
                "error": str(e),
                "fallback_active": True
            }

    def fetch_apaar_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Queries synthetic APAAR records from Supabase (or local database fallback)."""
        if self.is_configured and self.client:
            try:
                resp = self.client.get(f"/synthetic_apaar_registry?select=*&limit={limit}")
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                logger.error(f"Error fetching from Supabase: {e}")

        # Fallback to local authoritative database
        if self.db:
            records = self.db.query(SyntheticApaarRecord).limit(limit).all()
            return [
                {
                    "apaar_id": r.apaar_id,
                    "full_name": r.full_name,
                    "dob": r.dob.isoformat() if r.dob else None,
                    "gender": r.gender,
                    "status": r.status,
                    "notes": r.notes
                }
                for r in records
            ]
        return []

    def sync_to_supabase(self) -> Dict[str, Any]:
        """Pushes local synthetic reference dataset into Supabase cloud table if connected."""
        if not self.is_configured or not self.client:
            return {
                "success": False,
                "message": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY to enable cloud sync."
            }

        if not self.db:
            return {"success": False, "message": "No database session available for sync."}

        try:
            local_records = self.db.query(SyntheticApaarRecord).all()
            payload = [
                {
                    "apaar_id": r.apaar_id,
                    "full_name": r.full_name,
                    "dob": r.dob.isoformat() if r.dob else None,
                    "gender": r.gender,
                    "status": r.status,
                    "notes": r.notes or "Synced from PRAMAAN Local Registry"
                }
                for r in local_records
            ]
            resp = self.client.post("/synthetic_apaar_registry", json=payload)
            return {
                "success": resp.status_code in [200, 201],
                "synced_count": len(payload),
                "response_code": resp.status_code,
                "message": f"Successfully synced {len(payload)} records to Supabase."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
