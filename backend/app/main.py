from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import (
    auth, institutions, approvals, uploads, admissions,
    conflicts, anomalies, verification, dashboards, reports, audit, health
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "PRAMAAN-AICTE: Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network. "
        "SIH 2026 Problem Statement SIH26263."
    ),
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routers
api_v1 = settings.API_V1_STR
app.include_router(health.router, prefix=api_v1)
app.include_router(auth.router, prefix=api_v1)
app.include_router(institutions.router, prefix=api_v1)
app.include_router(approvals.router, prefix=api_v1)
app.include_router(uploads.router, prefix=api_v1)
app.include_router(admissions.router, prefix=api_v1)
app.include_router(conflicts.router, prefix=api_v1)
app.include_router(anomalies.router, prefix=api_v1)
app.include_router(verification.router, prefix=api_v1)
app.include_router(dashboards.router, prefix=api_v1)
app.include_router(reports.router, prefix=api_v1)
app.include_router(audit.router, prefix=api_v1)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": api_v1
    }
