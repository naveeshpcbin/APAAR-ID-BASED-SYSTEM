from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.api.v1 import (
    auth, institutions, approvals, uploads, admissions,
    conflicts, anomalies, verification, dashboards, reports, audit, health,
    reference_data
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
import os

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
configured_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
if not configured_origins:
    configured_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Pramaan-Security-Layer"] = "Ed25519-HMAC-SHA256-AuditChain-Active"
    response.headers["X-Privacy-Standard"] = "DPDP-Act-2023-Consent-Compliant"
    return response

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
app.include_router(reference_data.router, prefix=api_v1)

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": api_v1
    }
