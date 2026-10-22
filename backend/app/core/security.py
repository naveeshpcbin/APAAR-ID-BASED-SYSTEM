import hmac
import hashlib
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Tuple
import jwt
import bcrypt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from app.core.config import settings

# Direct robust bcrypt password hashing (no passlib version bug)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Truncate at 72 bytes as per bcrypt specification
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

# JWT Creation & Verification
def create_access_token(subject: str | Any, role: str, institution_id: Optional[int] = None, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "institution_id": institution_id,
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Privacy-Aware Identifier Handling
def hash_apaar_id(apaar_id: str) -> str:
    """Computes keyed HMAC-SHA256 for deterministic matching without storing raw identifiers in indices."""
    cleaned = apaar_id.strip().replace(" ", "").replace("-", "")
    key = settings.HMAC_APAAR_KEY.encode("utf-8")
    h = hmac.new(key, cleaned.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()

def mask_apaar_id(apaar_id: str) -> str:
    """Masks 12-digit APAAR ID for authorized display: XXXXXXXX1234."""
    cleaned = apaar_id.strip().replace(" ", "").replace("-", "")
    if len(cleaned) == 12:
        return f"XXXXXXXX{cleaned[-4:]}"
    elif len(cleaned) > 4:
        return f"{'X' * (len(cleaned) - 4)}{cleaned[-4:]}"
    return "XXXXXXXXXXXX"

# Ed25519 Cryptographic Asymmetric Signatures for Verification Receipts
class ReceiptSigner:
    _instance = None
    _private_key: Optional[ed25519.Ed25519PrivateKey] = None
    _public_key: Optional[ed25519.Ed25519PublicKey] = None

    @classmethod
    def get_keys(cls) -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        if cls._private_key is None:
            # Deterministic prototype key for reproducible verification
            seed = hashlib.sha256(b"pramaan_aicte_ed25519_production_ready_signer_2026").digest()
            cls._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
            cls._public_key = cls._private_key.public_key()
        return cls._private_key, cls._public_key

    @classmethod
    def get_public_key_b64(cls) -> str:
        _, public_key = cls.get_keys()
        raw_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(raw_bytes).decode("utf-8")

    @classmethod
    def sign_payload(cls, canonical_payload: bytes) -> str:
        private_key, _ = cls.get_keys()
        signature = private_key.sign(canonical_payload)
        return base64.b64encode(signature).decode("utf-8")

    @classmethod
    def verify_signature(cls, canonical_payload: bytes, signature_b64: str) -> bool:
        try:
            _, public_key = cls.get_keys()
            sig_bytes = base64.b64decode(signature_b64)
            public_key.verify(sig_bytes, canonical_payload)
            return True
        except Exception:
            return False
