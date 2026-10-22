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
        Calculates intake utilization against versioned ApprovalSnapshot.
        Distinguishes general intake from supernumerary quotas (e.g. TFW, EWS).
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
                "incoming_count": incoming_count,
                "projected_total": incoming_count,
                "overage": incoming_count,
                "supernumerary_quota": {},
                "policy_version": "NO_APPROVAL_FOUND",
                "letter_ref": "NONE",
                "explanation": f"No active approval snapshot registered for {prog_code} in academic year {academic_year}."
            }

        # Count active admissions (general intake)
        active_records = db.query(AdmissionRecord).filter(
            AdmissionRecord.institution_id == institution_id,
            AdmissionRecord.programme_id == programme_id,
            AdmissionRecord.academic_year == academic_year,
            AdmissionRecord.status.in_(["ACTIVE", "UNDER_REVIEW"])
        ).all()

        current_active = len(active_records)
        projected_total = current_active + incoming_count
        approved_intake = snapshot.approved_intake
        overage = max(0, projected_total - approved_intake)
        is_compliant = (projected_total <= approved_intake)

        # Category and quota breakdown
        cat_counts: Dict[str, int] = {}
        quota_counts: Dict[str, int] = {}
        for r in active_records:
            cat_counts[r.category] = cat_counts.get(r.category, 0) + 1
            quota_counts[r.admission_quota] = quota_counts.get(r.admission_quota, 0) + 1

        explanation = (
            f"Approved intake: {approved_intake}. Current enrolled: {current_active}. "
            f"Incoming proposed: {incoming_count}. Projected: {projected_total}/{approved_intake} "
            f"({round((projected_total / approved_intake) * 100, 1)}% utilization)."
        )
        if overage > 0:
            explanation += f" WARNING: Proposed intake exceeds sanctioned capacity by {overage} seats."

        return {
            "has_approval": True,
            "is_compliant": is_compliant,
            "programme_id": programme_id,
            "programme_code": prog_code,
            "programme_name": prog_name,
            "academic_year": academic_year,
            "approved_intake": approved_intake,
            "current_active": current_active,
            "incoming_count": incoming_count,
            "projected_total": projected_total,
            "overage": overage,
            "utilization_pct": round((projected_total / approved_intake) * 100, 1) if approved_intake > 0 else 0,
            "supernumerary_quota": snapshot.supernumerary_quota or {},
            "active_categories": cat_counts,
            "active_quotas": quota_counts,
            "policy_version": snapshot.policy_version,
            "letter_ref": snapshot.approval_letter_ref,
            "explanation": explanation
        }
