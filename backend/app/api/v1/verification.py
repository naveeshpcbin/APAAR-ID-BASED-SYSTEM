from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import VerificationReceipt, InstitutionUser
from app.schemas.receipt import (
    ReceiptIssueRequest, ReceiptIssueResponse, ReceiptVerificationResponse, ReceiptRevokeRequest,
    ConsentGrantRequest, ConsentGrantResponse
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

@router.get("/consent/{student_id}")
def get_student_consent(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    DPDP Act 2023 Consent Inquiry: Retrieves the active data-sharing consent status for a student.
    """
    try:
        return ReceiptService.get_student_consent(db=db, student_id=student_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/consent", response_model=ConsentGrantResponse)
def set_student_consent(
    req: ConsentGrantRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    DPDP Act 2023 Consent Management: Allows student or authorized institution nodal officer
    to grant or revoke digital verification consent with tamper-evident audit logging.
    """
    try:
        return ReceiptService.set_student_consent(
            db=db,
            student_id=req.student_id,
            is_granted=req.is_granted,
            consent_type=req.consent_type,
            granted_by=req.granted_by,
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
