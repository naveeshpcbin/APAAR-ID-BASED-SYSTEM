from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import UploadBatch, ValidationFinding, InstitutionUser
from app.schemas.batch import UploadBatchResponse, ValidationFindingResponse, BatchCommitRequest
from app.services.reconciliation_engine import ReconciliationEngine
from app.api.deps import get_current_user, verify_institution_access

router = APIRouter(prefix="/uploads", tags=["Uploads & Smart Ingestion"])

@router.post("/preflight")
async def upload_preflight_file(
    file: UploadFile = File(...),
    institution_id: int = Form(...),
    academic_year: str = Form("2026-27"),
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    verify_institution_access(institution_id, current_user)
    
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    engine = ReconciliationEngine(db=db)
    try:
        result = engine.parse_and_validate_preflight(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            institution_id=institution_id,
            academic_year=academic_year,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[UploadBatchResponse])
def list_upload_batches(
    institution_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(UploadBatch)
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(UploadBatch.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(UploadBatch.institution_id == institution_id)

    if academic_year:
        query = query.filter(UploadBatch.academic_year == academic_year)

    return query.order_by(UploadBatch.created_at.desc()).all()

@router.get("/{batch_id}")
def get_batch_details(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    findings = db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id).order_by(ValidationFinding.row_index.asc()).all()

    return {
        "batch": {
            "id": batch.id,
            "institution_id": batch.institution_id,
            "filename": batch.filename,
            "academic_year": batch.academic_year,
            "total_rows": batch.total_rows,
            "valid_rows": batch.valid_rows,
            "warning_rows": batch.warning_rows,
            "error_rows": batch.error_rows,
            "status": batch.status,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "mapping_config": batch.mapping_config
        },
        "findings": [
            {
                "id": f.id,
                "row_index": f.row_index,
                "field_name": f.field_name,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "message": f.message,
                "recommended_action": f.recommended_action
            }
            for f in findings
        ]
    }

@router.post("/{batch_id}/commit")
def commit_upload_batch(
    batch_id: int,
    commit_req: BatchCommitRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    engine = ReconciliationEngine(db=db)
    try:
        result = engine.commit_batch(
            batch_id=batch_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            skip_errors=commit_req.skip_errors
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
