from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    UploadBatch, ValidationFinding, ValidationRun, InstitutionUser,
    AdmissionRecord, AdmissionConflict, Institution, StagedBatchRow, BatchDisputeQuery, Programme,
    AicteCentralAdvisory
)
from app.schemas.batch import (
    UploadBatchResponse, ValidationFindingResponse, BatchCommitRequest, BatchReviewRequest,
    StagedRowUpdateRequest, BatchQueryCreate, BatchQueryResolveRequest,
    RawCsvUpdateRequest, QuickFixRequest, CentralAdvisoryCreate, CentralAdvisoryResponse,
    DatasetGenerateRequest, DatasetExportRequest, BatchFileInfoResponse
)
from app.services.reconciliation_engine import ReconciliationEngine
from app.core.hash_chain import append_audit_event
from app.api.deps import get_current_user, verify_institution_access, require_roles

router = APIRouter(prefix="/uploads", tags=["Uploads & Smart Ingestion"])


@router.post("/generate-dataset")
def generate_web_dataset(
    req: DatasetGenerateRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    verify_institution_access(req.institution_id, current_user)

    inst = db.query(Institution).filter(Institution.id == req.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    progs = db.query(Programme).filter(Programme.institution_id == req.institution_id).all()
    approved_codes = [p.programme_code for p in progs] if progs else ["BTECH-CSE"]
    default_code = req.programme_code or approved_codes[0]

    names_pool = [
        ("Aarav Sharma", "MALE", "2005-03-14"),
        ("Pooja Patel", "FEMALE", "2005-07-22"),
        ("Rohan Iyer", "MALE", "2005-01-30"),
        ("Kavya Nair", "FEMALE", "2005-11-05"),
        ("Ananya Reddy", "FEMALE", "2005-09-18"),
        ("Vikramaditya Singh", "MALE", "2005-05-12"),
        ("Meera Mukherjee", "FEMALE", "2005-08-25"),
        ("Siddharth Deshmukh", "MALE", "2005-02-17"),
        ("Sneha Kulkarni", "FEMALE", "2005-12-09"),
        ("Arjun Menon", "MALE", "2005-06-20"),
        ("Divya Choudhary", "FEMALE", "2005-04-03"),
        ("Tanvi Joshi", "FEMALE", "2005-10-15"),
        ("Gaurav Malhotra", "MALE", "2005-08-11"),
        ("Ishaan Gupta", "MALE", "2005-02-28"),
        ("Rhea Sen", "FEMALE", "2005-07-04")
    ]
    categories = ["OPEN", "OBC_NCL", "SC", "ST", "EWS"]
    quotas = ["STATE_GOVT", "STATE_GOVT", "MANAGEMENT", "TFW"]

    count = min(max(req.count, 1), 50)
    import re, io, csv
    inst_short = re.sub(r'[^A-Z]', '', inst.name.upper())[:4] or "INST"

    rows = []
    base_apaar = 900000000000 + (inst.id * 100000)

    for i in range(count):
        name_info = names_pool[i % len(names_pool)]
        apaar = str(base_apaar + i + 1)
        prog = default_code
        category = categories[i % len(categories)]
        quota = quotas[i % len(quotas)]

        is_discrepant = (req.mode or "").upper() == "DISCREPANT" or req.include_discrepancies is True
        if is_discrepant:
            if i == 0:
                prog = "BTECH-AI"
            elif i == 1:
                apaar = ""

        row_dict = {
            "student_name": f"{name_info[0]} {i+1}" if i >= len(names_pool) else name_info[0],
            "apaar_id": apaar,
            "dob": name_info[2],
            "gender": name_info[1],
            "programme_code": prog,
            "enrollment_no": f"{inst_short}/{req.academic_year[:4]}/{prog.replace('-', '')[:3]}/{101 + i}",
            "category": category,
            "admission_quota": quota,
            "is_supernumerary": quota in ["TFW", "NRI"],
            "nationality_type": "NRI" if quota == "NRI" else "DOMESTIC",
            "admission_date": f"{req.academic_year[:4]}-08-01"
        }
        rows.append(row_dict)

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow([
        "student_name", "apaar_id", "dob", "gender", "programme_code",
        "enrollment_no", "category", "admission_quota", "is_supernumerary", "nationality_type", "admission_date"
    ])
    for r in rows:
        writer.writerow([
            r["student_name"], r["apaar_id"], r["dob"], r["gender"],
            r["programme_code"], r["enrollment_no"], r["category"],
            r["admission_quota"], r["is_supernumerary"], r["nationality_type"], r["admission_date"]
        ])
    csv_text = out.getvalue()

    return {
        "success": True,
        "institution_id": inst.id,
        "institution_name": inst.name,
        "total_rows": len(rows),
        "rows": rows,
        "csv_content": csv_text,
        "suggested_filename": f"dataset_{inst_short.lower()}_{req.academic_year.replace('-', '_')}.csv"
    }


@router.post("/export-dataset")
def export_dataset(
    req: DatasetExportRequest,
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Exports manually built or generated in-browser student rows as a genuine
    styled Excel (.xlsx) workbook or RFC-4180 CSV file.
    Prevents 12-digit scientific notation corruption in Excel.
    """
    verify_institution_access(req.institution_id, current_user)
    if not req.rows:
        raise HTTPException(status_code=400, detail="Cannot export empty dataset.")

    df = pd.DataFrame(req.rows)
    if "apaar_id" in df.columns:
        df["apaar_id"] = df["apaar_id"].astype(str)

    requested_fmt = (req.format or "xlsx").lower()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"student_admissions_inst_{req.institution_id}_{timestamp}"

    if requested_fmt in ["xlsx", "excel"]:
        import io
        import openpyxl.styles
        import openpyxl.utils
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Admissions_Roster")
            ws = writer.sheets["Admissions_Roster"]
            header_fill = openpyxl.styles.PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
            header_font = openpyxl.styles.Font(color="FFFFFF", bold=True, name="Calibri")
            for col in range(1, len(df.columns) + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")
            for col_idx, col_name in enumerate(df.columns, start=1):
                if "apaar" in str(col_name).lower():
                    for row_idx in range(2, len(df) + 2):
                        ws.cell(row=row_idx, column=col_idx).number_format = '@'
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                max_len = max(len(str(val or '')) for val in df[col_name])
                ws.column_dimensions[col_letter].width = max(max_len + 4, 14)
        out.seek(0)
        return Response(
            content=out.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{base_name}.xlsx"',
                "X-File-Format": "XLSX",
                "Access-Control-Expose-Headers": "Content-Disposition, X-File-Format"
            }
        )
    else:
        csv_bytes = df.to_csv(index=False, encoding="utf-8").encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{base_name}.csv"',
                "X-File-Format": "CSV",
                "Access-Control-Expose-Headers": "Content-Disposition, X-File-Format"
            }
        )


@router.post("/preflight")
async def upload_preflight_file(
    file: UploadFile = File(...),
    institution_id: Optional[int] = Form(None),
    academic_year: str = Form("2026-27"),
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    if institution_id is not None:
        target_inst_id = institution_id
        verify_institution_access(target_inst_id, current_user)
    else:
        target_inst_id = current_user.institution_id if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"] else 1

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    engine = ReconciliationEngine(db=db)
    try:
        result = engine.parse_and_validate_preflight(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            institution_id=target_inst_id,
            academic_year=academic_year,
            user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_upload_batches(
    institution_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    query = db.query(UploadBatch).join(Institution)
    if current_user.role not in ["AICTE_ADMIN", "REGIONAL_OFFICER"]:
        query = query.filter(UploadBatch.institution_id == current_user.institution_id)
    elif institution_id:
        query = query.filter(UploadBatch.institution_id == institution_id)

    if academic_year:
        query = query.filter(UploadBatch.academic_year == academic_year)

    batches = query.order_by(UploadBatch.created_at.desc()).all()
    results = []
    for b in batches:
        reviewer = db.query(InstitutionUser).filter(InstitutionUser.id == b.reviewed_by_user_id).first() if b.reviewed_by_user_id else None
        mapping_cfg = b.mapping_config or {}
        is_excel = b.filename.lower().endswith(('.xlsx', '.xls'))
        results.append({
            "id": b.id,
            "institution_id": b.institution_id,
            "institution_name": b.institution.name if b.institution else None,
            "aicte_id": b.institution.aicte_id if b.institution else None,
            "filename": b.filename,
            "academic_year": b.academic_year,
            "total_rows": b.total_rows,
            "valid_rows": b.valid_rows,
            "warning_rows": b.warning_rows,
            "error_rows": b.error_rows,
            "status": b.status,
            "file_format": mapping_cfg.get("_file_format") or ("XLSX" if is_excel else "CSV"),
            "storage_path_xlsx": mapping_cfg.get("_storage_file_xlsx"),
            "storage_path_csv": mapping_cfg.get("_storage_file_csv"),
            "full_storage_path": mapping_cfg.get("_storage_file"),
            "download_url_xlsx": f"/api/v1/uploads/{b.id}/download?format=xlsx",
            "download_url_csv": f"/api/v1/uploads/{b.id}/download?format=csv",
            "review_notes": b.review_notes,
            "reviewed_by": reviewer.full_name if reviewer else None,
            "reviewed_at": b.reviewed_at.isoformat() if b.reviewed_at else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "updated_at": b.updated_at.isoformat() if b.updated_at else None
        })
    return results


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

    inst = db.query(Institution).filter(Institution.id == batch.institution_id).first()
    reviewer = db.query(InstitutionUser).filter(InstitutionUser.id == batch.reviewed_by_user_id).first() if batch.reviewed_by_user_id else None

    # Retrieve all validation runs for complete historical traceability
    validation_runs = db.query(ValidationRun).filter(
        ValidationRun.batch_id == batch_id
    ).order_by(ValidationRun.run_number.desc()).all()

    runs_data = [
        {
            "id": r.id,
            "run_number": r.run_number,
            "status": r.status,
            "total_rows": r.total_rows,
            "duplicate_rows": r.duplicate_rows,
            "unique_records": r.unique_records,
            "blocking_errors": r.blocking_errors,
            "requiring_review": r.requiring_review,
            "eligible_to_proceed": r.eligible_to_proceed,
            "declared_intake": r.declared_intake,
            "declared_discrepancy": r.declared_discrepancy,
            "reference_versions": r.reference_versions_json,
            "summary": r.summary_json,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in validation_runs
    ]

    latest_run = runs_data[0] if runs_data else None

    # Get findings for latest validation run (or all findings if run not linked)
    findings_query = db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id)
    if latest_run:
        findings_query = findings_query.filter(ValidationFinding.validation_run_id == latest_run["id"])

    findings = findings_query.order_by(ValidationFinding.row_index.asc()).all()

    return {
        "batch": {
            "id": batch.id,
            "institution_id": batch.institution_id,
            "institution_name": inst.name if inst else None,
            "aicte_id": inst.aicte_id if inst else None,
            "filename": batch.filename,
            "academic_year": batch.academic_year,
            "total_rows": batch.total_rows,
            "valid_rows": batch.valid_rows,
            "warning_rows": batch.warning_rows,
            "error_rows": batch.error_rows,
            "status": batch.status,
            "file_format": (batch.mapping_config or {}).get("_file_format") or ("XLSX" if batch.filename.lower().endswith(('.xlsx', '.xls')) else "CSV"),
            "storage_path_xlsx": (batch.mapping_config or {}).get("_storage_file_xlsx"),
            "storage_path_csv": (batch.mapping_config or {}).get("_storage_file_csv"),
            "full_storage_path": (batch.mapping_config or {}).get("_storage_file"),
            "download_url_xlsx": f"/api/v1/uploads/{batch.id}/download?format=xlsx",
            "download_url_csv": f"/api/v1/uploads/{batch.id}/download?format=csv",
            "review_notes": batch.review_notes,
            "reviewed_by": reviewer.full_name if reviewer else None,
            "reviewed_at": batch.reviewed_at.isoformat() if batch.reviewed_at else None,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
            "mapping_config": batch.mapping_config
        },
        "latest_validation_run": latest_run,
        "validation_runs_history": runs_data,
        "findings": [
            {
                "id": f.id,
                "validation_run_id": f.validation_run_id,
                "row_index": f.row_index,
                "field_name": f.field_name,
                "finding_type": f.finding_type,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "submitted_value": f.submitted_value,
                "expected_value": f.expected_value,
                "reference_source_id": f.reference_source_id,
                "rule_version": f.rule_version,
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
    """
    Explicit 'Commit & Submit to AICTE' action.
    Triggers backend 3-way reconciliation, saves validation findings, and submits batch for central review.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    engine = ReconciliationEngine(db=db)
    try:
        result = engine.commit_and_submit_batch(
            batch_id=batch_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            skip_errors=commit_req.skip_errors
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{batch_id}/review")
def review_upload_batch(
    batch_id: int,
    review_req: BatchReviewRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    AICTE Central review adjudication endpoint:
    Authorized central reviewer can APPROVE, RETURN FOR CORRECTION, or REJECT with recorded notes.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    decision = review_req.decision.upper()
    if decision not in ["APPROVED", "RETURNED_FOR_CORRECTION", "REJECTED_NEEDS_CORRECTION", "REJECTED"]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED, RETURNED_FOR_CORRECTION, or REJECTED."
        )

    # Standardize return status
    if decision == "REJECTED_NEEDS_CORRECTION":
        decision = "RETURNED_FOR_CORRECTION"

    # Enforce approval conditions: cannot approve if blocking errors exist
    if decision == "APPROVED":
        blocking_errors = db.query(ValidationFinding).filter(
            ValidationFinding.batch_id == batch_id,
            ValidationFinding.severity == "ERROR"
        ).count()
        if blocking_errors > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot APPROVE batch: Contains {blocking_errors} unresolved blocking errors."
            )

    batch.status = decision
    batch.review_notes = review_req.notes
    batch.reviewed_by_user_id = current_user.id
    batch.reviewed_at = datetime.utcnow()
    batch.updated_at = datetime.utcnow()

    # Update admission records based on review decision
    admissions = db.query(AdmissionRecord).filter(AdmissionRecord.batch_id == batch.id).all()
    if decision == "APPROVED":
        for adm in admissions:
            open_conflict = db.query(AdmissionConflict).filter(
                (AdmissionConflict.record_a_id == adm.id) | (AdmissionConflict.record_b_id == adm.id),
                AdmissionConflict.status == "OPEN"
            ).first()
            if not open_conflict:
                adm.status = "ACTIVE"
    elif decision == "REJECTED":
        for adm in admissions:
            adm.status = "REJECTED"

    db.commit()

    action_map = {
        "APPROVED": "BATCH_APPROVED",
        "RETURNED_FOR_CORRECTION": "BATCH_RETURNED_FOR_CORRECTION",
        "REJECTED": "BATCH_REJECTED"
    }
    action_name = action_map.get(decision, "BATCH_REVIEWED")

    append_audit_event(
        db=db,
        action=action_name,
        entity_type="UploadBatch",
        entity_id=str(batch.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch.id,
            "institution_id": batch.institution_id,
            "decision": decision,
            "notes": review_req.notes,
            "reviewed_by": current_user.full_name
        }
    )

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "decision": decision,
        "notes": review_req.notes,
        "reviewed_by": current_user.full_name,
        "reviewed_at": batch.reviewed_at.isoformat(),
        "message": f"Batch #{batch.id} review recorded as {batch.status}."
    }


@router.get("/{batch_id}/rows")
def get_batch_staged_rows(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Returns all staged spreadsheet rows for interactive grid display.
    Includes row-level validation findings, error highlights, and algorithm advice.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    engine = ReconciliationEngine(db=db)
    staged_rows = engine.get_or_sync_staged_rows(batch_id)

    # Get findings for latest validation run of this batch
    latest_run = db.query(ValidationRun).filter(
        ValidationRun.batch_id == batch_id
    ).order_by(ValidationRun.run_number.desc()).first()

    findings_query = db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id)
    if latest_run:
        findings_query = findings_query.filter(ValidationFinding.validation_run_id == latest_run.id)
    findings = findings_query.all()
    findings_by_row: Dict[int, List[Dict[str, Any]]] = {}
    for f in findings:
        findings_by_row.setdefault(f.row_index, []).append({
            "id": f.id,
            "field_name": f.field_name,
            "finding_type": f.finding_type,
            "rule_id": f.rule_id,
            "severity": f.severity,
            "submitted_value": f.submitted_value,
            "expected_value": f.expected_value,
            "message": f.message,
            "recommended_action": f.recommended_action
        })

    # Get any active dispute query per row
    queries = db.query(BatchDisputeQuery).filter(BatchDisputeQuery.batch_id == batch_id).all()
    query_by_row: Dict[int, Dict[str, Any]] = {}
    for q in queries:
        if q.row_id:
            query_by_row[q.row_id] = {
                "id": q.id,
                "subject": q.subject,
                "category": q.category,
                "status": q.status,
                "message": q.message,
                "aicte_reply": q.aicte_reply
            }

    results = []
    for r in staged_rows:
        row_finds = findings_by_row.get(r.row_index, [])
        results.append({
            "id": r.id,
            "batch_id": r.batch_id,
            "row_index": r.row_index,
            "apaar_id": r.apaar_id,
            "student_name": r.student_name,
            "programme_code": r.programme_code,
            "category": r.category,
            "gender": r.gender,
            "dob": r.dob.isoformat() if r.dob else None,
            "admission_quota": r.admission_quota,
            "status": r.status,
            "findings": row_finds,
            "query": query_by_row.get(r.id)
        })

    return {
        "batch_id": batch_id,
        "total_rows": len(results),
        "rows": results
    }


@router.patch("/{batch_id}/rows/{row_id}")
def update_batch_staged_row(
    batch_id: int,
    row_id: int,
    update_req: StagedRowUpdateRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Inline spreadsheet correction endpoint.
    Modifies cell data in-place and triggers instantaneous deterministic Python re-reconciliation.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    engine = ReconciliationEngine(db=db)
    try:
        update_data = update_req.model_dump(exclude_unset=True)
        result = engine.update_staged_row(
            batch_id=batch_id,
            row_id=row_id,
            updates=update_data,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{batch_id}/queries")
def create_batch_dispute_query(
    batch_id: int,
    query_req: BatchQueryCreate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Raises an official exemption request or communication to AICTE Central.
    Specifically accommodates students without APAAR ID (due to UIDAI biometric issues or technical exceptions).
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    staged_row = None
    if query_req.row_id:
        staged_row = db.query(StagedBatchRow).filter(
            StagedBatchRow.id == query_req.row_id,
            StagedBatchRow.batch_id == batch_id
        ).first()

    query = BatchDisputeQuery(
        batch_id=batch_id,
        row_id=query_req.row_id,
        institution_id=batch.institution_id,
        raised_by_user_id=current_user.id,
        subject=query_req.subject,
        category=query_req.category,
        student_identifier=query_req.student_identifier or (staged_row.student_name if staged_row else None),
        message=query_req.message,
        status="PENDING_REVIEW"
    )
    db.add(query)

    if staged_row:
        staged_row.status = "EXEMPTION_REQUESTED"

    db.flush()

    append_audit_event(
        db=db,
        action="INSTITUTION_EXEMPTION_QUERY_RAISED",
        entity_type="BatchDisputeQuery",
        entity_id=str(query.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch_id,
            "row_id": query_req.row_id,
            "subject": query_req.subject,
            "category": query_req.category,
            "message": query_req.message
        }
    )
    db.commit()
    db.refresh(query)

    return {
        "id": query.id,
        "batch_id": query.batch_id,
        "row_id": query.row_id,
        "subject": query.subject,
        "category": query.category,
        "student_identifier": query.student_identifier,
        "message": query.message,
        "status": query.status,
        "created_at": query.created_at.isoformat()
    }


@router.get("/{batch_id}/queries")
def list_batch_dispute_queries(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """Lists all exemption requests and communication queries for this batch."""
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    queries = db.query(BatchDisputeQuery).filter(
        BatchDisputeQuery.batch_id == batch_id
    ).order_by(BatchDisputeQuery.created_at.desc()).all()

    results = []
    for q in queries:
        raised_by = db.query(InstitutionUser).filter(InstitutionUser.id == q.raised_by_user_id).first()
        resolved_by = db.query(InstitutionUser).filter(InstitutionUser.id == q.resolved_by_user_id).first()
        results.append({
            "id": q.id,
            "batch_id": q.batch_id,
            "row_id": q.row_id,
            "institution_id": q.institution_id,
            "subject": q.subject,
            "category": q.category,
            "student_identifier": q.student_identifier,
            "message": q.message,
            "status": q.status,
            "aicte_reply": q.aicte_reply,
            "raised_by_name": raised_by.full_name if raised_by else None,
            "resolved_by_name": resolved_by.full_name if resolved_by else None,
            "resolved_at": q.resolved_at.isoformat() if q.resolved_at else None,
            "created_at": q.created_at.isoformat() if q.created_at else None
        })

    return results


@router.patch("/{batch_id}/queries/{query_id}/resolve")
def resolve_batch_dispute_query(
    batch_id: int,
    query_id: int,
    resolve_req: BatchQueryResolveRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    AICTE Central Committee review endpoint to resolve institutional exemption requests.
    Action can be APPROVE_EXEMPTION (grants provisional exemption under APH 2026-27),
    REJECT_QUERY, or REPLY_ONLY.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    query = db.query(BatchDisputeQuery).filter(
        BatchDisputeQuery.id == query_id,
        BatchDisputeQuery.batch_id == batch_id
    ).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    action = resolve_req.action.upper()
    if action not in ["APPROVE_EXEMPTION", "REJECT_QUERY", "REPLY_ONLY"]:
        raise HTTPException(status_code=400, detail="Action must be APPROVE_EXEMPTION, REJECT_QUERY, or REPLY_ONLY")

    if action == "APPROVE_EXEMPTION":
        query.status = "PROVISIONALLY_EXEMPTED"
        if query.row_id:
            staged_row = db.query(StagedBatchRow).filter(StagedBatchRow.id == query.row_id).first()
            if staged_row:
                staged_row.status = "EXEMPTED"
    elif action == "REJECT_QUERY":
        query.status = "RESOLVED_REJECTED"
        if query.row_id:
            staged_row = db.query(StagedBatchRow).filter(StagedBatchRow.id == query.row_id).first()
            if staged_row:
                staged_row.status = "BLOCKING_ERROR"

    query.aicte_reply = resolve_req.reply_message
    query.resolved_by_user_id = current_user.id
    query.resolved_at = datetime.utcnow()
    query.updated_at = datetime.utcnow()
    db.flush()

    # Trigger re-evaluation so batch disposition immediately reflects the approved exemption
    engine = ReconciliationEngine(db=db)
    reval_res = engine.revalidate_batch(
        batch_id=batch_id,
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role
    )

    append_audit_event(
        db=db,
        action="INSTITUTION_EXEMPTION_QUERY_RESOLVED",
        entity_type="BatchDisputeQuery",
        entity_id=str(query.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch_id,
            "query_id": query.id,
            "action": action,
            "status": query.status,
            "aicte_reply": resolve_req.reply_message,
            "updated_batch_status": reval_res.get("status")
        }
    )
    db.commit()

    return {
        "query_id": query.id,
        "status": query.status,
        "aicte_reply": query.aicte_reply,
        "resolved_by": current_user.full_name,
        "batch_status": reval_res.get("status"),
        "disposition": reval_res.get("disposition")
    }


@router.get("/{batch_id}/download")
def download_batch_file(
    batch_id: int,
    format: str = Query("csv", description="File format to download: 'csv' or 'xlsx'"),
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Downloads the updated batch dataset incorporating all inline website modifications.
    Supports genuine OpenXML Excel (.xlsx) and RFC-4180 CSV (.csv).
    Guarantees synchronization with local disk storage files.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    engine = ReconciliationEngine(db=db)
    staged_rows = engine.get_or_sync_staged_rows(batch_id)

    rows_data = []
    for r in staged_rows:
        rows_data.append({
            "apaar_id": str(r.apaar_id or ""),
            "student_name": r.student_name or "",
            "dob": r.dob.isoformat() if r.dob else "",
            "gender": r.gender or "MALE",
            "programme_code": r.programme_code or "",
            "category": r.category or "OPEN",
            "admission_quota": r.admission_quota or "STATE_GOVT",
            "is_supernumerary": getattr(r, "is_supernumerary", False),
            "status": r.status or "ELIGIBLE"
        })
    df = pd.DataFrame(rows_data)

    # Sync both files on disk to guarantee disk files are always fresh
    sync_res = engine.sync_storage_files(batch, df)
    db.commit()

    base_name = batch.filename.rsplit(".", 1)[0] if batch.filename else f"batch_{batch.id}"

    if format.lower() in ["xlsx", "excel"]:
        import io
        import openpyxl.styles
        import openpyxl.utils
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Admissions_Roster")
            ws = writer.sheets["Admissions_Roster"]
            header_fill = openpyxl.styles.PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid")
            header_font = openpyxl.styles.Font(color="FFFFFF", bold=True, name="Calibri")
            for col in range(1, len(df.columns) + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")
            for col_idx, col_name in enumerate(df.columns, start=1):
                if "apaar" in str(col_name).lower():
                    for row_idx in range(2, len(df) + 2):
                        ws.cell(row=row_idx, column=col_idx).number_format = '@'
                col_letter = openpyxl.utils.get_column_letter(col_idx)
                max_len = max(len(str(val or '')) for val in df[col_name])
                ws.column_dimensions[col_letter].width = max(max_len + 4, 14)
        out.seek(0)
        filename = f"corrected_{base_name}.xlsx"
        xlsx_disk_path = sync_res.get("xlsx") or (batch.mapping_config or {}).get("_storage_file_xlsx", "")
        return Response(
            content=out.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Storage-Path": xlsx_disk_path,
                "X-File-Format": "XLSX",
                "Access-Control-Expose-Headers": "Content-Disposition, X-Storage-Path, X-File-Format"
            }
        )
    else:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        filename = f"corrected_{base_name}.csv"
        csv_disk_path = sync_res.get("csv") or (batch.mapping_config or {}).get("_storage_file_csv", "")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Storage-Path": csv_disk_path,
                "X-File-Format": "CSV",
                "Access-Control-Expose-Headers": "Content-Disposition, X-Storage-Path, X-File-Format"
            }
        )


@router.get("/{batch_id}/download-excel")
def download_batch_excel_direct(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """Direct convenience route to download batch as genuine Excel (.xlsx)."""
    return download_batch_file(batch_id=batch_id, format="xlsx", db=db, current_user=current_user)


@router.get("/{batch_id}/file-info")
def get_batch_file_info(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Returns full file metadata including absolute disk storage paths,
    file sizes, and direct download links for both Excel (.xlsx) and CSV (.csv).
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    mapping_config = batch.mapping_config or {}
    xlsx_path_str = mapping_config.get("_storage_file_xlsx")
    csv_path_str = mapping_config.get("_storage_file_csv")

    xlsx_path = Path(xlsx_path_str).resolve() if xlsx_path_str else None
    csv_path = Path(csv_path_str).resolve() if csv_path_str else None

    is_excel = batch.filename.lower().endswith(('.xlsx', '.xls'))
    primary_format = "XLSX" if is_excel else "CSV"

    xlsx_exists = xlsx_path.exists() if xlsx_path else False
    csv_exists = csv_path.exists() if csv_path else False

    return {
        "batch_id": batch.id,
        "filename": batch.filename,
        "primary_format": primary_format,
        "storage_path_xlsx": str(xlsx_path) if xlsx_path else None,
        "storage_path_csv": str(csv_path) if csv_path else None,
        "full_storage_path": str(xlsx_path if is_excel else csv_path) if (xlsx_path or csv_path) else None,
        "download_url_xlsx": f"/api/v1/uploads/{batch.id}/download?format=xlsx",
        "download_url_csv": f"/api/v1/uploads/{batch.id}/download?format=csv",
        "xlsx_exists": xlsx_exists,
        "csv_exists": csv_exists,
        "xlsx_size_bytes": xlsx_path.stat().st_size if xlsx_exists else 0,
        "csv_size_bytes": csv_path.stat().st_size if csv_exists else 0
    }


@router.post("/{batch_id}/quick-fix")
def quick_fix_batch_errors(
    batch_id: int,
    req: QuickFixRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Innovative Quick-Fix: Automatically resolves unknown programme code errors (e.g. BTECH-AI, BTECH-ELEC)
    by mapping them to the institution's approved offering (e.g. BTECH-CSE), updating storage and re-running
    reconciliation in one atomic operation.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    # Determine replacement programme
    replacement = req.replacement_value
    if not replacement:
        approved_progs = db.query(Programme).filter(Programme.institution_id == batch.institution_id).all()
        if not approved_progs:
            raise HTTPException(status_code=400, detail="No approved programmes registered for this institution.")
        replacement = approved_progs[0].programme_code

    engine = ReconciliationEngine(db=db)
    staged_rows = engine.get_or_sync_staged_rows(batch_id)

    # Query latest run findings for matching rule
    latest_run = db.query(ValidationRun).filter(ValidationRun.batch_id == batch_id).order_by(ValidationRun.run_number.desc()).first()
    if not latest_run:
        raise HTTPException(status_code=400, detail="No validation run found for batch.")

    target_rule = req.target_rule or "RULE_UNKNOWN_PROGRAMME"
    prog_findings = db.query(ValidationFinding).filter(
        ValidationFinding.batch_id == batch_id,
        ValidationFinding.validation_run_id == latest_run.id,
        ValidationFinding.rule_id == target_rule
    ).all()

    row_indices_to_fix = set(f.row_index for f in prog_findings)
    fixed_count = 0

    for sr in staged_rows:
        if sr.row_index in row_indices_to_fix:
            sr.programme_code = replacement.upper().strip()
            sr.updated_at = datetime.utcnow()
            fixed_count += 1

    db.commit()

    # Re-write backing storage files (both CSV and XLSX) from updated staged_rows before revalidating
    mapping_config = batch.mapping_config or {}
    canonical_to_source = {v: k for k, v in mapping_config.items() if not k.startswith("_")}
    rows_data = []
    for r in staged_rows:
        rows_data.append({
            canonical_to_source.get("apaar_id", "apaar_id"): r.apaar_id or "",
            canonical_to_source.get("student_name", "student_name"): r.student_name or "",
            canonical_to_source.get("programme_code", "programme_code"): r.programme_code or "",
            canonical_to_source.get("category", "category"): r.category or "OPEN",
            canonical_to_source.get("gender", "gender"): r.gender or "MALE",
            canonical_to_source.get("admission_quota", "admission_quota"): r.admission_quota or "STATE_GOVT",
            canonical_to_source.get("dob", "dob"): r.dob.isoformat() if r.dob else ""
        })
    updated_df = pd.DataFrame(rows_data)
    engine.sync_storage_files(batch, updated_df)

    # Re-run reconciliation on updated rows
    reval_res = engine.revalidate_batch(
        batch_id=batch_id,
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role
    )

    append_audit_event(
        db=db,
        action="BATCH_QUICK_FIX_APPLIED",
        entity_type="UploadBatch",
        entity_id=str(batch.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch.id,
            "target_rule": target_rule,
            "fixed_count": fixed_count,
            "replacement_value": replacement,
            "updated_error_rows": batch.error_rows
        }
    )
    db.commit()

    return {
        "success": True,
        "fixed_count": fixed_count,
        "replacement_value": replacement,
        "batch_id": batch.id,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "warning_rows": batch.warning_rows,
        "error_rows": batch.error_rows,
        "status": batch.status,
        "disposition": reval_res.get("disposition"),
        "message": f"Successfully corrected {fixed_count} row(s) to approved programme {replacement}. Hard errors: {batch.error_rows}."
    }


@router.put("/{batch_id}/raw")
def update_raw_batch_csv(
    batch_id: int,
    req: RawCsvUpdateRequest,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Direct in-browser Raw CSV web editor update.
    Accepts full CSV text, updates backing storage, syncs staged database rows, and re-validates.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    import io
    try:
        df = pd.read_csv(io.StringIO(req.csv_content), dtype=str).fillna("")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV structure: {str(e)}")

    engine = ReconciliationEngine(db=db)
    engine.sync_storage_files(batch, df)

    mapping_config = batch.mapping_config or {}
    canonical_to_source = {v: k for k, v in mapping_config.items() if not k.startswith("_")}
    if not canonical_to_source:
        canonical_to_source = {
            "apaar_id": "apaar_id",
            "student_name": "student_name",
            "programme_code": "programme_code",
            "dob": "dob",
            "gender": "gender",
            "category": "category",
            "admission_quota": "admission_quota"
        }

    # Clear prior staged rows and re-populate
    db.query(StagedBatchRow).filter(StagedBatchRow.batch_id == batch_id).delete()
    db.flush()

    for idx, row in df.iterrows():
        row_num = idx + 1
        raw_apaar = str(row.get(canonical_to_source.get("apaar_id", "apaar_id"), "")).strip()
        name = str(row.get(canonical_to_source.get("student_name", "student_name"), "")).strip()
        prog_code = str(row.get(canonical_to_source.get("programme_code", "programme_code"), "")).strip().upper()
        raw_dob = str(row.get(canonical_to_source.get("dob", "dob"), "")).strip()
        raw_gender = str(row.get(canonical_to_source.get("gender", "MALE"), "MALE")).strip().upper()
        category = str(row.get(canonical_to_source.get("category", "OPEN"), "OPEN")).strip().upper()
        quota = str(row.get(canonical_to_source.get("admission_quota", "STATE_GOVT"), "STATE_GOVT")).strip()

        parsed_dob = None
        if raw_dob:
            try:
                parsed_dob = pd.to_datetime(raw_dob).date()
            except Exception:
                parsed_dob = None

        new_sr = StagedBatchRow(
            batch_id=batch.id,
            row_index=row_num,
            apaar_id=raw_apaar or None,
            student_name=name or None,
            programme_code=prog_code or None,
            category=category,
            gender=raw_gender,
            dob=parsed_dob,
            admission_quota=quota,
            status="VALID",
            raw_data={k: str(v) for k, v in row.items()}
        )
        db.add(new_sr)

    db.commit()

    # Clear prior findings and re-run reconciliation
    db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch_id).delete()
    db.commit()

    val_run, findings = engine.execute_three_way_reconciliation(
        df=df,
        batch=batch,
        user_id=current_user.id,
        trigger_action="REVALIDATION",
        canonical_to_source=canonical_to_source
    )

    append_audit_event(
        db=db,
        action="BATCH_RAW_CSV_UPDATE",
        entity_type="UploadBatch",
        entity_id=str(batch.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch.id,
            "total_rows": len(df),
            "errors": val_run.blocking_errors
        }
    )
    db.commit()

    return {
        "success": True,
        "batch_id": batch.id,
        "total_rows": batch.total_rows,
        "valid_rows": batch.valid_rows,
        "warning_rows": batch.warning_rows,
        "error_rows": batch.error_rows,
        "status": batch.status,
        "message": f"Raw CSV updated and re-validated. Errors remaining: {batch.error_rows}."
    }


# ---------------------------------------------------------
# AICTE Central "Give an Idea" / Advisory Recommendations
# ---------------------------------------------------------

@router.get("/{batch_id}/advisories")
def get_batch_advisories(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """Returns all official AICTE Central Governance Advisories / Ideas for this batch."""
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    advisories = db.query(AicteCentralAdvisory).filter(
        AicteCentralAdvisory.batch_id == batch_id
    ).order_by(AicteCentralAdvisory.created_at.desc()).all()

    results = []
    for adv in advisories:
        author = db.query(InstitutionUser).filter(InstitutionUser.id == adv.created_by_user_id).first() if adv.created_by_user_id else None
        results.append({
            "id": adv.id,
            "batch_id": adv.batch_id,
            "institution_id": adv.institution_id,
            "advisory_type": adv.advisory_type,
            "title": adv.title,
            "idea_description": adv.idea_description,
            "recommended_action": adv.recommended_action or {},
            "status": adv.status,
            "created_by_name": author.full_name if author else "AICTE Central Committee",
            "created_at": adv.created_at.isoformat() if adv.created_at else None,
            "applied_at": adv.applied_at.isoformat() if adv.applied_at else None
        })
    return results


@router.post("/{batch_id}/advisories", status_code=status.HTTP_201_CREATED)
def issue_central_advisory(
    batch_id: int,
    payload: CentralAdvisoryCreate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    AICTE Central Government officer manually issues an Advisory / Remediation Idea
    to guide the college on how to resolve discrepancy or apply regulatory dispensations.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    adv = AicteCentralAdvisory(
        batch_id=batch.id,
        institution_id=batch.institution_id,
        advisory_type=payload.advisory_type or "PROGRAMME_REMAP_RECOMMENDATION",
        title=payload.title,
        idea_description=payload.idea_description,
        recommended_action=payload.recommended_action or {},
        status="ACTIVE",
        created_by_user_id=current_user.id
    )
    db.add(adv)
    db.flush()

    append_audit_event(
        db=db,
        action="AICTE_ADVISORY_ISSUED",
        entity_type="AicteCentralAdvisory",
        entity_id=str(adv.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "batch_id": batch.id,
            "institution_id": batch.institution_id,
            "title": adv.title,
            "advisory_type": adv.advisory_type,
            "recommended_action": adv.recommended_action
        }
    )
    db.commit()
    db.refresh(adv)

    return {
        "id": adv.id,
        "batch_id": adv.batch_id,
        "title": adv.title,
        "idea_description": adv.idea_description,
        "status": adv.status,
        "message": "AICTE Central Advisory / Idea successfully dispatched to institution."
    }


@router.post("/{batch_id}/advisories/{advisory_id}/apply")
def apply_central_advisory(
    batch_id: int,
    advisory_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    One-click resolution: College or AICTE officer applies the Central Government's
    remediation idea. Staged rows and batch storage file are automatically remapped,
    and reconciliation is re-executed with audit ledger chaining.
    """
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    verify_institution_access(batch.institution_id, current_user)

    adv = db.query(AicteCentralAdvisory).filter(
        AicteCentralAdvisory.id == advisory_id,
        AicteCentralAdvisory.batch_id == batch_id
    ).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Advisory not found")

    rec_action = adv.recommended_action or {}
    action_type = rec_action.get("action")

    engine = ReconciliationEngine(db=db)
    mapping_config = batch.mapping_config or {}
    storage_file_path = mapping_config.get("_storage_file")
    storage_path = Path(storage_file_path) if storage_file_path else None

    applied_changes = 0
    if action_type == "REMAP_PROGRAMME":
        from_code = str(rec_action.get("from_code", "")).strip().upper()
        to_code = str(rec_action.get("to_code", "")).strip().upper()

        if from_code and to_code:
            staged_rows = db.query(StagedBatchRow).filter(
                StagedBatchRow.batch_id == batch.id,
                StagedBatchRow.programme_code == from_code
            ).all()

            for sr in staged_rows:
                sr.programme_code = to_code
                if sr.raw_data and isinstance(sr.raw_data, dict):
                    raw_copy = dict(sr.raw_data)
                    for k in list(raw_copy.keys()):
                        if "prog" in k.lower() or "branch" in k.lower() or "course" in k.lower():
                            raw_copy[k] = to_code
                    sr.raw_data = raw_copy
                sr.updated_at = datetime.utcnow()
                applied_changes += 1

            db.commit()

            # Reconstruct and rewrite backing storage file
            all_staged = db.query(StagedBatchRow).filter(
                StagedBatchRow.batch_id == batch.id
            ).order_by(StagedBatchRow.row_index.asc()).all()
            if not all_staged:
                all_staged = engine.get_or_sync_staged_rows(batch.id)

            canonical_to_source = {v: k for k, v in mapping_config.items() if not k.startswith("_")}
            if not canonical_to_source:
                canonical_to_source = {
                    "apaar_id": "apaar_id",
                    "student_name": "student_name",
                    "programme_code": "programme_code",
                    "category": "category",
                    "gender": "gender",
                    "admission_quota": "admission_quota",
                    "dob": "dob"
                }

            rows_data = []
            for r in all_staged:
                rows_data.append({
                    canonical_to_source.get("apaar_id", "apaar_id"): r.apaar_id or "",
                    canonical_to_source.get("student_name", "student_name"): r.student_name or "",
                    canonical_to_source.get("programme_code", "programme_code"): r.programme_code or "",
                    canonical_to_source.get("category", "category"): r.category or "OPEN",
                    canonical_to_source.get("gender", "gender"): r.gender or "MALE",
                    canonical_to_source.get("admission_quota", "admission_quota"): r.admission_quota or "STATE_GOVT",
                    canonical_to_source.get("dob", "dob"): r.dob.isoformat() if r.dob else ""
                })
            updated_df = pd.DataFrame(rows_data)

            if storage_path and not updated_df.empty:
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                updated_df.to_csv(storage_path, index=False)

    # Mark advisory as applied
    adv.status = "APPLIED_BY_COLLEGE"
    adv.applied_at = datetime.utcnow()
    db.commit()

    # Re-run reconciliation
    run_result = engine.revalidate_batch(
        batch_id=batch.id,
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role
    )

    append_audit_event(
        db=db,
        action="AICTE_ADVISORY_APPLIED",
        entity_type="AicteCentralAdvisory",
        entity_id=str(adv.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "advisory_id": adv.id,
            "batch_id": batch.id,
            "action_applied": action_type,
            "records_adjusted": applied_changes,
            "new_blocking_errors": run_result["disposition"]["blocking_errors"]
        }
    )
    db.commit()

    return {
        "success": True,
        "advisory_id": adv.id,
        "advisory_status": adv.status,
        "records_adjusted": applied_changes,
        "batch_status": batch.status,
        "error_rows": batch.error_rows,
        "valid_rows": batch.valid_rows,
        "message": f"Successfully applied AICTE Central Advisory '{adv.title}'. Batch re-evaluated."
    }

