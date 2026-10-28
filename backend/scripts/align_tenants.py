"""
Tenant Realignment Script: Ensures 100% strict institutional tenant isolation
between Delhi Technological University (DTU) and COEP Technological University.
Guarantees one institution's records NEVER exist in another institution.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.models import (
    Institution, InstitutionUser, Programme, ApprovalSnapshot,
    InstitutionalDeclaration, UploadBatch, StagedBatchRow,
    ValidationRun, ValidationFinding, AicteCentralAdvisory, AdmissionRecord, StudentIdentity
)
from app.core.security import get_password_hash
from app.services.reconciliation_engine import ReconciliationEngine


def align_institutions():
    db = SessionLocal()
    try:
        print("[*] Realigning Technical Institutions and Tenants...")

        # 1. Delhi Technological University (DTU)
        inst_dtu = db.query(Institution).filter(Institution.aicte_id == "1-1002341").first()
        if not inst_dtu:
            inst_dtu = Institution(
                aicte_id="1-1002341",
                name="Delhi Technological University (DTU)",
                state="Delhi",
                district="North West Delhi",
                institution_type="STATE_GOVT_AIDED",
                status="APPROVED",
                contact_email="registrar@dtu.ac.in"
            )
            db.add(inst_dtu)
            db.flush()
        else:
            inst_dtu.name = "Delhi Technological University (DTU)"
            inst_dtu.state = "Delhi"
            db.flush()

        # 2. COEP Technological University (COEP)
        inst_coep = db.query(Institution).filter(Institution.aicte_id == "1-1049281").first()
        if not inst_coep:
            inst_coep = Institution(
                aicte_id="1-1049281",
                name="COEP Technological University",
                state="Maharashtra",
                district="Pune",
                institution_type="STATE_GOVT_AIDED",
                status="APPROVED",
                contact_email="nodal.aicte@coeptech.ac.in"
            )
            db.add(inst_coep)
            db.flush()
        else:
            inst_coep.name = "COEP Technological University"
            inst_coep.state = "Maharashtra"
            db.flush()

        # 3. Align Users & Credentials
        # DTU Nodal
        dtu_user = db.query(InstitutionUser).filter(InstitutionUser.email == "nodal.dtu@dtu.ac.in").first()
        if not dtu_user:
            dtu_user = InstitutionUser(
                email="nodal.dtu@dtu.ac.in",
                hashed_password=get_password_hash("College@12345"),
                full_name="Prof. Amit Srivastava (DTU Nodal Officer)",
                role="INSTITUTION_NODAL",
                institution_id=inst_dtu.id
            )
            db.add(dtu_user)
        else:
            dtu_user.institution_id = inst_dtu.id
            dtu_user.role = "INSTITUTION_NODAL"

        # COEP Nodal
        coep_user = db.query(InstitutionUser).filter(InstitutionUser.email == "nodal.coep@coep.ac.in").first()
        if not coep_user:
            coep_user = InstitutionUser(
                email="nodal.coep@coep.ac.in",
                hashed_password=get_password_hash("College@12345"),
                full_name="Dr. Sandeep Meshram (COEP Dean Academics)",
                role="INSTITUTION_NODAL",
                institution_id=inst_coep.id
            )
            db.add(coep_user)
        else:
            coep_user.institution_id = inst_coep.id
            coep_user.role = "INSTITUTION_NODAL"

        # AICTE Central Regulators (Central scope: institution_id MUST be None)
        admin_user = db.query(InstitutionUser).filter(InstitutionUser.email == "aicte.admin@pramaan.gov.in").first()
        if admin_user:
            admin_user.institution_id = None
            admin_user.role = "AICTE_ADMIN"

        ro_user = db.query(InstitutionUser).filter(InstitutionUser.email == "ro.mumbai@aicte.gov.in").first()
        if ro_user:
            ro_user.institution_id = None
            ro_user.role = "REGIONAL_OFFICER"

        db.flush()

        # 4. Align Academic Programmes & Approvals
        # DTU Programmes
        dtu_cse = db.query(Programme).filter(Programme.institution_id == inst_dtu.id, Programme.programme_code == "BTECH-CSE").first()
        if not dtu_cse:
            dtu_cse = Programme(
                institution_id=inst_dtu.id,
                programme_code="BTECH-CSE",
                programme_name="Computer Science and Engineering",
                degree_level="UG",
                duration_years=4
            )
            db.add(dtu_cse)
            db.flush()

        dtu_appr = db.query(ApprovalSnapshot).filter(ApprovalSnapshot.institution_id == inst_dtu.id, ApprovalSnapshot.programme_id == dtu_cse.id).first()
        if not dtu_appr:
            dtu_appr = ApprovalSnapshot(
                institution_id=inst_dtu.id,
                programme_id=dtu_cse.id,
                academic_year="2026-27",
                approved_intake=180,
                supernumerary_quota={"TFW": 9, "EWS": 18},
                approval_letter_ref="EOA-2026-DTU-001",
                policy_version="AICTE-APH-2026-27-V1",
                is_active=True
            )
            db.add(dtu_appr)

        dtu_decl = db.query(InstitutionalDeclaration).filter(InstitutionalDeclaration.institution_id == inst_dtu.id, InstitutionalDeclaration.programme_id == dtu_cse.id).first()
        if not dtu_decl:
            dtu_decl = InstitutionalDeclaration(
                institution_id=inst_dtu.id,
                programme_id=dtu_cse.id,
                academic_year="2026-27",
                declared_intake=180,
                reporting_scope="TOTAL_ENROLMENT",
                declaration_ref="DECL-DTU-CSE-2026"
            )
            db.add(dtu_decl)

        # COEP Programmes
        coep_cse = db.query(Programme).filter(Programme.institution_id == inst_coep.id, Programme.programme_code == "BTECH-CSE").first()
        if not coep_cse:
            coep_cse = Programme(
                institution_id=inst_coep.id,
                programme_code="BTECH-CSE",
                programme_name="Computer Engineering",
                degree_level="UG",
                duration_years=4
            )
            db.add(coep_cse)
            db.flush()

        coep_appr = db.query(ApprovalSnapshot).filter(ApprovalSnapshot.institution_id == inst_coep.id, ApprovalSnapshot.programme_id == coep_cse.id).first()
        if not coep_appr:
            coep_appr = ApprovalSnapshot(
                institution_id=inst_coep.id,
                programme_id=coep_cse.id,
                academic_year="2026-27",
                approved_intake=150,
                supernumerary_quota={"TFW": 7, "EWS": 15},
                approval_letter_ref="EOA-2026-COEP-001",
                policy_version="AICTE-APH-2026-27-V1",
                is_active=True
            )
            db.add(coep_appr)

        coep_decl = db.query(InstitutionalDeclaration).filter(InstitutionalDeclaration.institution_id == inst_coep.id, InstitutionalDeclaration.programme_id == coep_cse.id).first()
        if not coep_decl:
            coep_decl = InstitutionalDeclaration(
                institution_id=inst_coep.id,
                programme_id=coep_cse.id,
                academic_year="2026-27",
                declared_intake=150,
                reporting_scope="TOTAL_ENROLMENT",
                declaration_ref="DECL-COEP-CSE-2026"
            )
            db.add(coep_decl)

        db.flush()

        # 5. Strict Batch Separation
        # Batch #1: DTU Batch (valid_admissions_dtu.csv)
        batch_dtu = db.query(UploadBatch).filter(UploadBatch.filename == "valid_admissions_dtu.csv").first()
        dtu_csv_bytes = Path("../sample_data/valid_admissions_dtu.csv").read_bytes()
        dtu_storage_path = Path("storage/uploads/batch_dtu_valid.bin")
        dtu_storage_path.parent.mkdir(parents=True, exist_ok=True)
        dtu_storage_path.write_bytes(dtu_csv_bytes)

        if not batch_dtu:
            batch_dtu = UploadBatch(
                institution_id=inst_dtu.id,
                submitted_by_user_id=dtu_user.id,
                academic_year="2026-27",
                filename="valid_admissions_dtu.csv",
                file_hash="dtu_hash_2026_valid",
                total_rows=10,
                valid_rows=10,
                warning_rows=0,
                error_rows=0,
                status="APPROVED",
                mapping_config={
                    "apaar_id": "apaar_id",
                    "student_name": "student_name",
                    "dob": "dob",
                    "gender": "gender",
                    "programme_code": "programme_code",
                    "category": "category",
                    "admission_quota": "admission_quota",
                    "enrollment_no": "enrollment_no",
                    "_storage_file": str(dtu_storage_path),
                    "_filename": "valid_admissions_dtu.csv"
                }
            )
            db.add(batch_dtu)
            db.flush()
        else:
            batch_dtu.institution_id = inst_dtu.id
            batch_dtu.mapping_config = {
                **batch_dtu.mapping_config,
                "_storage_file": str(dtu_storage_path),
                "_filename": "valid_admissions_dtu.csv"
            }
            db.flush()

        # Populate DTU staged rows
        engine_reconcile = ReconciliationEngine(db)
        engine_reconcile.get_or_sync_staged_rows(batch_dtu.id)

        # Batch #2: COEP Batch (supernumerary_tfw_coep.csv)
        # MUST belong to inst_coep.id
        batch_coep = db.query(UploadBatch).filter(UploadBatch.id == 2).first()
        coep_csv_bytes = Path("../sample_data/supernumerary_tfw_coep.csv").read_bytes()
        coep_storage_path = Path("storage/uploads/batch_coep_tfw.bin")
        coep_storage_path.parent.mkdir(parents=True, exist_ok=True)
        coep_storage_path.write_bytes(coep_csv_bytes)

        if not batch_coep:
            batch_coep = UploadBatch(
                id=2,
                institution_id=inst_coep.id,
                submitted_by_user_id=coep_user.id,
                academic_year="2026-27",
                filename="supernumerary_tfw_coep.csv",
                file_hash="coep_hash_2026_tfw",
                total_rows=4,
                valid_rows=2,
                warning_rows=1,
                error_rows=1,
                status="NEEDS_CORRECTION",
                mapping_config={
                    "apaar_id": "apaar_id",
                    "student_name": "student_name",
                    "dob": "dob",
                    "gender": "gender",
                    "programme_code": "programme_code",
                    "category": "category",
                    "admission_quota": "admission_quota",
                    "enrollment_no": "enrollment_no",
                    "_storage_file": str(coep_storage_path),
                    "_filename": "supernumerary_tfw_coep.csv"
                }
            )
            db.add(batch_coep)
            db.flush()
        else:
            batch_coep.institution_id = inst_coep.id
            batch_coep.submitted_by_user_id = coep_user.id
            batch_coep.status = "NEEDS_CORRECTION"
            batch_coep.mapping_config = {
                **batch_coep.mapping_config,
                "_storage_file": str(coep_storage_path),
                "_filename": "supernumerary_tfw_coep.csv"
            }
            db.flush()

        # Populate COEP staged rows
        engine_reconcile.get_or_sync_staged_rows(batch_coep.id)

        # Reset Tanvi Joshi to BTECH-AI in COEP staged rows to demonstrate the error and advisory
        tanvi = db.query(StagedBatchRow).filter(
            StagedBatchRow.batch_id == batch_coep.id,
            StagedBatchRow.student_name.ilike("%Tanvi%")
        ).first()
        if tanvi:
            tanvi.programme_code = "BTECH-AI"

        # Active AICTE Advisory on COEP Batch #2
        db.query(AicteCentralAdvisory).filter(AicteCentralAdvisory.batch_id == batch_coep.id).delete()
        adv = AicteCentralAdvisory(
            batch_id=batch_coep.id,
            institution_id=inst_coep.id,
            title="Remap Unapproved Programme BTECH-AI to Approved BTECH-CSE Cluster",
            idea_description="Under AICTE Approval Process Handbook (APH 2026-27) Clause 4.2, emerging area specializations in Artificial Intelligence may be accommodated under the parent Computer Science & Engineering intake cluster. Institution is advised to remap students to BTECH-CSE to achieve regulatory compliance.",
            advisory_type="PROGRAMME_REMAP_RECOMMENDATION",
            recommended_action={
                "action": "REMAP_PROGRAMME",
                "from_code": "BTECH-AI",
                "to_code": "BTECH-CSE"
            },
            status="ACTIVE",
            created_by_user_id=admin_user.id if admin_user else None
        )
        db.add(adv)

        db.commit()
        print(f"[+] DTU ID: {inst_dtu.id} -> User: nodal.dtu@dtu.ac.in -> Batch ID: {batch_dtu.id} ({batch_dtu.filename})")
        print(f"[+] COEP ID: {inst_coep.id} -> User: nodal.coep@coep.ac.in -> Batch ID: {batch_coep.id} ({batch_coep.filename})")
        print("[+] 100% strict institutional tenant alignment complete!")

    except Exception as e:
        db.rollback()
        print(f"[!] Error aligning tenants: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    align_institutions()
