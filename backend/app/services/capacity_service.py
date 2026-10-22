from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import ApprovalSnapshot, AdmissionRecord, Programme

class ApprovalCapacityService:
    @staticmethod
    def evaluate_programme_capacity(
        db: Session,
        institution_id: int,
        programme_id: int,
        academic_year: str,
        incoming_count: int = 0,
        incoming_quotas: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Calculates intake utilization against versioned ApprovalSnapshot for SIH-R02.
        Distinguishes sanctioned approved intake, actual general enrolment,
        supernumerary seats (TFW, EWS supernumerary), NRI, OCI, and Foreign National (FN) statuses.
        """
        snapshot = db.query(ApprovalSnapshot).filter(
            ApprovalSnapshot.institution_id == institution_id,
            ApprovalSnapshot.programme_id == programme_id,
            ApprovalSnapshot.academic_year == academic_year,
            ApprovalSnapshot.is_active == True
        ).first()

        programme = db.query(Programme).filter(Programme.id == programme_id).first()
        prog_name = programme.programme_name if programme else "Unknown Programme"
        prog_code = programme.programme_code if programme else "N/A"

        if not snapshot:
            return {
                "has_approval": False,
                "is_compliant": False,
                "programme_code": prog_code,
                "programme_name": prog_name,
                "academic_year": academic_year,
                "approved_intake": 0,
                "current_active": 0,
                "general_enrolment": 0,
                "supernumerary_enrolment": 0,
                "nri_count": 0,
                "oci_count": 0,
                "foreign_national_count": 0,
                "incoming_count": incoming_count,
                "projected_total": incoming_count,
                "overage": incoming_count,
                "supernumerary_quota": {},
                "policy_version": "NO_APPROVAL_FOUND",
                "letter_ref": "NONE",
                "explanation": f"No active approval snapshot registered for {prog_code} in academic year {academic_year}."
            }

        # Query all active or under review admissions for this programme & academic year
        active_records = db.query(AdmissionRecord).filter(
            AdmissionRecord.institution_id == institution_id,
            AdmissionRecord.programme_id == programme_id,
            AdmissionRecord.academic_year == academic_year,
            AdmissionRecord.status.in_(["ACTIVE", "UNDER_REVIEW"])
        ).all()

        current_active = len(active_records)

        # Distinguish general enrolment vs supernumerary & international statuses
        general_enrolled = 0
        supernumerary_enrolled = 0
        nri_count = 0
        oci_count = 0
        foreign_national_count = 0
        supernumerary_breakdown: Dict[str, int] = {}
        reservation_breakdown: Dict[str, int] = {}

        for r in active_records:
            # Check supernumerary flag or quota
            is_sup = getattr(r, "is_supernumerary", False) or "TFW" in (r.admission_quota or "").upper()
            if is_sup:
                supernumerary_enrolled += 1
                q_name = r.admission_quota or "SUPERNUMERARY_OTHER"
                supernumerary_breakdown[q_name] = supernumerary_breakdown.get(q_name, 0) + 1
            else:
                general_enrolled += 1

            # International / Nationality type
            nat_type = getattr(r, "nationality_type", "DOMESTIC") or "DOMESTIC"
            if nat_type == "NRI" or "NRI" in (r.admission_quota or "").upper():
                nri_count += 1
            elif nat_type == "OCI":
                oci_count += 1
            elif nat_type == "FOREIGN_NATIONAL" or "PIO" in (r.admission_quota or "").upper():
                foreign_national_count += 1

            # Reservation categories
            cat = r.category or "OPEN"
            reservation_breakdown[cat] = reservation_breakdown.get(cat, 0) + 1

        approved_intake = snapshot.approved_intake
        # Compliance evaluation: General enrolment cannot exceed approved intake.
        # Supernumerary seats are over and above the sanctioned intake according to AICTE Approval Process Handbook.
        projected_general = general_enrolled + incoming_count
        projected_total = current_active + incoming_count
        overage = max(0, projected_general - approved_intake)
        is_compliant = (projected_general <= approved_intake)

        utilization_pct = round((projected_general / approved_intake) * 100, 1) if approved_intake > 0 else 0

        explanation = (
            f"Sanctioned intake: {approved_intake}. General enrolled: {general_enrolled}. "
            f"Supernumerary: {supernumerary_enrolled} (TFW/EWS/Quotas). "
            f"International: NRI={nri_count}, OCI={oci_count}, FN={foreign_national_count}. "
            f"Projected general utilization: {projected_general}/{approved_intake} ({utilization_pct}%)."
        )
        if overage > 0:
            explanation += f" WARNING: Proposed general intake exceeds sanctioned capacity by {overage} seats."

        return {
            "has_approval": True,
            "is_compliant": is_compliant,
            "programme_id": programme_id,
            "programme_code": prog_code,
            "programme_name": prog_name,
            "academic_year": academic_year,
            "approved_intake": approved_intake,
            "current_active": current_active,
            "general_enrolment": general_enrolled,
            "supernumerary_enrolment": supernumerary_enrolled,
            "nri_count": nri_count,
            "oci_count": oci_count,
            "foreign_national_count": foreign_national_count,
            "incoming_count": incoming_count,
            "projected_total": projected_total,
            "overage": overage,
            "utilization_pct": utilization_pct,
            "supernumerary_quota": snapshot.supernumerary_quota or {},
            "supernumerary_breakdown": supernumerary_breakdown,
            "reservation_breakdown": reservation_breakdown,
            "policy_version": snapshot.policy_version,
            "letter_ref": snapshot.approval_letter_ref,
            "explanation": explanation
        }
