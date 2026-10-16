"""Block until the database accepts connections (used by the container entrypoint).

On Kubernetes the API and PostgreSQL start at the same time; waiting here
avoids a crash-loop of failed migrations while Postgres initialises.
    python -m app.wait_for_db
"""

import os
import sys
import time

from sqlalchemy import create_engine, text

from app.config import settings


def wait(url: str, timeout: float, interval: float = 2.0) -> bool:
    connect_args = {} if url.startswith("sqlite") else {"connect_timeout": 3}
    engine = create_engine(url, connect_args=connect_args)
    deadline = time.monotonic() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database is ready (attempt {attempt})", flush=True)
            return True
        except Exception as exc:  # noqa: BLE001 - any failure means "not yet"
            if time.monotonic() >= deadline:
                print(f"Database still unavailable after {timeout:.0f}s: {exc}", file=sys.stderr, flush=True)
                return False
            print(f"Waiting for database (attempt {attempt}): {type(exc).__name__}", flush=True)
            time.sleep(interval)
        finally:
            engine.dispose()


if __name__ == "__main__":
    sys.exit(0 if wait(settings.database_url, float(os.getenv("DB_WAIT_SECONDS", "90"))) else 1)
