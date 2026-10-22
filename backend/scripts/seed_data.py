import sys
import os
from datetime import datetime, date, timedelta
import hashlib

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash, hash_apaar_id, mask_apaar_id
from app.models import (
    Institution, InstitutionUser, Programme, ApprovalSnapshot,
    StudentIdentity, AdmissionRecord, UploadBatch, ValidationFinding,
    AdmissionConflict, AnomalyCase, VerificationReceipt, AuditEvent
)
from app.core.hash_chain import append_audit_event
from app.services.receipt_service import ReceiptService

def seed_database():
    print("[*] Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Institution).count() > 0:
            print("[!] Database already populated. Skipping duplicate seeding.")
            return

        print("[*] Seeding Technical Institutions...")
        inst_dtu = Institution(
            aicte_id="1-1002341",
            name="Delhi Technological University (DTU)",
            state="Delhi",
            district="North West Delhi",
            institution_type="STATE_GOVT_AIDED",
            status="APPROVED",
            contact_email="registrar@dtu.ac.in"
        )
        inst_coep = Institution(
            aicte_id="1-1049281",
            name="COEP Technological University",
            state="Maharashtra",
            district="Pune",
            institution_type="STATE_GOVT_AIDED",
            status="APPROVED",
            contact_email="nodal.aicte@coeptech.ac.in"
        )
        inst_rvce = Institution(
            aicte_id="1-1088492",
            name="R.V. College of Engineering (RVCE)",
            state="Karnataka",
            district="Bengaluru Urban",
            institution_type="PRIVATE_UNAIDED",
            status="APPROVED",
            contact_email="admissions@rvce.edu.in"
        )
        inst_ju = Institution(
            aicte_id="1-1055219",
            name="Jadavpur University Faculty of Engineering",
            state="West Bengal",
            district="Kolkata",
            institution_type="STATE_GOVT_AIDED",
            status="APPROVED",
            contact_email="dean.engg@jadavpuruniversity.in"
        )
        db.add_all([inst_dtu, inst_coep, inst_rvce, inst_ju])
        db.flush()

        print("[*] Seeding Seed Users...")
        admin_user = InstitutionUser(
            email="aicte.admin@pramaan.gov.in",
            hashed_password=get_password_hash("Admin@12345"),
            full_name="Dr. Sunita Deshmukh (Advisor-I, Bureau of Approval)",
            role="AICTE_ADMIN",
            institution_id=None
        )
        ro_mumbai = InstitutionUser(
            email="ro.mumbai@aicte.gov.in",
            hashed_password=get_password_hash("Officer@12345"),
            full_name="Rajesh Verma (Regional Officer - WRO)",
            role="REGIONAL_OFFICER",
            institution_id=None
        )
        dtu_nodal = InstitutionUser(
            email="nodal.dtu@dtu.ac.in",
            hashed_password=get_password_hash("College@12345"),
            full_name="Prof. Amit Srivastava (Nodal Officer)",
            role="INSTITUTION_NODAL",
            institution_id=inst_dtu.id
        )
        coep_nodal = InstitutionUser(
            email="nodal.coep@coep.ac.in",
            hashed_password=get_password_hash("College@12345"),
            full_name="Dr. Sandeep Meshram (Dean Academics)",
            role="INSTITUTION_NODAL",
            institution_id=inst_coep.id
        )
        verifier_user = InstitutionUser(
            email="verifier.corp@tcs.com",
            hashed_password=get_password_hash("Verify@12345"),
            full_name="Vikramaditya Sen (Talent Acquisition Lead)",
            role="VERIFIER",
            institution_id=None
        )
        db.add_all([admin_user, ro_mumbai, dtu_nodal, coep_nodal, verifier_user])
        db.flush()

        print("[*] Seeding Technical Programmes & Sanctioned Approval Snapshots (2026-27)...")
        programmes_data = [
            # DTU
            (inst_dtu.id, "BTECH-CSE", "Computer Science and Engineering", "UG", 4, 180, {"TFW": 9, "EWS": 18}),
            (inst_dtu.id, "BTECH-ECE", "Electronics and Communication Engg", "UG", 4, 120, {"TFW": 6, "EWS": 12}),
            (inst_dtu.id, "BTECH-MECH", "Mechanical Engineering", "UG", 4, 120, {"TFW": 6, "EWS": 12}),
            (inst_dtu.id, "MCA", "Master of Computer Applications", "PG", 2, 60, {"TFW": 3, "EWS": 6}),
            # COEP
            (inst_coep.id, "BTECH-CSE", "Computer Engineering", "UG", 4, 150, {"TFW": 7, "EWS": 15}),
            (inst_coep.id, "BTECH-AI", "Artificial Intelligence & Data Science", "UG", 4, 60, {"TFW": 3, "EWS": 6}),
            (inst_coep.id, "BTECH-ELEC", "Electrical Engineering", "UG", 4, 120, {"TFW": 6, "EWS": 12}),
            # RVCE
            (inst_rvce.id, "BTECH-CSE", "Computer Science and Engineering", "UG", 4, 180, {"TFW": 9, "EWS": 18}),
            (inst_rvce.id, "BTECH-IS", "Information Science and Engineering", "UG", 4, 60, {"TFW": 3, "EWS": 6}),
            # Jadavpur
            (inst_ju.id, "BTECH-CSE", "Computer Science and Engineering", "UG", 4, 100, {"TFW": 5, "EWS": 10}),
        ]

        saved_progs = {}
        for inst_id, p_code, p_name, deg, dur, intake, quotas in programmes_data:
            prog = Programme(
                institution_id=inst_id,
                programme_code=p_code,
                programme_name=p_name,
                degree_level=deg,
                duration_years=dur
            )
            db.add(prog)
            db.flush()
            saved_progs[(inst_id, p_code)] = prog

            approval = ApprovalSnapshot(
                institution_id=inst_id,
                programme_id=prog.id,
                academic_year="2026-27",
                approved_intake=intake,
                supernumerary_quota=quotas,
                approval_letter_ref=f"AICTE/EOA/2026-27/{inst_id}-{prog.id}",
                policy_version="AICTE-APH-2026-V1"
            )
            db.add(approval)
        db.flush()

        print("[*] Seeding Synthetic Student Identities & Admissions...")
        # 1. Standard verified DTU student batch
        names = [
            ("Aarav Mehta", "MALE", "2005-04-12", "OPEN", "STATE_GOVT"),
            ("Ananya Sharma", "FEMALE", "2005-08-23", "OBC_NCL", "STATE_GOVT"),
            ("Rohan Iyer", "MALE", "2004-11-05", "OPEN", "AICTE_TFW"),
            ("Ishita Banerjee", "FEMALE", "2005-01-30", "EWS", "STATE_GOVT"),
            ("Kavya Patel", "FEMALE", "2005-06-15", "OBC_NCL", "STATE_GOVT"),
            ("Siddharth Rao", "MALE", "2004-09-18", "SC", "STATE_GOVT"),
            ("Sneha Joshi", "FEMALE", "2005-03-22", "OPEN", "MANAGEMENT"),
            ("Aditya Verma", "MALE", "2004-12-08", "ST", "STATE_GOVT"),
            ("Pooja Nair", "FEMALE", "2005-07-11", "OPEN", "STATE_GOVT"),
            ("Varun Deshpande", "MALE", "2005-02-14", "OPEN", "STATE_GOVT"),
        ]

        dtu_cse = saved_progs[(inst_dtu.id, "BTECH-CSE")]
        coep_cse = saved_progs[(inst_coep.id, "BTECH-CSE")]
        rvce_cse = saved_progs[(inst_rvce.id, "BTECH-CSE")]

        sample_admissions = []
        for i, (name, gender, dob_str, cat, quota) in enumerate(names):
            apaar_num = f"40019283{1000 + i}"
            student = StudentIdentity(
                apaar_hash=hash_apaar_id(apaar_num),
                apaar_masked=mask_apaar_id(apaar_num),
                full_name=name,
                dob=datetime.strptime(dob_str, "%Y-%m-%d").date(),
                gender=gender,
                verification_status="VERIFIED",
                provider_reference=f"MOCK-ABC-VERIFIED-{1000 + i}"
            )
            db.add(student)
            db.flush()

            adm = AdmissionRecord(
                student_id=student.id,
                institution_id=inst_dtu.id,
                programme_id=dtu_cse.id,
                academic_year="2026-27",
                enrollment_no=f"DTU/2026/CSE/{101 + i}",
                category=cat,
                admission_quota=quota,
                admission_date=date(2026, 7, 15 + (i % 10)),
                status="ACTIVE"
            )
            db.add(adm)
            db.flush()
            sample_admissions.append(adm)

        # 2. Deliberate Cross-Institution Conflict Test Case:
        # Student "Kunal Singhania" (APAAR: 512398459012) actively enrolled in both COEP and DTU
        conflict_apaar = "512398459012"
        conflict_student = StudentIdentity(
            apaar_hash=hash_apaar_id(conflict_apaar),
            apaar_masked=mask_apaar_id(conflict_apaar),
            full_name="Kunal Singhania",
            dob=date(2005, 5, 20),
            gender="MALE",
            verification_status="VERIFIED",
            provider_reference="MOCK-ABC-VERIFIED-9012"
        )
        db.add(conflict_student)
        db.flush()

        adm_coep = AdmissionRecord(
            student_id=conflict_student.id,
            institution_id=inst_coep.id,
            programme_id=coep_cse.id,
            academic_year="2026-27",
            enrollment_no="COEP/2026/BTECH/304",
            category="OPEN",
            admission_quota="STATE_GOVT",
            admission_date=date(2026, 7, 10),
            status="ACTIVE",
            notes="CAP Round 1 Seat Allocation confirmed."
        )
        adm_dtu = AdmissionRecord(
            student_id=conflict_student.id,
            institution_id=inst_dtu.id,
            programme_id=dtu_cse.id,
            academic_year="2026-27",
            enrollment_no="DTU/2026/CSE/199",
            category="OPEN",
            admission_quota="MANAGEMENT",
            admission_date=date(2026, 7, 24),
            status="UNDER_REVIEW",
            notes="Flagged: Concurrent active enrolment detected at COEP Pune."
        )
        db.add_all([adm_coep, adm_dtu])
        db.flush()

        # Generate formal cross-institution conflict case
        conflict_case = AdmissionConflict(
            case_number="CONF-2026-0042",
            student_id=conflict_student.id,
            record_a_id=adm_coep.id,
            record_b_id=adm_dtu.id,
            conflict_type="CROSS_INSTITUTION_DUPLICATE",
            status="OPEN",
            resolution_notes="Awaiting student submission of official seat relinquishment certificate from COEP Pune."
        )
        db.add(conflict_case)
        db.flush()

        # 3. Legitimate Transfer Case (RVCE -> DTU with WITHDRAWN status)
        transfer_apaar = "619283748231"
        transfer_student = StudentIdentity(
            apaar_hash=hash_apaar_id(transfer_apaar),
            apaar_masked=mask_apaar_id(transfer_apaar),
            full_name="Tarun Krishnan",
            dob=date(2004, 10, 14),
            gender="MALE",
            verification_status="VERIFIED"
        )
        db.add(transfer_student)
        db.flush()

        past_adm = AdmissionRecord(
            student_id=transfer_student.id,
            institution_id=inst_rvce.id,
            programme_id=rvce_cse.id,
            academic_year="2025-26",
            enrollment_no="RVCE/2025/CS/088",
            category="OPEN",
            admission_quota="STATE_GOVT",
            status="TRANSFERRED",
            notes="Transferred with valid Migration Certificate #MC-2026-99."
        )
        new_adm = AdmissionRecord(
            student_id=transfer_student.id,
            institution_id=inst_dtu.id,
            programme_id=dtu_cse.id,
            academic_year="2026-27",
            enrollment_no="DTU/2026/CSE/205",
            category="OPEN",
            admission_quota="STATE_GOVT",
            status="ACTIVE"
        )
        db.add_all([past_adm, new_adm])
        db.flush()

        # 4. Anomaly Case: Intake Spike near deadline
        anomaly_case = AnomalyCase(
            case_number="ANOM-2026-0019",
            institution_id=inst_rvce.id,
            programme_id=rvce_cse.id,
            academic_year="2026-27",
            risk_score=78.5,
            anomaly_type="INTAKE_SPIKE",
            signals_json={
                "batch_records": 160,
                "total_approved_intake": 180,
                "intake_surge_ratio": 0.89,
                "days_before_portal_closure": 1
            },
            explanation=(
                "Batch upload concentrated 89% (160/180) of annual sanctioned Computer Science intake "
                "within 24 hours of portal closure deadline. Recommended for regional director spot verification."
            ),
            status="PENDING_REVIEW"
        )
        db.add(anomaly_case)
        db.flush()

        # 5. Pre-issue an Ed25519 Signed Verification Receipt for the first student
        receipt_info = ReceiptService.issue_receipt(
            db=db,
            admission_id=sample_admissions[0].id,
            expiry_days=30,
            claim_scope="ACTIVE_ENROLMENT_STATUS",
            actor_id=admin_user.id,
            actor_email=admin_user.email,
            actor_role="AICTE_ADMIN"
        )
        print(f"[*] Pre-generated Signed Receipt Token: {receipt_info['receipt_token']}")

        # 6. Build initial tamper-evident hash-chain audit ledger
        print("[*] Generating Tamper-Evident SHA-256 Hash Chain...")
        audit_events_data = [
            ("POLICY_SNAPSHOT_CREATED", "ApprovalSnapshot", "1", admin_user.email, "AICTE_ADMIN", {"year": "2026-27", "regulations": "AICTE-APH-2026-V1"}),
            ("BATCH_COMMITTED", "UploadBatch", "1", dtu_nodal.email, "INSTITUTION_NODAL", {"institution": "DTU", "records": 10, "status": "VERIFIED"}),
            ("CONFLICT_DETECTED", "AdmissionConflict", str(conflict_case.id), "system", "SYSTEM_RECONCILER", {"case": "CONF-2026-0042", "type": "CROSS_INSTITUTION_DUPLICATE"}),
            ("ANOMALY_FLAGGED", "AnomalyCase", str(anomaly_case.id), "anomaly_engine", "AICTE_INTELLIGENCE", {"case": "ANOM-2026-0019", "risk_score": 78.5}),
        ]
        for act, etype, eid, aemail, arole, meta in audit_events_data:
            append_audit_event(
                db=db,
                action=act,
                entity_type=etype,
                entity_id=eid,
                actor_email=aemail,
                actor_role=arole,
                metadata_json=meta
            )

        db.commit()
        print("[+] Database seeding completed successfully with 100% deterministic test fixtures!")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
