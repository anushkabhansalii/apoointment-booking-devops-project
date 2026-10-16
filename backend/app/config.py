"""Runtime configuration, read from environment variables.

Everything that changes between laptop, CI and Kubernetes lives here so the
rest of the code never touches os.environ directly.
"""

import os
from dataclasses import dataclass, field


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "SlotSync API"
    app_version: str = os.getenv("APP_VERSION", "dev")
    environment: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://slotsync:slotsync@localhost:5432/slotsync",
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _split(os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"))
    )
    # Opening hours of the studio, used to validate bookings (24h clock).
    opening_hour: int = int(os.getenv("OPENING_HOUR", "7"))
    closing_hour: int = int(os.getenv("CLOSING_HOUR", "21"))


settings = Settings()
