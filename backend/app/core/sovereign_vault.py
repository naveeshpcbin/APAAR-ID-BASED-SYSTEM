"""
PRAMAAN-AICTE Sovereign Cryptographic Data Vault
Provides tamper-evident cryptographic integrity seals, Merkle digests,
and cloud synchronization verification for synthetic reference datasets
stored in Supabase Cloud PostgreSQL and Authoritative Local Standby.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.models import (
    SyntheticApaarRecord, ApprovalSnapshot, InstitutionalDeclaration,
    Programme, Institution, AuditEvent
)
from app.core.hash_chain import append_audit_event

logger = logging.getLogger(__name__)


class SovereignDataVault:
    """
    Sovereign Cryptographic Integrity Engine for PRAMAAN-AICTE.
    Guarantees that synthetic reference datasets (APAAR registry, approved intakes, declarations)
    cannot be altered out-of-band without invalidating the regulatory cryptographic seal.
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_dataset_digest(self) -> Dict[str, Any]:
        """
        Computes a deterministic SHA-256 Merkle root across all reference datasets.
        """
        # 1. Canonicalize Synthetic APAAR records
        apaar_records = self.db.query(SyntheticApaarRecord).order_by(asc(SyntheticApaarRecord.apaar_id)).all()
        apaar_serialized = [
            f"{r.apaar_id}:{r.full_name}:{r.dob.isoformat() if r.dob else ''}:{r.gender}:{r.status}"
            for r in apaar_records
        ]
        apaar_hash = hashlib.sha256("\n".join(apaar_serialized).encode("utf-8")).hexdigest()

        # 2. Canonicalize Approved Intakes
        approvals = self.db.query(ApprovalSnapshot).order_by(asc(ApprovalSnapshot.id)).all()
        approvals_serialized = [
            f"{a.id}:{a.institution_id}:{a.programme_id}:{a.academic_year}:{a.approved_intake}:{json.dumps(a.supernumerary_quota or {}, sort_keys=True)}"
            for a in approvals
        ]
        approvals_hash = hashlib.sha256("\n".join(approvals_serialized).encode("utf-8")).hexdigest()

        # 3. Canonicalize Institutional Declarations
        declarations = self.db.query(InstitutionalDeclaration).order_by(asc(InstitutionalDeclaration.id)).all()
        declarations_serialized = [
            f"{d.id}:{d.institution_id}:{d.programme_id}:{d.academic_year}:{d.declared_intake}:{d.reporting_scope}"
            for d in declarations
        ]
        declarations_hash = hashlib.sha256("\n".join(declarations_serialized).encode("utf-8")).hexdigest()

        # 4. Master Sovereign Merkle Seal
        master_payload = f"{apaar_hash}|{approvals_hash}|{declarations_hash}"
        sovereign_seal = hashlib.sha256(master_payload.encode("utf-8")).hexdigest()

        return {
            "sovereign_seal": sovereign_seal,
            "components": {
                "synthetic_apaar_digest": apaar_hash,
                "approved_intake_digest": approvals_hash,
                "institutional_declarations_digest": declarations_hash
            },
            "record_counts": {
                "synthetic_apaar_records": len(apaar_records),
                "approval_snapshots": len(approvals),
                "institutional_declarations": len(declarations)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def verify_vault_integrity(self) -> Dict[str, Any]:
        """
        Compares live database state against the latest recorded sovereign audit seal.
        """
        current_digest = self.compute_dataset_digest()

        # Find latest VAULT_SEAL audit event
        last_seal_event = self.db.query(AuditEvent).filter(
            AuditEvent.action.in_(["SOVEREIGN_VAULT_SEALED", "REFERENCE_DATA_INITIALIZED"])
        ).order_by(AuditEvent.id.desc()).first()

        recorded_seal = None
        if last_seal_event and last_seal_event.metadata_json:
            recorded_seal = last_seal_event.metadata_json.get("sovereign_seal")

        is_verified = bool(recorded_seal and recorded_seal == current_digest["sovereign_seal"])

        return {
            "status": "VERIFIED" if is_verified else "UNSEALED_OR_MODIFIED",
            "is_valid": is_verified,
            "current_seal": current_digest["sovereign_seal"],
            "recorded_seal": recorded_seal,
            "components": current_digest["components"],
            "record_counts": current_digest["record_counts"],
            "last_seal_timestamp": last_seal_event.created_at.isoformat() if last_seal_event else None,
            "algorithm": "SHA-256 Merkle Sovereign Consensus Digest"
        }

    def seal_vault(self, actor_id: Optional[int], actor_email: Optional[str], actor_role: str, reason: str = "Admin Reference Data Update") -> Dict[str, Any]:
        """
        Commits a new cryptographic sovereign seal to the immutable audit event hash chain.
        """
        digest_info = self.compute_dataset_digest()

        event = append_audit_event(
            db=self.db,
            action="SOVEREIGN_VAULT_SEALED",
            entity_type="SovereignDataVault",
            entity_id="MASTER_REGULATORY_VAULT",
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            metadata_json={
                "sovereign_seal": digest_info["sovereign_seal"],
                "reason": reason,
                "record_counts": digest_info["record_counts"],
                "components": digest_info["components"]
            }
        )
        self.db.commit()

        return {
            "success": True,
            "sovereign_seal": digest_info["sovereign_seal"],
            "audit_sequence_no": event.sequence_no,
            "current_hash": event.current_hash,
            "message": "Sovereign cryptographic vault sealed and chained into immutable audit ledger."
        }
