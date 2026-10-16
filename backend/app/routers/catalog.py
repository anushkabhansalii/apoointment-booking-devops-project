"""Read-only lookups the booking form needs: providers and services."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog import SERVICES
from app.database import get_db
from app.models import Provider
from app.schemas import ProviderOut, ServiceOut

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/providers", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return db.scalars(select(Provider).where(Provider.active.is_(True)).order_by(Provider.name)).all()


@router.get("/services", response_model=list[ServiceOut])
def list_services():
    return [ServiceOut(name=name, **details) for name, details in SERVICES.items()]
