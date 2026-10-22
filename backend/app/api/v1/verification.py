from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import VerificationReceipt, InstitutionUser
from app.schemas.receipt import (
    ReceiptIssueRequest, ReceiptIssueResponse, ReceiptVerificationResponse, ReceiptRevokeRequest
)
from app.services.receipt_service import ReceiptService
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/verification", tags=["Cryptographic Verification & Receipts"])

@router.post("/receipts", response_model=ReceiptIssueResponse)
def issue_signed_receipt(
    req: ReceiptIssueRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    try:
        return ReceiptService.issue_receipt(
            db=db,
            admission_id=req.admission_id,
            expiry_days=req.expiry_days,
            claim_scope=req.claim_scope,
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/receipt/{receipt_token}", response_model=ReceiptVerificationResponse)
def verify_receipt_public(
    receipt_token: str,
    db: Session = Depends(get_db)
):
    """
    Public verification gateway: Validates Ed25519 signature, expiration, and revocation status.
    Guarantees zero raw PII is exposed in URL or unmasked.
    """
    return ReceiptService.verify_receipt(db=db, receipt_token=receipt_token)

@router.post("/receipts/revoke")
def revoke_receipt(
    req: ReceiptRevokeRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER", "INSTITUTION_NODAL"]))
):
    try:
        return ReceiptService.revoke_receipt(
            db=db,
            receipt_token=req.receipt_token,
            reason=req.reason,
            actor_id=current_user.id,
            actor_email=current_user.email
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
