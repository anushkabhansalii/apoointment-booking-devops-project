"""SlotSync API - FastAPI application entry point."""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import appointments, catalog

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Appointment booking API for the SlotSync wellness studio.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointments.router)
app.include_router(catalog.router)

# Request count, latency histogram and in-progress gauge per route, served on
# /metrics. Probes and the metrics endpoint itself are excluded so they do not
# drown out real traffic in the dashboards.
Instrumentator(
    excluded_handlers=["/metrics", "/health", "/ready"],
    should_group_status_codes=False,
).instrument(app).expose(app, include_in_schema=False)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    """Liveness: the process is up and serving requests. Never touches the DB."""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the API can reach PostgreSQL and is safe to receive traffic."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any DB failure means not ready
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "database unavailable") from exc
    return {"status": "ready", "database": "ok"}
