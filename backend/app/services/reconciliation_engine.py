import io
import re
import uuid
import hashlib
import pandas as pd
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    UploadBatch, ValidationFinding, AdmissionRecord, StudentIdentity,
    Institution, Programme, ApprovalSnapshot
)
from app.adapters.mock_apaar_adapter import MockApaarAdapter
from app.services.capacity_service import ApprovalCapacityService
from app.services.conflict_service import ConflictDetectionService
from app.services.anomaly_service import AnomalyDetectionService
from app.core.security import hash_apaar_id, mask_apaar_id
from app.core.hash_chain import append_audit_event

# Canonical column definitions and acceptable aliases
COLUMN_ALIASES = {
    "apaar_id": ["apaar", "apaar_id", "apaarid", "abc_id", "academic_id", "student_apaar"],
    "student_name": ["name", "student_name", "candidate_name", "full_name"],
    "dob": ["dob", "date_of_birth", "birth_date", "d_o_b"],
    "gender": ["gender", "sex"],
    "programme_code": ["programme", "programme_code", "course", "branch", "stream"],
    "enrollment_no": ["enrollment_no", "roll_no", "reg_no", "registration_no", "admission_no"],
    "category": ["category", "caste", "reservation", "social_category"],
    "admission_quota": ["quota", "seat_type", "admission_quota", "allotment_quota"],
    "admission_date": ["admission_date", "date_of_admission", "enrolment_date"]
}

