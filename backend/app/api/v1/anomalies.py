from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AnomalyCase, Institution, InstitutionUser
from app.schemas.anomaly import AnomalyCaseResponse, AnomalyReviewRequest
from app.api.deps import get_current_user, require_roles
from app.core.hash_chain import append_audit_event

router = APIRouter(prefix="/anomalies", tags=["Explainable Anomalies"])

@router.get("", response_model=List[AnomalyCaseResponse])
def list_anomalies(
    status: Optional[str] = None,
    min_risk: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(AnomalyCase).join(Institution)

    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(AnomalyCase.institution_id == current_user.institution_id)

    if status:
        query = query.filter(AnomalyCase.status == status)
    if min_risk is not None:
        query = query.filter(AnomalyCase.risk_score >= min_risk)

    cases = query.order_by(AnomalyCase.risk_score.desc(), AnomalyCase.created_at.desc()).all()
    results = []
    for c in cases:
        results.append(AnomalyCaseResponse(
            id=c.id,
            case_number=c.case_number,
            institution_id=c.institution_id,
            institution_name=c.institution.name,
            academic_year=c.academic_year,
            risk_score=c.risk_score,
            anomaly_type=c.anomaly_type,
            signals_json=c.signals_json or {},
            explanation=c.explanation,
            status=c.status,
            created_at=c.created_at
        ))
    return results

@router.get("/{anomaly_id}", response_model=AnomalyCaseResponse)
def get_anomaly_detail(
    anomaly_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    c = db.query(AnomalyCase).filter(AnomalyCase.id == anomaly_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Anomaly case not found")

    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        if c.institution_id != current_user.institution_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    return AnomalyCaseResponse(
        id=c.id,
        case_number=c.case_number,
        institution_id=c.institution_id,
        institution_name=c.institution.name,
        academic_year=c.academic_year,
        risk_score=c.risk_score,
        anomaly_type=c.anomaly_type,
        signals_json=c.signals_json or {},
        explanation=c.explanation,
        status=c.status,
        created_at=c.created_at
    )

@router.post("/{anomaly_id}/review")
def review_anomaly_case(
    anomaly_id: int,
    review_req: AnomalyReviewRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    c = db.query(AnomalyCase).filter(AnomalyCase.id == anomaly_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Anomaly case not found")

    c.status = review_req.status
    db.commit()

    append_audit_event(
        db=db,
        action="ANOMALY_REVIEWED",
        entity_type="AnomalyCase",
        entity_id=str(c.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "case_number": c.case_number,
            "new_status": review_req.status,
            "review_notes": review_req.review_notes
        }
    )

    return {
        "case_number": c.case_number,
        "status": c.status,
        "message": f"Anomaly case successfully updated to {c.status}."
    }
