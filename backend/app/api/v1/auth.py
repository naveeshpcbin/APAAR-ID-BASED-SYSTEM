from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models import InstitutionUser, Institution, Programme, ApprovalSnapshot
from app.schemas.auth import Token, UserResponse, LoginRequest, InstitutionRegisterRequest
from app.api.deps import get_current_user
from app.core.hash_chain import append_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register-institution", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_new_institution(
    data: InstitutionRegisterRequest,
    db: Session = Depends(get_db)
):
    clean_aicte_id = data.aicte_id.strip()
    clean_email = data.nodal_email.strip().lower()

    # 1. Verify uniqueness of AICTE Permanent ID
    existing_inst = db.query(Institution).filter(Institution.aicte_id == clean_aicte_id).first()
    if existing_inst:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An institution is already registered with AICTE ID '{clean_aicte_id}'."
        )

    # 2. Verify uniqueness of Nodal Officer Email
    existing_user = db.query(InstitutionUser).filter(InstitutionUser.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A user with email '{clean_email}' already exists. Please sign in or use a different institutional email."
        )

    # 3. Create Institution
    inst = Institution(
        aicte_id=clean_aicte_id,
        name=data.name.strip(),
        state=data.state.strip(),
        district=data.district.strip(),
        institution_type=data.institution_type,
        status="APPROVED",
        contact_email=data.contact_email.strip() if data.contact_email else clean_email
    )
    db.add(inst)
    db.flush()

    # 4. Create Primary Academic Programme
    clean_prog_code = data.programme_code.strip().upper()
    prog = Programme(
        institution_id=inst.id,
        programme_code=clean_prog_code,
        programme_name=data.programme_name.strip(),
        degree_level=data.degree_level,
        duration_years=4 if data.degree_level == "UG" else 2
    )
    db.add(prog)
    db.flush()

    # 5. Create Sanctioned Approval Snapshot
    approval = ApprovalSnapshot(
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year=data.academic_year,
        approved_intake=data.approved_intake,
        supernumerary_quota={"TFW": data.tfw_quota},
        approval_letter_ref=data.approval_letter_ref or f"AICTE/AB/{data.academic_year}/{clean_aicte_id}",
        policy_version="AICTE-APH-2026-V1",
        is_active=True
    )
    db.add(approval)

    # 6. Create Nodal User Account
    user = InstitutionUser(
        institution_id=inst.id,
        email=clean_email,
        hashed_password=get_password_hash(data.password),
        full_name=data.nodal_name.strip(),
        role="INSTITUTION_NODAL",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(inst)

    # 7. Record to Audit Ledger Hash Chain
    append_audit_event(
        db=db,
        action="INSTITUTION_REGISTERED",
        entity_type="Institution",
        entity_id=str(inst.id),
        actor_id=user.id,
        actor_email=user.email,
        actor_role="INSTITUTION_NODAL",
        metadata_json={
            "aicte_id": inst.aicte_id,
            "institution_name": inst.name,
            "state": inst.state,
            "primary_programme": prog.programme_code,
            "approved_intake": approval.approved_intake
        }
    )

    # 8. Issue JWT Access Token for instant access
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
        institution_id=inst.id,
        institution_name=inst.name,
        aicte_id=inst.aicte_id
    )

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
