"""Appointment CRUD, status changes and dashboard statistics."""

from collections import Counter as Tally
from datetime import UTC, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.catalog import SERVICES, STUDIO_TZ
from app.config import settings
from app.database import get_db
from app.metrics import APPOINTMENTS_CREATED, BOOKING_CONFLICTS, STATUS_CHANGES
from app.models import SLOT_HOLDING_STATUSES, Appointment, AppointmentStatus, Provider
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentStats,
    AppointmentUpdate,
    StatusUpdate,
)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _studio_day_bounds(day) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=STUDIO_TZ).astimezone(UTC)
    return start, start + timedelta(days=1)


def _get_or_404(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Appointment {appointment_id} not found")
    return appointment


def _check_provider(db: Session, provider_id: int) -> Provider:
    provider = db.get(Provider, provider_id)
    if provider is None or not provider.active:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Provider does not exist or is inactive")
    return provider


def _check_opening_hours(start: datetime, duration: int) -> None:
    local_start = start.astimezone(STUDIO_TZ)
    local_end = local_start + timedelta(minutes=duration)
    opens = local_start.replace(hour=settings.opening_hour, minute=0, second=0, microsecond=0)
    closes = local_start.replace(hour=settings.closing_hour, minute=0, second=0, microsecond=0)
    if local_start < opens or local_end > closes:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Appointments must fit between {settings.opening_hour:02d}:00 and "
            f"{settings.closing_hour:02d}:00 studio time",
        )


def _check_conflict(
    db: Session, provider_id: int, start: datetime, duration: int, ignore_id: int | None = None
) -> None:
    """Reject a booking that overlaps another slot-holding booking of the same provider."""
    end = start + timedelta(minutes=duration)
    # No booking is longer than 4 hours, so only that window can overlap.
    query = select(Appointment).where(
        Appointment.provider_id == provider_id,
        Appointment.status.in_(SLOT_HOLDING_STATUSES),
        Appointment.start_time < end,
        Appointment.start_time > start - timedelta(hours=4),
    )
    if ignore_id is not None:
        query = query.where(Appointment.id != ignore_id)
    for other in db.scalars(query):
        if _utc(other.start_time) < end and other.end_time > start:
            BOOKING_CONFLICTS.inc()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"{other.provider.name} is already booked from "
                f"{_utc(other.start_time).astimezone(STUDIO_TZ):%H:%M} to "
                f"{other.end_time.astimezone(STUDIO_TZ):%H:%M}",
            )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    db: Session = Depends(get_db),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    provider_id: int | None = None,
    day: str | None = Query(default=None, description="Studio-local date, YYYY-MM-DD"),
    search: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=200, ge=1, le=500),
):
    query = select(Appointment).order_by(Appointment.start_time)
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    if provider_id:
        query = query.where(Appointment.provider_id == provider_id)
    if day:
        try:
            parsed = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "day must be YYYY-MM-DD") from exc
        start, end = _studio_day_bounds(parsed)
        query = query.where(Appointment.start_time >= start, Appointment.start_time < end)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Appointment.customer_name.ilike(pattern),
                Appointment.customer_email.ilike(pattern),
                Appointment.service.ilike(pattern),
            )
        )
    return db.scalars(query.limit(limit)).unique().all()


@router.get("/stats", response_model=AppointmentStats)
def appointment_stats(db: Session = Depends(get_db)):
    appointments = db.scalars(select(Appointment)).unique().all()
    now = datetime.now(UTC)
    today_start, today_end = _studio_day_bounds(now.astimezone(STUDIO_TZ).date())

    by_status = Tally(a.status.value for a in appointments)
    holding = [a for a in appointments if a.status in SLOT_HOLDING_STATUSES]
    upcoming = sorted(
        (
            a
            for a in appointments
            if _utc(a.start_time) >= now and a.status in (AppointmentStatus.scheduled, AppointmentStatus.confirmed)
        ),
        key=lambda a: _utc(a.start_time),
    )
    finished = by_status["completed"] + by_status["no_show"]
    total = len(appointments)

    return AppointmentStats(
        total=total,
        today=sum(1 for a in holding if today_start <= _utc(a.start_time) < today_end),
        upcoming=len(upcoming),
        by_status={s.value: by_status.get(s.value, 0) for s in AppointmentStatus},
        by_service=dict(Tally(a.service for a in holding)),
        by_provider=dict(Tally(a.provider.name for a in holding)),
        completion_rate=round(by_status["completed"] / finished, 3) if finished else 0.0,
        cancellation_rate=round(by_status["cancelled"] / total, 3) if total else 0.0,
        booked_revenue=sum(SERVICES[a.service]["price"] for a in holding if a.service in SERVICES),
        next_appointment=upcoming[0] if upcoming else None,
    )


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, appointment_id)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    _check_provider(db, payload.provider_id)
    duration = payload.duration_minutes or SERVICES[payload.service]["duration"]
    _check_opening_hours(payload.start_time, duration)
    _check_conflict(db, payload.provider_id, payload.start_time, duration)

    appointment = Appointment(**payload.model_dump(exclude={"duration_minutes"}), duration_minutes=duration)
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    APPOINTMENTS_CREATED.labels(service=appointment.service).inc()
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = _get_or_404(db, appointment_id)
    changes = payload.model_dump(exclude_unset=True)
    if "service" in changes and "duration_minutes" not in changes:
        changes["duration_minutes"] = SERVICES[changes["service"]]["duration"]

    provider_id = changes.get("provider_id", appointment.provider_id)
    start = changes.get("start_time", _utc(appointment.start_time))
    duration = changes.get("duration_minutes", appointment.duration_minutes)
    new_status = changes.get("status", appointment.status)

    if "provider_id" in changes:
        _check_provider(db, provider_id)
    if {"start_time", "duration_minutes", "service"} & changes.keys():
        _check_opening_hours(start, duration)
    if new_status in SLOT_HOLDING_STATUSES and (
        {"provider_id", "start_time", "duration_minutes", "service"} & changes.keys()
        or appointment.status == AppointmentStatus.cancelled
    ):
        _check_conflict(db, provider_id, start, duration, ignore_id=appointment.id)

    if "status" in changes and changes["status"] != appointment.status:
        STATUS_CHANGES.labels(status=changes["status"].value).inc()
    for field, value in changes.items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def change_status(appointment_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    return update_appointment(appointment_id, AppointmentUpdate(status=payload.status), db)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = _get_or_404(db, appointment_id)
    db.delete(appointment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
