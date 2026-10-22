from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AuditEvent, InstitutionUser
from app.schemas.audit import AuditEventResponse, HashChainVerificationResponse
from app.core.hash_chain import verify_hash_chain_integrity
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])

@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(AuditEvent)
    if action:
        query = query.filter(AuditEvent.action == action)
    return query.order_by(AuditEvent.sequence_no.desc()).offset(offset).limit(limit).all()

@router.post("/verify-chain", response_model=HashChainVerificationResponse)
def verify_ledger_hash_chain(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Cryptographic verification endpoint: Computes and tests SHA-256 links across all sequential audit events.
    Verifies that no rows have been deleted, inserted, or modified.
    """
    result = verify_hash_chain_integrity(db=db)
    return HashChainVerificationResponse(
        is_valid=result["is_valid"],
        total_events=result["total_events"],
        head_hash=result.get("head_hash"),
        broken_at_sequence=result.get("broken_at_sequence"),
        reason=result.get("reason"),
        message=result["message"]
    )
