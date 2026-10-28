from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AdmissionConflict, AdmissionRecord, StudentIdentity, InstitutionUser
from app.schemas.conflict import ConflictCaseResponse, ConflictResolveRequest
from app.schemas.admission import AdmissionRecordResponse, StudentIdentityResponse
from app.services.conflict_service import ConflictDetectionService
from app.api.deps import get_current_user, require_roles

router = APIRouter(prefix="/conflicts", tags=["Cross-Institution Conflicts"])

def format_record(r: AdmissionRecord) -> AdmissionRecordResponse:
    student_resp = StudentIdentityResponse(
        id=r.student.id,
        apaar_masked=r.student.apaar_masked,
        full_name=r.student.full_name,
        dob=r.student.dob,
        gender=r.student.gender,
        verification_status=r.student.verification_status,
        provider_name=r.student.provider_name
    )
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
        admission_date=r.admission_date,
        status=r.status,
        notes=r.notes,
        student=student_resp
    )

@router.get("", response_model=List[ConflictCaseResponse])
def list_conflicts(
    status: Optional[str] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    # Verifiers have no access to conflict adjudication data
    if current_user.role == "VERIFIER":
        raise HTTPException(status_code=403, detail="Verifiers are not authorized to access conflict cases")

    query = db.query(AdmissionConflict).join(StudentIdentity)

    # Institution users only see conflicts involving their institution
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.join(AdmissionRecord, AdmissionConflict.record_a_id == AdmissionRecord.id).filter(
            (AdmissionConflict.record_a.has(institution_id=current_user.institution_id)) |
            (AdmissionConflict.record_b.has(institution_id=current_user.institution_id))
        )

    if status:
        query = query.filter(AdmissionConflict.status == status)

    conflicts = query.order_by(AdmissionConflict.created_at.desc()).all()
    results = []
    for c in conflicts:
        student_resp = StudentIdentityResponse(
            id=c.student.id,
            apaar_masked=c.student.apaar_masked,
            full_name=c.student.full_name,
            dob=c.student.dob,
            gender=c.student.gender,
            verification_status=c.student.verification_status,
            provider_name=c.student.provider_name
        )
        results.append(ConflictCaseResponse(
            id=c.id,
            case_number=c.case_number,
            student_id=c.student_id,
            student=student_resp,
            record_a_id=c.record_a_id,
            record_a=format_record(c.record_a),
            record_b_id=c.record_b_id,
            record_b=format_record(c.record_b),
            conflict_type=c.conflict_type,
            status=c.status,
            resolution_notes=c.resolution_notes,
            created_at=c.created_at,
            resolved_at=c.resolved_at
        ))
    return results

@router.get("/{conflict_id}", response_model=ConflictCaseResponse)
def get_conflict_detail(
    conflict_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    if current_user.role == "VERIFIER":
        raise HTTPException(status_code=403, detail="Verifiers are not authorized to access conflict cases")

    c = db.query(AdmissionConflict).filter(AdmissionConflict.id == conflict_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Conflict case not found")

    student_resp = StudentIdentityResponse(
        id=c.student.id,
        apaar_masked=c.student.apaar_masked,
        full_name=c.student.full_name,
        dob=c.student.dob,
        gender=c.student.gender,
        verification_status=c.student.verification_status,
        provider_name=c.student.provider_name
    )
    return ConflictCaseResponse(
        id=c.id,
        case_number=c.case_number,
        student_id=c.student_id,
        student=student_resp,
        record_a_id=c.record_a_id,
        record_a=format_record(c.record_a),
        record_b_id=c.record_b_id,
        record_b=format_record(c.record_b),
        conflict_type=c.conflict_type,
        status=c.status,
        resolution_notes=c.resolution_notes,
        created_at=c.created_at,
        resolved_at=c.resolved_at
    )

@router.post("/{conflict_id}/resolve")
def resolve_conflict_case(
    conflict_id: int,
    resolve_data: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    try:
        return ConflictDetectionService.resolve_conflict(
            db=db,
            conflict_id=conflict_id,
            resolution_status=resolve_data.resolution_status,
            winning_record_id=resolve_data.winning_record_id,
            resolution_notes=resolve_data.resolution_notes,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
