"""Pydantic request/response models."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.catalog import SERVICES, STUDIO_TZ
from app.models import AppointmentStatus


def _as_studio_time(value: datetime) -> datetime:
    """Treat a naive datetime as studio-local time (what a booking form sends)
    and normalise everything to UTC before it reaches the database."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=STUDIO_TZ)
    return value.astimezone(UTC)


def _as_utc(value: datetime) -> datetime:
    """SQLite (used by the tests) hands back naive datetimes; they are UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: str
    color: str
    active: bool


class ServiceOut(BaseModel):
    name: str
    duration: int
    price: int


class AppointmentBase(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_phone: str | None = Field(default=None, max_length=32)
    service: str
    provider_id: int = Field(gt=0)
    start_time: datetime
    duration_minutes: int | None = Field(default=None, ge=15, le=240)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("customer_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("customer name is too short")
        return value

    @field_validator("service")
    @classmethod
    def known_service(cls, value: str) -> str:
        if value not in SERVICES:
            raise ValueError(f"unknown service; choose one of {sorted(SERVICES)}")
        return value

    @field_validator("start_time")
    @classmethod
    def localise(cls, value: datetime) -> datetime:
        return _as_studio_time(value)


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    """Full or partial update; only the fields sent are changed."""

    customer_name: str | None = Field(default=None, min_length=2, max_length=120)
    customer_email: EmailStr | None = None
    customer_phone: str | None = Field(default=None, max_length=32)
    service: str | None = None
    provider_id: int | None = Field(default=None, gt=0)
    start_time: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=240)
    status: AppointmentStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("service")
    @classmethod
    def known_service(cls, value: str | None) -> str | None:
        if value is not None and value not in SERVICES:
            raise ValueError(f"unknown service; choose one of {sorted(SERVICES)}")
        return value

    @field_validator("start_time")
    @classmethod
    def localise(cls, value: datetime | None) -> datetime | None:
        return _as_studio_time(value) if value else value


class StatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_email: str
    customer_phone: str | None
    service: str
    provider_id: int
    provider: ProviderOut
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    status: AppointmentStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("start_time", "end_time", "created_at", "updated_at")
    @classmethod
    def utc(cls, value: datetime) -> datetime:
        return _as_utc(value)


class AppointmentStats(BaseModel):
    total: int
    today: int
    upcoming: int
    by_status: dict[str, int]
    by_service: dict[str, int]
    by_provider: dict[str, int]
    completion_rate: float
    cancellation_rate: float
    booked_revenue: int
    next_appointment: AppointmentOut | None
