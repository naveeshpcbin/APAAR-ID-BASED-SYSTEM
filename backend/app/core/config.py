import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PRAMAAN-AICTE"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "pramaan_aicte_dev_secret_key_sih2026_secure_random_change_in_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # HMAC key for keyed identifier hashing (preventing rainbow tables)
    HMAC_APAAR_KEY: str = os.getenv("HMAC_APAAR_KEY", "pramaan_apaar_hmac_salt_2026_confidential")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pramaan.db")
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_STORAGE_DIR: str = os.getenv("UPLOAD_STORAGE_DIR", "./storage/uploads")
    
    # Verifier settings
    VERIFIER_TOKEN_EXPIRY_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