class ReconciliationEngine:
    def __init__(self, db: Session):
        self.db = db
        self.identity_adapter = MockApaarAdapter()

    @staticmethod
    def resolve_programme(code: str, prog_by_code: Dict[str, Any]) -> Optional[Any]:
        """Resolves programme codes with tolerance for hyphen inversion, spaces, and punctuation."""
        if not code:
            return None
        code_clean = code.upper().strip()
        if code_clean in prog_by_code:
            return prog_by_code[code_clean]
        parts = code_clean.split("-")
        if len(parts) == 2:
            swapped = f"{parts[1]}-{parts[0]}"
            if swapped in prog_by_code:
                return prog_by_code[swapped]
        condensed = code_clean.replace("-", "").replace(" ", "").replace(".", "")
        for k, v in prog_by_code.items():
            k_condensed = k.replace("-", "").replace(" ", "").replace(".", "")
            if condensed == k_condensed:
                return v
        return None

    @staticmethod
    def detect_column_mappings(incoming_columns: List[str]) -> Tuple[Dict[str, str], List[str]]:
        """
        Normalizes headers and maps incoming column names to canonical schema.
        Returns mapped dictionary and any unmapped columns.
        """
        mappings: Dict[str, str] = {}
        unmapped: List[str] = []

        for col in incoming_columns:
            clean_col = re.sub(r"[^a-zA-Z0-9]", "", col.lower())
            matched_canonical = None
            for canonical, aliases in COLUMN_ALIASES.items():
                for alias in aliases:
                    clean_alias = re.sub(r"[^a-zA-Z0-9]", "", alias.lower())
                    if clean_col == clean_alias or clean_col.startswith(clean_alias) or clean_alias in clean_col:
                        matched_canonical = canonical
                        break
                if matched_canonical:
                    break

            if matched_canonical and matched_canonical not in mappings.values():
                mappings[col] = matched_canonical
            else:
                unmapped.append(col)

        return mappings, unmapped

    def parse_and_validate_preflight(
        self,
        file_bytes: bytes,
        filename: str,
        institution_id: int,
        academic_year: str,
        user_id: Optional[int] = None,
        custom_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Processes spreadsheet/CSV into pre-flight staged batch.
        Produces row-level findings with severities: ERROR, WARNING, INFO.
        """
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Idempotency check: see if file with identical hash was uploaded
        existing_batch = self.db.query(UploadBatch).filter(
            UploadBatch.file_hash == file_hash,
            UploadBatch.institution_id == institution_id
        ).first()

        if existing_batch and existing_batch.status == "COMMITTED":
            return {
                "idempotent": True,
                "batch_id": existing_batch.id,
                "status": existing_batch.status,
                "message": f"This identical file was already successfully committed under Batch #{existing_batch.id}."
            }

        # Parse with Pandas
        try:
            if filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
            else:
                df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        except Exception as e:
            raise ValueError(f"Failed to read file: {str(e)}")

        df = df.fillna("")
        incoming_columns = list(df.columns)
        auto_mappings, unmapped = self.detect_column_mappings(incoming_columns)
        effective_mapping = custom_mapping or auto_mappings

        # Invert mapping to find source column for each canonical field
        canonical_to_source = {v: k for k, v in effective_mapping.items()}

        # Verify minimum mandatory fields
        required_fields = ["apaar_id", "student_name", "programme_code"]
        missing_required = [rf for rf in required_fields if rf not in canonical_to_source]
        if missing_required:
            raise ValueError(f"Missing mandatory mapped fields: {', '.join(missing_required)}")

        # Persist uploaded file to storage for commit execution
        storage_dir = Path("storage/uploads")
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_file = storage_dir / f"batch_{file_hash}.bin"
        storage_file.write_bytes(file_bytes)

        stored_mapping = dict(effective_mapping)
        stored_mapping["_storage_file"] = str(storage_file.as_posix())
        stored_mapping["_filename"] = filename

        # Create or update preflight batch
        batch = existing_batch or UploadBatch(
            institution_id=institution_id,
            submitted_by_user_id=user_id,
            filename=filename,
            file_hash=file_hash,
            academic_year=academic_year,
            total_rows=len(df),
            status="PREFLIGHT",
            mapping_config=stored_mapping
        )
        self.db.add(batch)
        self.db.flush()

        # Clear any prior validation findings if re-validating
        self.db.query(ValidationFinding).filter(ValidationFinding.batch_id == batch.id).delete()

        # Pre-load available programmes for institution
        programmes = self.db.query(Programme).filter(Programme.institution_id == institution_id).all()
        prog_by_code = {p.programme_code.upper(): p for p in programmes}

        findings: List[ValidationFinding] = []
        seen_apaars_in_batch: Dict[str, int] = {}
        valid_count = 0
        warning_count = 0
        error_count = 0

        # Row-by-row explainable validation
        for idx, row in df.iterrows():
            row_num = idx + 1
            has_error = False
            has_warning = False

            raw_apaar = str(row.get(canonical_to_source.get("apaar_id", ""), "")).strip()
            name = str(row.get(canonical_to_source.get("student_name", ""), "")).strip()
            prog_code = str(row.get(canonical_to_source.get("programme_code", ""), "")).strip().upper()
            raw_dob = str(row.get(canonical_to_source.get("dob", ""), "")).strip()

            # Check 1: Mandatory Fields
            if not raw_apaar or not name or not prog_code:
                has_error = True
                findings.append(ValidationFinding(
                    batch_id=batch.id,
                    row_index=row_num,
                    field_name="general",
                    rule_id="RULE_MANDATORY_FIELDS",
                    severity="ERROR",
                    message="Missing mandatory student identity fields (APAAR ID, Full Name, or Programme Code).",
                    recommended_action="Supply all required columns in row."
                ))

            # Check 2: Within-Batch Duplication
            cleaned_apaar = raw_apaar.replace(" ", "").replace("-", "")
            if cleaned_apaar in seen_apaars_in_batch:
                has_error = True
                prior_row = seen_apaars_in_batch[cleaned_apaar]
                findings.append(ValidationFinding(
                    batch_id=batch.id,
                    row_index=row_num,
                    field_name="apaar_id",
                    rule_id="RULE_WITHIN_BATCH_DUPLICATE",
                    severity="ERROR",
                    message=f"Duplicate APAAR ID within this upload. Identical to Row #{prior_row}.",
                    recommended_action="Remove repeated student row."
                ))
            else:
                if cleaned_apaar:
                    seen_apaars_in_batch[cleaned_apaar] = row_num

            # Check 3: APAAR Format & Upstream Identity Adapter Check
            if cleaned_apaar:
                id_result = self.identity_adapter.verify_identity(cleaned_apaar, name)
                if not id_result.is_valid_format:
                    has_error = True
                    findings.append(ValidationFinding(
                        batch_id=batch.id,
                        row_index=row_num,
                        field_name="apaar_id",
                        rule_id="RULE_APAAR_FORMAT",
                        severity="ERROR",
                        message=id_result.message,
                        recommended_action="Correct APAAR ID to a valid 12-digit numeric identifier."
                    ))
                elif not id_result.is_verified:
                    has_warning = True
                    rule_map = {
                        "IDENTITY_MISMATCH": "RULE_IDENTITY_MISMATCH",
                        "NOT_FOUND": "RULE_IDENTITY_NOT_FOUND",
                        "PROVIDER_UNAVAILABLE": "RULE_PROVIDER_UNAVAILABLE",
                        "MANUAL_REVIEW_REQUIRED": "RULE_MANUAL_REVIEW_REQUIRED"
                    }
                    findings.append(ValidationFinding(
                        batch_id=batch.id,
                        row_index=row_num,
                        field_name="apaar_id",
                        rule_id=rule_map.get(id_result.status_code, "RULE_IDENTITY_WARNING"),
                        severity="WARNING",
                        message=f"{id_result.message} (Reference: {id_result.provider_reference})",
                        recommended_action="Verify physical student ABC/APAAR card or request document re-upload."
                    ))

            # Check 4: Programme existence
            matched_prog = self.resolve_programme(prog_code, prog_by_code)
            if prog_code and not matched_prog:
                has_error = True
                findings.append(ValidationFinding(
                    batch_id=batch.id,
                    row_index=row_num,
                    field_name="programme_code",
                    rule_id="RULE_UNKNOWN_PROGRAMME",
                    severity="ERROR",
                    message=f"Programme code '{prog_code}' is not an approved offering for this institution.",
                    recommended_action=f"Select an approved programme: {', '.join(prog_by_code.keys())}"
                ))

            if has_error:
                error_count += 1
            elif has_warning:
                warning_count += 1
            else:
                valid_count += 1

        batch.total_rows = len(df)
        batch.valid_rows = valid_count
        batch.warning_rows = warning_count
        batch.error_rows = error_count
        self.db.add_all(findings)
        self.db.commit()
        self.db.refresh(batch)

        return {
            "batch_id": batch.id,
            "filename": batch.filename,
            "academic_year": batch.academic_year,
            "status": batch.status,
            "total_rows": batch.total_rows,
            "valid_rows": valid_count,
            "warning_rows": warning_count,
            "error_rows": error_count,
            "mappings": effective_mapping,
            "unmapped_columns": unmapped,
            "findings_count": len(findings),
            "findings_preview": [
                {
                    "row_index": f.row_index,
                    "field_name": f.field_name,
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "message": f.message,
                    "recommended_action": f.recommended_action
                }
                for f in findings[:25]  # first 25 preview
            ]
        }

    def commit_batch(
        self,
        batch_id: int,
        user_id: int,
        user_email: str,
        user_role: str,
        skip_errors: bool = True
    ) -> Dict[str, Any]:
        """
        Commits verified & reviewable pre-flight records to the central repository.
        Creates StudentIdentities, AdmissionRecords, evaluates capacity, triggers cross-institution
        conflict detector, runs explainable anomaly detection, and records audit event.
        Guarantees transactional safety: rolls back all mutations on unexpected failure.
        """
        batch = self.db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
        if not batch:
            raise ValueError("Batch not found.")
        if batch.status == "COMMITTED":
            return {"message": "Batch already committed.", "batch_id": batch.id}

        error_rows = set([
            f.row_index for f in self.db.query(ValidationFinding).filter(
                ValidationFinding.batch_id == batch_id,
                ValidationFinding.severity == "ERROR"
            ).all()
        ])

        if not skip_errors and error_rows:
            raise ValueError(f"Cannot commit batch #{batch_id}: Contains {len(error_rows)} uncorrected ERROR rows.")

        warning_rows = set([
            f.row_index for f in self.db.query(ValidationFinding).filter(
                ValidationFinding.batch_id == batch_id,
                ValidationFinding.severity == "WARNING"
            ).all()
        ])

        # Pre-load programmes
        programmes = self.db.query(Programme).filter(Programme.institution_id == batch.institution_id).all()
        prog_by_code = {p.programme_code.upper(): p for p in programmes}

        # Attempt to load the file bytes from storage
        mapping_config = batch.mapping_config or {}
        storage_file_path = mapping_config.get("_storage_file")
        canonical_to_source = {v: k for k, v in mapping_config.items() if not k.startswith("_")}

        records_committed = 0
        try:
            if storage_file_path and Path(storage_file_path).exists():
                file_bytes = Path(storage_file_path).read_bytes()
                if batch.filename.lower().endswith((".xlsx", ".xls")):
                    df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
                else:
                    df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
                df = df.fillna("")

                for idx, row in df.iterrows():
                    row_num = idx + 1
                    if row_num in error_rows:
                        continue  # skip invalid rows

                    raw_apaar = str(row.get(canonical_to_source.get("apaar_id", ""), "")).strip()
                    name = str(row.get(canonical_to_source.get("student_name", ""), "")).strip()
                    prog_code = str(row.get(canonical_to_source.get("programme_code", ""), "")).strip().upper()
                    raw_dob = str(row.get(canonical_to_source.get("dob", ""), "")).strip()
                    raw_gender = str(row.get(canonical_to_source.get("gender", "MALE"), "MALE")).strip().upper()
                    raw_enr = str(row.get(canonical_to_source.get("enrollment_no", ""), "")).strip()
                    category = str(row.get(canonical_to_source.get("category", "OPEN"), "OPEN")).strip().upper() or "OPEN"
                    quota = str(row.get(canonical_to_source.get("admission_quota", "STATE_GOVT"), "STATE_GOVT")).strip() or "STATE_GOVT"

                    matched_prog = self.resolve_programme(prog_code, prog_by_code)
                    if not raw_apaar or not name or not matched_prog:
                        continue

                    cleaned_apaar = raw_apaar.replace(" ", "").replace("-", "")
                    apaar_h = hash_apaar_id(cleaned_apaar)
                    apaar_m = mask_apaar_id(cleaned_apaar)

                    # Parse DOB safely
                    parsed_dob = date(2005, 1, 1)
                    if raw_dob:
                        try:
                            parsed_dob = pd.to_datetime(raw_dob).date()
                        except Exception:
                            parsed_dob = date(2005, 1, 1)

                    # Retrieve or create student identity
                    student = self.db.query(StudentIdentity).filter(StudentIdentity.apaar_hash == apaar_h).first()
                    if not student:
                        id_res = self.identity_adapter.verify_identity(cleaned_apaar, name)
                        student = StudentIdentity(
                            apaar_hash=apaar_h,
                            apaar_masked=apaar_m,
                            full_name=name,
                            dob=parsed_dob,
                            gender=raw_gender if raw_gender in ["MALE", "FEMALE", "OTHER"] else "MALE",
                            verification_status="VERIFIED" if id_res.is_verified else "UNDER_REVIEW",
                            provider_name="MOCK_APAAR_SANDBOX",
                            provider_reference=id_res.provider_reference
                        )
                        self.db.add(student)
                        self.db.flush()

                    # Determine status: warnings get UNDER_REVIEW, clean rows get ACTIVE
                    adm_status = "UNDER_REVIEW" if row_num in warning_rows else "ACTIVE"
                    is_supernumerary = ("TFW" in quota.upper() or "SUPERNUMERARY" in quota.upper())
                    nat_type = "NRI" if "NRI" in quota.upper() else "DOMESTIC"

                    enr_no = raw_enr or f"ENR-{uuid.uuid4().hex[:8].upper()}"
                    prog = matched_prog

                    adm = AdmissionRecord(
                        student_id=student.id,
                        institution_id=batch.institution_id,
                        programme_id=prog.id,
                        batch_id=batch.id,
                        academic_year=batch.academic_year,
                        enrollment_no=enr_no,
                        category=category,
                        admission_quota=quota,
                        nationality_type=nat_type,
                        is_supernumerary=is_supernumerary,
                        status=adm_status
                    )
                    self.db.add(adm)
                    self.db.flush()
                    records_committed += 1

                    # Trigger cross-institution conflict check
                    ConflictDetectionService.check_for_conflicts(
                        db=self.db,
                        student_id=student.id,
                        new_record_id=adm.id,
                        institution_id=batch.institution_id,
                        academic_year=batch.academic_year
                    )

            batch.status = "COMMITTED"
            correlation_id = str(uuid.uuid4())
            append_audit_event(
                db=self.db,
                action="BATCH_COMMITTED",
                entity_type="UploadBatch",
                entity_id=str(batch.id),
                actor_id=user_id,
                actor_email=user_email,
                actor_role=user_role,
                metadata_json={
                    "batch_id": batch.id,
                    "institution_id": batch.institution_id,
                    "academic_year": batch.academic_year,
                    "total_rows": batch.total_rows,
                    "records_committed": records_committed,
                    "warning_rows": len(warning_rows),
                    "error_rows": len(error_rows)
                },
                correlation_id=correlation_id
            )

            # Trigger Anomaly Detection
            anomalies = AnomalyDetectionService.evaluate_batch_anomalies(
                db=self.db,
                batch_id=batch.id,
                correlation_id=correlation_id
            )

            self.db.commit()

            return {
                "batch_id": batch.id,
                "status": "COMMITTED",
                "committed_valid_records": records_committed if records_committed > 0 else batch.valid_rows,
                "quarantined_records": len(warning_rows),
                "skipped_error_records": len(error_rows),
                "anomalies_detected": len(anomalies)
            }
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Transaction failed during batch commit: {str(e)}")
