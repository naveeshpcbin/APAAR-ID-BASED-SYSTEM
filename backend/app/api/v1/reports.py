import io
import csv
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Response, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt

from app.core.config import settings
from app.core.database import get_db
from app.models import (
    AdmissionRecord, StudentIdentity, Institution, Programme,
    InstitutionUser, AdmissionConflict, ApprovalSnapshot
)
from app.api.deps import oauth2_scheme

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])


oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_current_user_from_header_or_token(
    token_param: Optional[str] = Query(None, alias="token"),
    auth_header_token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> InstitutionUser:
    """
    Authenticates requests via either Bearer header OR query param ?token=...
    Enables secure authenticated direct downloads from browser <a> tags while preserving RBAC.
    """
    raw_token = token_param or auth_header_token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required via Bearer header or ?token= query parameter",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or invalid token")

    user = db.query(InstitutionUser).filter(InstitutionUser.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


@router.get("/summary")
def get_reports_summary(
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user_from_header_or_token)
):
    """Provides high-level aggregation metrics for policy formulation and regulatory audits."""
    is_admin = current_user.role in ["AICTE_ADMIN", "REGIONAL_OFFICER"]
    inst_id = None if is_admin else current_user.institution_id

    # 1. Total Admissions
    adm_q = db.query(func.count(AdmissionRecord.id)).filter(AdmissionRecord.academic_year == academic_year)
    if inst_id:
        adm_q = adm_q.filter(AdmissionRecord.institution_id == inst_id)
    total_admissions = adm_q.scalar() or 0

    # 2. Approved Intake Capacity
    app_q = db.query(func.sum(ApprovalSnapshot.approved_intake)).filter(
        ApprovalSnapshot.academic_year == academic_year,
        ApprovalSnapshot.is_active == True
    )
    if inst_id:
        app_q = app_q.filter(ApprovalSnapshot.institution_id == inst_id)
    total_approved = app_q.scalar() or 0

    # 3. Active Conflicts
    conf_q = db.query(func.count(AdmissionConflict.id)).filter(AdmissionConflict.status.in_(["OPEN", "UNDER_INVESTIGATION"]))
    if inst_id:
        conf_q = conf_q.join(AdmissionRecord, AdmissionConflict.record_a_id == AdmissionRecord.id).filter(
            (AdmissionConflict.record_a.has(institution_id=inst_id)) |
            (AdmissionConflict.record_b.has(institution_id=inst_id))
        )
    open_conflicts = conf_q.scalar() or 0

    return {
        "academic_year": academic_year,
        "role_scope": current_user.role,
        "total_admissions": total_admissions,
        "total_approved_intake": total_approved,
        "capacity_utilization_pct": round((total_admissions / max(1, total_approved)) * 100, 1),
        "open_conflicts_pending": open_conflicts
    }


@router.get("/admissions.csv")
def export_admissions_csv(
    academic_year: str = "2026-27",
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user_from_header_or_token)
):
    """
    SIH Requirement 9 & 10: Master Admission Register Export.
    Exports verified admission records linked to masked APAAR academic identity and student enrolment ID.
    """
    query = db.query(AdmissionRecord).join(StudentIdentity).join(Institution).join(Programme).filter(
        AdmissionRecord.academic_year == academic_year
    )
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(AdmissionRecord.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(AdmissionRecord.institution_id == institution_id)

    records = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record_ID", "AICTE_ID", "Institution_Name", "Programme_Code", "Programme_Name", "Academic_Year",
        "Enrollment_No", "Student_Name", "Masked_APAAR", "Category", "Quota", "Nationality_Type",
        "Supernumerary_Seat", "Status", "Admission_Date"
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.institution.aicte_id,
            r.institution.name,
            r.programme.programme_code,
            r.programme.programme_name,
            r.academic_year,
            r.enrollment_no,
            r.student.full_name,
            r.student.apaar_masked,
            r.category,
            r.admission_quota,
            r.nationality_type,
            "YES" if r.is_supernumerary else "NO",
            r.status,
            r.admission_date.isoformat() if r.admission_date else ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pramaan_admissions_{academic_year}.csv"}
    )


