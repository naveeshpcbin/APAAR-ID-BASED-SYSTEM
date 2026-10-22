import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import AdmissionConflict, AdmissionRecord, StudentIdentity, Institution, Programme
from app.core.hash_chain import append_audit_event

class ConflictDetectionService:
    @staticmethod
    def check_for_conflicts(
        db: Session,
        student_id: int,
        new_record_id: int,
        institution_id: int,
        academic_year: str,
        correlation_id: Optional[str] = None
    ) -> Optional[AdmissionConflict]:
        """
        Inspects existing admissions for this student. If another active admission
        exists in the same academic year (at a different institution or same institution),
        creates a formal AdmissionConflict case.
        """
        existing_active = db.query(AdmissionRecord).filter(
            AdmissionRecord.student_id == student_id,
            AdmissionRecord.academic_year == academic_year,
            AdmissionRecord.id != new_record_id,
            AdmissionRecord.status.in_(["ACTIVE", "UNDER_REVIEW"])
        ).first()

        if not existing_active:
            return None

        # Check if already flagged in an open case
        existing_conflict = db.query(AdmissionConflict).filter(
            AdmissionConflict.student_id == student_id,
            AdmissionConflict.status.in_(["OPEN", "UNDER_INVESTIGATION"]),
            ((AdmissionConflict.record_a_id == existing_active.id) | (AdmissionConflict.record_b_id == existing_active.id))
        ).first()

        if existing_conflict:
            return existing_conflict

        conflict_type = "CROSS_INSTITUTION_DUPLICATE" if existing_active.institution_id != institution_id else "WITHIN_INSTITUTION_DUPLICATE"
        case_num = f"CONF-{academic_year[:4]}-{uuid.uuid4().hex[:6].upper()}"

        conflict = AdmissionConflict(
            case_number=case_num,
            student_id=student_id,
            record_a_id=existing_active.id,
            record_b_id=new_record_id,
            conflict_type=conflict_type,
            status="OPEN",
            resolution_notes=None
        )
        db.add(conflict)
        db.commit()
        db.refresh(conflict)

        # Log to tamper-evident audit ledger
        append_audit_event(
            db=db,
            action="CONFLICT_DETECTED",
            entity_type="AdmissionConflict",
            entity_id=str(conflict.id),
            actor_role="SYSTEM_RECONCILER",
            metadata_json={
                "case_number": case_num,
                "conflict_type": conflict_type,
                "record_a_id": existing_active.id,
                "record_a_inst": existing_active.institution_id,
                "record_b_id": new_record_id,
                "record_b_inst": institution_id,
                "academic_year": academic_year
            },
            correlation_id=correlation_id
        )

        return conflict

    @staticmethod
    def resolve_conflict(
        db: Session,
        conflict_id: int,
        resolution_status: str,  # "RESOLVED_VALID", "RESOLVED_CANCELLED", "ESCALATED"
        winning_record_id: Optional[int],
        resolution_notes: str,
        user_id: int,
        user_email: str,
        user_role: str
    ) -> Dict[str, Any]:
        conflict = db.query(AdmissionConflict).filter(AdmissionConflict.id == conflict_id).first()
        if not conflict:
            raise ValueError("Conflict case not found.")

        conflict.status = resolution_status
        conflict.resolution_notes = resolution_notes
        conflict.resolved_by_user_id = user_id
        conflict.resolved_at = datetime.utcnow()

        if resolution_status == "RESOLVED_VALID" and winning_record_id:
            # Confirm winning record, mark losing record as CANCELLED
            if conflict.record_a_id == winning_record_id:
                winner = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_a_id).first()
                loser = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_b_id).first()
            else:
                winner = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_b_id).first()
                loser = db.query(AdmissionRecord).filter(AdmissionRecord.id == conflict.record_a_id).first()

            if winner:
                winner.status = "ACTIVE"
            if loser:
                loser.status = "CANCELLED"
                loser.notes = f"Cancelled via conflict resolution case {conflict.case_number}. Adjudicated to record #{winner.id if winner else 'N/A'}."

        db.commit()
        db.refresh(conflict)

        append_audit_event(
            db=db,
            action="CONFLICT_RESOLVED",
            entity_type="AdmissionConflict",
            entity_id=str(conflict.id),
            actor_id=user_id,
            actor_email=user_email,
            actor_role=user_role,
            metadata_json={
                "case_number": conflict.case_number,
                "resolution_status": resolution_status,
                "winning_record_id": winning_record_id,
                "notes": resolution_notes
            }
        )

        return {
            "case_number": conflict.case_number,
            "status": conflict.status,
            "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None
        }
