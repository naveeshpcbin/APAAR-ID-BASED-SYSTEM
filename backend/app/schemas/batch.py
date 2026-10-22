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

    class Config:
        from_attributes = True

class BatchCommitRequest(BaseModel):
    skip_errors: bool = True
