from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings

router = APIRouter(tags=["Health & Readiness"])

@router.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "CONNECTED"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"

    return {
        "status": "READY" if db_status == "CONNECTED" else "DEGRADED",
        "database": db_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
