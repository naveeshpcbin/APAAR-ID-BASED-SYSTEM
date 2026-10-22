import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import AuditEvent

GENESIS_HASH = "0" * 64

def calculate_event_hash(
    sequence_no: int,
    actor_email: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    metadata_json: Dict[str, Any],
    correlation_id: str,
    previous_hash: str
) -> str:
    """Calculates canonical SHA-256 hash for an audit ledger event."""
    # Ensure deterministic json serialization
    sorted_meta = json.dumps(metadata_json, sort_keys=True, separators=(",", ":"))
    payload = f"{sequence_no}|{actor_email or 'system'}|{action}|{entity_type}|{entity_id}|{sorted_meta}|{correlation_id}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = "system",
    actor_role: str = "SYSTEM",
    metadata_json: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> AuditEvent:
    """Appends an event to the tamper-evident hash chain ledger."""
    if metadata_json is None:
        metadata_json = {}
    if correlation_id is None:
        import uuid
        correlation_id = str(uuid.uuid4())

    # Get last event in chain
    last_event = db.query(AuditEvent).order_by(AuditEvent.sequence_no.desc()).first()
    if last_event:
        seq = last_event.sequence_no + 1
        prev_hash = last_event.current_hash
    else:
        seq = 1
        prev_hash = GENESIS_HASH

    curr_hash = calculate_event_hash(
        sequence_no=seq,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata_json=metadata_json,
        correlation_id=correlation_id,
        previous_hash=prev_hash
    )

    event = AuditEvent(
        sequence_no=seq,
        actor_id=actor_id,
        actor_email=actor_email,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata_json=metadata_json,
        correlation_id=correlation_id,
        previous_hash=prev_hash,
        current_hash=curr_hash
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def verify_hash_chain_integrity(db: Session) -> Dict[str, Any]:
    """
    Verifies cryptographic integrity of the entire audit event hash chain.
    Returns status, verified event count, and any compromised index.
    """
    events = db.query(AuditEvent).order_by(AuditEvent.sequence_no.asc()).all()
    if not events:
        return {
            "is_valid": True,
            "total_events": 0,
            "head_hash": GENESIS_HASH,
            "message": "Audit ledger is empty (genesis state)."
        }

    expected_prev = GENESIS_HASH
    for ev in events:
        if ev.previous_hash != expected_prev:
            return {
                "is_valid": False,
                "total_events": len(events),
                "broken_at_sequence": ev.sequence_no,
                "reason": f"Previous hash mismatch at sequence {ev.sequence_no}. Expected {expected_prev}, found {ev.previous_hash}",
                "event_id": ev.id
            }

        recomputed = calculate_event_hash(
            sequence_no=ev.sequence_no,
            actor_email=ev.actor_email,
            action=ev.action,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            metadata_json=ev.metadata_json or {},
            correlation_id=ev.correlation_id,
            previous_hash=ev.previous_hash
        )

        if recomputed != ev.current_hash:
            return {
                "is_valid": False,
                "total_events": len(events),
                "broken_at_sequence": ev.sequence_no,
                "reason": f"Cryptographic integrity failed at sequence {ev.sequence_no}. Event data or hash altered.",
                "event_id": ev.id
            }

        expected_prev = ev.current_hash

    return {
        "is_valid": True,
        "total_events": len(events),
        "head_hash": events[-1].current_hash,
        "message": f"Successfully verified unbroken cryptographic integrity of {len(events)} audit events."
    }
