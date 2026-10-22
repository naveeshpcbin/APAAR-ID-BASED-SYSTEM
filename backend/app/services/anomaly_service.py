import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import AnomalyCase, UploadBatch, AdmissionRecord, Institution, Programme, ApprovalSnapshot
from app.core.hash_chain import append_audit_event

class AnomalyDetectionService:
    @staticmethod
    def evaluate_batch_anomalies(
        db: Session,
        batch_id: int,
        correlation_id: Optional[str] = None
    ) -> List[AnomalyCase]:
        """
        Calculates explainable regulatory anomaly indicators for an uploaded batch.
        Transparent scoring based on business rules and statistical deviations.
        """
        batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
        if not batch:
            return []

        detected_cases: List[AnomalyCase] = []
        inst = db.query(Institution).filter(Institution.id == batch.institution_id).first()

        # Fetch admissions in this batch
        batch_admissions = db.query(AdmissionRecord).filter(AdmissionRecord.batch_id == batch_id).all()
        if not batch_admissions:
            return []

        # 1. Capacity Spike Signal: Upload batch size > 85% of total annual approved intake
        total_approved = sum([
            app.approved_intake for app in db.query(ApprovalSnapshot).filter(
                ApprovalSnapshot.institution_id == batch.institution_id,
                ApprovalSnapshot.academic_year == batch.academic_year,
                ApprovalSnapshot.is_active == True
            ).all()
        ]) or 1

        intake_ratio = len(batch_admissions) / total_approved
        if intake_ratio >= 0.85 and len(batch_admissions) >= 50:
            case_num = f"ANOM-{batch.academic_year[:4]}-{uuid.uuid4().hex[:6].upper()}"
            risk = round(min(95.0, 50.0 + (intake_ratio * 35.0)), 1)
            signals = {
                "batch_records": len(batch_admissions),
                "total_approved_intake": total_approved,
                "intake_surge_ratio": round(intake_ratio, 2),
                "trigger_threshold": 0.85
            }
            explanation = (
                f"Batch #{batch.id} submitted {len(batch_admissions)} records in a single ingestion event, "
                f"representing {round(intake_ratio * 100, 1)}% of the institution's total approved annual capacity ({total_approved} seats). "
                f"Concentrated batch uploads near regulatory deadlines warrant validation of fee receipt dates and admission committee minutes."
            )
            case = AnomalyCase(
                case_number=case_num,
                institution_id=batch.institution_id,
                academic_year=batch.academic_year,
                risk_score=risk,
                anomaly_type="INTAKE_SPIKE",
                signals_json=signals,
                explanation=explanation,
                status="PENDING_REVIEW"
            )
            db.add(case)
            detected_cases.append(case)

        # 2. Collision Burst Signal: Batch with multiple duplicate/quarantine records
        if batch.warning_rows > 0:
            collision_ratio = batch.warning_rows / max(1, batch.total_rows)
            if collision_ratio >= 0.10:  # 10% or more warnings/conflicts
                case_num = f"ANOM-{batch.academic_year[:4]}-{uuid.uuid4().hex[:6].upper()}"
                risk = round(min(90.0, 40.0 + (collision_ratio * 100)), 1)
                signals = {
                    "total_rows": batch.total_rows,
                    "warning_rows": batch.warning_rows,
                    "collision_ratio": round(collision_ratio, 2)
                }
                explanation = (
                    f"Batch #{batch.id} contains {batch.warning_rows} collision or warning rows out of {batch.total_rows} total rows "
                    f"({round(collision_ratio * 100, 1)}% dispute rate). Unusually high overlap with records in other colleges."
                )
                case = AnomalyCase(
                    case_number=case_num,
                    institution_id=batch.institution_id,
                    academic_year=batch.academic_year,
                    risk_score=risk,
                    anomaly_type="COLLISION_BURST",
                    signals_json=signals,
                    explanation=explanation,
                    status="PENDING_REVIEW"
                )
                db.add(case)
                detected_cases.append(case)

        # 3. Category Distribution Anomaly (e.g. 0% SC/ST/OBC in a state-aided technical institution)
        if inst and inst.institution_type in ["STATE_GOVT_AIDED", "CENTRAL_UNIVERSITY"] and len(batch_admissions) >= 30:
            reserved_count = sum(1 for a in batch_admissions if a.category in ["SC", "ST", "OBC_NCL", "EWS"])
            if reserved_count == 0:
                case_num = f"ANOM-{batch.academic_year[:4]}-{uuid.uuid4().hex[:6].upper()}"
                risk = 82.5
                signals = {
                    "batch_size": len(batch_admissions),
                    "reserved_category_count": 0,
                    "institution_type": inst.institution_type
                }
                explanation = (
                    f"Batch #{batch.id} submitted {len(batch_admissions)} records with zero representation of reserved categories "
                    f"(SC, ST, OBC-NCL, EWS) at a {inst.institution_type} institution. AICTE mandate requires audit against state reservation quota policy."
                )
                case = AnomalyCase(
                    case_number=case_num,
                    institution_id=batch.institution_id,
                    academic_year=batch.academic_year,
                    risk_score=risk,
                    anomaly_type="CATEGORY_DISTRIBUTION_ANOMALY",
                    signals_json=signals,
                    explanation=explanation,
                    status="PENDING_REVIEW"
                )
                db.add(case)
                detected_cases.append(case)

        if detected_cases:
            db.commit()
            for c in detected_cases:
                db.refresh(c)
                append_audit_event(
                    db=db,
                    action="ANOMALY_FLAGGED",
                    entity_type="AnomalyCase",
                    entity_id=str(c.id),
                    actor_role="ANOMALY_ENGINE",
                    metadata_json={
                        "case_number": c.case_number,
                        "anomaly_type": c.anomaly_type,
                        "risk_score": c.risk_score
                    },
                    correlation_id=correlation_id
                )

        return detected_cases

    @staticmethod
    def review_anomaly(
        db: Session,
        anomaly_id: int,
        new_status: str,
        notes: str,
        reviewed_by_user_id: int,
        reviewed_by_email: str,
        reviewed_by_role: str
    ) -> AnomalyCase:
        c = db.query(AnomalyCase).filter(AnomalyCase.id == anomaly_id).first()
        if not c:
            raise ValueError("Anomaly case not found.")
        c.status = new_status
        signals = dict(c.signals_json or {})
        signals["review_notes"] = notes
        c.signals_json = signals
        db.commit()
        db.refresh(c)

        append_audit_event(
            db=db,
            action="ANOMALY_REVIEWED",
            entity_type="AnomalyCase",
            entity_id=str(c.id),
            actor_id=reviewed_by_user_id,
            actor_email=reviewed_by_email,
            actor_role=reviewed_by_role,
            metadata_json={
                "case_number": c.case_number,
                "new_status": new_status,
                "review_notes": notes
            }
        )
        return c
