"""Shared fixtures.

Every test gets a brand-new in-memory SQLite database, so tests never touch
the real PostgreSQL instance and cannot leak state into each other.
"""

import os

# Must be set before the app (and its engine) is imported.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Provider  # noqa: E402

PROVIDERS = [
    Provider(name="Aarav Mehta", specialty="Yoga & Pilates", color="#6366f1"),
    Provider(name="Diya Sharma", specialty="Physiotherapy", color="#10b981"),
    Provider(name="Retired Person", specialty="Massage Therapy", color="#999999", active=False),
]


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    session.add_all([Provider(name=p.name, specialty=p.specialty, color=p.color, active=p.active) for p in PROVIDERS])
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def booking():
    """A valid booking payload; tests tweak individual fields."""

    def make(**overrides):
        payload = {
            "customer_name": "Riya Kapoor",
            "customer_email": "riya@example.com",
            "customer_phone": "+91 98765 43210",
            "service": "Yoga Session",
            "provider_id": 1,
            "start_time": "2030-01-15T10:00:00",
            "notes": "First visit",
        }
        payload.update(overrides)
        return payload

    return make
