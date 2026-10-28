from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AdmissionRecord, StudentIdentity, Institution, Programme, InstitutionUser
from app.schemas.admission import AdmissionRecordResponse, ManualAdmissionCreate, StudentIdentityResponse
from app.api.deps import get_current_user, verify_institution_access
from app.adapters.mock_apaar_adapter import MockApaarAdapter
from app.core.security import hash_apaar_id, mask_apaar_id
from app.services.conflict_service import ConflictDetectionService
from app.core.hash_chain import append_audit_event

router = APIRouter(prefix="/admissions", tags=["Admissions"])

@router.get("", response_model=List[AdmissionRecordResponse])
def list_admissions(
    institution_id: Optional[int] = None,
    programme_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(AdmissionRecord).join(StudentIdentity).join(Institution).join(Programme)

    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(AdmissionRecord.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(AdmissionRecord.institution_id == institution_id)

    if programme_id:
        query = query.filter(AdmissionRecord.programme_id == programme_id)
    if academic_year:
        query = query.filter(AdmissionRecord.academic_year == academic_year)
    if status:
        query = query.filter(AdmissionRecord.status == status)
    if category:
        query = query.filter(AdmissionRecord.category == category)
    if search:
        query = query.filter(
            (StudentIdentity.full_name.ilike(f"%{search}%")) |
            (AdmissionRecord.enrollment_no.ilike(f"%{search}%")) |
            (StudentIdentity.apaar_masked.ilike(f"%{search}%"))
        )

    records = query.order_by(AdmissionRecord.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for r in records:
        student_resp = StudentIdentityResponse(
            id=r.student.id,
            apaar_masked=r.student.apaar_masked,
            full_name=r.student.full_name,
            dob=r.student.dob,
            gender=r.student.gender,
            verification_status=r.student.verification_status,
            provider_name=r.student.provider_name
        )
        is_consent = True
        if r.student and r.student.consent_grants:
            latest_cg = sorted(r.student.consent_grants, key=lambda x: x.created_at)[-1]
            is_consent = latest_cg.is_granted

        results.append(AdmissionRecordResponse(
            id=r.id,
            student_id=r.student_id,
            institution_id=r.institution_id,
            institution_name=r.institution.name,
            programme_id=r.programme_id,
            programme_code=r.programme.programme_code,
            programme_name=r.programme.programme_name,
            academic_year=r.academic_year,
            enrollment_no=r.enrollment_no,
            category=r.category,
            admission_quota=r.admission_quota,
            nationality_type=getattr(r, "nationality_type", "DOMESTIC") or "DOMESTIC",
            is_supernumerary=bool(getattr(r, "is_supernumerary", False)),
            admission_date=r.admission_date,
            status=r.status,
            consent_granted=is_consent,
            notes=r.notes,
            student=student_resp
        ))

    return results

@router.get("/{admission_id}", response_model=AdmissionRecordResponse)
def get_admission_detail(
    admission_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    r = db.query(AdmissionRecord).filter(AdmissionRecord.id == admission_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Admission record not found")
    verify_institution_access(r.institution_id, current_user)

    student_resp = StudentIdentityResponse(
        id=r.student.id,
        apaar_masked=r.student.apaar_masked,
        full_name=r.student.full_name,
        dob=r.student.dob,
        gender=r.student.gender,
        verification_status=r.student.verification_status,
        provider_name=r.student.provider_name
    )
    is_consent = True
    if r.student and r.student.consent_grants:
        latest_cg = sorted(r.student.consent_grants, key=lambda x: x.created_at)[-1]
        is_consent = latest_cg.is_granted

    return AdmissionRecordResponse(
        id=r.id,
        student_id=r.student_id,
        institution_id=r.institution_id,
        institution_name=r.institution.name,
        programme_id=r.programme_id,
        programme_code=r.programme.programme_code,
        programme_name=r.programme.programme_name,
        academic_year=r.academic_year,
        enrollment_no=r.enrollment_no,
        category=r.category,
        admission_quota=r.admission_quota,
        nationality_type=getattr(r, "nationality_type", "DOMESTIC") or "DOMESTIC",
        is_supernumerary=bool(getattr(r, "is_supernumerary", False)),
        admission_date=r.admission_date,
        status=r.status,
        consent_granted=is_consent,
        notes=r.notes,
        student=student_resp
    )

@router.post("/manual", response_model=AdmissionRecordResponse)
def create_manual_admission(
    data: ManualAdmissionCreate,
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    target_inst_id = current_user.institution_id or institution_id
    if not target_inst_id:
        raise HTTPException(status_code=400, detail="Target institution_id required")
    verify_institution_access(target_inst_id, current_user)

    prog = db.query(Programme).filter(
        Programme.institution_id == target_inst_id,
        Programme.programme_code.ilike(data.programme_code)
    ).first()
    if not prog:
        raise HTTPException(status_code=400, detail=f"Programme {data.programme_code} not offered at this institution.")

    # Upstream adapter validation
    adapter = MockApaarAdapter()
    id_result = adapter.verify_identity(data.apaar_id, data.student_name, data.dob, data.gender)
    if not id_result.is_valid_format:
        raise HTTPException(status_code=400, detail=id_result.message)

    h_apaar = hash_apaar_id(data.apaar_id)
    m_apaar = mask_apaar_id(data.apaar_id)

    student = db.query(StudentIdentity).filter(StudentIdentity.apaar_hash == h_apaar).first()
    if not student:
        student = StudentIdentity(
            apaar_hash=h_apaar,
            apaar_masked=m_apaar,
            full_name=data.student_name,
            dob=data.dob,
            gender=data.gender,
            verification_status="VERIFIED" if id_result.is_verified else id_result.status_code,
            provider_reference=id_result.provider_reference
        )
        db.add(student)
        db.flush()

    status_val = "ACTIVE" if id_result.is_verified else "UNDER_REVIEW"
    record = AdmissionRecord(
        student_id=student.id,
        institution_id=target_inst_id,
        programme_id=prog.id,
        academic_year=data.academic_year,
        enrollment_no=data.enrollment_no,
        category=data.category,
        admission_quota=data.admission_quota,
        nationality_type=data.nationality_type or "DOMESTIC",
        is_supernumerary=bool(data.is_supernumerary),
        admission_date=data.admission_date,
        status=status_val
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Check for cross-institution conflicts
    ConflictDetectionService.check_for_conflicts(
        db=db,
        student_id=student.id,
        new_record_id=record.id,
        institution_id=target_inst_id,
        academic_year=data.academic_year
    )

    append_audit_event(
        db=db,
        action="MANUAL_ADMISSION_CREATED",
        entity_type="AdmissionRecord",
        entity_id=str(record.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "enrollment_no": record.enrollment_no,
            "programme_code": prog.programme_code,
            "nationality_type": record.nationality_type,
            "is_supernumerary": record.is_supernumerary,
            "status": record.status
        }
    )

    inst = db.query(Institution).filter(Institution.id == target_inst_id).first()
    return AdmissionRecordResponse(
        id=record.id,
        student_id=student.id,
        institution_id=target_inst_id,
        institution_name=inst.name if inst else "Unknown",
        programme_id=prog.id,
        programme_code=prog.programme_code,
        programme_name=prog.programme_name,
        academic_year=record.academic_year,
        enrollment_no=record.enrollment_no,
        category=record.category,
        admission_quota=record.admission_quota,
        nationality_type=record.nationality_type,
        is_supernumerary=record.is_supernumerary,
        admission_date=record.admission_date,
        status=record.status,
        student=StudentIdentityResponse(
            id=student.id,
            apaar_masked=student.apaar_masked,
            full_name=student.full_name,
            dob=student.dob,
            gender=student.gender,
            verification_status=student.verification_status,
            provider_name=student.provider_name
        )
    )
