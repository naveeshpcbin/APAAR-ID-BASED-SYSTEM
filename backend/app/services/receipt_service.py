import json
import uuid
import hashlib
import io
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import qrcode
from sqlalchemy.orm import Session

from app.models import VerificationReceipt, AdmissionRecord, StudentIdentity, Institution, Programme, ConsentGrant
from app.core.security import ReceiptSigner
from app.core.hash_chain import append_audit_event
from app.core.config import settings

class ReceiptService:
    @staticmethod
    def generate_qr_base64(target_url: str) -> str:
        """Generates a high-contrast QR code as a base64 PNG data URI."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

    @staticmethod
    def issue_receipt(
        db: Session,
        admission_id: int,
        expiry_days: int = 30,
        claim_scope: str = "ACTIVE_ENROLMENT_STATUS",
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = "verifier@aicte.gov.in",
        actor_role: str = "INSTITUTION_NODAL"
    ) -> Dict[str, Any]:
        adm = db.query(AdmissionRecord).filter(AdmissionRecord.id == admission_id).first()
        if not adm:
            raise ValueError(f"Admission record #{admission_id} not found.")

        student = db.query(StudentIdentity).filter(StudentIdentity.id == adm.student_id).first()
        inst = db.query(Institution).filter(Institution.id == adm.institution_id).first()
        prog = db.query(Programme).filter(Programme.id == adm.programme_id).first()

        receipt_token = f"rcpt_{uuid.uuid4().hex}"
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expiry_days)

        canonical_dict = {
            "token": receipt_token,
            "issuer": "PRAMAAN-AICTE-NATIONAL-REGISTRY",
            "claim_scope": claim_scope,
            "institution_name": inst.name if inst else "Unknown Institution",
            "aicte_id": inst.aicte_id if inst else "N/A",
            "programme_name": prog.programme_name if prog else "N/A",
            "programme_code": prog.programme_code if prog else "N/A",
            "academic_year": adm.academic_year,
            "enrollment_no": adm.enrollment_no,
            "student_name": student.full_name if student else "N/A",
            "apaar_masked": student.apaar_masked if student else "XXXXXXXXXXXX",
            "enrolment_status": adm.status,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }

        canonical_bytes = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_digest = hashlib.sha256(canonical_bytes).hexdigest()
        ed25519_sig = ReceiptSigner.sign_payload(canonical_bytes)

        receipt = VerificationReceipt(
            receipt_token=receipt_token,
            student_id=adm.student_id,
            admission_record_id=adm.id,
            claim_scope=claim_scope,
            ed25519_signature=ed25519_sig,
            payload_digest=payload_digest,
            canonical_payload=canonical_dict,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

        append_audit_event(
            db=db,
            action="RECEIPT_ISSUED",
            entity_type="VerificationReceipt",
            entity_id=str(receipt.id),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            metadata_json={
                "receipt_token": receipt_token,
                "admission_id": adm.id,
                "student_masked": student.apaar_masked if student else "N/A",
                "expires_at": expires_at.isoformat()
            }
        )

        verification_url = f"/verification/receipt/{receipt_token}"
        qr_data_uri = ReceiptService.generate_qr_base64(verification_url)

        return {
            "receipt_token": receipt_token,
            "verification_url": verification_url,
            "qr_code_base64": qr_data_uri,
            "ed25519_public_key": ReceiptSigner.get_public_key_b64(),
            "payload_digest": payload_digest,
            "signature": ed25519_sig,
            "canonical_payload": canonical_dict,
            "expires_at": expires_at.isoformat()
        }

    @staticmethod
    def verify_receipt(
        db: Session,
        receipt_token: str
    ) -> Dict[str, Any]:
        receipt = db.query(VerificationReceipt).filter(VerificationReceipt.receipt_token == receipt_token).first()
        if not receipt:
            return {
                "is_valid": False,
                "status": "NOT_FOUND",
                "message": "Verification receipt token was not found in the central registry."
            }

        now = datetime.utcnow()
        if receipt.is_revoked:
            return {
                "is_valid": False,
                "status": "REVOKED",
                "message": f"This receipt was revoked by the issuing authority. Reason: {receipt.revocation_reason or 'Administrative revocation'}.",
                "revocation_reason": receipt.revocation_reason,
                "revoked_at": receipt.expires_at.isoformat(),
                "canonical_payload": receipt.canonical_payload
            }

        if now > receipt.expires_at:
            return {
                "is_valid": False,
                "status": "EXPIRED",
                "message": f"This verification receipt expired on {receipt.expires_at.strftime('%d-%b-%Y')}.",
                "canonical_payload": receipt.canonical_payload
            }

        # DPDP Act 2023: Check student consent status
        if receipt.student_id:
            latest_consent = db.query(ConsentGrant).filter(
                ConsentGrant.student_id == receipt.student_id
            ).order_by(ConsentGrant.created_at.desc()).first()
            
            if latest_consent and not latest_consent.is_granted:
                return {
                    "is_valid": False,
                    "status": "CONSENT_REVOKED",
                    "message": "Verification denied: Student has explicitly revoked academic verification consent under DPDP Act 2023.",
                    "canonical_payload": {
                        "token": receipt.receipt_token,
                        "student_name": "[PROTECTED - CONSENT WITHDRAWN]",
                        "apaar_masked": "XXXXXXXXXXXX",
                        "institution_name": receipt.canonical_payload.get("institution_name", "Confidential"),
                        "claim_scope": "RESTRICTED"
                    }
                }

        # Cryptographically verify the Ed25519 signature
        canonical_bytes = json.dumps(receipt.canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        is_sig_valid = ReceiptSigner.verify_signature(canonical_bytes, receipt.ed25519_signature)

        if not is_sig_valid:
            return {
                "is_valid": False,
                "status": "INVALID_SIGNATURE",
                "message": "Cryptographic signature validation failed. Payload integrity cannot be guaranteed."
            }

        return {
            "is_valid": True,
            "status": "AUTHENTIC_AND_VERIFIED",
            "message": "Cryptographic Ed25519 digital signature verified. Record is authentic, currently active, and authorized under DPDP Act 2023 student consent.",
            "canonical_payload": receipt.canonical_payload,
            "signature": receipt.ed25519_signature,
            "payload_digest": receipt.payload_digest,
            "public_key": ReceiptSigner.get_public_key_b64(),
            "expires_at": receipt.expires_at.isoformat(),
            "consent_status": "ACTIVE_GRANTED"
        }

    @staticmethod
    def revoke_receipt(
        db: Session,
        receipt_token: str,
        reason: str,
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = "admin@aicte.gov.in"
    ) -> Dict[str, Any]:
        receipt = db.query(VerificationReceipt).filter(VerificationReceipt.receipt_token == receipt_token).first()
        if not receipt:
            raise ValueError("Receipt not found.")

        receipt.is_revoked = True
        receipt.revocation_reason = reason
        db.commit()

        append_audit_event(
            db=db,
            action="RECEIPT_REVOKED",
            entity_type="VerificationReceipt",
            entity_id=str(receipt.id),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role="AICTE_ADMIN",
            metadata_json={
                "receipt_token": receipt_token,
                "revocation_reason": reason
            }
        )

        return {
            "receipt_token": receipt_token,
            "is_revoked": True,
            "revocation_reason": reason
        }

    @staticmethod
    def get_student_consent(db: Session, student_id: int) -> Dict[str, Any]:
        latest = db.query(ConsentGrant).filter(
            ConsentGrant.student_id == student_id
        ).order_by(ConsentGrant.created_at.desc()).first()
        if not latest:
            # By default, verified admissions are created with initial implicit consent, but we make it explicit
            return {
                "student_id": student_id,
                "is_granted": True,
                "consent_type": "APAAR_IDENTITY_VERIFICATION",
                "granted_by": "STUDENT",
                "grant_timestamp": datetime.utcnow().isoformat(),
                "status": "DEFAULT_GRANTED"
            }
        return {
            "student_id": student_id,
            "id": latest.id,
            "is_granted": latest.is_granted,
            "consent_type": latest.consent_type,
            "granted_by": latest.granted_by,
            "grant_timestamp": latest.grant_timestamp.isoformat(),
            "status": "EXPLICIT_GRANTED" if latest.is_granted else "REVOKED"
        }

    @staticmethod
    def set_student_consent(
        db: Session,
        student_id: int,
        is_granted: bool,
        consent_type: str = "APAAR_IDENTITY_VERIFICATION",
        granted_by: str = "STUDENT",
        ip_address: Optional[str] = None,
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = "student@aicte.gov.in",
        actor_role: str = "STUDENT"
    ) -> Dict[str, Any]:
        student = db.query(StudentIdentity).filter(StudentIdentity.id == student_id).first()
        if not student:
            raise ValueError(f"Student identity #{student_id} not found.")

        grant = ConsentGrant(
            student_id=student_id,
            consent_type=consent_type,
            granted_by=granted_by,
            is_granted=is_granted,
            ip_address=ip_address,
            grant_timestamp=datetime.utcnow()
        )
        db.add(grant)
        db.commit()
        db.refresh(grant)

        # Chained audit event
        append_audit_event(
            db=db,
            action="CONSENT_UPDATED" if is_granted else "CONSENT_REVOKED",
            entity_type="ConsentGrant",
            entity_id=str(grant.id),
            actor_id=actor_id,
            actor_email=actor_email,
            actor_role=actor_role,
            metadata_json={
                "student_id": student_id,
                "is_granted": is_granted,
                "consent_type": consent_type,
                "granted_by": granted_by
            }
        )

        return {
            "id": grant.id,
            "student_id": student_id,
            "consent_type": grant.consent_type,
            "granted_by": grant.granted_by,
            "is_granted": grant.is_granted,
            "grant_timestamp": grant.grant_timestamp,
            "message": "Student verification consent granted successfully." if is_granted else "Student verification consent revoked. External verifier queries will be blocked under DPDP Act 2023."
        }
