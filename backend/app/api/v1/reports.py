import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AdmissionRecord, StudentIdentity, Institution, Programme, InstitutionUser
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports & Exports"])

@router.get("/admissions.csv")
def export_admissions_csv(
    academic_year: str = "2026-27",
    institution_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: InstitutionUser = Depends(get_current_user)
):
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
        "Record_ID", "AICTE_ID", "Institution_Name", "Programme_Code", "Academic_Year",
        "Enrollment_No", "Student_Name", "Masked_APAAR", "Category", "Quota", "Status", "Admission_Date"
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.institution.aicte_id,
            r.institution.name,
            r.programme.programme_code,
            r.academic_year,
            r.enrollment_no,
            r.student.full_name,
            r.student.apaar_masked,
            r.category,
            r.admission_quota,
            r.status,
            r.admission_date.isoformat()
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pramaan_admissions_{academic_year}.csv"}
    )