@router.get("/conflicts.csv")
def export_conflicts_csv(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user_from_header_or_token)
):
    """
    SIH Requirement 3 & 9: Cross-Institution Duplicate & Collision Export.
    Exports all flagged concurrent active enrolments and their adjudication history.
    """
    query = db.query(AdmissionConflict).join(StudentIdentity)
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.join(AdmissionRecord, AdmissionConflict.record_a_id == AdmissionRecord.id).filter(
            (AdmissionConflict.record_a.has(institution_id=current_user.institution_id)) |
            (AdmissionConflict.record_b.has(institution_id=current_user.institution_id))
        )
    if status_filter:
        query = query.filter(AdmissionConflict.status == status_filter)

    conflicts = query.order_by(AdmissionConflict.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Conflict_ID", "Case_Number", "Student_Name", "Masked_APAAR",
        "Institution_A_AICTE_ID", "Institution_A_Name", "Programme_A",
        "Institution_B_AICTE_ID", "Institution_B_Name", "Programme_B",
        "Conflict_Status", "Resolution_Notes", "Flagged_Date", "Resolved_Date"
    ])

    for c in conflicts:
        rec_a = c.record_a
        rec_b = c.record_b
        writer.writerow([
            c.id,
            c.case_number,
            c.student.full_name if c.student else "N/A",
            c.student.apaar_masked if c.student else "N/A",
            rec_a.institution.aicte_id if rec_a and rec_a.institution else "N/A",
            rec_a.institution.name if rec_a and rec_a.institution else "N/A",
            rec_a.programme.programme_code if rec_a and rec_a.programme else "N/A",
            rec_b.institution.aicte_id if rec_b and rec_b.institution else "N/A",
            rec_b.institution.name if rec_b and rec_b.institution else "N/A",
            rec_b.programme.programme_code if rec_b and rec_b.programme else "N/A",
            c.status,
            c.resolution_notes or "",
            "",
            c.created_at.isoformat() if c.created_at else "",
            c.resolved_at.isoformat() if c.resolved_at else ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pramaan_cross_institution_conflicts.csv"}
    )


@router.get("/compliance.csv")
def export_compliance_csv(
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user_from_header_or_token)
):
    """
    SIH Requirement 2 & 9: Approval Capacity Compliance Audit Log.
    Compares sanctioned intake, supernumerary quotas (TFW, EWS), and actual verified enrolment.
    """
    is_admin = current_user.role in ["AICTE_ADMIN", "REGIONAL_OFFICER"]
    inst_id = None if is_admin else current_user.institution_id

    query = db.query(ApprovalSnapshot).join(Institution).join(Programme).filter(
        ApprovalSnapshot.academic_year == academic_year,
        ApprovalSnapshot.is_active == True
    )
    if inst_id:
        query = query.filter(ApprovalSnapshot.institution_id == inst_id)

    approvals = query.order_by(Institution.name.asc(), Programme.programme_code.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Approval_ID", "AICTE_ID", "Institution_Name", "State", "Programme_Code", "Programme_Name",
        "Academic_Year", "Sanctioned_Intake", "Verified_Enrolled", "Utilization_Percentage",
        "TFW_Supernumerary_Quota", "EWS_Supernumerary_Quota", "Approval_Letter_Ref", "Policy_Version", "Compliance_Status"
    ])

    for app in approvals:
        enrolled = db.query(func.count(AdmissionRecord.id)).filter(
            AdmissionRecord.institution_id == app.institution_id,
            AdmissionRecord.programme_id == app.programme_id,
            AdmissionRecord.academic_year == academic_year,
            AdmissionRecord.status == "ACTIVE"
        ).scalar() or 0

        pct = round((enrolled / max(1, app.approved_intake)) * 100, 1)
        tfw = (app.supernumerary_quota or {}).get("TFW", 0)
        ews = (app.supernumerary_quota or {}).get("EWS", 0)

        if enrolled > app.approved_intake:
            comp_status = "EXCEEDED_SANCTIONED_INTAKE"
        elif enrolled == app.approved_intake:
            comp_status = "100%_CAPACITY_FILLED"
        else:
            comp_status = "WITHIN_SANCTIONED_LIMIT"

        writer.writerow([
            app.id,
            app.institution.aicte_id,
            app.institution.name,
            app.institution.state,
            app.programme.programme_code,
            app.programme.programme_name,
            app.academic_year,
            app.approved_intake,
            enrolled,
            f"{pct}%",
            tfw,
            ews,
            app.approval_letter_ref,
            app.policy_version,
            comp_status
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pramaan_intake_compliance_{academic_year}.csv"}
    )
