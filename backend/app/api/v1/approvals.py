from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ApprovalSnapshot, Programme, InstitutionUser
from app.schemas.institution import ApprovalSnapshotResponse
from app.services.capacity_service import ApprovalCapacityService
from app.api.deps import get_current_user, require_roles, verify_institution_access

router = APIRouter(prefix="/approvals", tags=["Approvals & Policy Rules"])

@router.get("", response_model=List[ApprovalSnapshotResponse])
def list_approvals(
    institution_id: Optional[int] = None,
    academic_year: Optional[str] = Query(None, description="e.g. 2026-27"),
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(ApprovalSnapshot).join(Programme)
    
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(ApprovalSnapshot.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(ApprovalSnapshot.institution_id == institution_id)

    if academic_year:
        query = query.filter(ApprovalSnapshot.academic_year == academic_year)

    snapshots = query.all()
    results = []
    for s in snapshots:
        prog = db.query(Programme).filter(Programme.id == s.programme_id).first()
        results.append(ApprovalSnapshotResponse(
            id=s.id,
            programme_id=s.programme_id,
            programme_code=prog.programme_code if prog else None,
            academic_year=s.academic_year,
            approved_intake=s.approved_intake,
            supernumerary_quota=s.supernumerary_quota or {},
            approval_letter_ref=s.approval_letter_ref,
            policy_version=s.policy_version,
            is_active=s.is_active
        ))
    return results

@router.get("/capacity/evaluate")
def evaluate_programme_capacity(
    institution_id: int,
    programme_id: int,
    academic_year: str = "2026-27",
    incoming_count: int = 0,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    verify_institution_access(institution_id, current_user)
    return ApprovalCapacityService.evaluate_programme_capacity(
        db=db,
        institution_id=institution_id,
        programme_id=programme_id,
        academic_year=academic_year,
        incoming_count=incoming_count
    )
