from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ValidationFindingResponse(BaseModel):
    id: int
    row_index: int
    field_name: str
    rule_id: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    recommended_action: Optional[str] = None

    class Config:
        from_attributes = True

class UploadBatchResponse(BaseModel):
    id: int
    institution_id: int
    filename: str
    academic_year: str
    total_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int
    status: str
    created_at: datetime
    mapping_config: Dict[str, Any] = {}
    storage_path_xlsx: Optional[str] = None
    storage_path_csv: Optional[str] = None
    full_storage_path: Optional[str] = None
    file_format: Optional[str] = "CSV"

    class Config:
        from_attributes = True

class BatchCommitRequest(BaseModel):
    skip_errors: bool = True

class BatchReviewRequest(BaseModel):
    decision: str  # APPROVED, RETURNED_FOR_CORRECTION, REJECTED
    notes: Optional[str] = "Adjudicated by AICTE central review committee."


class StagedRowResponse(BaseModel):
    id: int
    batch_id: int
    row_index: int
    apaar_id: Optional[str] = None
    student_name: Optional[str] = None
    programme_code: Optional[str] = None
    category: Optional[str] = "OPEN"
    gender: Optional[str] = "MALE"
    dob: Optional[str] = None
    admission_quota: Optional[str] = "STATE_GOVT"
    admission_date: Optional[str] = None
    merit_rank: Optional[int] = None
    status: str  # ELIGIBLE, REQUIRES_REVIEW, BLOCKING_ERROR, EXEMPTION_REQUESTED, EXEMPTED
    findings: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class StagedRowUpdateRequest(BaseModel):
    apaar_id: Optional[str] = None
    student_name: Optional[str] = None
    programme_code: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    admission_quota: Optional[str] = None
    admission_date: Optional[str] = None
    merit_rank: Optional[int] = None


class BatchQueryCreate(BaseModel):
    row_id: Optional[int] = None
    subject: str
    category: str = "MISSING_APAAR_UIDAI_FAIL"  # MISSING_APAAR_UIDAI_FAIL, QUOTA_DISPUTE, TECHNICAL_EXCEPTION, OTHER
    student_identifier: Optional[str] = None
    message: str


class BatchQueryResolveRequest(BaseModel):
    action: str  # APPROVE_EXEMPTION, REJECT_QUERY, REPLY_ONLY
    reply_message: str


class BatchQueryResponse(BaseModel):
    id: int
    batch_id: int
    row_id: Optional[int] = None
    institution_id: int
    raised_by_name: Optional[str] = None
    subject: str
    category: str
    student_identifier: Optional[str] = None
    message: str
    status: str
    aicte_reply: Optional[str] = None
    resolved_by_name: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class RawCsvUpdateRequest(BaseModel):
    csv_content: str


class QuickFixRequest(BaseModel):
    target_rule: Optional[str] = "RULE_UNKNOWN_PROGRAMME"
    replacement_value: Optional[str] = None


class CentralAdvisoryCreate(BaseModel):
    title: str
    idea_description: str
    advisory_type: Optional[str] = "PROGRAMME_REMAP_RECOMMENDATION"
    recommended_action: Optional[Dict[str, Any]] = {}


class CentralAdvisoryResponse(BaseModel):
    id: int
    batch_id: int
    institution_id: int
    title: str
    idea_description: str
    advisory_type: str
    recommended_action: Dict[str, Any] = {}
    status: str
    created_by_name: Optional[str] = None
    created_at: Optional[str] = None
    applied_at: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetGenerateRequest(BaseModel):
    institution_id: int
    count: int = 10
    mode: str = "CLEAN"  # "CLEAN" or "DISCREPANT"
    include_discrepancies: Optional[bool] = None
    academic_year: str = "2026-27"
    programme_code: Optional[str] = None


class DatasetExportRequest(BaseModel):
    institution_id: int
    format: str = "xlsx"  # "xlsx" or "csv"
    academic_year: str = "2026-27"
    rows: List[Dict[str, Any]]


class BatchFileInfoResponse(BaseModel):
    batch_id: int
    filename: str
    primary_format: str
    storage_path_xlsx: Optional[str] = None
    storage_path_csv: Optional[str] = None
    full_storage_path: Optional[str] = None
    download_url_xlsx: str
    download_url_csv: str
    xlsx_exists: bool = False
    csv_exists: bool = False
    xlsx_size_bytes: int = 0
    csv_size_bytes: int = 0

