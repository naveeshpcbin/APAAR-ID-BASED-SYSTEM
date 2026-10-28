import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

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
    BACKEND_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")).replace("\\", "/")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR}/pramaan.db")
    
    # Supabase Cloud Database & Registry Configuration
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", None)
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY", None)
    SUPABASE_DATABASE_URL: Optional[str] = os.getenv("SUPABASE_DATABASE_URL", None)
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_STORAGE_DIR: str = os.getenv("UPLOAD_STORAGE_DIR", "./storage/uploads")
    
    # Verifier settings
    VERIFIER_TOKEN_EXPIRY_DAYS: int = 30

settings = Settings()
