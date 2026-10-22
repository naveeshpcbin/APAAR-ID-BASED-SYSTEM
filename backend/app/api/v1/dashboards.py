from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models import (
    AdmissionRecord, StudentIdentity, Institution, Programme,
    ApprovalSnapshot, UploadBatch, AdmissionConflict, AnomalyCase, AuditEvent, InstitutionUser
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboards", tags=["Regulatory Dashboards"])

@router.get("/metrics")
def get_dashboard_metrics(
    academic_year: str = "2026-27",
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    is_admin = current_user.role in ["AICTE_ADMIN", "REGIONAL_OFFICER"]
    inst_id = None if is_admin else current_user.institution_id

    # 1. Total admissions by status
    adm_query = db.query(AdmissionRecord.status, func.count(AdmissionRecord.id)).filter(
        AdmissionRecord.academic_year == academic_year
    )
    if inst_id:
        adm_query = adm_query.filter(AdmissionRecord.institution_id == inst_id)
    status_counts = dict(adm_query.group_by(AdmissionRecord.status).all())

    total_admissions = sum(status_counts.values())
    active_admissions = status_counts.get("ACTIVE", 0)
    under_review = status_counts.get("UNDER_REVIEW", 0)
    withdrawn = status_counts.get("WITHDRAWN", 0) + status_counts.get("CANCELLED", 0)

    # 2. Distinct student identities
    stud_query = db.query(func.count(func.distinct(AdmissionRecord.student_id))).filter(
        AdmissionRecord.academic_year == academic_year
    )
    if inst_id:
        stud_query = stud_query.filter(AdmissionRecord.institution_id == inst_id)
    distinct_students = stud_query.scalar() or 0

    # 3. Total approved intake across programmes
    app_query = db.query(func.sum(ApprovalSnapshot.approved_intake)).filter(
        ApprovalSnapshot.academic_year == academic_year,
        ApprovalSnapshot.is_active == True
    )
    if inst_id:
        app_query = app_query.filter(ApprovalSnapshot.institution_id == inst_id)
    total_approved_intake = app_query.scalar() or 0

    # 4. Open conflicts
    conf_query = db.query(func.count(AdmissionConflict.id)).filter(
        AdmissionConflict.status.in_(["OPEN", "UNDER_INVESTIGATION"])
    )
    if inst_id:
        conf_query = conf_query.join(AdmissionRecord, AdmissionConflict.record_a_id == AdmissionRecord.id).filter(
            (AdmissionConflict.record_a.has(institution_id=inst_id)) |
            (AdmissionConflict.record_b.has(institution_id=inst_id))
        )
    open_conflicts = conf_query.scalar() or 0

    # 5. Pending anomalies
    anom_query = db.query(func.count(AnomalyCase.id)).filter(
        AnomalyCase.academic_year == academic_year,
        AnomalyCase.status == "PENDING_REVIEW"
    )
    if inst_id:
        anom_query = anom_query.filter(AnomalyCase.institution_id == inst_id)
    pending_anomalies = anom_query.scalar() or 0

    # 6. Programme-level capacity utilization
    prog_utilization = []
    approvals = db.query(ApprovalSnapshot).join(Programme).filter(
        ApprovalSnapshot.academic_year == academic_year,
        ApprovalSnapshot.is_active == True
    )
    if inst_id:
        approvals = approvals.filter(ApprovalSnapshot.institution_id == inst_id)
    else:
        approvals = approvals.limit(10)  # Top 10 for overview

    for app in approvals.all():
        prog = db.query(Programme).filter(Programme.id == app.programme_id).first()
        inst = db.query(Institution).filter(Institution.id == app.institution_id).first()
        enrolled = db.query(func.count(AdmissionRecord.id)).filter(
            AdmissionRecord.institution_id == app.institution_id,
            AdmissionRecord.programme_id == app.programme_id,
            AdmissionRecord.academic_year == academic_year,
            AdmissionRecord.status == "ACTIVE"
        ).scalar() or 0
        pct = round((enrolled / max(1, app.approved_intake)) * 100, 1)
        prog_utilization.append({
            "programme_name": prog.programme_name if prog else "Unknown",
            "programme_code": prog.programme_code if prog else "N/A",
            "institution_name": inst.name if inst else "Unknown",
            "approved_intake": app.approved_intake,
            "enrolled": enrolled,
            "utilization_pct": pct
        })

    # 7. Category breakdown
    cat_query = db.query(AdmissionRecord.category, func.count(AdmissionRecord.id)).filter(
        AdmissionRecord.academic_year == academic_year
    )
    if inst_id:
        cat_query = cat_query.filter(AdmissionRecord.institution_id == inst_id)
    category_distribution = dict(cat_query.group_by(AdmissionRecord.category).all())

    # 8. Recent audit activity
    recent_audits = db.query(AuditEvent).order_by(AuditEvent.sequence_no.desc()).limit(6).all()
    audit_preview = [
        {
            "sequence_no": a.sequence_no,
            "action": a.action,
            "actor_email": a.actor_email,
            "entity_type": a.entity_type,
            "created_at": a.created_at.strftime("%H:%M:%S")
        }
        for a in recent_audits
    ]

    return {
        "user_role": current_user.role,
        "academic_year": academic_year,
        "summary": {
            "total_admissions": total_admissions,
            "active_admissions": active_admissions,
            "under_review": under_review,
            "withdrawn": withdrawn,
            "distinct_students": distinct_students,
            "total_approved_intake": total_approved_intake,
            "intake_utilization_pct": round((active_admissions / max(1, total_approved_intake)) * 100, 1) if total_approved_intake else 0,
            "open_conflicts": open_conflicts,
            "pending_anomalies": pending_anomalies
        },
        "programme_utilization": prog_utilization,
        "category_distribution": [
            {"category": k, "count": v} for k, v in category_distribution.items()
        ],
        "recent_audits": audit_preview
    }
