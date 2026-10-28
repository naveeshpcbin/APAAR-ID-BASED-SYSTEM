from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models import (
    Institution, Programme, ApprovalSnapshot, InstitutionalDeclaration,
    SyntheticApaarRecord, UploadBatch, ValidationRun, ValidationFinding,
    InstitutionUser, PolicyRuleSet, AuditEvent
)
from app.schemas.reference_data import (
    InstitutionCreate, InstitutionUpdate,
    ProgrammeCreate, ProgrammeUpdate,
    ApprovalUpdate, DeclarationUpdate,
    SyntheticApaarCreate, SyntheticApaarUpdate,
    ReferenceOverviewResponse
)
from app.api.deps import get_current_user, require_roles
from app.core.hash_chain import append_audit_event

router = APIRouter(prefix="/reference-data", tags=["Demo Reference Data Management"])


@router.get("/overview", response_model=ReferenceOverviewResponse)
def get_reference_overview(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """Returns overview of all synthetic reference registries for demonstration administrators."""
    inst_count = db.query(Institution).count()
    prog_count = db.query(Programme).count()
    appr_count = db.query(ApprovalSnapshot).count()
    decl_count = db.query(InstitutionalDeclaration).count()
    apaar_count = db.query(SyntheticApaarRecord).count()

    status_counts = {}
    statuses = db.query(SyntheticApaarRecord.status, func.count(SyntheticApaarRecord.id)).group_by(SyntheticApaarRecord.status).all()
    for s, c in statuses:
        status_counts[s] = c

    policies = [p.policy_version for p in db.query(ApprovalSnapshot.policy_version).distinct().all() if p.policy_version]
    if not policies:
        policies = ["AICTE-APH-2026-V1"]

    last_event = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    last_event_dict = None
    if last_event:
        last_event_dict = {
            "id": last_event.id,
            "action": last_event.action,
            "entity_type": last_event.entity_type,
            "actor_email": last_event.actor_email,
            "timestamp": last_event.created_at.isoformat() if last_event.created_at else None,
            "current_hash": last_event.current_hash
        }

    return ReferenceOverviewResponse(
        total_institutions=inst_count,
        total_programmes=prog_count,
        total_approvals=appr_count,
        total_declarations=decl_count,
        total_synthetic_apaar=apaar_count,
        synthetic_apaar_by_status=status_counts,
        policy_versions=policies,
        last_audit_event=last_event_dict
    )


# ---------------------------------------------------------
# Institutions Management
# ---------------------------------------------------------

@router.get("/institutions")
def list_institutions(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    institutions = db.query(Institution).all()
    return [
        {
            "id": inst.id,
            "aicte_id": inst.aicte_id,
            "name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "institution_type": inst.institution_type,
            "status": inst.status,
            "contact_email": inst.contact_email,
            "created_at": inst.created_at.isoformat() if inst.created_at else None
        }
        for inst in institutions
    ]


@router.post("/institutions", status_code=status.HTTP_201_CREATED)
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    existing = db.query(Institution).filter(Institution.aicte_id == payload.aicte_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Institution with AICTE ID {payload.aicte_id} already exists.")

    inst = Institution(
        aicte_id=payload.aicte_id,
        name=payload.name,
        state=payload.state,
        district=payload.district,
        institution_type=payload.institution_type,
        status=payload.status,
        contact_email=payload.contact_email
    )
    db.add(inst)
    db.flush()

    append_audit_event(
        db=db,
        action="INSTITUTION_CREATED",
        entity_type="Institution",
        entity_id=str(inst.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={"aicte_id": inst.aicte_id, "name": inst.name}
    )
    db.commit()
    db.refresh(inst)

    return {"id": inst.id, "aicte_id": inst.aicte_id, "name": inst.name, "status": inst.status}


@router.put("/institutions/{inst_id}")
def update_institution(
    inst_id: int,
    payload: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    inst = db.query(Institution).filter(Institution.id == inst_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    changes = {}
    for field, val in payload.dict(exclude_unset=True).items():
        if val is not None:
            old_val = getattr(inst, field)
            if old_val != val:
                changes[field] = {"old": old_val, "new": val}
                setattr(inst, field, val)

    if changes:
        append_audit_event(
            db=db,
            action="INSTITUTION_UPDATED",
            entity_type="Institution",
            entity_id=str(inst.id),
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            metadata_json={"institution_id": inst.id, "changes": changes}
        )
        db.commit()
        db.refresh(inst)

    return {
        "id": inst.id,
        "aicte_id": inst.aicte_id,
        "name": inst.name,
        "state": inst.state,
        "district": inst.district,
        "status": inst.status,
        "contact_email": inst.contact_email
    }


# ---------------------------------------------------------
# Programmes Management
# ---------------------------------------------------------

@router.get("/programmes")
def list_programmes(
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    query = db.query(Programme)
    if institution_id:
        query = query.filter(Programme.institution_id == institution_id)
    programmes = query.all()
    return [
        {
            "id": p.id,
            "institution_id": p.institution_id,
            "institution_name": p.institution.name if p.institution else None,
            "programme_code": p.programme_code,
            "programme_name": p.programme_name,
            "degree_level": p.degree_level,
            "duration_years": p.duration_years
        }
        for p in programmes
    ]


@router.post("/programmes", status_code=status.HTTP_201_CREATED)
def create_programme(
    payload: ProgrammeCreate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    prog = Programme(
        institution_id=payload.institution_id,
        programme_code=payload.programme_code.upper().strip(),
        programme_name=payload.programme_name,
        degree_level=payload.degree_level,
        duration_years=payload.duration_years
    )
    db.add(prog)
    db.flush()

    append_audit_event(
        db=db,
        action="PROGRAMME_CREATED",
        entity_type="Programme",
        entity_id=str(prog.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "institution_id": prog.institution_id,
            "programme_code": prog.programme_code,
            "programme_name": prog.programme_name
        }
    )
    db.commit()
    db.refresh(prog)

    return {
        "id": prog.id,
        "institution_id": prog.institution_id,
        "programme_code": prog.programme_code,
        "programme_name": prog.programme_name
    }


# ---------------------------------------------------------
# Approval References Management
# ---------------------------------------------------------

@router.get("/approvals")
def list_approvals(
    institution_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    query = db.query(ApprovalSnapshot).join(Programme).join(Institution)
    if institution_id:
        query = query.filter(ApprovalSnapshot.institution_id == institution_id)
    if academic_year:
        query = query.filter(ApprovalSnapshot.academic_year == academic_year)

    approvals = query.all()
    return [
        {
            "id": a.id,
            "institution_id": a.institution_id,
            "institution_name": a.institution.name if a.institution else None,
            "programme_id": a.programme_id,
            "programme_code": a.programme.programme_code if a.programme else None,
            "programme_name": a.programme.programme_name if a.programme else None,
            "academic_year": a.academic_year,
            "approved_intake": a.approved_intake,
            "supernumerary_quota": a.supernumerary_quota or {},
            "approval_letter_ref": a.approval_letter_ref,
            "policy_version": a.policy_version,
            "is_active": a.is_active
        }
        for a in approvals
    ]


@router.put("/approvals/{approval_id}")
def update_approval_snapshot(
    approval_id: int,
    payload: ApprovalUpdate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    approval = db.query(ApprovalSnapshot).filter(ApprovalSnapshot.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval snapshot reference not found.")

    if payload.approved_intake < 0:
        raise HTTPException(status_code=422, detail="Approved intake cannot be negative.")

    old_intake = approval.approved_intake
    old_quotas = approval.supernumerary_quota

    approval.approved_intake = payload.approved_intake
    if payload.supernumerary_quota is not None:
        approval.supernumerary_quota = payload.supernumerary_quota
    if payload.approval_letter_ref is not None:
        approval.approval_letter_ref = payload.approval_letter_ref
    if payload.policy_version is not None:
        approval.policy_version = payload.policy_version

    append_audit_event(
        db=db,
        action="APPROVAL_SNAPSHOT_UPDATED",
        entity_type="ApprovalSnapshot",
        entity_id=str(approval.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "approval_id": approval.id,
            "institution_id": approval.institution_id,
            "programme_id": approval.programme_id,
            "old_intake": old_intake,
            "new_intake": approval.approved_intake,
            "old_quotas": old_quotas,
            "new_quotas": approval.supernumerary_quota
        }
    )
    db.commit()
    db.refresh(approval)

    return {
        "id": approval.id,
        "institution_id": approval.institution_id,
        "programme_id": approval.programme_id,
        "academic_year": approval.academic_year,
        "approved_intake": approval.approved_intake,
        "supernumerary_quota": approval.supernumerary_quota,
        "policy_version": approval.policy_version
    }


# ---------------------------------------------------------
# Institutional Declarations Management
# ---------------------------------------------------------

@router.get("/declarations")
def list_declarations(
    institution_id: Optional[int] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    query = db.query(InstitutionalDeclaration).join(Programme).join(Institution)
    if institution_id:
        query = query.filter(InstitutionalDeclaration.institution_id == institution_id)
    if academic_year:
        query = query.filter(InstitutionalDeclaration.academic_year == academic_year)

    declarations = query.all()
    return [
        {
            "id": d.id,
            "institution_id": d.institution_id,
            "institution_name": d.institution.name if d.institution else None,
            "programme_id": d.programme_id,
            "programme_code": d.programme.programme_code if d.programme else None,
            "programme_name": d.programme.programme_name if d.programme else None,
            "academic_year": d.academic_year,
            "declared_intake": d.declared_intake,
            "reporting_scope": d.reporting_scope,
            "declaration_ref": d.declaration_ref,
            "declared_at": d.declared_at.isoformat() if d.declared_at else None
        }
        for d in declarations
    ]


@router.put("/declarations/{declaration_id}")
def update_declaration(
    declaration_id: int,
    payload: DeclarationUpdate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    decl = db.query(InstitutionalDeclaration).filter(InstitutionalDeclaration.id == declaration_id).first()
    if not decl:
        raise HTTPException(status_code=404, detail="Institutional declaration not found.")

    if payload.declared_intake < 0:
        raise HTTPException(status_code=422, detail="Declared intake cannot be negative.")

    old_declared = decl.declared_intake
    decl.declared_intake = payload.declared_intake
    if payload.reporting_scope is not None:
        decl.reporting_scope = payload.reporting_scope
    if payload.declaration_ref is not None:
        decl.declaration_ref = payload.declaration_ref
    decl.updated_at = datetime.utcnow()

    append_audit_event(
        db=db,
        action="INSTITUTIONAL_DECLARATION_UPDATED",
        entity_type="InstitutionalDeclaration",
        entity_id=str(decl.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "declaration_id": decl.id,
            "institution_id": decl.institution_id,
            "programme_id": decl.programme_id,
            "old_declared": old_declared,
            "new_declared": decl.declared_intake
        }
    )
    db.commit()
    db.refresh(decl)

    return {
        "id": decl.id,
        "institution_id": decl.institution_id,
        "programme_id": decl.programme_id,
        "academic_year": decl.academic_year,
        "declared_intake": decl.declared_intake,
        "reporting_scope": decl.reporting_scope,
        "declaration_ref": decl.declaration_ref
    }


# ---------------------------------------------------------
# Synthetic APAAR Reference Registry Management
# ---------------------------------------------------------

@router.get("/synthetic-apaar")
def list_synthetic_apaar(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    query = db.query(SyntheticApaarRecord)
    if status_filter:
        query = query.filter(SyntheticApaarRecord.status == status_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (SyntheticApaarRecord.apaar_id.like(s)) | (SyntheticApaarRecord.full_name.like(s))
        )

    total = query.count()
    records = query.order_by(SyntheticApaarRecord.id.asc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "records": [
            {
                "id": r.id,
                "apaar_id": r.apaar_id,
                "full_name": r.full_name,
                "dob": r.dob.isoformat() if r.dob else None,
                "gender": r.gender,
                "status": r.status,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            }
            for r in records
        ]
    }


@router.post("/synthetic-apaar", status_code=status.HTTP_201_CREATED)
def create_synthetic_apaar(
    payload: SyntheticApaarCreate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    clean_apaar = payload.apaar_id.replace(" ", "").replace("-", "")
    if not clean_apaar.isdigit() or len(clean_apaar) != 12:
        raise HTTPException(status_code=422, detail="APAAR ID must be exactly 12 numeric digits.")

    existing = db.query(SyntheticApaarRecord).filter(SyntheticApaarRecord.apaar_id == clean_apaar).first()
    if existing:
        existing.full_name = payload.full_name
        existing.dob = payload.dob
        existing.gender = payload.gender.upper() if payload.gender else "MALE"
        existing.status = payload.status
        existing.notes = f"[DEMO DATA - NOT OFFICIAL PII] {payload.notes or ''}".strip()
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return {
            "id": existing.id,
            "apaar_id": existing.apaar_id,
            "full_name": existing.full_name,
            "status": existing.status,
            "dob": existing.dob.isoformat() if existing.dob else None,
            "notes": existing.notes,
            "message": f"Updated existing synthetic APAAR record {clean_apaar}."
        }

    rec = SyntheticApaarRecord(
        apaar_id=clean_apaar,
        full_name=payload.full_name,
        dob=payload.dob,
        gender=payload.gender.upper() if payload.gender else "MALE",
        status=payload.status,
        notes=f"[DEMO DATA - NOT OFFICIAL PII] {payload.notes or ''}".strip()
    )
    db.add(rec)
    db.flush()

    append_audit_event(
        db=db,
        action="SYNTHETIC_APAAR_RECORD_CREATED",
        entity_type="SyntheticApaarRecord",
        entity_id=str(rec.id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "record_id": rec.id,
            "apaar_id": rec.apaar_id,
            "status": rec.status,
            "full_name": rec.full_name
        }
    )
    db.commit()
    db.refresh(rec)

    return {
        "id": rec.id,
        "apaar_id": rec.apaar_id,
        "full_name": rec.full_name,
        "status": rec.status,
        "dob": rec.dob.isoformat() if rec.dob else None,
        "notes": rec.notes
    }


@router.post("/synthetic-apaar/seed-batch")
def seed_synthetic_apaar_batch(
    count: int = Query(5, ge=1, le=50),
    with_discrepancies: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    Seeds a batch of synthetic APAAR reference records into the live database.
    Facilitates instant simulation and validation testing for central regulators.
    """
    import random
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
    ]
    created = []
    base_prefix = 980000000000

    for i in range(count):
        name_info = names_pool[i % len(names_pool)]
        candidate_apaar = str(base_prefix + random.randint(10000000, 99999999))

        status_val = "DEMO_REFERENCE_MATCH"
        note = "Generated synthetic candidate for dynamic simulation"
        if with_discrepancies:
            if i % 2 == 0:
                status_val = "NO_DEMO_REFERENCE_MATCH"
                note = "Simulated discrepancy: Non-matching reference in central registry"
            else:
                status_val = "MANUAL_REVIEW_REQUIRED"
                note = "Simulated discrepancy: Biometric manual review required"

        rec = db.query(SyntheticApaarRecord).filter(SyntheticApaarRecord.apaar_id == candidate_apaar).first()
        if not rec:
            rec = SyntheticApaarRecord(
                apaar_id=candidate_apaar,
                full_name=f"{name_info[0]} (Demo {i+1})",
                dob=datetime.strptime(name_info[2], "%Y-%m-%d").date(),
                gender=name_info[1],
                status=status_val,
                notes=f"[DEMO DATA - NOT OFFICIAL PII] {note}"
            )
            db.add(rec)
            db.flush()
            created.append({
                "id": rec.id,
                "apaar_id": rec.apaar_id,
                "full_name": rec.full_name,
                "status": rec.status,
                "dob": rec.dob.isoformat() if rec.dob else None
            })

    append_audit_event(
        db=db,
        action="SYNTHETIC_APAAR_BATCH_SEEDED",
        entity_type="SyntheticApaarRecord",
        entity_id="batch",
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "count": len(created),
            "with_discrepancies": with_discrepancies
        }
    )
    db.commit()

    return {
        "success": True,
        "seeded_count": len(created),
        "records": created,
        "message": f"Successfully seeded {len(created)} synthetic APAAR reference records into database."
    }


@router.put("/synthetic-apaar/{record_id}")
def update_synthetic_apaar(
    record_id: int,
    payload: SyntheticApaarUpdate,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    rec = db.query(SyntheticApaarRecord).filter(SyntheticApaarRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Synthetic APAAR record not found.")

    changes = {}
    if payload.full_name is not None and rec.full_name != payload.full_name:
        changes["full_name"] = {"old": rec.full_name, "new": payload.full_name}
        rec.full_name = payload.full_name
    if payload.dob is not None and rec.dob != payload.dob:
        changes["dob"] = {"old": rec.dob.isoformat(), "new": payload.dob.isoformat()}
        rec.dob = payload.dob
    if payload.gender is not None and rec.gender != payload.gender:
        changes["gender"] = {"old": rec.gender, "new": payload.gender}
        rec.gender = payload.gender
    if payload.status is not None and rec.status != payload.status:
        changes["status"] = {"old": rec.status, "new": payload.status}
        rec.status = payload.status
    if payload.notes is not None:
        rec.notes = payload.notes

    rec.updated_at = datetime.utcnow()

    if changes:
        append_audit_event(
            db=db,
            action="SYNTHETIC_APAAR_RECORD_UPDATED",
            entity_type="SyntheticApaarRecord",
            entity_id=str(rec.id),
            actor_id=current_user.id,
            actor_email=current_user.email,
            actor_role=current_user.role,
            metadata_json={
                "record_id": rec.id,
                "apaar_id": rec.apaar_id,
                "changes": changes
            }
        )
        db.commit()
        db.refresh(rec)

    return {
        "id": rec.id,
        "apaar_id": rec.apaar_id,
        "full_name": rec.full_name,
        "status": rec.status,
        "dob": rec.dob.isoformat() if rec.dob else None,
        "notes": rec.notes
    }


@router.delete("/synthetic-apaar/{record_id}")
def delete_synthetic_apaar(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    rec = db.query(SyntheticApaarRecord).filter(SyntheticApaarRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Synthetic APAAR record not found.")

    deleted_info = {
        "id": rec.id,
        "apaar_id": rec.apaar_id,
        "full_name": rec.full_name,
        "status": rec.status
    }

    db.delete(rec)
    append_audit_event(
        db=db,
        action="SYNTHETIC_APAAR_RECORD_DELETED",
        entity_type="SyntheticApaarRecord",
        entity_id=str(record_id),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json=deleted_info
    )
    db.commit()

    return {
        "success": True,
        "message": f"Synthetic APAAR record #{record_id} ({deleted_info['apaar_id']}) deleted successfully.",
        "deleted_record": deleted_info
    }


# ---------------------------------------------------------
# Dynamic Revalidation Trigger Endpoint (Tests A, B, C, D, E)
# ---------------------------------------------------------

@router.post("/revalidate/{batch_id}")
def revalidate_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    SIH Core Requirement: Dynamic Revalidation against updated database reference information.
    Proves that validation results depend on live database reference data rather than hardcoded rules.
    Preserves historical traceability by persisting a new ValidationRun.
    """
    from app.services.reconciliation_engine import ReconciliationEngine

    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found.")

    engine = ReconciliationEngine(db=db)
    try:
        run_result = engine.revalidate_batch(
            batch_id=batch_id,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role
        )
        return run_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Revalidation failed: {str(e)}")


# ---------------------------------------------------------
# Supabase Cloud Database & Registry Connector Endpoints
# ---------------------------------------------------------

@router.get("/supabase/status")
def get_supabase_status(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """Returns the live connection status of the Supabase PostgreSQL cloud adapter."""
    from app.adapters.supabase_adapter import SupabaseAdapter
    adapter = SupabaseAdapter(db=db)
    return adapter.get_status()


@router.post("/supabase/sync")
def sync_supabase_registry(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """Synchronizes local synthetic reference data with Supabase Cloud table."""
    from app.adapters.supabase_adapter import SupabaseAdapter
    adapter = SupabaseAdapter(db=db)
    result = adapter.sync_to_supabase()
    return result


# ---------------------------------------------------------
# Sovereign Cryptographic Data Vault & Integrity Proof
# ---------------------------------------------------------

@router.get("/vault/integrity")
def get_vault_integrity(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
    """
    Returns real-time SHA-256 Merkle root sovereign consensus seal and verification proof
    for all synthetic reference datasets (APAAR registry, approved intakes, institutional declarations).
    """
    from app.core.sovereign_vault import SovereignDataVault
    vault = SovereignDataVault(db=db)
    return vault.verify_vault_integrity()


@router.post("/vault/seal")
def seal_vault_snapshot(
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    Locks and seals the current synthetic reference state into the immutable audit hash chain.
    """
    from app.core.sovereign_vault import SovereignDataVault
    vault = SovereignDataVault(db=db)
    result = vault.seal_vault(
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        reason="Manual Sovereign Cryptographic Seal committed by AICTE Admin"
    )
    return result


# ---------------------------------------------------------
# Central Government Manual Add: Programme With Approval
# ---------------------------------------------------------

@router.post("/programmes-with-approval", status_code=status.HTTP_201_CREATED)
def create_programme_with_approval(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(require_roles(["AICTE_ADMIN", "REGIONAL_OFFICER"]))
):
    """
    Enables AICTE Central Admin to add a new approved academic programme and
    sanctioned intake quota in a single regulatory action.
    """
    institution_id = int(payload.get("institution_id", 0))
    prog_code = str(payload.get("programme_code", "")).strip().upper()
    prog_name = str(payload.get("programme_name", "")).strip()
    academic_year = str(payload.get("academic_year", "2026-27")).strip()
    approved_intake = int(payload.get("approved_intake", 60))
    tfw_quota = int(payload.get("tfw_quota", 3))

    if not institution_id or not prog_code or not prog_name:
        raise HTTPException(status_code=400, detail="institution_id, programme_code, and programme_name are required.")

    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    # Check if programme code already exists for this institution
    prog = db.query(Programme).filter(
        Programme.institution_id == institution_id,
        Programme.programme_code == prog_code
    ).first()

    if not prog:
        prog = Programme(
            institution_id=institution_id,
            programme_code=prog_code,
            programme_name=prog_name,
            degree_level=payload.get("degree_level", "UG"),
            duration_years=int(payload.get("duration_years", 4))
        )
        db.add(prog)
        db.flush()

    # Create or update approval snapshot
    appr = db.query(ApprovalSnapshot).filter(
        ApprovalSnapshot.institution_id == institution_id,
        ApprovalSnapshot.programme_id == prog.id,
        ApprovalSnapshot.academic_year == academic_year
    ).first()

    if not appr:
        appr = ApprovalSnapshot(
            institution_id=institution_id,
            programme_id=prog.id,
            academic_year=academic_year,
            approved_intake=approved_intake,
            supernumerary_quota={"TFW": tfw_quota, "EWS": int(approved_intake * 0.1)},
            approval_letter_ref=f"AICTE/APH/{academic_year}/{prog_code}",
            policy_version="AICTE-APH-2026-V1",
            is_active=True
        )
        db.add(appr)
    else:
        appr.approved_intake = approved_intake
        appr.supernumerary_quota = {"TFW": tfw_quota, "EWS": int(approved_intake * 0.1)}

    db.flush()

    # Auto-generate or update institutional declaration
    decl = db.query(InstitutionalDeclaration).filter(
        InstitutionalDeclaration.institution_id == institution_id,
        InstitutionalDeclaration.programme_id == prog.id,
        InstitutionalDeclaration.academic_year == academic_year
    ).first()

    if not decl:
        decl = InstitutionalDeclaration(
            institution_id=institution_id,
            programme_id=prog.id,
            academic_year=academic_year,
            declared_intake=approved_intake,
            reporting_scope="ALL",
            declaration_ref=f"DECL/{academic_year}/{prog_code}"
        )
        db.add(decl)

    append_audit_event(
        db=db,
        action="PROGRAMME_AND_APPROVAL_CREATED",
        entity_type="ApprovalSnapshot",
        entity_id=str(appr.id if appr.id else "NEW"),
        actor_id=current_user.id,
        actor_email=current_user.email,
        actor_role=current_user.role,
        metadata_json={
            "institution_id": institution_id,
            "programme_code": prog_code,
            "approved_intake": approved_intake,
            "academic_year": academic_year
        }
    )
    db.commit()

    return {
        "success": True,
        "institution_id": institution_id,
        "programme_id": prog.id,
        "programme_code": prog.programme_code,
        "approved_intake": appr.approved_intake,
        "message": f"Successfully registered approved programme {prog_code} ({approved_intake} seats) for {inst.name}."
    }
