from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models import InstitutionUser, Institution
from app.schemas.auth import Token, UserResponse, LoginRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login_for_access_token(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(InstitutionUser).filter(InstitutionUser.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    inst_name = None
    aicte_id = None
    if user.institution_id:
        inst = db.query(Institution).filter(Institution.id == user.institution_id).first()
        if inst:
            inst_name = inst.name
            aicte_id = inst.aicte_id

    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        institution_id=user.institution_id
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        email=user.email,
        full_name=user.full_name,
        institution_id=user.institution_id,
        institution_name=inst_name,
        aicte_id=aicte_id
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    inst_name = None
    if current_user.institution_id:
        inst = db.query(Institution).filter(Institution.id == current_user.institution_id).first()
        if inst:
            inst_name = inst.name

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        institution_id=current_user.institution_id,
        institution_name=inst_name,
        is_active=current_user.is_active
    )
