from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class AuditEventResponse(BaseModel):
    id: int
    sequence_no: int
    actor_email: Optional[str] = None
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    metadata_json: Dict[str, Any] = {}
    correlation_id: str
    previous_hash: str
    current_hash: str
    created_at: datetime

    class Config:
        from_attributes = True

class HashChainVerificationResponse(BaseModel):
    is_valid: bool
    total_events: int
    head_hash: Optional[str] = None
    broken_at_sequence: Optional[int] = None
    reason: Optional[str] = None
    message: str
