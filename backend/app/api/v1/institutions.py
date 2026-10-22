from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Institution, Programme, InstitutionUser
from app.schemas.institution import InstitutionResponse, ProgrammeResponse
from app.api.deps import get_current_user, verify_institution_access

router = APIRouter(prefix="/institutions", tags=["Institutions"])

@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    state: Optional[str] = None,
    institution_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(Institution)
    
    # Institution users only see their own institution
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(Institution.id == current_user.institution_id)
    else:
        if state:
            query = query.filter(Institution.state.ilike(f"%{state}%"))
        if institution_type:
            query = query.filter(Institution.institution_type == institution_type)
        if search:
            query = query.filter(
                (Institution.name.ilike(f"%{search}%")) | 
                (Institution.aicte_id.ilike(f"%{search}%"))
            )

    return query.order_by(Institution.name.asc()).all()

@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    verify_institution_access(institution_id, current_user)
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return inst

@router.get("/{institution_id}/programmes", response_model=List[ProgrammeResponse])
def get_institution_programmes(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    verify_institution_access(institution_id, current_user)
    return db.query(Programme).filter(Programme.institution_id == institution_id).all()
