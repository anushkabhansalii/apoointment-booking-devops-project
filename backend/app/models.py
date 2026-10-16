"""Database tables.

providers     - the practitioners customers can book (yoga teacher, physio...)
appointments  - a booked time slot with one provider
"""

import enum
from datetime import UTC, datetime, timedelta

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class AppointmentStatus(enum.StrEnum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


# A cancelled booking frees its slot; every other status keeps it occupied.
SLOT_HOLDING_STATUSES = (
    AppointmentStatus.scheduled,
    AppointmentStatus.confirmed,
    AppointmentStatus.completed,
    AppointmentStatus.no_show,
)


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    specialty: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="provider")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(254), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(32))
    service: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.scheduled,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    provider: Mapped[Provider] = relationship(back_populates="appointments", lazy="joined")

    @property
    def end_time(self) -> datetime:
        start = self.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        return start + timedelta(minutes=self.duration_minutes)
