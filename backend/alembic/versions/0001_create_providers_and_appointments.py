"""create providers and appointments tables

Revision ID: 0001
Revises:
Create Date: 2026-10-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

appointment_status = sa.Enum("scheduled", "confirmed", "completed", "cancelled", "no_show", name="appointment_status")


def upgrade() -> None:
    providers = op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("specialty", sa.String(80), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(120), nullable=False),
        sa.Column("customer_email", sa.String(254), nullable=False),
        sa.Column("customer_phone", sa.String(32)),
        sa.Column("service", sa.String(80), nullable=False),
        sa.Column(
            "provider_id",
            sa.Integer(),
            sa.ForeignKey("providers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("status", appointment_status, nullable=False, server_default="scheduled"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("duration_minutes BETWEEN 15 AND 240", name="ck_appointments_duration"),
    )
    op.create_index("ix_appointments_provider_id", "appointments", ["provider_id"])
    op.create_index("ix_appointments_start_time", "appointments", ["start_time"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    # The studio's practitioners. Seeded here so a fresh database is usable
    # immediately after `alembic upgrade head`.
    op.bulk_insert(
        providers,
        [
            {"name": "Aarav Mehta", "specialty": "Yoga & Pilates", "color": "#6366f1", "active": True},
            {"name": "Diya Sharma", "specialty": "Physiotherapy", "color": "#10b981", "active": True},
            {"name": "Kabir Rao", "specialty": "Massage Therapy", "color": "#f59e0b", "active": True},
            {"name": "Meera Iyer", "specialty": "Nutrition", "color": "#ec4899", "active": True},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_start_time", table_name="appointments")
    op.drop_index("ix_appointments_provider_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("providers")
    appointment_status.drop(op.get_bind(), checkfirst=True)
